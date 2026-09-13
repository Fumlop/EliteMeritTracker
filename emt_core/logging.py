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


plugin_name = "EliteMeritTracker"

# The logger is named after the folder holding load.py, as EDMC's plugin docs
# say. EDMC sets up the fields its formatter needs (osthreadid, qualname) on
# the logger of that name; a fixed name broke every log line for anyone who
# unpacked into a versioned folder like EliteMeritTracker-0.4.3.1.200.
plugin_folder = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(f'{appname}.{plugin_folder}')

if not logger.hasHandlers():
    logger.setLevel(logging.INFO)
    # Add filter to inject missing EDMC logging fields
    logger.addFilter(EDMCLogRecordFilter())
    # Don't add custom handlers - use EDMC's logging system
    # EDMC will handle formatting and output
