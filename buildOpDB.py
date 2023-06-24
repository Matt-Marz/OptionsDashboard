# -*- coding: utf-8 -*-
"""
Build out the options database with scheduled execution

Start with the top 10 S&P500 + daily top volume 

"""

import schedule
import time
import QueryYF
import datetime as dte

# import threading
# try:
#     import queue
# except ImportError:
#     import Queue as queue

# start_time = time.time()
# [price, nReqs] = QueryYF.scrapeOptionsData("GME")
# print("--- %s seconds ---" % (time.time() - start_time))
# print(price)
# print(nReqs)

  
def main():

    getDOW, getQQQ, getSPY, getOTC, getTop = False, False, False, False, True
    [_,_,_,_,TopVol] = QueryYF.getTickers(getDOW, getQQQ, getSPY, getOTC, getTop)
    
    MyTickers = ["AAPL" ,"ABNB","NFLX","MSFT","TSLA",
                 "GOOG","GME","VXX","SPY","QQQ","^VIX","^SPX"]
    MyTickers = QueryYF.concatTickers([TopVol[0:24],MyTickers])
    print(MyTickers)
    # buildOpDatabase(MyTickers)
    
    # for i in ["15:00"]:
    #     schedule.every().sunday.at(i).do(buildOpDatabase, MyTickers)
    # while True:
    #     schedule.run_pending()
    #     time.sleep(30) 
    
    for i in ["09:31", "12:30"]:
        schedule.every().monday.at(i).do(buildOpDatabase, MyTickers)
        schedule.every().tuesday.at(i).do(buildOpDatabase, MyTickers)
        schedule.every().wednesday.at(i).do(buildOpDatabase, MyTickers)
        schedule.every().thursday.at(i).do(buildOpDatabase, MyTickers)
        schedule.every().friday.at(i).do(buildOpDatabase, MyTickers)

    while True:
        schedule.run_pending()
    #     time.sleep(30)
    print("\n\tScraping on my scraper bike")
    return()
    
def pullTickers():
    getDOW, getQQQ, getSPY, getOTC, getTop = False, False, False, False, True
    [DOW,QQQ,OTC,SPY,TP] = QueryYF.getTickers(getDOW, getQQQ, 
                                              getSPY, getOTC, getTop)
    #sortedSPY = QueryYF.sortTickersByCap(SPY)
    topVol = TP[0:24]    
    indices = [topVol]#, sortedSPY.iloc[0:9]["Ticker"]]
    MyTickers = QueryYF.concatTickers(indices)
    print("\nPulling a limited ticker subset to stay under YF limit")
    print(MyTickers)
    return(MyTickers)

def buildOpDatabase(scrapeTickers):
    nReqs = 0
    start_time = time.time()
    print("\nBegan querying options data at %s" % dte.datetime.now())
    for ticker in scrapeTickers:
        print("\tPulling options data from ticker %s" % ticker)
        ticker_time = time.time()
        try:
            [price, yReqCount] = QueryYF.scrapeOptionsData(ticker)
            time.sleep(100)
        except Exception as e:
            print("\t\tFailed to fully pull options for %s" % ticker)
            print("\t\tError: %s" % e)
            continue
        tickerEndTime = (time.time() - ticker_time)
        nReqs = nReqs + yReqCount
        print("\tAdded %s to opDB in %.2f seconds using %i queries" % (ticker, 
                                                               tickerEndTime, 
                                                               yReqCount))
        print("\t%s current price: %.2f" % (ticker,price))
              
        if nReqs >= 1950:
            print("\n\tQueries about to exceed YF limit, exiting")
            break
       
    TotQueryTime = (time.time() - start_time)
    print("\tTotal queries from YF = %i in %i seconds" % (nReqs, TotQueryTime)) 
    
    return()
    
if __name__ == "__main__":
    main()