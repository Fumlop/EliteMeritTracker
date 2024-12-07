import os
import tkinter as tk
import sys
import json
import requests
import myNotebook as nb
from typing import Dict, Any
from PIL import Image, ImageTk 
import re
import event_handler
from os import path
from companion import CAPIData, SERVER_LIVE, SERVER_LEGACY, SERVER_BETA
from config import config, appname
import logging
from datetime import datetime, timedelta
this = sys.modules[__name__]  # For holding module globals
this.debug = False
plugin_name = os.path.basename(os.path.dirname(__file__))

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
    logger.debug("entry['event'] in ['MarketSell']")
    sellPrice = entry['SellPrice']
    totalSale = entry['TotalSale']
    pricePaid = entry['AvgPricePaid']
    count = entry['Count']
    merits = (totalSale / factors["MarketSell"]["normal"])*4
    return merits

def handleAltruism(entry, factors,currSys):
    logger.debug("entry['Name'] in ['Mission_AltruismCredits_name']")
    pattern = r'\b\d+(?:[.,]\d+)*\b'
    logger.debug("Pattern: %s", pattern)
    match = re.search(pattern, entry['LocalisedName']).group()
    logger.debug("match: %s", match)
    if match:
        creditsnumber = int(re.sub(r'[,\.]', '', match))
        logger.debug("creditsnumber: %s", creditsnumber)
        merits = creditsnumber / factors["Mission_AltruismCredits_name"]
        logger.debug("creditsnumber: %s", merits)
        return merits
    return 0

def handlePowerKill(entry, factors,currSys):
    logger.debug("entry['event'] in ['MissionCompleted']")
    
def handleShipScan(entry, factors,currSys):
    logger.debug("entry['event'] in ['MissionCompleted']")

def handleAdvertiseHack(entry, factors,currSys):
    logger.debug("entry['event'] in ['MissionCompleted']")
    
def handleSalvage(entry, factors,currSys):
    logger.debug("entry['event'] in ['MissionCompleted']")