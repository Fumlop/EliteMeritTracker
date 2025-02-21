from imports import *

this = sys.modules[__name__]  # For holding module globals
this.debug = False
plugin_name = os.path.basename(os.path.dirname(__file__))

this.beta = False

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

def handleCombat(entry, factors, targets,power):
    logger.debug("entry['Bounty']")
    if "TotalReward" in entry and entry["Power"] not in ["",power]:
        logger.debug("entry['Bounty'] - Power")
        if entry["PilotName"] in targets:
            logger.debug("entry['Pilot'] - %s",entry["PilotName"])
            logger.debug("entry['Rank'] - %s",targets[entry["PilotName"]]["Rank"])
            try:
                size = "M"
                if targets[entry["PilotName"]]["Rank"] in factors["CombatPower"]:
                    merits = factors["CombatPower"][entry["PilotName"]]["Rank"]
                else:
                    merits = 0
                logger.debug("merits['Bounty'] - %s", merits)
                return merits
            except KeyError as e:
                logger.debug(e)
    else:
        logger.debug("entry['Bounty'] - Normal")
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