from imports import *
from events import *

this = sys.modules[__name__]  # For holding module globals
this.debug = False
plugin_name = os.path.basename(os.path.dirname(__file__))

this.beta = False


this.RecentlyScannedShips = []

logger = logging.getLogger(f'{appname}.{plugin_name}')
if not logger.hasHandlers():
    level = logging.INFO  # So logger.info(...) is equivalent to print()

    logger.setLevel(level)
    logger_channel = logging.StreamHandler()
    logger_formatter = logging.Formatter(f'%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d:%(funcName)s: %(message)s')
    logger_formatter.default_time_format = '%Y-%m-%d %H:%M:%S'
    logger_formatter.default_msec_format = '%s.%03d'
    logger_channel.setFormatter(logger_formatter)
    logger.addHandler(logger_channel)

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

def handleAltruism(entry, factors):
    logger.debug("entry['Name'] in ['Mission_AltruismCredits_name']")
    pattern = r'\b\d+(?:[.,]\d+)*\b'
    logger.debug("Pattern: %s", pattern)
    match = re.search(pattern, entry['LocalisedName']).group()
    logger.debug("match: %s", match)
    if match:
        credittext = re.sub(r'[,\.]', '', match)
        logger.debug("creditsnumber: %s", credittext)
        merits = math.ceil((factors["Mission_AltruismCredits_name"]-1.2)*0.000108)
        logger.debug("creditsnumber: %s", merits)
        return merits
    return 0    

def handlePowerKill(entry, factors):
    logger.debug("entry['event'] in ['MissionCompleted']")

def handleAdvertiseHack(entry, factors, power):
    logger.debug("entry['event'] in ['handleAdvertiseHack']")
    if entry['event'] == "HoloscreenHacked" and entry['PowerAfter'] == power:
        logger.debug("HoloscreenHacked %s", factors["Hacking"]["Holoscreen"])
        return factors["Hacking"]["Holoscreen"]
    return 0
    
def handleSalvage(entry, factors):
    logger.debug("entry['event'] in ['handleSalvage']")
    merits = factors["Salvage" ][entry['Name']]
    logger.debug("handleSalvage %s", merits)
    return merits

def handleBounty(entry, factors):
    bountyValue = entry["TotalReward"]
    #Currently this seems more accurate than math.ceil for bounties:
    merits = round(bountyValue / factors["Bounty"])
    #Log bounty earned and calculated merits earned, for troubleshooting
    logger.info("Bounty earned: %d", bountyValue)
    logger.info("Total merits from this bounty: %d", merits)
    return merits

def handleShipTargeted(entry, factors):
    if "ScanStage" in entry and entry['ScanStage'] == 3:
        pilotName = entry['PilotName']
        if pilotName in this.RecentlyScannedShips:
            #This ship has been scanned already, ignore it
            return 0

        logger.debug("ShipTargeted - fully scanned")
        merits = factors["ShipScan"]
        logger.debug("Scan merits: %s", merits)
        this.RecentlyScannedShips.append(pilotName)
        if len(this.RecentlyScannedShips) > 25:
            #Remove oldest entry from the list
            this.RecentlyScannedShips.pop(0)
        return merits
    else:
        return 0

def handleSupercruise():
    #On entering or exiting supercruise, clear tracking of recently scanned ships
    this.RecentlyScannedShips = []
