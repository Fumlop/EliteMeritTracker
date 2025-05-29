import os
import sys
import json
import math
import requests
import zipfile
import shutil
import io
import csv
import re
import logging
from datetime import datetime, timedelta

from configPlugin import ConfigPlugin
from config import config, appname
from report import Report
from history import PowerPlayHistory
from power import PledgedPower
# Singleton-Config (wird überall importiert, immer gleiches Objekt)
configPlugin = ConfigPlugin()
pledgedPower = PledgedPower()
report = Report()
history = PowerPlayHistory()
systems = {}  # leeres Dict

# Logger-Konfiguration für das gesamte Plugin
plugin_name = os.path.basename(os.path.dirname(__file__))
logger = logging.getLogger(f'{appname}.{plugin_name}')

if not logger.hasHandlers():
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d:%(funcName)s: %(message)s'
    )
    formatter.default_time_format = '%Y-%m-%d %H:%M:%S'
    formatter.default_msec_format = '%s.%03d'
    handler.setFormatter(formatter)
    logger.addHandler(handler)
