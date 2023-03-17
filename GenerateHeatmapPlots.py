# -*- coding: utf-8 -*-
"""
#Plotting Tools
"""
import os
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['font.family'] = 'Gill Sans MT'
import seaborn as sns
import pandas as pd
import numpy as np
import datetime as dte
import QueryOptionsDB as qdb
import QueryYF as qYF
#from yahoo_fin import stock_info as si
import math

import pytz
est = pytz.timezone("US/Eastern") 
utc = pytz.utc 
fmt = "%Y-%m-%d %H:%M"

def getLatestOpts(Price,Calls,Puts):
    
    availDates = sorted(Calls.keys())
    latestDate = availDates[-1]
    latestPuts = Puts[latestDate]
    latestCalls = Calls[latestDate]
    latestPrice = Price[latestDate] 
    
    return(latestPrice, latestCalls, latestPuts,latestDate)

def dfToPivot(df,var):
   pivotTble = df.pivot("Strike", "Expiry", var)
   pivotTble = pivotTble.replace(np.nan,0)
   return(pivotTble)

def buildOptTables(ticker,price,calls,puts):

    [crntPrice, crntCalls, crntPuts, lastDate] = getLatestOpts(price,calls,puts)
    # [Float, tenDayVol] = qYF.getTargetStats(ticker)
    
    crntPuts["Open Interest"] = crntPuts["Open Interest"].replace("-",int(0))
    crntPuts["Open Interest"] = crntPuts["Open Interest"].astype(int)
    crntPuts["Implied Volatility"] = crntPuts["Implied Volatility"].map(
                    lambda element : element.rstrip("%").replace(',',''))
    crntPuts["Implied Volatility"] = crntPuts["Implied Volatility"].astype(float)
    crntPuts["Ask"] = crntPuts["Ask"].replace("-",float(0))
    crntPuts["Bid"] = crntPuts["Bid"].replace("-",float(0))
    crntPuts["Ask"] = crntPuts["Ask"] .astype(float)
    crntPuts["Bid"] = crntPuts["Bid"] .astype(float)
    crntPuts["Spread"] = crntPuts["Ask"].subtract(crntPuts["Bid"])
    crntPuts["Quote"] =  crntPuts["Ask"].add(crntPuts["Bid"]).divide(2)

    
    OIPuts = dfToPivot(crntPuts,"Open Interest")
    QuotePuts = dfToPivot(crntPuts,"Quote")
    SpreadPuts = dfToPivot(crntPuts,"Spread")
    IVPuts = dfToPivot(crntPuts,"Implied Volatility")

    
    crntCalls["Open Interest"] = crntCalls["Open Interest"].replace("-",int(0))
    crntCalls["Open Interest"] = crntCalls["Open Interest"].astype(int)
    crntCalls["Implied Volatility"] = crntCalls["Implied Volatility"].map(
                    lambda element : element.rstrip("%").replace(',',''))
    crntCalls["Implied Volatility"] = crntCalls["Implied Volatility"].astype(float)
    crntCalls["Ask"] = crntCalls["Ask"].replace("-",float(0))
    crntCalls["Bid"] = crntCalls["Bid"].replace("-",float(0))
    crntCalls["Ask"] = crntCalls["Ask"] .astype(float)
    crntCalls["Bid"] = crntCalls["Bid"] .astype(float)
    crntCalls["Spread"] = crntCalls["Ask"].subtract(crntCalls["Bid"])
    crntCalls["Quote"] =  crntCalls["Ask"].add(crntCalls["Bid"]).divide(2)
    
    OICalls = dfToPivot(crntCalls,"Open Interest")
    QuoteCalls = dfToPivot(crntCalls,"Quote")
    SpreadCalls = dfToPivot(crntCalls,"Spread")
    IVCalls = dfToPivot(crntCalls,"Implied Volatility")
    
    fmtDateTime = lastDate.astimezone(est).strftime("%Y-%m-%d %H:%M")
    
    for idx, strike in enumerate(OIPuts.index):
        #print(strike)
        if crntPrice < strike:
            lineLoc = idx
            break
        
    return(OICalls,OIPuts,QuoteCalls,QuotePuts,
           SpreadCalls,SpreadPuts,IVCalls,IVPuts,lineLoc,fmtDateTime)

