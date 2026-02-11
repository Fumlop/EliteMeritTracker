# core/logging.py
import logging
import os
from config import appname


class EDMCLogRecordFilter(logging.Filter):
    """
    Filter to add missing fields required by EDMC's logging formatter.

    EDMC's log formatter expects 'osthreadid' field which causes KeyError
    if not present. This filter adds it to prevent logging failures.
    """
    def filter(self, record):
        # Add osthreadid field if missing (EDMC formatter requirement)
        if not hasattr(record, 'osthreadid'):
            # Use current thread's native ID if available (Python 3.8+)
            try:
                record.osthreadid = getattr(os, 'gettid', lambda: 0)()
            except:
                record.osthreadid = 0
        return True


# Use fixed plugin name instead of path-based detection
# This is more reliable and avoids issues with versioned directory names
plugin_name = "EliteMeritTracker"

logger = logging.getLogger(f'{appname}.{plugin_name}')

if not logger.hasHandlers():
    logger.setLevel(logging.INFO)
    # Add filter to inject missing EDMC logging fields
    logger.addFilter(EDMCLogRecordFilter())
    # Don't add custom handlers - use EDMC's logging system
    # EDMC will handle formatting and output
