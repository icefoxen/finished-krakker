#!/usr/bin/env python3
import krakenex.api

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

def constructPotentialTrades(assets, assetpairs):
    """Produces a table of, for each asset, what it can be traded for."""
    trades = {}
    for asset in assets.keys():
        trades[asset] = []
    for k,v in assetpairs.items():
        base = v['base']
        quote = v['quote']
        trades[base].append(quote)

    return trades


def main():
    k = krakenex.API()
    assets = getAssetInfo(k)
    assetPairs = getAssetPairs(k)
    #print('-----------ASSET PAIRS-------------------')
    #for key,val in res.items():
    #    print(key)
    #    print(val)
    pairs = assetPairs.keys()
    tickers = getTickers(k, pairs)
    print('-----------TICKERS-----------------------')
    formstr = "{:<10}{:>15}{:>15}"
    print(formstr.format("Ticker", "Bid", "Ask"))
    for key, val in tickers.items():
        bid = val['b'][0]
        ask = val['a'][0]
        print(formstr.format(key, bid, ask))
    print(constructPotentialTrades(assets, assetPairs))

if __name__ == '__main__':
    main()
