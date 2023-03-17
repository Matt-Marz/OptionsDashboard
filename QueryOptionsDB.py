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
    opDB = client["optionsDB"]
    tickerData = opDB.list_collection_names()
    return(tickerData)

def queryDB(ticker,d1,d2): 
    
    timeQuery = {"timestamp" : {"$gt": d1,"$lt": d2}}
    
    # Making a Connection with MongoClient
    client = mndb.MongoClient("mongodb://localhost:27017")
    # database
    opDB = client["optionsDB"]
    # collection
    tickerData = opDB[ticker]
    
    tickerDataQry = tickerData.find(timeQuery,{"_id":0})    
    price = {}
    callData = {}
    putData = {}
    #print(tickerDataQry)
    for x in tickerDataQry:
        try:
            if len(ticker.split("-")) > 1:
                tickerSplt = ticker.split("-")[0] + ticker.split("-")[1]
            elif ticker == "^GSPC":
                tickerSplt = "SPX"
            elif ticker == "^VIX":
                tickerSplt = "VIX"
            else:
                tickerSplt = ticker
            price[x["timestamp"]] = x["price"]
            callData[x["timestamp"]] = pd.DataFrame(x["callData"])
            callData[x["timestamp"]]["Expiry"] = callData[x["timestamp"]
                ]["Contract Name"].map(
                    lambda element : element
                    .split(tickerSplt.upper())[-1]
                    .split("C")[0][-6::])
            callData[x["timestamp"]]["Expiry"] = pd.to_datetime(callData[
                x["timestamp"]]["Expiry"],format='%y%m%d')
            callData[x["timestamp"]]["Expiry"] = callData[
                x["timestamp"]]["Expiry"].dt.date
            callData[x["timestamp"]].set_index("Contract Name",inplace=True)
          
            putData[x["timestamp"]] = pd.DataFrame(x["putData"])
            putData[x["timestamp"]]["Expiry"] = putData[x["timestamp"]
                ]["Contract Name"].map(
                    lambda element : element
                    .split(tickerSplt.upper())[-1]
                    .split("P")[0][-6::])
            putData[x["timestamp"]]["Expiry"] = pd.to_datetime(putData[
                x["timestamp"]]["Expiry"],format='%y%m%d')
            putData[x["timestamp"]]["Expiry"] = putData[
                x["timestamp"]]["Expiry"].dt.date
            putData[x["timestamp"]].set_index("Contract Name",inplace=True)
        except Exception as e:
            print("Unexpected irregularity from yahoo data for %s at %s" 
                  % (ticker, x["timestamp"]))
            print("\tError %s" % e)
            print("\t Dropping entry for %s at %s" 
                  % (ticker, x["timestamp"]))
            continue
    return(price,callData,putData)

def cleanDB(ticker,d1,d2):
    #Only run after backing up database
    timeQuery = {"timestamp" : {"$gt": d1,"$lt": d2}}
    # Making a Connection with MongoClient
    client = mndb.MongoClient("mongodb://localhost:27017")
    # database
    opDB = client["optionsDB"]
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
    
    ocLengths = pd.DataFrame.from_dict(chainSize,orient="index",columns=["count"]).reset_index().rename(columns={"index":"timestamp"})
    removeSubSet = ocLengths[ocLengths["count"] < 0.25*ocLengths["count"].median()]

    for set in removeSubSet["timestamp"]:
        # print(set)
        delQuery = {"timestamp": set}
        tickerData.delete_one(delQuery)
        print("\tRemoved data at time %s from database due to incomplete data"%  set)

    # print(ocLengths['count'].value_counts())

    return()

# currentTime = dte.datetime.utcnow()
# origTime = dte.datetime(2021,1,1,0,0)
# tickerList = getTickers(origTime,currentTime)
# # ticker = "MSFT"
# # cleanDB(ticker,origTime,currentTime)
# for ticker in tickerList:
#     print(ticker)
#     cleanDB(ticker,origTime,currentTime)
# [Price,Calls,Puts] = queryDB(ticker,origTime,currentTime)
