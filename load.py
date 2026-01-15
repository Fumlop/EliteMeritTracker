import os
import requests
import shutil
import zipfile
import myNotebook as nb
import io
import re
import gzip
import threading
from typing import Dict, Any

from emt_core.report import report
from emt_models.system import systems, StarSystem, loadSystems, dumpSystems
from emt_models.salvage import Salvage, salvageInventory, save_salvage, load_salvage, VALID_POWERPLAY_SALVAGE_TYPES
from emt_models.power import pledgedPower
from emt_ui.main import TrackerFrame
from emt_core.duplicate import track_journal_event, process_powerplay_event, reset_duplicate_tracking
from emt_core.config import configPlugin
from emt_core.logging import logger
from config import config, appname
from emt_ui.config import create_config_frame
from emt_models.backpack import playerBackpack, save_backpack, load_backpack
from emt_ppdata.undermining import is_valid_um_data
from emt_ppdata.reinforcement import is_valid_reinf_data
from emt_ppdata.acquisition import is_valid_acq_data
from emt_core.state import state

# Module globals
trackerFrame = None
autosave_timer = None

def _get_github_release_data():
    """Fetch latest GitHub release data"""
    try:
        response = requests.get('https://api.github.com/repos/Fumlop/EliteMeritTracker/releases/latest', timeout=10)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        logger.exception('Error fetching GitHub release data')
        return None


def _get_github_prerelease_data():
    """Fetch latest GitHub pre-release data"""
    try:
        response = requests.get('https://api.github.com/repos/Fumlop/EliteMeritTracker/releases', timeout=10)
        if response.status_code != 200:
            return None
        releases = response.json()
        # Find the first pre-release
        for release in releases:
            if release.get('prerelease', False):
                return release
        return None
    except Exception as e:
        logger.exception('Error fetching GitHub pre-release data')
        return None


# Legacy files that have been moved to subfolders and should be cleaned up
# JSON files are migrated to data/ by storage.py before this cleanup runs
LEGACY_FILES_TO_REMOVE = [
    "pluginUI.py", "pluginDetailsUI.py", "pluginConfigUI.py",  # moved to ui/
    "system.py", "power.py", "backpack.py", "salvage.py", "ppcargo.py",  # moved to models/
    "umdata.py", "reinfdata.py", "acqdata.py",  # moved to ppdata/
    "pluginConfig.py", "plugin_state.py", "storage.py", "merit_log.py",  # moved to core/
    "duplicate.py", "report.py",  # moved to core/
    "test_backpack.py",  # moved to tests/
    "INSTALLATION_GUIDE.md", "CODE_OF_CONDUCT.md", "SECURITY.md",  # moved to docs/
    "systems.json", "power.json", "backpack.json", "salvage.json",  # migrated to data/
]

# Legacy folders that have been renamed to avoid EDMC plugin loading conflicts
LEGACY_FOLDERS_TO_REMOVE = [
    "ui",      # renamed to emt_ui
    "core",    # renamed to emt_core
    "models",  # renamed to emt_models
    "ppdata",  # renamed to emt_ppdata
]


def _cleanup_legacy_files(plugin_dir):
    """Backup and remove legacy files/folders that have been moved or renamed.

    JSON files are already migrated to data/ by storage.py before this runs.
    """
    backup_dir = os.path.join(plugin_dir, "backup_legacy")
    files_backed_up = False

    # Clean up legacy files
    for filename in LEGACY_FILES_TO_REMOVE:
        filepath = os.path.join(plugin_dir, filename)
        if os.path.exists(filepath):
            try:
                # Create backup directory if needed
                if not files_backed_up:
                    os.makedirs(backup_dir, exist_ok=True)
                    files_backed_up = True

                # Move to backup instead of deleting
                backup_path = os.path.join(backup_dir, filename)
                shutil.move(filepath, backup_path)
                logger.info(f"Backed up legacy file: {filename}")
            except Exception as e:
                logger.warning(f"Failed to backup legacy file {filename}: {e}")

    # Clean up legacy folders (renamed to avoid EDMC conflicts)
    for foldername in LEGACY_FOLDERS_TO_REMOVE:
        folderpath = os.path.join(plugin_dir, foldername)
        if os.path.exists(folderpath) and os.path.isdir(folderpath):
            try:
                # Create backup directory if needed
                if not files_backed_up:
                    os.makedirs(backup_dir, exist_ok=True)
                    files_backed_up = True

                # Move folder to backup
                backup_path = os.path.join(backup_dir, foldername)
                if os.path.exists(backup_path):
                    shutil.rmtree(backup_path)
                shutil.move(folderpath, backup_path)
                logger.info(f"Backed up legacy folder: {foldername}")
            except Exception as e:
                logger.warning(f"Failed to backup legacy folder {foldername}: {e}")


