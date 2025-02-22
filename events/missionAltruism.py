from imports import *

this = sys.modules[__name__]  # For holding module globals
this.debug = False

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