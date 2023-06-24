 # -*- coding: utf-8 -*-

"""
Query MongoDB, test plotting

"""
#from yahoo_fin import stock_info as si
#import yahoo_fin.options as ops
#import matplotlib as plt
import pandas as pd
#import numpy as np
import datetime as dte
#from itertools import chain
import pymongo as mndb
import os
import shutil
import glob

def getTickers(d1,d2):    
    # Making a Connection with MongoClient
    client = mndb.MongoClient("mongodb://localhost:27017")
    # database
    opDB = client["optionsDB_2023"]
    tickerList = opDB.list_collection_names()
    timeQuery = {"timestamp" : {"$gt": d1,"$lt": d2}}
    validTickers = []
    for ticker in tickerList:
        tickerData = opDB[ticker]
        tickerDataQry = tickerData.find(timeQuery,{"_id":0})
        if len(list(tickerDataQry)) != 0: validTickers.append(ticker) 
    return(validTickers)

def queryDB(ticker,d1,d2): 
    
    timeQuery = {"timestamp" : {"$gt": d1,"$lt": d2}}
    
    # Making a Connection with MongoClient
    client = mndb.MongoClient("mongodb://localhost:27017")
    # database
    opDB = client["optionsDB_2023"]
    # collection
    tickerData = opDB[ticker]
    
    tickerDataQry = tickerData.find(timeQuery,{"_id":0})    
    price = {}
    callData = {}
    putData = {}

    # Build a data structure for transmission to front end visualization tool
    for x in tickerDataQry:
        try:

            # Convert date to string for JSONification 
            dateStr = str(x["timestamp"])

            # Add price data to the output data structure
            price[dateStr] = x["price"]
            
            # Format dates to standardize to DB format, use contract name to get expiry date
            callData[dateStr] = pd.DataFrame(x["callData"])
            
            callData[dateStr]["Expiry"] = extractExpiryFromContractName(callData[dateStr]["Contract Name"], 
                                                                        ticker, 
                                                                        isCall=True)
            
            # Format the date to ymd and save as date
            callData[dateStr]["Expiry"] = pd.to_datetime(callData[
                dateStr]["Expiry"],format='%y%m%d')
            
            callData[dateStr]["Expiry"] = callData[
                dateStr]["Expiry"].dt.date
            
            # Set the index to the contract name which is unique
            callData[dateStr].set_index("Contract Name",inplace=True)
          
            # Repeat above for put contracts
            putData[dateStr] = pd.DataFrame(x["putData"])

            putData[dateStr]["Expiry"] = extractExpiryFromContractName(putData[dateStr]["Contract Name"], 
                                                                        ticker, 
                                                                        isCall=False)
            
            putData[dateStr]["Expiry"] = pd.to_datetime(putData[
                dateStr]["Expiry"],format='%y%m%d')
            putData[dateStr]["Expiry"] = putData[
                dateStr]["Expiry"].dt.date
            
            putData[dateStr].set_index("Contract Name",inplace=True)

            # Convert dataframes to JSON files for serialization and data exchange to front end 
            callData[dateStr] = callData[dateStr].to_json(orient='split', date_format='iso')
            putData[dateStr]  = putData[dateStr].to_json(orient='split', date_format='iso')
            
        except Exception as e:
            print("Unexpected irregularity from yahoo data for %s at %s" 
                  % (ticker, dateStr))
            print("\tError %s" % e)
            print("\t Dropping entry for %s at %s" 
                  % (ticker, dateStr))
            continue
    return(price,callData,putData)

