from imports import *

this = sys.modules[__name__]  # For holding module globals
this.debug = False

def handleMarketSell(entry, factors, currSys):
    if this.beta:
        logger.debug("entry['event'] in ['MarketSell']")
        sellPrice = entry['SellPrice']
        totalSale = entry['TotalSale']
        pricePaid = entry['AvgPricePaid']
        count = entry['Count']
        merits = (totalSale / factors["MarketSell"]["normal"])*4
        return merits
    return 0
