# -*- coding: utf-8 -*-
"""
#Plotting Option Time History Tools

@author: mattm
"""

import os
import matplotlib.pyplot as plt
import matplotlib.ticker as tkr
import matplotlib as mpl
mpl.rcParams['font.family'] = 'Arial'
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

def getOptDates(Calls,Puts):
    
    availDates = sorted(Calls.keys())
    latestDate = availDates[-1]
    
    return(latestDate,availDates)

def cleanOptTables(crntCalls,crntPuts):

    crntPuts["Open Interest"] = crntPuts["Open Interest"].replace("-",int(0))
    crntPuts["Open Interest"] = crntPuts["Open Interest"].astype(int)
    try:
        crntPuts["Implied Volatility"] = crntPuts["Implied Volatility"].map(
                        lambda element : element.rstrip("%").replace(',',''))
        crntPuts["Implied Volatility"] = crntPuts["Implied Volatility"].astype(float)
    except Exception as e:
        print("\tTyping for IV is non-standard: %s" % e)
    
    crntPuts["Ask"] = crntPuts["Ask"].replace("-",float(0))
    crntPuts["Bid"] = crntPuts["Bid"].replace("-",float(0))
    crntPuts["Last Price"] = crntPuts["Last Price"].replace("-",float(0))
    crntPuts["Ask"] = crntPuts["Ask"].astype(float)
    crntPuts["Bid"] = crntPuts["Bid"].astype(float)
    crntPuts["Last Price"] = crntPuts["Last Price"].astype(float)
    crntPuts["Spread"] = crntPuts["Ask"].subtract(crntPuts["Bid"])
    crntPuts["Quote"] =  crntPuts["Ask"].add(crntPuts["Bid"]).divide(2)
    
    crntCalls["Open Interest"] = crntCalls["Open Interest"].replace("-",int(0))
    crntCalls["Open Interest"] = crntCalls["Open Interest"].astype(int)
    try:
        crntCalls["Implied Volatility"] = crntCalls["Implied Volatility"].map(
                        lambda element : element.rstrip("%").replace(',',''))
        crntCalls["Implied Volatility"] = crntCalls["Implied Volatility"].astype(float)
    except Exception as f:
        print("\tTyping for IV is non-standard: %s" % f)
        
    crntCalls["Ask"] = crntCalls["Ask"].replace("-",float(0))
    crntCalls["Bid"] = crntCalls["Bid"].replace("-",float(0))
    crntCalls["Last Price"] = crntCalls["Last Price"].replace("-",float(0))
    crntCalls["Ask"] = crntCalls["Ask"].astype(float)
    crntCalls["Bid"] = crntCalls["Bid"].astype(float)
    crntCalls["Last Price"] = crntCalls["Last Price"].astype(float)
    crntCalls["Spread"] = crntCalls["Ask"].subtract(crntCalls["Bid"])
    crntCalls["Quote"] =  crntCalls["Ask"].add(crntCalls["Bid"]).divide(2)
    
    crntCalls.reset_index(drop=True)
    crntPuts.reset_index(drop=True)
    
    crntCalls.drop(crntCalls[crntCalls['Ask'] == 0].index,  inplace=True)
    crntPuts.drop(crntPuts[crntPuts['Ask'] == 0].index,  inplace=True)
    
    return(crntCalls,crntPuts)
    
