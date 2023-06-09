# -*- coding: utf-8 "-*-

"""
Scrape Options Data from Yahoo Finance, add to MongoDB

"""

from yahoo_fin import stock_info as si
import yahoo_fin.options as ops
#import matplotlib as plt
import pandas as pd
#import numpy as np
import datetime as dte
import time
from itertools import chain
import pymongo as mndb

from sklearn.cluster import OPTICS
from sklearn.preprocessing import StandardScaler, QuantileTransformer
import warnings

import QueryOptionsDB as qdb


# def main():    

def scrapeOptionsData(ticker):
    # [DOW,QQQ,OTC,SPY] = getTickers()
  
    currentTime = dte.datetime.utcnow()
    
    # Making a Connection with MongoClient
    client = mndb.MongoClient("mongodb://localhost:27017/")
    # database
    opDB = client["optionsDB_2023"]
    # collection
    dTicker = opDB[ticker]
    
    price = si.get_live_price(ticker)
    
    [Calls,Puts,opReqCount] = getOptionsData(ticker)
    Calls.reset_index(inplace=True)
    Puts.reset_index(inplace=True)

    [CallsClean, CleanPuts] = cleanOptTables(Calls,Puts,ticker)

    callsDict = CallsClean.to_dict("records")
    putsDict = CleanPuts.to_dict("records")
    
    tickerData = {"timestamp":currentTime,"price":price,
                       "callData":callsDict,"putData":putsDict}
    dTicker.insert_one(tickerData)
    
    yReqCount = opReqCount + 1
    
    return(price, yReqCount)
    
def getTickers(getDOW,getQQQ,getSPY,getOTC,getTop):
    
    if getDOW == True:
        DOW = si.tickers_dow()
        DOW = [sub.replace('.','-') for sub in DOW] 
    else:
        DOW = []
        print("No request for DOW, list empty")
        
    if getQQQ == True:
        QQQ = si.tickers_nasdaq()
        QQQ = [sub.replace('.','-') for sub in QQQ] 
    else:
        QQQ = []
        print("No request for NASDAQ, list empty")
        
    if getSPY == True:
        SPY = si.tickers_sp500()
        SPY = [sub.replace('.','-') for sub in SPY] 
    else:
        SPY = []
        print("No request for S&P500, list empty")

    if getOTC == True:
        OTC = si.tickers_other()
        OTC = [sub.replace('.','-') for sub in OTC] 
    else:
        OTC = []
        print("No request for pink sheets, list empty")
         
    if getTop == True:
        TopData = si.get_day_most_active()
        TopTickers = TopData["Symbol"].tolist()
    else:
        TopTickers = []
        print("No request for top volume tickers")
    
    # print(len(allTickers))
    return(DOW,QQQ,OTC,SPY,TopTickers)

def sortTickersByCap(listOfTickers):
    MktCap = []
    for ticker in listOfTickers:
        #print(ticker)
        try:
            temp = si.get_stats_valuation(ticker)
            time.sleep(10)
            temp = temp.iloc[0,1]
            suffix = temp[-1]
            if suffix == "M":
                temp = float(temp.split(temp[-1])[0])*10e6
            elif suffix == "B":
                temp = float(temp.split(temp[-1])[0])*10e9
            elif suffix == "T":
                temp = float(temp.split(temp[-1])[0])*10e12
            else:
                temp = temp
            MktCap.append(temp)
        except IndexError as e:
            print("Error: %s" % e)
            print("Couldn't find ticker %s" % ticker )
            continue
        except Exception as u:
            print("Error: %s" % u)
            print("Hit unknown error at ticker: %s" % ticker)
            continue
        
    mktCapDict = dict(zip(listOfTickers,MktCap))
    sortedTickers = pd.DataFrame.from_dict(data = mktCapDict,orient="index")
    sortedTickers.reset_index(inplace=True)
    sortedTickers.columns = ["Ticker","Market Cap"]
    sortedTickers.sort_values(by=["Market Cap"])
    print(sortedTickers)
    return(sortedTickers)

