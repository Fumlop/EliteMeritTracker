# Core utilities
from .logging import logger, plugin_name
from .config import configPlugin, ConfigPlugin
from .state import state
from .storage import get_plugin_dir, get_data_dir
from .duplicate import merit_ledger, MeritLedger, reset_merit_tracking
from .report import report, Report