def _download_system_game_data(release_data):
    """Download systems-game-data.json.gz from release assets and decompress"""
    try:
        assets = release_data.get('assets', [])
        game_data_asset = None

        # Find systems-game-data.json.gz in release assets
        for asset in assets:
            if asset.get('name') == 'systems-game-data.json.gz':
                game_data_asset = asset
                break

        if not game_data_asset:
            logger.warning("systems-game-data.json.gz not found in release assets, skipping")
            return False

        download_url = game_data_asset.get('browser_download_url')
        if not download_url:
            logger.error("No download URL for systems-game-data.json.gz")
            return False

        file_size_mb = game_data_asset.get('size', 0) / (1024*1024)
        logger.info(f"Downloading systems-game-data.json.gz ({file_size_mb:.1f}MB)...")

        # Download the compressed file
        response = requests.get(download_url, timeout=60)
        if response.status_code != 200:
            logger.error(f"Failed to download systems-game-data.json.gz: HTTP {response.status_code}")
            return False

        # Decompress and save to system_data folder
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        system_data_dir = os.path.join(plugin_dir, "system_data")
        os.makedirs(system_data_dir, exist_ok=True)

        dest_file = os.path.join(system_data_dir, "systems-game-data.json")

        logger.info("Decompressing systems-game-data.json.gz...")
        decompressed_data = gzip.decompress(response.content)

        with open(dest_file, 'wb') as f:
            f.write(decompressed_data)

        logger.info(f"systems-game-data.json updated successfully ({len(decompressed_data) // (1024*1024)}MB decompressed)")
        return True

    except Exception as e:
        logger.exception("Error downloading systems-game-data.json.gz")
        return False


def _backup_data_files():
    """Create backup of all data files before update"""
    try:
        logger.info("Creating data backups before update...")

        # Save current state with backups enabled
        from emt_models.system import dumpSystems
        from emt_models.salvage import save_salvage
        from emt_models.backpack import save_backpack
        from emt_models.power import pledgedPower

        # Save all data files with backup flag
        pledgedPower.dumpJson(create_backup=True)
        dumpSystems(create_backup=True)
        save_salvage(create_backup=True)
        save_backpack(create_backup=True)

        logger.info("Data backups created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create data backups: {e}")
        return False


