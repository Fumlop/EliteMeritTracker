# storage.py - JSON file I/O utilities with error handling and backup
import json
import os
import shutil
from merit_log import logger


def get_plugin_dir():
    """Get the plugin directory path"""
    return os.path.dirname(os.path.abspath(__file__))


def get_file_path(filename: str) -> str:
    """Get full path to a file in the plugin directory"""
    return os.path.join(get_plugin_dir(), filename)


def load_json(filename: str, default=None):
    """Load JSON file with error handling.

    Args:
        filename: Name of the JSON file in plugin directory
        default: Default value to return if file doesn't exist or is invalid

    Returns:
        Parsed JSON data or default value
    """
    filepath = get_file_path(filename)

    if not os.path.exists(filepath):
        return default if default is not None else {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        # Create backup of corrupted file
        backup_path = filepath + ".corrupted"
        try:
            shutil.copy2(filepath, backup_path)
            logger.error(f"{filename} is corrupted: {e}. Backup saved to {backup_path}")
        except Exception as backup_error:
            logger.error(f"{filename} is corrupted: {e}. Failed to create backup: {backup_error}")
        return default if default is not None else {}
    except Exception as e:
        logger.error(f"Failed to load {filename}: {e}", exc_info=True)
        return default if default is not None else {}


def save_json(filename: str, data, encoder=None, indent=4) -> bool:
    """Save data to JSON file.

    Args:
        filename: Name of the JSON file in plugin directory
        data: Data to save (must be JSON serializable)
        encoder: Optional custom JSON encoder class
        indent: JSON indentation level (default 4)

    Returns:
        True if save succeeded, False otherwise
    """
    filepath = get_file_path(filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            if encoder:
                json.dump(data, f, cls=encoder, indent=indent)
            else:
                json.dump(data, f, indent=indent)
        return True
    except Exception as e:
        logger.error(f"Failed to save {filename}: {e}", exc_info=True)
        return False
