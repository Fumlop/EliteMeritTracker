# core/logging.py
import logging
from config import appname

# Use fixed plugin name instead of path-based detection
# This is more reliable and avoids issues with versioned directory names
plugin_name = "EliteMeritTracker"

logger = logging.getLogger(f'{appname}.{plugin_name}')

if not logger.hasHandlers():
    logger.setLevel(logging.INFO)
    # Don't add custom handlers - use EDMC's logging system
    # EDMC will handle formatting and output