def extractExpiryFromContractName(contractNameSeries, tick, isCall=True):
    # Extract expiry date by separating out strike information, demarcated by C for calls, P for puts
    if isCall == True:
        contractPrefix = "C"
    else:
        contractPrefix = "P"

    # Drop the ticker prefix, handle edge case for euro style options on VIX and sp500 indices
    if len(tick.split("-")) > 1:
        tickerSplt = tick.split("-")[0] + tick.split("-")[1]
    elif tick[0] == "^":
        tickerSplt_a = tick.split("^")[-1]
        tickerSplt_b = "W"
        expirySeries = contractNameSeries.map(
                        lambda element : element
                        .split(tickerSplt_a.upper())[-1]
                        .split(tickerSplt_b.upper())[-1]
                        .split(contractPrefix)[0])
    else:
        tickerSplt   = tick
        expirySeries = contractNameSeries.map(
                        lambda element : element
                        .split(tickerSplt.upper())[-1]
                        .split(contractPrefix)[0])
        
    return(expirySeries)


def cleanDB(ticker,d1,d2):
    #Only run after backing up database
    timeQuery = {"timestamp" : {"$gt": d1,"$lt": d2}}
    # Making a Connection with MongoClient
    client = mndb.MongoClient("mongodb://localhost:27017")
    # database
    opDB = client["optionsDB_2023"]
    # collection
    tickerData = opDB[ticker]
    tickerDataQry = tickerData.find(timeQuery,{"_id":0})    
    price = {}
    callData = {}
    putData = {}
    chainSize = {}
    for x in tickerDataQry:
        try:                
            price[x["timestamp"]] = x["price"]
            callData[x["timestamp"]] = pd.DataFrame(x["callData"])
            putData[x["timestamp"]] = pd.DataFrame(x["putData"])
            callData[x["timestamp"]].set_index("Contract Name",inplace=True)
            putData[x["timestamp"]].set_index("Contract Name",inplace=True)
            chainSize[x["timestamp"]] = len(x["callData"]) + len(x["putData"])
        except Exception as e:
            print("\tError %s" % e)
            delQuery = {"timestamp": x["timestamp"]}
            tickerData.delete_one(delQuery)
            print("\tBad data found for ticker %s" %ticker)
            print("\tRemoved data at time %s from database due to corrupt or missing data"%  x["timestamp"])
    
    # Remove options chains that are less than 10% of the option chain median length
    ocLengths = pd.DataFrame.from_dict(chainSize,orient="index",columns=["count"]).reset_index().rename(columns={"index":"timestamp"})
    removeSubSet = ocLengths[ocLengths["count"] < 0.1*ocLengths["count"].median()]

    for set in removeSubSet["timestamp"]:
        # print(set)
        delQuery = {"timestamp": set}
        tickerData.delete_one(delQuery)
        print("\tRemoved data at time %s from database due to incomplete data"%  set)

    print(ocLengths['count'].value_counts())

    return()



# import json
# tickers = getTickers(dte.datetime.today() - dte.timedelta(days=10),dte.datetime.today())
# maxMoney = pd.DataFrame()
# for ticker in tickers:
#     try:
#         [Price,Calls,Puts] = queryDB(ticker, dte.datetime.today() - dte.timedelta(days=2), dte.datetime.today())
#         if Price:
#             # print(ticker)
#             expiries = list(Calls.keys())
#             expiries.sort()
#             callDF = pd.read_json(Calls[expiries[-1]], orient='split')
#             putDF = pd.read_json(Puts[expiries[-1]], orient='split')
#             callMax = callDF[callDF['Money'] == callDF['Money'].max()]
#             putMax = putDF[putDF['Money'] == putDF['Money'].max()]
#             maxMoney = pd.concat([maxMoney,callMax,putMax])
#     except Exception as e:
#         print("\tError %s" % e)
#         # print("\tBad data found for ticker %s" %ticker)   

# print(maxMoney[maxMoney['Money']>10^6].sort_values(by='Money'))    
    
    
# # [Price,Calls,Puts] = queryDB(ticker,origTime,currentTime)
# currentTime = dte.datetime.utcnow()
# origTime = dte.datetime(2021,3,1,0,0)
# tickerList = getTickers(origTime,currentTime)
# # ticker = "SPY"
# # cleanDB(ticker,origTime,currentTime)
# for ticker in tickerList:
#     print(ticker)
#     cleanDB(ticker,origTime,currentTime)
# # [Price,Calls,Puts] = queryDB(ticker,origTime,currentTime)
