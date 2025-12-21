"""
Streaming parser for systems-game-data.json

This module provides efficient lookups in the large game data file without loading
the entire 40MB file into memory. It streams through the JSON array and returns
as soon as the target system is found.
"""

import os
import json
from typing import Optional, Dict, Any
from emt_core.logging import logger


def get_system_data_file_path() -> str:
    """Get the path to systems-game-data.json"""
    plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(plugin_dir, "system_data", "systems-game-data.json")


def lookup_system_economy(system_name: str) -> Optional[str]:
    """
    Look up the primary economy type for a system.

    Streams through the JSON file without loading it entirely into memory.
    Returns None if system not found or file doesn't exist.

    Args:
        system_name: The exact name of the star system

    Returns:
        Primary economy type string (e.g., "Industrial", "High Tech") or None
    """
    try:
        file_path = get_system_data_file_path()

        if not os.path.exists(file_path):
            logger.debug(f"System game data file not found: {file_path}")
            return None

        # Stream through the JSON array
        with open(file_path, 'r', encoding='utf-8') as f:
            # Skip opening bracket
            char = f.read(1)
            if char != '[':
                logger.error("Invalid JSON format in systems-game-data.json")
                return None

            buffer = ""
            in_object = False
            brace_depth = 0

            while True:
                char = f.read(1)
                if not char:
                    break

                if char == '{':
                    in_object = True
                    brace_depth += 1
                    buffer += char
                elif char == '}':
                    buffer += char
                    brace_depth -= 1

                    if brace_depth == 0 and in_object:
                        # Complete object found, parse it
                        try:
                            system_obj = json.loads(buffer)

                            # Check if this is the system we're looking for
                            if system_obj.get('name') == system_name:
                                return system_obj.get('primaryEconomy')

                        except json.JSONDecodeError:
                            pass  # Skip malformed objects

                        # Reset buffer for next object
                        buffer = ""
                        in_object = False
                elif in_object:
                    buffer += char

        return None  # System not found

    except Exception as e:
        logger.debug(f"Error looking up system economy for '{system_name}': {e}")
        return None


def lookup_system_info(system_name: str) -> Optional[Dict[str, Any]]:
    """
    Look up full system information.

    Streams through the JSON file without loading it entirely into memory.
    Returns None if system not found or file doesn't exist.

    Args:
        system_name: The exact name of the star system

    Returns:
        Dictionary with system data or None
    """
    try:
        file_path = get_system_data_file_path()

        if not os.path.exists(file_path):
            logger.debug(f"System game data file not found: {file_path}")
            return None

        # Stream through the JSON array
        with open(file_path, 'r', encoding='utf-8') as f:
            # Skip opening bracket
            char = f.read(1)
            if char != '[':
                logger.error("Invalid JSON format in systems-game-data.json")
                return None

            buffer = ""
            in_object = False
            brace_depth = 0

            while True:
                char = f.read(1)
                if not char:
                    break

                if char == '{':
                    in_object = True
                    brace_depth += 1
                    buffer += char
                elif char == '}':
                    buffer += char
                    brace_depth -= 1

                    if brace_depth == 0 and in_object:
                        # Complete object found, parse it
                        try:
                            system_obj = json.loads(buffer)

                            # Check if this is the system we're looking for
                            if system_obj.get('name') == system_name:
                                return system_obj

                        except json.JSONDecodeError:
                            pass  # Skip malformed objects

                        # Reset buffer for next object
                        buffer = ""
                        in_object = False
                elif in_object:
                    buffer += char

        return None  # System not found

    except Exception as e:
        logger.debug(f"Error looking up system info for '{system_name}': {e}")
        return None
