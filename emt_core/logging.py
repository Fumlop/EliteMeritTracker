# core/logging.py
import logging
import os
import re
from config import appname

# Get plugin name from parent directory (EliteMeritTracker), not current directory (core)
# Strip version suffix if present (e.g., "EliteMeritTracker-0.4.300.1.025" -> "EliteMeritTracker")
_raw_plugin_name = os.path.basename(os.path.dirname(os.path.dirname(__file__)))
plugin_name = re.sub(r'-\d+\.\d+\.\d+(\.\d+)*$', '', _raw_plugin_name)

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
