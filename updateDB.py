import pandas as pd
import numpy as np
import QueryOptionsDB as qdb
import datetime as dte
import pymongo as mndb
import warnings

from bson.objectid import ObjectId
from tqdm import tqdm

from sklearn.cluster import OPTICS
from sklearn.preprocessing import StandardScaler, QuantileTransformer

## Use OPTICS clustering to remove stock splits, good for convex clusters
def categoricalSplits(ticker, db):

    # Query mongoDB collection corresponding to input ticker
    tickerData = db[ticker]
    # Only pull the id and option chains
    tickerDataQry = tickerData.find({},{'callData','putData'})
    
    # print("Updating DB for %s" % ticker)    

    # Iterate through query and assign option chain to a dataframe
    for item in tqdm(tickerDataQry):
        try:
            # print("Updating DB for %s" % item['_id'])    
            callDF = pd.DataFrame.from_records(item['callData'])
            putDF = pd.DataFrame.from_records(item['putData'])


            X = callDF[['Ask','Strike']]

            # Normalize via quantile transform to a gaissan distribution, normalize magnitude of ask, strike to 0-1
            # X_normalized = pd.concat([callDF['Ask'], callDF['Strike']/callDF['Strike'].max()],axis=1)
            quantile_transformer = QuantileTransformer(output_distribution='normal', random_state=0)

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
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

            # Clean the DB, remove improperly categorized contracts
            callDF = callDF[~callDF['Contract Name'].str.contains(ticker+".*P.*", regex=True)]
            putDF = putDF[~putDF['Contract Name'].str.contains(ticker+".*C.*", regex=True)]

            # Extract expiries and match put option chain outliers and splits based on call expiries and strikes
            callExpiry =  pd.to_datetime(qdb.extractExpiryFromContractName(callDF["Contract Name"], ticker, isCall=True))
            # putExpiry =  pd.to_datetime(qdb.extractExpiryFromContractName(putDF["Contract Name"], ticker, isCall=False))

            # Match Call option clustering, more efficient and easier to identify than put clusters
            putDF['SplitLogic'] = 'current'
            try:
                putDF.loc[(~callExpiry.isin(callDF[clust.labels_ == 1])) &
                    (~putDF['Strike'].isin(callDF[clust.labels_ == 1]['Strike'])), 'SplitLogic'] = 'lastSplit'
                
                putDF.loc[(~callExpiry.isin(callDF[clust.labels_ == -1])) &
                    (~putDF['Strike'].isin(callDF[clust.labels_ == -1]['Strike'])), 'SplitLogic'] = 'outlier'
            except Exception as e:
                print('Put/Call option chain mismatch, data should be dropped')
                putDF['SplitLogic'] = 'outlier'
                print(e)
            
            # Use pymongo UPDATE MANY to replace array in db with new data frames
            idQuery = { "_id" :  item['_id']}
            updateCalls = tickerData.update_many(idQuery, {"$set":{"callData":callDF.to_dict("records")}})
            updatePuts  = tickerData.update_many(idQuery, {"$set":{"putData":putDF.to_dict("records")}})

            # print(updateCalls.raw_result)
            # print(updatePuts.raw_result)

        except Exception as e: 
            print(e)
            print("Failed to update for DB entry %s" % item('_id'))
            # putDF.to_csv('testOutputPuts.csv')
            # callDF.to_csv('testOutputCalls.csv')



if __name__ == "__main__":
    # Making a Connection with MongoClient
    client = mndb.MongoClient("mongodb://localhost:27017")
    # database
    opDB = client["optionsDB_2023"]

    tickerList = opDB.list_collection_names()

    for ticker in tqdm(tickerList):
        categoricalSplits(ticker, opDB)