def buildDerivedOptTables(ticker,price,calls,puts):
    [crntPrice, crntCalls, crntPuts, lastDate] = getLatestOpts(price,calls,puts)
    [Float, tenDayVol] = qYF.getTargetStats(ticker)
    
    crntPuts["Open Interest"] = crntPuts["Open Interest"].replace("-",int(0))
    crntPuts["Open Interest"] = crntPuts["Open Interest"].astype(int)
    crntPuts["Ask"] = crntPuts["Ask"].replace("-",float(0))
    crntPuts["Bid"] = crntPuts["Bid"].replace("-",float(0))
    crntPuts["Ask"] = crntPuts["Ask"] .astype(float)
    crntPuts["Bid"] = crntPuts["Bid"] .astype(float)
    crntPuts["Spread"] = crntPuts["Ask"].subtract(crntPuts["Bid"])
    crntPuts["Quote"] =  crntPuts["Ask"].add(crntPuts["Bid"]).divide(2)
    crntPuts["MaR"] =  crntPuts["Quote"].multiply(crntPuts["Open Interest"]).multiply(100)
    crntPuts["VolImpact"] =  crntPuts["Open Interest"].multiply(100).divide(tenDayVol)
    
    MaRPuts = dfToPivot(crntPuts,"MaR")
    VImpPuts = dfToPivot(crntPuts,"VolImpact")
    
    crntCalls["Open Interest"] = crntCalls["Open Interest"].replace("-",int(0))
    crntCalls["Open Interest"] = crntCalls["Open Interest"].astype(int)
    crntCalls["Ask"] = crntCalls["Ask"].replace("-",float(0))
    crntCalls["Bid"] = crntCalls["Bid"].replace("-",float(0))
    crntCalls["Ask"] = crntCalls["Ask"] .astype(float)
    crntCalls["Bid"] = crntCalls["Bid"] .astype(float)
    crntCalls["Spread"] = crntCalls["Ask"].subtract(crntCalls["Bid"])
    crntCalls["Quote"] =  crntCalls["Ask"].add(crntCalls["Bid"]).divide(2)
    crntCalls["MaR"] =  crntCalls["Quote"].multiply(crntCalls["Open Interest"]).multiply(100)
    crntCalls["VolImpact"] =  crntCalls["Open Interest"].multiply(100).divide(tenDayVol)
    
    MaRCalls = dfToPivot(crntCalls,"MaR")
    VImpCalls = dfToPivot(crntCalls,"VolImpact")
    
    fmtDateTime = lastDate.astimezone(est).strftime("%Y-%m-%d %H:%M")
    
    for idx, strike in enumerate(MaRPuts.index):
        #print(strike)
        if crntPrice < strike:
            lineLoc = idx
            break
        
    return(MaRCalls,MaRPuts,VImpPuts,VImpCalls,lineLoc,fmtDateTime)

def generateHeatMap(callPivot,putPivot,aprxPrice,timeStamp,varName,rnd):
    
    medVal = np.median(np.concatenate((callPivot.values, putPivot.values)))
    
    stdVal = np.std(np.concatenate((callPivot.values, putPivot.values)))
    
    maxVal = math.ceil((medVal + 3*stdVal)/rnd)*rnd
    
    f,(ax1,ax2,axcb) = plt.subplots(1,3,gridspec_kw={'width_ratios':[1,1,0.08]})
    ax1.get_shared_y_axes().join(ax1,ax2)
    # sns.heatmap(OIPuts, annot=True, fmt="d", ax=ax)
    sns.heatmap(callPivot, ax=ax1,cmap="bone_r",vmin=0, vmax=maxVal,cbar=False)
    ax1.set_title("Calls")
    #ax1.set_ylim(200,500)
    #ax1.tick_params(axis='x', labelrotation = 45)
    ax1.hlines(aprxPrice, *ax1.get_xlim(),colors="Black", linestyles='dashed')
    sns.heatmap(putPivot, ax=ax2,cmap="bone_r",vmin=0, vmax=maxVal, cbar_ax=axcb)
    ax2.set_title("Puts")
     
    ax2.set_yticks([])
    #ax2.tick_params(axis='x', labelrotation = 45)
    #ax2.set_ylim(200,500)
    plt.title(timeStamp)
    ax2.hlines(aprxPrice, *ax2.get_xlim(),colors="Black", linestyles='dashed')
    plt.tight_layout()
    f.autofmt_xdate()
    plt.savefig(os.path.join("Plotting",'Heatmaps',varName+".png"), dpi=300)
    return()

