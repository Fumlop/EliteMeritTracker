from imports import *

this = sys.modules[__name__]  # For holding module globals
this.debug = False


def handleSalvage(entry, factors):
    logger.debug("entry['event'] in ['handleSalvage']")
    merits = factors["Salvage" ][entry['Name']]
    logger.debug("handleSalvage %s", merits)
    return merits