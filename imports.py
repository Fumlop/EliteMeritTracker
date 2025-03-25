import os
import tkinter as tk
import json
import math
import requests
import zipfile
import shutil
import io
import sys
import tkinter as tk
import csv
import os
from tkinter import filedialog
from datetime import datetime, timedelta
import myNotebook as nb
from typing import Dict, Any
from PIL import Image, ImageTk 
import re
from ttkHyperlinkLabel import HyperlinkLabel
from companion import CAPIData, SERVER_LIVE, SERVER_LEGACY, SERVER_BETA
from config import config, appname
import logging

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


def get_system_state_power(system_data):
    system_state = system_data.get("state")
    if system_state in ['Stronghold', 'Fortified', 'Exploited']:
        if len(system_data.get("power"))>1:
            return  [system_data.get("power"),next(p for p in system_data.get("powerCompetition") if p != system_data.get("power"))]
        else: 
            return  [system_data.get("power"),"None"]
    if system_state == 'Unoccupied':
       conflict = system_data.get('powerConflict')
       if len(conflict) == 1: 
           return [system_data.get("powerConflict")[0]['Power'], "None"]
       else:
           return [system_data.get("powerConflict")[0]['Power'], system_data.get("powerConflict")[1]['Power']]

def get_progress(system_data):
    system_state = system_data.get("state")
    if system_state in ['Stronghold', 'Fortified', 'Exploited']:
       return  system_data.get("progress", 0) * 100
    return system_data.get('powerConflict')[0]['ConflictProgress']*100

def get_system_state(system_data):
    system_state = system_data.get("state")
    if system_state in ['Stronghold', 'Fortified', 'Exploited']:
       return  system_state

    if system_state == 'Unoccupied':
       progress = system_data.get('powerConflict')[0]['ConflictProgress']*100
       if progress < 30: return 'Unoccupied'
       if progress < 100: return 'Contested'
       if progress >= 100: return 'Controlled'
       
def get_system_power_status_text(reinforcement, undermining):
    if reinforcement == 0 and undermining == 0:
        return "Neutral"  # If both are 0, show neutral

    total = reinforcement + undermining  # Total value

    # Calculate actual percentage share
    reinforcement_percentage = (reinforcement / total) * 100
    undermining_percentage = (undermining / total) * 100

    if reinforcement > undermining:
        return f"NET +{reinforcement_percentage:.2f}%"
    else:
        return f"NET -{undermining_percentage:.2f}%"
    
def get_reinf_undermine(system_data):
    system_state = system_data.get("state")
    if system_state in ['Stronghold', 'Fortified', 'Exploited']:
       return [system_data.get("statereinforcement", 0),system_data.get("stateundermining", 0)]
    else:
       return [system_data.get('powerConflict')[0]['ConflictProgress'],0]