def _download_and_extract_update(zip_url, release_data=None):
    """Download and extract update ZIP"""
    try:
        # Create backups of data files before updating
        _backup_data_files()

        zip_response = requests.get(zip_url, timeout=30)
        if zip_response.status_code != 200:
            logger.error("Failed to download update ZIP")
            return False

        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        temp_dir = os.path.join(plugin_dir, "temp_update")

        # Clean up legacy files before extracting new structure
        _cleanup_legacy_files(plugin_dir)

        # Clean previous temp directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)

        # Extract ZIP
        with zipfile.ZipFile(io.BytesIO(zip_response.content), 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Find extracted subdirectory
        extracted_subdir = None
        for item in os.listdir(temp_dir):
            if item.startswith("Fumlop-EliteMeritTracker-"):
                extracted_subdir = os.path.join(temp_dir, item)
                break

        if not extracted_subdir or not os.path.isdir(extracted_subdir):
            logger.error("Extracted directory not found")
            return False

        # Copy files to plugin directory (but protect data/ directory)
        for item in os.listdir(extracted_subdir):
            # Skip data/ directory to preserve user data
            if item == "data":
                logger.info("Skipping data/ directory during update to preserve user data")
                continue

            src_path = os.path.join(extracted_subdir, item)
            dest_path = os.path.join(plugin_dir, item)

            if os.path.isdir(src_path):
                if os.path.exists(dest_path):
                    shutil.rmtree(dest_path)
                shutil.copytree(src_path, dest_path)
            else:
                shutil.copy2(src_path, dest_path)

        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to delete temp_update folder: {e}")

        # Download systems-game-data.json from release assets if available
        # DISABLED: Economy/security now comes from FSDJump events
        # if release_data:
        #     _download_system_game_data(release_data)

        return True
    except Exception as e:
        logger.exception("Error during update download/extraction")
        return False


def auto_update():
    """Download and install plugin update"""
    global trackerFrame

    data = _get_github_release_data()
    if not data:
        logger.error("Failed to fetch latest release information")
        return

    zip_url = data.get("zipball_url")
    if not zip_url:
        logger.error("No ZIP file found in latest release")
        return

    logger.info(f"Downloading update from {zip_url}")

    if _download_and_extract_update(zip_url, release_data=data):
        logger.info("Update successfully installed. Restart required.")
        trackerFrame.updateButtonText()
    else:
        logger.error("Update installation failed")


def update_to_prerelease():
    """Download and install pre-release version"""
    global trackerFrame

    data = _get_github_prerelease_data()
    if not data:
        logger.error("No pre-release version found")
        return False

    zip_url = data.get("zipball_url")
    if not zip_url:
        logger.error("No ZIP file found in pre-release")
        return False

    version = data.get('tag_name', 'unknown')
    logger.info(f"Downloading pre-release {version} from {zip_url}")

    if _download_and_extract_update(zip_url, release_data=data):
        configPlugin.beta = True
        configPlugin.dumpConfig()
        logger.info(f"Pre-release {version} installed. Restart required.")
        return True
    else:
        logger.error("Pre-release installation failed")
        return False


def revert_to_release():
    """Revert from beta to latest stable release"""
    global trackerFrame

    data = _get_github_release_data()
    if not data:
        logger.error("Failed to fetch latest release information")
        return False

    zip_url = data.get("zipball_url")
    if not zip_url:
        logger.error("No ZIP file found in latest release")
        return False

    version = data.get('tag_name', 'unknown')
    logger.info(f"Reverting to stable release {version} from {zip_url}")

    if _download_and_extract_update(zip_url, release_data=data):
        configPlugin.beta = False
        configPlugin.dumpConfig()
        logger.info(f"Reverted to stable release {version}. Restart required.")
        return True
    else:
        logger.error("Revert to stable release failed")
        return False


def check_prerelease_available():
    """Check if a pre-release is available and newer than current version"""
    data = _get_github_prerelease_data()
    if not data:
        return None

    try:
        prerelease_version = parse_version(data['tag_name'])
        current_version = parse_version(configPlugin.version)

        if prerelease_version > current_version:
            return data['tag_name']
        return None
    except Exception as e:
        logger.exception('Error checking pre-release version')
        return None

def restart_edmc():
    logger.info("Restarting EDMC...")
    global trackerFrame
    trackerFrame.destroy_tracker_frame()
    os._exit(0)  # Terminate the current Python process

def parse_version(version_str):
    """Parse version string to tuple of integers"""
    return tuple(int(part) for part in re.findall(r'\d+', version_str))


def report_on_FSD(sourceSystem):
    """Report system merits on FSD jump if configured"""
    if not configPlugin.discordHook.get() or not configPlugin.reportOnFSDJump.get():
        return
        
    dcText = configPlugin.copyText.get().replace('@MeritsValue', str(sourceSystem.Merits))

    if '@SystemStatus' in dcText:
        dcText = dcText.replace('@SystemStatus', sourceSystem.getSystemStatusShort())

    dcText = dcText.replace('@System', sourceSystem.StarSystem)

    if '@CPControlling' in dcText:
        # For acquisition systems, show progress percentage instead of reinforcement
        if sourceSystem.PowerplayConflictProgress and len(sourceSystem.PowerplayConflictProgress) > 0:
            progress = sourceSystem.getSystemProgressNumber()
            dcText = dcText.replace('@CPControlling', f"{sourceSystem.ControllingPower} {progress:.2f}%")
        else:
            dcText = dcText.replace('@CPControlling', f"{sourceSystem.ControllingPower} {sourceSystem.PowerplayStateReinforcement}")

    if '@CPOpposition' in dcText:
        # For acquisition systems, show 2nd place power progress percentage
        if sourceSystem.PowerplayConflictProgress and len(sourceSystem.PowerplayConflictProgress) > 1:
            second_power = sourceSystem.PowerplayConflictProgress[1]
            progress = second_power.progress * 100
            dcText = dcText.replace('@CPOpposition', f"{second_power.power} {progress:.2f}%")
        else:
            dcText = dcText.replace('@CPOpposition', f"Opposition {sourceSystem.PowerplayStateUndermining}")

    if '@CPPledged' in dcText:
        dcText = dcText.replace('@CPPledged', f"Pledged {sourceSystem.PowerplayStateReinforcement}")
        
    systems[sourceSystem.StarSystem].Merits = 0
    report.send_to_discord(dcText)

def checkVersion():
    """Check if plugin update is available. Returns: -1=Error, 0=Current, 1=Update available"""
    data = _get_github_release_data()
    if not data:
        return -1

    try:
        latest_version = parse_version(data['tag_name'])
        current_version = parse_version(configPlugin.version)
        logger.info(f'Version check: current={current_version}, latest={latest_version}')
        
        return 0 if current_version >= latest_version else 1
    except Exception as e:
        logger.exception('Error parsing version data')
        return -1


def _autosave_data():
    """Periodic auto-save function called by timer"""
    try:
        logger.info("Auto-saving data (5-minute interval)")
        update_json_file()
    except Exception as e:
        logger.error(f"Auto-save failed: {e}")
    finally:
        # Schedule next auto-save
        _schedule_autosave()


def _schedule_autosave():
    """Schedule the next auto-save in 5 minutes"""
    global autosave_timer
    # Cancel existing timer if any
    if autosave_timer:
        autosave_timer.cancel()
    # Schedule new timer for 5 minutes (300 seconds)
    autosave_timer = threading.Timer(300.0, _autosave_data)
    autosave_timer.daemon = True  # Don't prevent program exit
    autosave_timer.start()


def _cancel_autosave():
    """Cancel the auto-save timer"""
    global autosave_timer
    if autosave_timer:
        autosave_timer.cancel()
        autosave_timer = None


def plugin_start3(plugin_dir):
    logger.info("EliteMeritTracker plugin starting")

    # Clean up legacy folders/files from older versions
    _cleanup_legacy_files(plugin_dir)

    configPlugin.loadConfig()
    state.newest = checkVersion()
    loadSystems()
    load_salvage()
    load_backpack()
    for system in systems.values():
        if system.Active:
            state.current_system = system
            # DISABLED: Validation feature disabled to prevent data loss
            # state.need_location_validation = True
            logger.info(f"Restored active system: {system.StarSystem}")
    pledgedPower.loadPower()
    logger.info(f"Plugin initialized - Systems: {len(systems)}, Power: {pledgedPower.Power}")

    # Start auto-save timer
    _schedule_autosave()
    logger.info("Auto-save scheduled for every 5 minutes")
        
def dashboard_entry(cmdr: str, is_beta: bool, entry: Dict[str, Any]):
    global trackerFrame
    if state.current_system:
        trackerFrame.update_display(state.current_system)

def plugin_stop():
    global report, systems, pledgedPower, configPlugin, trackerFrame

    # Cancel auto-save timer
    _cancel_autosave()
    logger.info("Auto-save timer cancelled")

    # Final save on shutdown
    update_json_file()
    if trackerFrame:
        logger.warning("Destroying tracker frame.")
        trackerFrame.destroy_tracker_frame()
        trackerFrame = None

    systems = None
    pledgedPower = None
    if configPlugin:
        configPlugin.reportOnFSDJump = None
        configPlugin.discordHook = None
        configPlugin.copyText = None
        configPlugin = None
    trackerFrame = None
    state.current_system = None
    logger.info("Shutting down EliteMeritTracker plugin.")

def plugin_app(parent):
    # Adds to the main page UI
    global trackerFrame
    trackerFrame = TrackerFrame(parent=parent, newest=state.newest)
    trackerFrame.create_tracker_frame(reset, auto_update)
    if state.current_system:
        trackerFrame.update_display(state.current_system)
    return trackerFrame.frame

def reset():
    import tkinter as tk
    from tkinter import messagebox
    global trackerFrame

    # Add logging
    logger.info("Reset button clicked")

    # Create a temporary toplevel window to position the dialog near EDMC
    dialog_parent = tk.Toplevel(trackerFrame.parent)
    dialog_parent.withdraw()  # Hide the window

    # Position near the EDMC window
    if trackerFrame.parent:
        try:
            x = trackerFrame.parent.winfo_rootx() + 50
            y = trackerFrame.parent.winfo_rooty() + 50
            dialog_parent.geometry(f"+{x}+{y}")
        except:
            pass  # Fall back to default position if positioning fails

    # Show confirmation dialog
    result = messagebox.askyesno(
        "Confirm Reset",
        "This will reset all merit counts to zero. Are you sure?",
        icon='warning',
        parent=dialog_parent
    )

    dialog_parent.destroy()  # Clean up the temporary window

    if not result:
        logger.info("Reset cancelled by user")
        return

    # Reset session merits for the pledged power
    pledgedPower.MeritsSession = 0

    # Find most recently active system from systems dict
    current_system_name = None
    for name, system_data in systems.items():
        if system_data.Active:
            current_system_name = name
            break

    # Fallback to state.current_system if available and no active system found
    if not current_system_name and state.current_system:
        current_system_name = state.current_system.StarSystem

    # Store current system data if it exists
    current_system_data = systems.get(current_system_name) if current_system_name else None

    logger.info(f"Reset preserving current system: {current_system_name}")

    # Clear all systems from cache
    systems.clear()

    # Restore current system with its data but reset merits
    if current_system_data:
        current_system_data.Merits = 0
        systems[current_system_name] = current_system_data
        logger.info(f"Restored current system with 0 merits: {current_system_name}")
    else:
        logger.warning("No current system found to preserve during reset")

    # Save the cleared systems to disk
    dumpSystems()

    # Update the display with current system
    trackerFrame.update_display(state.current_system)
    logger.info("Reset completed successfully")

def plugin_prefs(parent, cmdr, is_beta):
    return create_config_frame(parent, nb)

# Merit calculation constants
MERIT_CARGO_DIVISOR = 1.15
MERIT_CARGO_MULTIPLIER = 0.65


def _add_merits_to_system(system_name: str, merits: int):
    """Add merits to a system, creating it if necessary."""
    if system_name in systems:
        systems[system_name].Merits += merits
    else:
        new_system = StarSystem()
        new_system.StarSystem = system_name
        new_system.Merits = merits
        systems[system_name] = new_system


def update_system_merits(merits_value, system_name: str = None, apply_cargo_formula: bool = False, update_ui: bool = False):
    """Unified merit update function.

    Args:
        merits_value: Raw merit value to add
        system_name: Target system (uses current system if None)
        apply_cargo_formula: If True, applies cargo delivery reduction formula
        update_ui: If True, updates the tracker UI after adding merits
    """
    global trackerFrame

    if merits_value <= 0:
        return

    try:
        merits = int(merits_value)
    except (ValueError, TypeError):
        logger.debug("Invalid merits value")
        return

    # Apply cargo delivery formula if requested
    if apply_cargo_formula:
        original = merits
        merits = int((merits / MERIT_CARGO_DIVISOR) * MERIT_CARGO_MULTIPLIER)
        logger.info(f"PowerPlay cargo delivery: {system_name} gets {merits} merits (reduced from {original})")

    # Update session total
    pledgedPower.MeritsSession += merits

    # Determine target system
    if system_name:
        _add_merits_to_system(system_name, merits)
    else:
        sys_name = getattr(state.current_system, "StarSystem", None)
        if sys_name:
            current = systems.get(sys_name, state.current_system)
            current.Merits += merits
            systems[sys_name] = current

    # Update UI if requested
    if update_ui:
        trackerFrame.update_display(state.current_system)

def prefs_changed(cmdr, is_beta):
    configPlugin.dumpConfig()
           
def update_json_file():
    pledgedPower.dumpJson()
    dumpSystems()
    save_salvage()
    save_backpack()

def journal_entry(cmdr, is_beta, system, station, entry, game_state):
    global trackerFrame

    # Track any journal event timestamp for duplicate detection
    current_timestamp = entry.get('timestamp')
    if current_timestamp and entry['event'] != 'PowerplayMerits':
        track_journal_event(current_timestamp)

    # DISABLED: System validation feature temporarily disabled
    # Issue: Causes TypeError and data loss risk
    # Workaround: Jump to another system or dock to trigger system update
    # TODO: Implement safe validation that doesn't risk data loss
    pass

    if entry['event'] in ['LoadGame']:
        state.commander = entry.get('Commander', "")
    if entry['event'] == 'BackpackChange':
        # Track PowerPlay data collection
        current_system = state.current_system.StarSystem if state.current_system else None
        controlling_power = state.current_system.ControllingPower if state.current_system else None
        player_pledged_power = pledgedPower.Power

        # Process added items
        for item in entry.get('Added', []):
            item_name = item.get('Name', '').lower()
            item_count = item.get('Count', 1)
            if is_valid_um_data(item_name) or is_valid_reinf_data(item_name) or is_valid_acq_data(item_name):
                playerBackpack.add_item(item_name, item_count, current_system, controlling_power, player_pledged_power)

        # Process removed items
        for item in entry.get('Removed', []):
            item_name = item.get('Name', '').lower()
            item_count = item.get('Count', 1)
            if is_valid_um_data(item_name) or is_valid_reinf_data(item_name) or is_valid_acq_data(item_name):
                playerBackpack.remove_item(item_name, item_count)
    if entry['event'] == 'DeliverPowerMicroResources':
        # Hand-in PowerPlay data at power contact - capture system distribution for merit assignment
        state.last_delivery_counts = {}
        for item in entry.get('MicroResources', []):
            item_name = item.get('Name', '').lower()
            item_count = item.get('Count', 1)
            if is_valid_um_data(item_name) or is_valid_reinf_data(item_name) or is_valid_acq_data(item_name):
                systems_removed = playerBackpack.remove_item(item_name, item_count)
                # Aggregate system counts for merit distribution
                for sys_name, count in systems_removed.items():
                    state.add_delivery_count(sys_name, count)
    if entry['event'] == 'ShipLocker':
        # Cross-check backpack against game state (handles death, etc.)
        data_items = entry.get('Data', [])
        if data_items:
            playerBackpack.sync_from_shiplocker(data_items)
    if entry['event'] in ['CollectCargo']:
        # Only track PowerPlay salvage cargo, not mining commodities
        cargo_type = entry.get("Type", "Unknown").lower()
        if cargo_type in VALID_POWERPLAY_SALVAGE_TYPES:
            Salvage.process_collect_cargo(entry, state.current_system)
    if entry['event'] in ['SearchAndRescue']:
        # Remove cargo when delivered to Search and Rescue - from any system
        cargo_type = entry.get("Name", "Unknown").lower()
        if cargo_type in VALID_POWERPLAY_SALVAGE_TYPES:
            count = entry.get("Count", 1)
            remaining_count = count

            # Log significant PowerPlay cargo deliveries
            if count >= 10:
                logger.info(f"Large PowerPlay cargo delivery: {count}x {cargo_type}")

            # Initialize SAR tracking for this batch
            state.init_sar_tracking()

            # Sort systems alphabetically
            sorted_systems = sorted(salvageInventory.keys())

            # Try to remove cargo from each system until count is satisfied
            for system_name in sorted_systems:
                if remaining_count <= 0:
                    break
                if salvageInventory[system_name].has_cargo(cargo_type):
                    removed = salvageInventory[system_name].remove_cargo(cargo_type, remaining_count)
                    remaining_count -= removed
                    state.add_sar_count(system_name, removed)
    if entry['event'] in ['Powerplay']:
        logger.info(f"PowerPlay status changed - Power: {entry.get('Power', 'Unknown')}")
        pledgedPower.__init__(eventEntry=entry)
        trackerFrame.update_display(state.current_system)
    if entry['event'] in ['PowerplayRank']:
        new_rank = entry.get('Rank', pledgedPower.Rank)
        if new_rank != pledgedPower.Rank:
            logger.info(f"PowerPlay rank changed: {pledgedPower.Rank} -> {new_rank}")
        pledgedPower.Rank = new_rank
        pledgedPower.Power = entry.get('Power', pledgedPower.Power)
    if entry['event'] in ['PowerplayMerits']:
        # Process PowerplayMerits event through duplicate detection
        is_duplicate, retroactive_correction, log_message = process_powerplay_event(entry)

        if is_duplicate:
            logger.warning(log_message)
            return  # Skip duplicate event

        # Log successful processing
        logger.info(log_message)

        # Apply retroactive correction if needed
        if retroactive_correction:
            logger.info(f"Applying retroactive correction: -{retroactive_correction} merits")
            pledgedPower.MeritsSession -= retroactive_correction

            # Also correct system merits if they were affected
            if state.current_system and state.current_system.StarSystem in systems:
                if systems[state.current_system.StarSystem].Merits >= retroactive_correction:
                    systems[state.current_system.StarSystem].Merits -= retroactive_correction
                    logger.info(f"Corrected system merits for {state.current_system.StarSystem}: -{retroactive_correction}")

        # Process the valid PowerplayMerits event
        merits_gained = entry.get('MeritsGained', 0)

        # Check DeliverPowerMicroResources first (backpack hand-in at power contact)
        if state.last_delivery_counts:
            total_items = sum(state.last_delivery_counts.values())
            if total_items > 0:
                merits_per_item = merits_gained / total_items
                for system_name, item_count in state.last_delivery_counts.items():
                    system_merits = int(merits_per_item * item_count)
                    update_system_merits(system_merits, system_name=system_name)
            state.reset_delivery_tracking()
            # Update UI after distributing merits across systems
            trackerFrame.update_display(state.current_system)
        elif state.last_sar_counts is not None and state.last_sar_systems:
            total_items = sum(state.last_sar_counts.values())
            if total_items > 0:
                merits_per_item = merits_gained / total_items
                for system_name, item_count in state.last_sar_counts.items():
                    system_merits = int(merits_per_item * item_count)
                    update_system_merits(system_merits, system_name=system_name)
            state.reset_sar_tracking()
            # Update UI after distributing merits across systems
            trackerFrame.update_display(state.current_system)
        else:
            update_system_merits(merits_gained, update_ui=True)

        pledgedPower.Merits = entry.get('TotalMerits', pledgedPower.Merits)
        pledgedPower.Power = entry.get('Power', pledgedPower.Power)
    if entry['event'] in ['FSDJump', 'Location', 'Docked'] or (entry['event'] in ['CarrierJump'] and entry['Docked'] == True):
        nameSystem = entry.get('StarSystem', "Nomansland")

        if not systems or len(systems) == 0 or nameSystem not in systems:
            new_system = StarSystem(eventEntry=entry)
            new_system.setReported(False)
            systems[new_system.StarSystem] = new_system
        else:
            systems[nameSystem].updateSystem(eventEntry=entry)
        updateSystemTracker(state.current_system, systems[nameSystem])
        trackerFrame.update_display(state.current_system)


def updateSystemTracker(oldSystem, newSystem):
    if oldSystem is not None:
        systems[oldSystem.StarSystem].Active = False
    systems[newSystem.StarSystem].Active = True
    state.current_system = newSystem

    # Log only if system has meaningful merit activity
    if newSystem.Merits > 0 or (oldSystem and oldSystem.Merits > 0):
        logger.info(f"System changed: {oldSystem.StarSystem if oldSystem else 'None'} -> {newSystem.StarSystem} (Merits: {newSystem.Merits})")