def concatTickers(listOfTickers):
    tmpTickers = list(chain(*listOfTickers))
    tmpTickset = set(tmpTickers)
    allTickers = list(tmpTickset)
    return(allTickers)

def getOptionsData(opTicker):
    expDates = ops.get_expiration_dates(opTicker)
    expDateIsoFmt = [dte.datetime.strptime(rawDate, '%B %d, %Y') for rawDate in expDates]
    AllCalls = pd.DataFrame()
    AllPuts  = pd.DataFrame()
    
    reqCount = 0
    for expiry in expDateIsoFmt:
        try:
             tmpPuts        = ops.get_puts(opTicker,expiry) 
             tmpCalls       = ops.get_calls(opTicker,expiry) 
             AllPuts        = pd.concat([AllPuts, tmpPuts])
             AllCalls       = pd.concat([AllCalls, tmpCalls])
             reqCount = reqCount + 2
            #  print(expiry)
        except Exception as e:
            print("Failed to pull expiry for %s at %s" % (opTicker, expiry))
            # continue
    return(AllCalls,AllPuts,reqCount)

def getTargetStats(ticker):
    tmp = si.get_stats(ticker)
    tmp = tmp.set_index("Attribute")
    # MarketCap = largeNumStringToFloat(
    #             tmp.loc["Market Cap (intraday) 5"].item())
    Float = largeNumStringToFloat(tmp.loc["Float"].item())
    tenDayVol = largeNumStringToFloat(tmp.loc["Avg Vol (10 day) 3"].item())
    
    return(Float,tenDayVol)
    
def largeNumStringToFloat(numIn):
    suffix = numIn[-1]
    if suffix == "M":
        numOut = float(numIn.split(numIn[-1])[0])*10e6
    elif suffix == "B":
        numOut = float(numIn.split(numIn[-1])[0])*10e9
    elif suffix == "T":
        numOut = float(numIn.split(numIn[-1])[0])*10e12
    else:
        numOut = float(numIn)
        
    return(numOut)

