# core/storage.py - where the plugin's data folder is.
#
# The JSON reading and writing that used to live here went when the store
# moved to SQLite; emt_core/migrate.py reads data/*.json directly, once.
import os

# Data directory for JSON files
DATA_DIR = "data"


def get_plugin_dir():
    """Get the plugin directory path (parent of core/)"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_dir():
    """Get the data directory path, creating it if needed"""
    data_path = os.path.join(get_plugin_dir(), DATA_DIR)
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    return data_path