currentTime = dte.datetime.utcnow()
#currentTime = dte.datetime(2021,3,30,16,0)
origTime = dte.datetime(2021,6,1,0,0)
tickerList = qdb.getTickers(origTime,currentTime)
#tickerList.sort()
tickerList = ["GME"]

for ticker in tickerList:
    try:
        [Price,Calls,Puts] = qdb.queryDB(ticker,origTime,currentTime)
        
        [marCalls,marPuts,VImpPuts,VImpCalls,lineLoc,
         latestTimeDate] = buildDerivedOptTables(ticker,Price,Calls,Puts)
        
        [OICalls,OIPuts,QuoteCalls,QuotePuts,
        SpreadCalls,SpreadPuts,IVCalls,IVPuts, _,_
        ] = buildOptTables(ticker,Price,Calls,Puts)
        
        generateHeatMap(OICalls,OIPuts,lineLoc,latestTimeDate, 
                        os.path.join("OpenInterest", ticker+"-OI"), 1000)
        
        generateHeatMap(marCalls,marPuts,lineLoc,latestTimeDate, 
                        os.path.join("MoneyAtRisk", ticker+"-MAR"), 1000)
        
        generateHeatMap(VImpCalls,VImpPuts,lineLoc,latestTimeDate,  
                        os.path.join("VolumeImpact", ticker+"-VImp"), 0.001)
        
        generateHeatMap(QuoteCalls,QuotePuts,lineLoc,latestTimeDate,  
                os.path.join("Quote", ticker+"-Price"), 0.01)
        
        generateHeatMap(SpreadCalls,SpreadPuts,lineLoc,latestTimeDate,  
        os.path.join("Spread", ticker+"-Spread"), 0.01)
        
        generateHeatMap(IVCalls,IVPuts,lineLoc,latestTimeDate,  
        os.path.join("IV", ticker+"-IV"), 1)
        
        plt.close("all")
     
    except Exception as e:
        print("Failed to generate plot: %s" %ticker)
        print("Error %s" % e)
        continue

# pullTick = "RKT"
# #[_, _] = qYF.scrapeOptionsData(pullTick)
# [Price,Calls,Puts] = qdb.queryDB(pullTick,origTime,currentTime)

# [OICalls,OIPuts,marCalls,marPuts,VImpPuts,VImpCalls,
#   lineLoc,latestTimeDate]buildDerivedOptTables(pullTick,Price,Calls,Puts)

# [marCalls,marPuts,VImpPuts,VImpCalls,
#   lineLoc,latestTimeDate] = buildOptTables(pullTick,Price,Calls,Puts)

# generateHeatMap(OICalls,OIPuts,lineLoc,latestTimeDate, 
#                 os.path.join("OpenInterest", pullTick+"-OI"),1000)
# generateHeatMap(marCalls,marPuts,lineLoc,latestTimeDate, 
#                 os.path.join("MoneyAtRisk", pullTick+"-MAR"),1000)
# generateHeatMap(VImpCalls,VImpPuts,lineLoc,latestTimeDate,  
#                 os.path.join("VolumeImpact", pullTick+"-VImp"),0.0005)
# plt.close("all")