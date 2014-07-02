#!/usr/bin/env python3
import krakenex.api
from decimal import *

"""Krakker: A test program to download market info from the kraken.com
(crypto)currency exchange and look for profitable arbitrage trades."""

def checkResponseError(query, args, response):
    err = response['error']
    res = response['result']
    if len(err) == 0:
        return res
    else:
        raise Exception("Error in request: {} {}\n{}".format(query, args, err))

def doQuery(k, query, args):
    res = k.query_public(query, args)
    return checkResponseError(query, args, res)

def getAssetInfo(k):
    return doQuery(k, "Assets", '')

def getAssetPairs(k):
    return doQuery(k, "AssetPairs", '')

def getTickers(k, pairs):
    pairstring = ','.join(pairs)
    return doQuery(k, "Ticker", {'pair' : pairstring})

def constructPotentialTrades(assetpairs, tickers):
    """Produces a list of potential trades, of format (from, to, cost)."""
    trades = []
    #print(tickers)
    for k,v in assetpairs.items():
        #print(k,v)
        assetpair = k
        tickerforpair = tickers[k]
        #print(tickerforpair)
        ask = float(tickerforpair['a'][0])
        bid = float(tickerforpair['b'][0])
        base = v['base']
        quote = v['quote']
        if bid == float(0.0):
            bid = float(0.000000000001)
        trade1 = (base, quote, float(1.0)/bid)
        trades.append(trade1)
        trade2 = (quote, base, ask)
        trades.append(trade2)

    return trades

def turnTradesIntoTableBlah(trades):
    tradetable = {}
    for base, _, _ in trades:
        tradetable[base] = {}
    for base, quote, price in trades:
        tradetable[base][quote] = price
    #print(tradetable)
    return tradetable

def executeTrade(assetAmount, price):
    if price == 0.0:
        return "DIV0"
    if type(assetAmount) is not float:
        # Pass through error values
        return assetAmount
    else:
        return assetAmount / price

def testTrades(trades):
    tradetable = turnTradesIntoTableBlah(trades)
    tradeResults = []
    for asset1 in tradetable.keys():
        for asset2 in tradetable[asset1].keys():
            asset1Amount = 1.0
            asset1_2price = tradetable[asset1][asset2]
            asset2Amount = executeTrade(asset1Amount, (asset1, asset2, asset1_2price))
            print("Traded {} {} for {} {} at price {} {}/{}".format(
                asset1Amount, asset1, asset2Amount, asset2, asset1_2price,
                asset1, asset2))
            asset2_1price = tradetable[asset2][asset1]
            asset1FinalAmount = executeTrade(asset2Amount, (asset2, asset1, asset2_1price))
            print("Traded {} {} for {} {} at price {} {}/{}".format(
                asset2Amount, asset2, asset1FinalAmount, asset1, asset2_1price,
                asset2, asset1))
            print()

def findProfitableTrades(trades):
    """Brute-force through a bunch of trades to find the ones where you get more in the end than you started with.

Basically starts with asset A, runs A -> B -> C -> A, and sees how much A is left.

The REAL way to do this would be to represent trades as the edges of a directed
weighted graph, and try to find loops that add up to a positive weight.

"""
    tradetable = turnTradesIntoTableBlah(trades)
    tradeResults = []
    for asset1 in tradetable.keys():
        for asset2 in tradetable[asset1].keys():
            for asset3 in tradetable[asset2].keys():
                if asset3 == asset1:
                    continue
                #print(asset1, asset2, asset3)
                try:
                    asset1Amount = 1.0
                    asset1_2price = tradetable[asset1][asset2]
                    asset2Amount = executeTrade(asset1Amount, asset1_2price)
                    asset2_3price = tradetable[asset2][asset3]
                    asset3Amount = executeTrade(asset2Amount, asset2_3price)
                    try:
                        asset3_1price = tradetable[asset3][asset1]
                        asset1Final = executeTrade(asset3Amount, asset3_1price)
                        tradeResults.append((asset1, asset2, asset3, asset1Final))
                    except KeyError as e:
                        #print(e)
                        # asset3 cannot be traded for asset1 for some reason
                        # Which does happen...
                        tradeResults.append((asset1, asset2, asset3, "INEXCHANGABLE"))
                except ZeroDivisionError:
                    # The price of some asset is 0
                    tradeResults.append((asset1, asset2, asset3, "DIVZ"))
    return tradeResults
        

def main():
    k = krakenex.API()
    #assets = getAssetInfo(k)
    assetPairs = getAssetPairs(k)
    #print('-----------ASSET PAIRS-------------------')
    #for key,val in res.items():
    #    print(key)
    #    print(val)

    pairs = assetPairs.keys()
    tickers = getTickers(k, pairs)
    print('-----------TICKERS-----------------------')
    formstr = "{:<10}{:<10}{:>45}"
    print(formstr.format("Ticker", "Bid", "Ask"))
    for key, val in tickers.items():
        bid = val['b'][0]
        ask = val['a'][0]
        print(formstr.format(key, bid, ask))

    print('-----------POSSIBLE TRADES---------------')
    trades = constructPotentialTrades(assetPairs, tickers)
    trades.sort()
    for frm, to, price in trades:
        #print(frm, to, price)
        print(formstr.format(frm, to, price))

    #testTrades(trades)

    tradeResults = findProfitableTrades(trades)
    tradeResults.sort()
    anomalies = []
    profitableResults = []
    print('-----------TRADE RESULTS-----------------')
    for result in tradeResults:
        asset1, asset2, asset3, amount = result
        print("{} -> {} -> {} ==> {}".format(asset1, asset2, asset3, amount))
        if type(amount) is not float:
            anomalies.append(result)
        elif amount >= float(1.0):
            profitableResults.append(amount)

    print('-----------PROFITABLE TRADES-------------')
    for asset1, asset2, asset3, result in profitableResults:
        print("{} -> {} -> {} ==> {}".format(asset1, asset2, asset3, result))

    if False:
        print('-----------ANOMALOUS RESULTS-------------')
        def findTrade(asset1, asset2, trades):
            def _search(t):
                base, quote, _ = t
                return base == asset1 and quote == asset2
                return next((x for x in trades if _search(x)), (asset1, asset2, "INVALID_TRADE"))

        for asset1, asset2, asset3, result in anomalies:
            print("{} -> {} -> {} ==> {}".format(asset1, asset2, asset3, result))
            t1 = findTrade(asset1, asset2, trades)
            t2 = findTrade(asset2, asset3, trades)
            t3 = findTrade(asset3, asset1, trades)
            print(t1)
            print(t2)
            print(t3)

if __name__ == '__main__':
    main()
