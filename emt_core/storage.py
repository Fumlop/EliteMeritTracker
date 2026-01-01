# core/storage.py - JSON file I/O utilities with error handling and backup
import json
import os
import shutil
from emt_core.logging import logger

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


def _migrate_legacy_file(filename: str) -> bool:
    """Check for legacy file in plugin root and migrate to data/ folder.

    Returns:
        True if file was migrated, False otherwise
    """
    plugin_dir = get_plugin_dir()
    legacy_path = os.path.join(plugin_dir, filename)

    if os.path.exists(legacy_path):
        data_path = os.path.join(get_data_dir(), filename)
        # Only migrate if not already in data/
        if not os.path.exists(data_path):
            try:
                shutil.move(legacy_path, data_path)
                logger.info(f"Migrated {filename} to data/ folder")
                return True
            except Exception as e:
                logger.error(f"Failed to migrate {filename}: {e}")
    return False


def get_file_path(filename: str) -> str:
    """Get full path to a JSON file in the data directory.

    Automatically migrates legacy files from plugin root to data/ folder.
    """
    # Check for and migrate legacy files from plugin root
    _migrate_legacy_file(filename)
    return os.path.join(get_data_dir(), filename)


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


def save_json(filename: str, data, encoder=None, indent=4, create_backup=False) -> bool:
    """Save data to JSON file with atomic write to prevent corruption.

    Uses temp file + rename pattern to ensure atomicity. If save fails mid-write,
    the original file remains intact.

    Args:
        filename: Name of the JSON file in plugin directory
        data: Data to save (must be JSON serializable)
        encoder: Optional custom JSON encoder class
        indent: JSON indentation level (default 4)
        create_backup: If True, creates .backup file before overwriting (default False)
                      Only used during plugin updates for safety

    Returns:
        True if save succeeded, False otherwise
    """
    filepath = get_file_path(filename)
    temp_path = filepath + ".tmp"
    backup_path = filepath + ".backup"

    try:
        # Write to temporary file first
        with open(temp_path, "w", encoding="utf-8") as f:
            if encoder:
                json.dump(data, f, cls=encoder, indent=indent)
            else:
                json.dump(data, f, indent=indent)

        # Create backup of existing file before overwriting (only if requested)
        if create_backup and os.path.exists(filepath):
            try:
                shutil.copy2(filepath, backup_path)
                logger.info(f"Created backup: {backup_path}")
            except Exception as backup_error:
                logger.warning(f"Failed to create backup of {filename}: {backup_error}")
                # Continue anyway - temp file write succeeded

        # Atomic rename (replaces existing file)
        # On Windows, os.replace() is atomic if temp and target are on same drive
        os.replace(temp_path, filepath)
        return True

    except Exception as e:
        logger.error(f"Failed to save {filename}: {e}", exc_info=True)
        # Clean up temp file if it exists
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass
        return False
