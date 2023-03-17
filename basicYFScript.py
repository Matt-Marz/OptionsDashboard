# -*- coding: utf-8 "-*-

"""
Some experimentation with yahoo finance API

"""

from yahoo_fin import stock_info as si
import yahoo_fin.options as ops
import matplotlib as plt
import pandas as pd
import numpy as np
import datetime as dte
from itertools import chain
 
# def main():
def scrapeOptionsData():
    
    [DOW,QQQ,OTC,SPY] = getTickers()
    tmpTickers = list(chain(*[DOW,QQQ,OTC,SPY]))
    tmpTickset = set(tmpTickers)
    allTickers = list(tmpTickset)
    

    # print(len(allTickers))
    [AppleCalls,ApplePuts] = getOptionsData("AAPL")
    
    return(AppleCalls)
    

def getTickers():
    
    DOW = si.tickers_dow()
    QQQ = si.tickers_nasdaq()
    OTC = si.tickers_other()
    SPY = si.tickers_sp500()
    
    return(DOW,QQQ,OTC,SPY)

def getOptionsData(opTicker):
    
    expDates = ops.get_expiration_dates(opTicker)
    expDateIsoFmt = [dte.datetime.strptime(rawDate, '%B %d, %Y') for rawDate in expDates]
    AllCalls = pd.DataFrame()
    AllPuts  = pd.DataFrame()
    
    reqCount = 0
    for expiry in expDateIsoFmt:
         # print(expiry)
         tmpPuts        = ops.get_puts(opTicker,expiry) 
         tmpCalls       = ops.get_calls(opTicker,expiry) 
         AllPuts        = AllPuts.append(tmpPuts)
         AllCalls       = AllCalls.append(tmpCalls)
         reqCount = reqCount + 2
     
    return(AllCalls,AllPuts,reqCount)
    
callData = scrapeOptionsData()   

# if __name__ == "__main__":
#     main()