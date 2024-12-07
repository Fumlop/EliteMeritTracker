import os
import tkinter as tk
import sys
import json
import requests
import myNotebook as nb
from typing import Dict, Any
from PIL import Image, ImageTk 
import re
import math#
import event_handler
from os import path
from companion import CAPIData, SERVER_LIVE, SERVER_LEGACY, SERVER_BETA
from config import config, appname
import logging
from datetime import datetime, timedelta
this = sys.modules[__name__]  # For holding module globals
this.debug = False
plugin_name = os.path.basename(os.path.dirname(__file__))

this.beta = False

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

def handleCombat(entry, factors, targets):
    logger.debug("entry['Bounty']")
    if "TotalReward" in entry and entry["TotalReward"] <= 2000:
        logger.debug("entry['Bounty'] - Power")
        if entry["PilotName"] in targets:
            try:
                merits = factors["CombatPower"][entry["PilotRank"]]
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
    