def cleanOptTables(crntCalls,crntPuts, ticker):

    # Remove options with no open interest or undefined open interest
    crntPuts["Open Interest"] = crntPuts["Open Interest"].replace("-",int(0))
    crntPuts["Open Interest"] = crntPuts["Open Interest"].astype(int)
    # crntPuts = crntPuts.drop(crntPuts[crntPuts["Open Interest"] == 0].index)
    

    crntCalls["Open Interest"] = crntCalls["Open Interest"].replace("-",int(0))
    crntCalls["Open Interest"] = crntCalls["Open Interest"].astype(int)
    # crntCalls = crntCalls.drop(crntCalls[crntCalls["Open Interest"] == 0].index)

    # Clean up the volatility 
    crntPuts["Implied Volatility"] = crntPuts["Implied Volatility"].map(
                    lambda element : element.rstrip("%").replace(',',''))
    crntPuts["Implied Volatility"] = crntPuts["Implied Volatility"].astype(float)
    
    crntCalls["Implied Volatility"] = crntCalls["Implied Volatility"].map(
                    lambda element : element.rstrip("%").replace(',',''))
    crntCalls["Implied Volatility"] = crntCalls["Implied Volatility"].astype(float)
   
    # Replace non-numeric Bid-Ask
    crntPuts["Ask"] = crntPuts["Ask"].replace("-",float(0))
    crntPuts["Bid"] = crntPuts["Bid"].replace("-",float(0))
    crntPuts["Last Price"] = crntPuts["Last Price"].astype(float)

    crntPuts.loc[crntPuts["Ask"] == 0,"Ask"] = crntPuts.loc[
        crntPuts["Ask"] == 0, "Last Price"]
    crntPuts["Ask"] = crntPuts["Ask"].astype(float)
    crntPuts["Bid"] = crntPuts["Bid"].astype(float)

    crntCalls["Ask"] = crntCalls["Ask"].replace("-",float(0))
    crntCalls["Bid"] = crntCalls["Bid"].replace("-",float(0))
    crntCalls["Last Price"] = crntCalls["Last Price"].astype(float)
    crntCalls.loc[crntCalls["Ask"] == 0,"Ask"] = crntCalls.loc[
        crntCalls["Ask"] == 0, "Last Price"]
    crntCalls["Ask"] = crntCalls["Ask"].astype(float)
    crntCalls["Bid"] = crntCalls["Bid"].astype(float)
    
    # Add the spread 
    crntPuts["Spread"] = crntPuts["Ask"].subtract(crntPuts["Bid"])
    crntPuts.loc[crntPuts["Spread"] < 0, "Spread" ] = 0

    crntCalls["Spread"] = crntCalls["Ask"].subtract(crntCalls["Bid"])
    crntCalls.loc[crntCalls["Spread"] < 0, "Spread" ] = 0


    # Estimate leverged dollar amount being moved around
    crntPuts["Money"] =  crntPuts["Ask"]*crntPuts["Open Interest"]*100
    crntCalls["Money"] = crntCalls["Bid"]*crntCalls["Open Interest"]*100
    
    X = crntCalls[['Ask','Strike']]

    # Normalize via quantile transform to a gaissan distribution, normalize magnitude of ask, strike to 0-1
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
    crntCalls['SplitLogic'] = 'current'
    crntCalls.loc[clust.labels_ == 1, 'SplitLogic'] = 'lastSplit'
    crntCalls.loc[clust.labels_ == -1, 'SplitLogic']  = 'outlier'

    # Clean the DB, remove improperly categorized contracts
    crntCalls = crntCalls[~crntCalls['Contract Name'].str.contains(ticker+".*P.*", regex=True)]
    crntPuts = crntPuts[~crntPuts['Contract Name'].str.contains(ticker+".*C.*", regex=True)]

    # Extract expiries and match put option chain outliers and splits based on call expiries and strikes
    callExpiry =  pd.to_datetime(qdb.extractExpiryFromContractName(crntCalls["Contract Name"], ticker, isCall=True))
    putExpiry =  pd.to_datetime(qdb.extractExpiryFromContractName(crntPuts["Contract Name"], ticker, isCall=False))

    # Match Call option clustering, more efficient and easier to identify than put clusters
    crntPuts['SplitLogic'] = 'current'
    try:
        crntPuts.loc[(~callExpiry.isin(crntCalls[clust.labels_ == 1])) &
            (~crntPuts['Strike'].isin(crntCalls[clust.labels_ == 1]['Strike'])), 'SplitLogic'] = 'lastSplit'
        
        crntPuts.loc[(~callExpiry.isin(crntCalls[clust.labels_ == -1])) &
            (~crntPuts['Strike'].isin(crntCalls[clust.labels_ == -1]['Strike'])), 'SplitLogic'] = 'outlier'
    except Exception as e:
        print('Put/Call option chain mismatch, data should be dropped')
        putDF['SplitLogic'] = 'outlier'
        print(e)


    return(crntCalls,crntPuts)

def getPriceHistory(d1,d2,ticker):
    priceHistory = si.get_data(ticker, start_date = d2 , end_date = d1, interval="1d")
    return priceHistory


# Test functionality
# 
# getPriceHistory(dte.datetime.today(), dte.datetime.today() - dte.timedelta(days=10),"AAPL")
#     
#[price,reqCount] = scrapeOptionsData("^VIX")
# getOptionsData("BABA")
# expDates = ops.get_expiration_dates("SPY")
# expDateIsoFmt = [dte.datetime.strptime(rawDate, '%B %d, %Y') for rawDate in expDates]
# # print(expDateIsoFmt)
# print(ops.get_calls("SPY",dte.datetime(2023, 3, 22, 0, 0)))
# [Calls,Puts,opReqCount] = getOptionsData("RKT")
# scrapeOptionsData("SPY")
# if __name__ == "__main__":
#     main()