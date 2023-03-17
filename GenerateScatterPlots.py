# -*- coding: utf-8 -*-
"""
#Plotting Tools

"""

import os
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.ticker as tkr
mpl.rcParams['font.family'] = 'Gill Sans MT'
import seaborn as sns
import pandas as pd
import numpy as np
import datetime as dte
import QueryOptionsDB as qdb
import QueryYF as qYF
#from yahoo_fin import stock_info as si
import math
import time

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

def cleanOptTables(crntCalls,crntPuts):

    crntPuts["Open Interest"] = crntPuts["Open Interest"].replace("-",int(0))
    crntPuts["Open Interest"] = crntPuts["Open Interest"].astype(int)
    crntPuts["Implied Volatility"] = crntPuts["Implied Volatility"].map(
                    lambda element : element.rstrip("%").replace(',',''))
    crntPuts["Implied Volatility"] = crntPuts["Implied Volatility"].astype(float)
    crntPuts["Ask"] = crntPuts["Ask"].replace("-",float(0))
    crntPuts["Bid"] = crntPuts["Bid"].replace("-",float(0))
    crntPuts["Last Price"] = crntPuts["Last Price"].astype(float)
    crntPuts.loc[crntPuts["Ask"] == 0,"Ask"] = crntPuts.loc[
        crntPuts["Ask"] == 0, "Last Price"]
    crntPuts["Ask"] = crntPuts["Ask"].astype(float)
    crntPuts["Bid"] = crntPuts["Bid"].astype(float)
    
    crntPuts["Spread"] = crntPuts["Ask"].subtract(crntPuts["Bid"])
    crntPuts.loc[crntPuts["Spread"] < 0, "Spread" ] = 0 
    crntPuts["Money"] =  crntPuts["Ask"]*crntPuts["Open Interest"]*100
    
    crntCalls["Open Interest"] = crntCalls["Open Interest"].replace("-",int(0))
    crntCalls["Open Interest"] = crntCalls["Open Interest"].astype(int)
    crntCalls["Implied Volatility"] = crntCalls["Implied Volatility"].map(
                    lambda element : element.rstrip("%").replace(',',''))
    crntCalls["Implied Volatility"] = crntCalls["Implied Volatility"].astype(float)
    crntCalls["Ask"] = crntCalls["Ask"].replace("-",float(0))
    crntCalls["Bid"] = crntCalls["Bid"].replace("-",float(0))
    crntCalls["Last Price"] = crntCalls["Last Price"].astype(float)
    crntCalls.loc[crntCalls["Ask"] == 0,"Ask"] = crntCalls.loc[
    crntCalls["Ask"] == 0, "Last Price"]
    crntCalls["Ask"] = crntCalls["Ask"].astype(float)
    crntCalls["Bid"] = crntCalls["Bid"].astype(float)
    crntCalls["Spread"] = crntCalls["Ask"].subtract(crntCalls["Bid"])
    crntCalls.loc[crntCalls["Spread"] < 0, "Spread" ] = 0 
    crntCalls["Money"] = crntCalls["Bid"]*crntCalls["Open Interest"]*100
    
    
    return(crntCalls,crntPuts)
    
