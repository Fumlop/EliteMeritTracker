from imports import *

this = sys.modules[__name__]  # For holding module globals
this.debug = True

def handleAltruism(entry, factors):
    logger.debug("entry['Name'] in ['Mission_AltruismCredits_name']")
    pattern = r'\b\d+(?:[.,]\d+)*\b'
    logger.debug("Pattern: %s", pattern)
    match = re.search(pattern, entry['LocalisedName']).group()
    logger.debug("match: %s", match)
    if match:
        credits = int(re.sub(r'[,\.]', '', match))
        logger.debug("creditsnumber: %d", credits)
        merits = math.floor(credits / factors["Mission_AltruismCredits_name"])
        logger.debug("meritsnumber: %s", merits)
        return merits
    return 0   