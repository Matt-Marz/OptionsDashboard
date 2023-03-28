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
            if len(ticker.split("-")) > 1:
                tickerSplt = ticker.split("-")[0] + ticker.split("-")[1]
            elif ticker == "^SPX":
                tickerSplt = "SPXW"
            elif ticker == "^VIX":
                tickerSplt = "VIXW"
            else:
                tickerSplt = ticker

            # Convert date to string for JSONification 

            dateStr = str(x["timestamp"])

            # Add price data to the output data structure
            price[dateStr] = x["price"]
            
            # Format dates to standardize to DB format, use contract name to get expiry date
            callData[dateStr] = pd.DataFrame(x["callData"])
            # Split the contract name to get the expiry (pretty slow operation for now)
            callData[dateStr]["Expiry"] = callData[dateStr
                ]["Contract Name"].map(
                    lambda element : element
                    .split(tickerSplt.upper())[-1]
                    .split("C")[0])
            # Format the date to ymd and save as date
            callData[dateStr]["Expiry"] = pd.to_datetime(callData[
                dateStr]["Expiry"],format='%y%m%d')
            callData[dateStr]["Expiry"] = callData[
                dateStr]["Expiry"].dt.date
            
            # Set the index to the contract name which is unique
            callData[dateStr].set_index("Contract Name",inplace=True)
          
            # Repeat above for put contracts
            putData[dateStr] = pd.DataFrame(x["putData"])
            putData[dateStr]["Expiry"] = putData[dateStr
                ]["Contract Name"].map(
                    lambda element : element
                    .split(tickerSplt.upper())[-1]
                    .split("P")[0])
            putData[dateStr]["Expiry"] = pd.to_datetime(putData[
                dateStr]["Expiry"],format='%y%m%d')
            putData[dateStr]["Expiry"] = putData[
                dateStr]["Expiry"].dt.date
            putData[dateStr].set_index("Contract Name",inplace=True)

            # callData[dateStr].to_csv('Call-' + dateStr.split(" ")[0] + '.csv') 
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
    
    ocLengths = pd.DataFrame.from_dict(chainSize,orient="index",columns=["count"]).reset_index().rename(columns={"index":"timestamp"})
    removeSubSet = ocLengths[ocLengths["count"] < 0.1*ocLengths["count"].median()]

    for set in removeSubSet["timestamp"]:
        # print(set)
        delQuery = {"timestamp": set}
        tickerData.delete_one(delQuery)
        print("\tRemoved data at time %s from database due to incomplete data"%  set)

    print(ocLengths['count'].value_counts())

    return()

# currentTime = dte.datetime.utcnow()
# origTime = dte.datetime(2021,3,1,0,0)
# tickerList = getTickers(origTime,currentTime)
# # ticker = "SPY"
# # cleanDB(ticker,origTime,currentTime)
# for ticker in tickerList:
#     print(ticker)
#     cleanDB(ticker,origTime,currentTime)
# # [Price,Calls,Puts] = queryDB(ticker,origTime,currentTime)
