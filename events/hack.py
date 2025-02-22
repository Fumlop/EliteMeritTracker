from imports import *

this = sys.modules[__name__]  # For holding module globals
this.debug = False

def handleAdvertiseHack(entry, factors, power):
    logger.debug("entry['event'] in ['handleAdvertiseHack']")
    if entry['event'] == "HoloscreenHacked" and entry['PowerAfter'] == power:
        logger.debug("HoloscreenHacked %s", factors["Hacking"]["Holoscreen"])
        return factors["Hacking"]["Holoscreen"]
    return 0