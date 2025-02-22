from imports import *

this = sys.modules[__name__]  # For holding module globals
this.debug = False

this.RecentlyScannedShips = []

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
    
def handlePowerKill(entry, factors):
    logger.debug("entry['event'] in ['MissionCompleted']")

def handleBounty(entry, factors):
    bountyValue = entry["TotalReward"]
    #Currently this seems more accurate than math.ceil for bounties:
    merits = round(bountyValue / factors["Bounty"])
    #Log bounty earned and calculated merits earned, for troubleshooting
    logger.info("Bounty earned: %d", bountyValue)
    logger.info("Total merits from this bounty: %d", merits)
    return merits


def resetTargets():
    #On entering or exiting supercruise, clear tracking of recently scanned ships
    this.RecentlyScannedShips = []