def buildLinePlot(ticker,price,dtTme,callData,putData,yVar,bubSize,yMax):
    
    if len(callData) < 10 or  len(putData) < 10:
        return

    f,(ax1,ax2) = plt.subplots(1,2,
                               gridspec_kw={'width_ratios':[1,1]}, 
                               figsize=(12, 7))
    ax1.get_shared_y_axes().join(ax1,ax2)
    sns.set_style("darkgrid", {"axes.facecolor": ".9"})
    with sns.axes_style("darkgrid", {"axes.facecolor": ".9"}):
        
        mpl.rcParams['font.family'] = 'Gill Sans MT'
        callScat = sns.scatterplot(data=callData, x="Strike", y=yVar, hue="Expiry",
                         size=bubSize, sizes=(10, 100),
                         palette="mako",alpha=0.8, ax=ax1, zorder=10,legend=False)
        
        ax1.vlines(price, *ax1.get_ylim(),colors="Black", 
                   linestyles='dashed')
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.grid(color = 'black', linestyle = '--', linewidth = 0.75)
        
        ax1.set_ylim([0,yMax])
        ax1.set_title("Calls",fontsize=24)
        ax1.set_ylabel(yVar,fontsize=24)
        ax1.set_xlabel('Strike',fontsize=24)
        ax1.tick_params(axis='both', which='major', labelsize=14)



        putScat = sns.scatterplot(data=putData, x="Strike", y=yVar, hue="Expiry",
                         size=bubSize, sizes=(10, 100),
                         palette="rocket",alpha=0.8, ax=ax2, zorder=10,legend=False)
        ax2.vlines(price, *ax2.get_ylim(),colors="Black", 
                   linestyles='dashed')
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.grid(color = 'black', linestyle = '--', linewidth = 0.75)
        
        ax2.set_ylim([0,yMax])
        ax2.set_title("Puts",fontsize=24)
        ax2.set_ylabel('')
        ax2.set_xlabel('Strike',fontsize=24)
        ax2.tick_params(axis='both', which='major', labelsize=14)
        
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
            ax1.set_ylim([0.01,yMax])
            ax2.set_ylim([0.01,yMax])
            
        elif yVar == "Open Interest":
            callMax = np.max([np.max(callData[yVar].values)])
            putMax = np.max([np.max(callData[yVar].values)])
            maxMax =  np.max([callMax,putMax])
            ax1.set_ylim([0,yMax+250])
            ax2.set_ylim([0,yMax+250])
            ax1.get_shared_y_axes().join(ax1,ax2)

        
    plt.suptitle(ticker + "-" + dtTme, x=0.5, y=0.05, ha ='center', fontsize=18)#, bbox={"facecolor":"orange", "alpha":0.5, "pad":5}
    # callScat.legend(bbox_to_anchor=(1.01, 1), borderaxespad=0, 
    #     fontsize=9)

    # putScat.legend(bbox_to_anchor=(1.01, 1), borderaxespad=0, 
    #                 fontsize=9)
    if not os.path.exists(os.path.join(os.path.join("Plotting",
                                    "TimeSeriesScatter",ticker,yVar))):
        os.mkdir(os.path.join(os.path.join("Plotting",
                                    "TimeSeriesScatter",ticker,yVar)))
    f.tight_layout()
    f.savefig(os.path.join("Plotting","TimeSeriesScatter",ticker,
                           yVar,ticker+"-"+yVar+"-"+dtTme+".png"), dpi=300)
    return()

currentTime = dte.datetime.utcnow()
#currentTime = dte.datetime(2021,3,30,16,0)
# origTime = dte.datetime(2021,2,1,0,0)
origTime = dte.datetime(2021,3,30,16,0)
# tickerList = qdb.getTickers(origTime,currentTime)
# tickerList.sort()
tickerList = ["SPY"]

def getMax(callData,putData,yVar):
    maxY = np.max([np.max(callData[yVar].values),
                     np.max(putData[yVar].values)])
    return(maxY)

for ticker in tickerList:
    try:
        [Price,Calls,Puts] = qdb.queryDB(ticker,origTime,currentTime)
        [lastDate, allDates]  = getOptDates(Calls,Puts)
        
        if not os.path.exists(os.path.join(os.getcwd(),
                        "Plotting","TimeSeriesScatter",ticker)):
            os.makedirs(os.path.join(os.getcwd(),"Plotting",
                                  "TimeSeriesScatter",ticker))
       
        crntPrice = Price[lastDate]
        [crntCalls, crntPuts] = cleanOptTables(Calls[lastDate], Puts[lastDate])   
        maxAsk = getMax(crntCalls,crntPuts,"Ask")
        maxIV = getMax(crntCalls,crntPuts,"Implied Volatility")
        maxOI = getMax(crntCalls,crntPuts,"Open Interest")
        print("\tBuilding time series for: %s" % ticker)
        for date in allDates:
            try:
                nowCalls = Calls[date]
                nowPuts = Puts[date]
                nowPrice = Price[date]         
                [cleanCalls, cleanPuts] = cleanOptTables(nowCalls, nowPuts)
                fmtDateTime = date.astimezone(est).strftime("%Y-%m-%d-%H-%M")
                buildLinePlot(ticker,nowPrice,fmtDateTime,cleanCalls,cleanPuts
                              ,"Ask","Spread",maxAsk)
                buildLinePlot(ticker,nowPrice,fmtDateTime,cleanCalls,cleanPuts,
                              "Implied Volatility","Spread",maxIV)
                buildLinePlot(ticker,nowPrice,fmtDateTime,cleanCalls,cleanPuts,
                              "Open Interest","Ask",maxOI)
                plt.close("all")
            except Exception as f:
                print("\tSomething is jacked in the database for ticker %s at time %s" %(ticker,date))
                print("Error: " %f)
                continue
        sns.reset_orig()
    except Exception as e:
        print("\tCouldn't plot bitch ticker %s" % ticker)
        print("Error %s" % e)
        continue