def buildLinePlot(tick,price,dtTme,callData,putData,yVar,bubSize):
   
    
    f,(ax1,ax2) = plt.subplots(1,2,
                               gridspec_kw={'width_ratios':[1,1]}, 
                               figsize=(12, 7))
    # ax1.get_shared_y_axes().join(ax1,ax2)
    
    with sns.axes_style("darkgrid", {"axes.facecolor": ".9"}):

        callScat = sns.scatterplot(data=callData, x="Strike", y=yVar, hue="Expiry",
                         size=bubSize, sizes=(30, 100),
                         palette="mako",alpha=0.75, ax=ax1, zorder=10)
        
        ax1.vlines(price, *ax1.get_ylim(),colors="Black", 
                   linestyles='dashed')
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.grid(color = 'black', linestyle = '--', linewidth = 0.75)
        
        #ax1.set_ylim([0,3*price])
        ax1.set_title("Calls",fontsize=24)
        ax1.set_ylabel(yVar,fontsize=24)
        ax1.set_xlabel('Strike',fontsize=24)
        ax1.tick_params(axis='both', which='major', labelsize=14)

        callScat.legend(bbox_to_anchor=(1.01, 1), borderaxespad=0, 
                        fontsize=9)
        

        putScat = sns.scatterplot(data=putData, x="Strike", y=yVar, hue="Expiry",
                         size=bubSize, sizes=(30, 100),
                         palette="rocket",alpha=0.75, ax=ax2, zorder=10)
        ax2.vlines(price, *ax2.get_ylim(),colors="Black", 
                   linestyles='dashed')
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.grid(color = 'black', linestyle = '--', linewidth = 0.75)
        
        #ax2.set_ylim([0,3*price])
        ax2.set_title("Puts",fontsize=24)
        ax2.set_ylabel('')
        ax2.set_xlabel('Strike',fontsize=24)
        ax2.tick_params(axis='both', which='major', labelsize=14)

        
        putScat.legend(bbox_to_anchor=(1.01, 1), borderaxespad=0, 
                        fontsize=9)
        
        if yVar == "Ask":
            callMax = np.max([np.max(callData[yVar].values)])
            putMax = np.max([np.max(callData[yVar].values)])
            ax1.set(yscale="log")
            ax2.set(yscale="log")
            ax1.get_yaxis().set_minor_locator(tkr.LogLocator(base=10,subs='all'))
            ax2.get_yaxis().set_minor_locator(tkr.LogLocator(base=10,subs='all'))
            ax1.grid(b=True, which='minor', color='grey', linestyle = '--',
                     linewidth=0.5)
            ax2.grid(b=True, which='minor', color='grey',linestyle = '--',
                     linewidth=0.5)
            ax1.set_ylim([0.01,callMax])
            ax2.set_ylim([0.01,putMax])
        elif yVar == "Open Interest":
            callMax = np.max([np.max(callData[yVar].values)])
            putMax = np.max([np.max(callData[yVar].values)])
            maxMax =  np.max([callMax,putMax])
            ax1.set_ylim([0,maxMax+250])
            ax2.set_ylim([0,maxMax+250])
            ax1.get_shared_y_axes().join(ax1,ax2)
            
        

    plt.suptitle(tick + "-" + dtTme, x=0.5, y=0.05, ha ='center', fontsize=18)#, bbox={"facecolor":"orange", "alpha":0.5, "pad":5}
    f.tight_layout()
    plt.show()
    savePath = os.path.join("Plotting","ScatterPlots",yVar)
    if not os.path.exists(savePath):
        os.makedirs(savePath)
        
    f.savefig(os.path.join(savePath,
                           ticker+"-"+yVar+"-"+bubSize+".png"), dpi=300)
    return()

currentTime = dte.datetime.utcnow()
# currentTime = dte.datetime(2021,7,13,14,0)
origTime = dte.datetime(2021,10,1,0,0)
tickerList = qdb.getTickers(origTime,currentTime)
tickerList.sort()
# tickerList = ["GOOG"]
# tickerList = ["CCL","CLF","CLNE","CLOV","F","FCX","GE","GFI","HBAN","HMBL",
#                "INTC","ITUB","JNJ","JPM","LI","MSFT","MU","NCLH","NEGG","NIO",
#                "NLY","NOKPF","OCGN","OPEN","PBR","PFE","PLTR","PLUG","QQQ",
#                    "RIG","RLLCF","SOFI","SPY","SPCE","T","TIGR","XPEV","ZOM"]

for ticker in tickerList:
    try:
        ticker_time = time.time()
        [Price,Calls,Puts] = qdb.queryDB(ticker,origTime,currentTime)
        print("\tQueried %s in %0.2f seconds" % (ticker,(time.time() - ticker_time)))
        [nowPrice, nowCalls, nowPuts, lastDate]  = getLatestOpts(Price,Calls,Puts)
        [cleanCalls, cleanPuts] = cleanOptTables(nowCalls, nowPuts)
        
        fmtDateTime = lastDate.astimezone(est).strftime("%Y-%m-%d %H:%M")
        sns.set_style("darkgrid", {"axes.facecolor": ".9"})
        buildLinePlot(ticker,nowPrice,fmtDateTime,cleanCalls,cleanPuts
                      ,"Ask","Open Interest")
        buildLinePlot(ticker,nowPrice,fmtDateTime,cleanCalls,cleanPuts,
                      "Implied Volatility","Open Interest")
        buildLinePlot(ticker,nowPrice,fmtDateTime,cleanCalls,cleanPuts,
                      "Open Interest","Money")
        print("\tBuilt plots in %0.2f seconds" % ((time.time() - ticker_time)))
        plt.close("all")     
    except Exception as e:
        print("\tCouldn't plot bitch ticker %s" % ticker)
        print("Error %s" % e)

sns.reset_orig()