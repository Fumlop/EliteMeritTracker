import os
import tkinter as tk
from tkinter import ttk
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
from configPlugin import *
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

configPlugin = ConfigPlugin()

if not logger.hasHandlers():
    level = logging.INFO  # So logger.info(...) is equivalent to print()

    logger.setLevel(level)
    logger_channel = logging.StreamHandler()
    logger_formatter = logging.Formatter(f'%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d:%(funcName)s: %(message)s')
    logger_formatter.default_time_format = '%Y-%m-%d %H:%M:%S'
    logger_formatter.default_msec_format = '%s.%03d'
    logger_channel.setFormatter(logger_formatter)
    logger.addHandler(logger_channel)
