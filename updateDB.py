import pandas as pd
import numpy as np
import QueryYF as qyf
import QueryOptionsDB as qdb
import datetime as dte
import pymongo as mndb
from bson.objectid import ObjectId


from sklearn.cluster import OPTICS
from sklearn.preprocessing import StandardScaler, QuantileTransformer


# Making a Connection with MongoClient
client = mndb.MongoClient("mongodb://localhost:27017")
# database
opDB = client["optionsDB_2023"]

tickerList = opDB.list_collection_names()

def categoricalSplits(ticker, db):

    # Query mongoDB collection corresponding to input ticker
    tickerData = opDB[ticker]
    # Only pull the id and option chains
    tickerDataQry = tickerData.find({},{'callData','putData'})

    # Iterate through query and assign option chain to a dataframe
    for item in tickerDataQry:

        callDF = pd.DataFrame.from_records(item.callData)
        putDF = pd.DataFrame.from_records(item.putData)


        X = callDF[['Ask','Strike']]

        # Normalize via quantile transform to a gaissan distribution, normalize magnitude of ask, strike to 0-1
        # X_normalized = pd.concat([callDF['Ask'], callDF['Strike']/callDF['Strike'].max()],axis=1)
        quantile_transformer = QuantileTransformer(output_distribution='normal', random_state=0)
        X_trans = quantile_transformer.fit_transform(X)
        X_normalized = StandardScaler().fit_transform(X_trans)

        # Use OPTICS clustering to identify stock splits and outliers
        # Manual hyper-paremeter optimization using Jupyter notebook
        clust = OPTICS(min_samples=7, xi=0.05, min_cluster_size=0.1)

        # Run the fit
        clust.fit(X_normalized)

        # Verbose output options, review clustering output
        # space = np.arange(len(X))
        # reachability = clust.reachability_[clust.ordering_]
        # labels = clust.labels_[clust.ordering_]

        # Assume maximum of 3 groups for now, can update later 
        callDF['SplitLogic'] = 'current'
        callDF.loc[clust.labels_ == 1, 'SplitLogic'] = 'lastSplit'
        callDF.loc[clust.labels_ == -1, 'SplitLogic']  = 'outlier'


        # Match Call option clustering, more efficient and easier to identify than put clusters
        putDF['SplitLogic'] = 'current'
        putDF.loc[(~putDF['Expiry'].isin(callDF[clust.labels_ == 1]['Expiry'])) &
               (~putDF['Strike'].isin(callDF[clust.labels_ == 1]['Strike'])), 'SplitLogic'] = 'lastSplit'
        
        putDF.loc[(~putDF['Expiry'].isin(callDF[clust.labels_ == -1]['Expiry'])) &
               (~putDF['Strike'].isin(callDF[clust.labels_ == -1]['Strike'])), 'SplitLogic'] = 'outlier'
