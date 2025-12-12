import os
import sys
import requests
import shutil
import zipfile
import myNotebook as nb
import io
import re
from typing import Dict, Any
from datetime import datetime

from report import report
from system import systems, StarSystem, loadSystems, dumpSystems
from salvage import Salvage, salvageInventory, save_salvage, load_salvage, VALID_POWERPLAY_SALVAGE_TYPES
from power import pledgedPower
from pluginUI import TrackerFrame
from duplicate import track_journal_event, process_powerplay_event, reset_duplicate_tracking
from pluginConfig import configPlugin
from merit_log import logger
from config import config, appname
from pluginConfigUI import create_config_frame
from backpack import playerBackpack, save_backpack, load_backpack
from umdata import is_valid_um_data
from reinfdata import is_valid_reinf_data
from acqdata import is_valid_acq_data

# Module globals
this = sys.modules[__name__]
trackerFrame = None

# System state
this.currentSystemFlying = None
this.commander = ""

# UI state
this.parent = None
this.assetpath = ""

# SAR (Search and Rescue) tracking
this.lastSARCounts = None
this.lastSARSystems = []

# DeliverPowerMicroResources tracking (backpack hand-in)
this.lastDeliveryCounts = None

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


def _download_and_extract_update(zip_url):
    """Download and extract update ZIP"""
    try:
        zip_response = requests.get(zip_url, timeout=30)
        if zip_response.status_code != 200:
            logger.error("Failed to download update ZIP")
            return False

        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        temp_dir = os.path.join(plugin_dir, "temp_update")
        
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

        # Copy files to plugin directory
        for item in os.listdir(extracted_subdir):
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

    if _download_and_extract_update(zip_url):
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

    if _download_and_extract_update(zip_url):
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

    if _download_and_extract_update(zip_url):
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
    os._exit(0)  # Beendet das aktuelle Python-Programm

def parse_version(version_str):
    """Parse version string to tuple of integers"""
    return tuple(int(part) for part in re.findall(r'\d+', version_str))


def report_on_FSD(sourceSystem):
    """Report system merits on FSD jump if configured"""
    if not configPlugin.discordHook.get() or not configPlugin.reportOnFSDJump.get():
        return
        
    dcText = configPlugin.copyText.get().replace('@MeritsValue', str(sourceSystem.Merits)).replace('@System', sourceSystem.StarSystem)
    
    if '@CPOpposition' in dcText:
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


def plugin_start3(plugin_dir):
    logger.info("EliteMeritTracker plugin starting")
    configPlugin.loadConfig()
    #logger.debug(json.dumps(configPlugin, ensure_ascii=False, indent=4, cls=ConfigEncoder))    
    this.newest = checkVersion()
    loadSystems()  # Lädt die Systeme aus der JSON-Datei
    load_salvage()  # Lädt das Salvage Inventory
    load_backpack()  # Lädt das Backpack
    for system in systems.values():
        if (system.Active):
            this.currentSystemFlying = system
    pledgedPower.loadPower()  # Lädt die Power-Daten aus der JSON-Datei
    logger.info(f"Plugin initialized - Systems: {len(systems)}, Power: {pledgedPower.Power}")
        
def dashboard_entry(cmdr: str, is_beta: bool, entry: Dict[str, Any]):
    global trackerFrame
    if (this.currentSystemFlying):
        trackerFrame.update_display(this.currentSystemFlying)

def plugin_stop():
    global report, systems, pledgedPower, configPlugin, trackerFrame

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
    this.currentSystemFlying = None
    logger.info("Shutting down EliteMeritTracker plugin.")

def plugin_app(parent):
    # Adds to the main page UI
    global trackerFrame
    trackerFrame = TrackerFrame(parent=parent, newest=this.newest)
    trackerFrame.create_tracker_frame(reset, auto_update)
    if (this.currentSystemFlying):
        trackerFrame.update_display(this.currentSystemFlying)
    return trackerFrame.frame

def reset():
    global trackerFrame
    # Reset session merits for the pledged power
    pledgedPower.MeritsSession = 0
    
    # Reset merits for all systems but keep the systems themselves
    for system in systems.values():
        system.Merits = 0
    
    # Update the display with current system
    trackerFrame.update_display(this.currentSystemFlying)

def plugin_prefs(parent, cmdr, is_beta):
    return create_config_frame(parent, nb)

def update_system_merits_for_collection(merits_value, system_name):
    """Update merits for PowerPlay data collection system (backpack hand-in)"""
    if merits_value <= 0:
        return

    try:
        merits = int(merits_value)
    except (ValueError, TypeError):
        logger.debug("Invalid merits value for collection")
        return

    pledgedPower.MeritsSession += merits
    logger.info(f"PowerPlay data delivery: {system_name} gets {merits} merits")

    if system_name in systems:
        systems[system_name].Merits += merits
    else:
        new_system = StarSystem()
        new_system.StarSystem = system_name
        new_system.Merits = merits
        systems[system_name] = new_system


def update_system_merits_sar(merits_value, system_name):
    """Update merits for Search and Rescue activities"""
    if merits_value <= 0:
        return

    try:
        merits = int(merits_value)
    except (ValueError, TypeError):
        logger.debug("Invalid merits value for SAR")
        return

    pledgedPower.MeritsSession += merits

    if system_name in systems:
        systems[system_name].Merits += merits
    else:
        # Create new system if it doesn't exist
        new_system = StarSystem()
        new_system.StarSystem = system_name
        new_system.Merits = merits
        systems[system_name] = new_system


def update_system_merits_powerplay_delivery(merits_value, delivery_system_name):
    """Update merits for PowerPlay cargo delivery system with reduced formula: merits / 1.15 * 0.65"""
    if merits_value <= 0 or not delivery_system_name:
        return
    
    try:
        # Apply the formula: merits / 1.15 * 0.65
        reduced_merits = int((merits_value / 1.15) * 0.65)
        logger.info(f"PowerPlay cargo delivery: {delivery_system_name} gets {reduced_merits} merits (reduced from {merits_value})")
    except (ValueError, TypeError):
        logger.debug("Invalid merits value for PowerPlay delivery")
        return

    pledgedPower.MeritsSession += reduced_merits

    if delivery_system_name in systems:
        systems[delivery_system_name].Merits += reduced_merits
    else:
        # Create new system if it doesn't exist
        new_system = StarSystem()
        new_system.StarSystem = delivery_system_name
        new_system.Merits = reduced_merits
        systems[delivery_system_name] = new_system


def update_system_merits(merits_value):
    """Update merits for current system"""
    global trackerFrame
    
    try:
        merits = int(merits_value)
    except (ValueError, TypeError):
        logger.debug("Invalid merits value")
        return

    pledgedPower.MeritsSession += merits

    sys_name = getattr(this.currentSystemFlying, "StarSystem", None)
    if sys_name:
        current = systems.get(sys_name, this.currentSystemFlying)
        current.Merits += merits
        systems[sys_name] = current

    trackerFrame.update_display(this.currentSystemFlying)

def prefs_changed(cmdr, is_beta):
    configPlugin.dumpConfig()
           
def update_json_file():
    pledgedPower.dumpJson()
    dumpSystems()
    save_salvage()
    save_backpack()

def journal_entry(cmdr, is_beta, system, station, entry, state):
    global trackerFrame
    
    # Track any journal event timestamp for duplicate detection
    current_timestamp = entry.get('timestamp')
    if current_timestamp and entry['event'] != 'PowerplayMerits':
        track_journal_event(current_timestamp)
    
    if entry['event'] in ['LoadGame']:
        this.commander = entry.get('Commander', "")
    if entry['event'] == 'BackpackChange':
        # Track PowerPlay data collection
        current_system = this.currentSystemFlying.StarSystem if this.currentSystemFlying else None
        controlling_power = this.currentSystemFlying.ControllingPower if this.currentSystemFlying else None
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
        this.lastDeliveryCounts = {}
        for item in entry.get('MicroResources', []):
            item_name = item.get('Name', '').lower()
            item_count = item.get('Count', 1)
            if is_valid_um_data(item_name) or is_valid_reinf_data(item_name) or is_valid_acq_data(item_name):
                systems_removed = playerBackpack.remove_item(item_name, item_count)
                # Aggregate system counts for merit distribution
                for system, count in systems_removed.items():
                    this.lastDeliveryCounts[system] = this.lastDeliveryCounts.get(system, 0) + count
    if entry['event'] == 'ShipLocker':
        # Cross-check backpack against game state (handles death, etc.)
        data_items = entry.get('Data', [])
        if data_items:
            playerBackpack.sync_from_shiplocker(data_items)
    if entry['event'] in ['CollectCargo']:
        # Process cargo collection with new Salvage system
        Salvage.process_collect_cargo(entry, this.currentSystemFlying)
    if entry['event'] in ['SearchAndRescue']:
        # Remove cargo when delivered to Search and Rescue - from any system
        cargo_type = entry.get("Name", "Unknown").lower()  # Use Name field from SearchAndRescue event
        if cargo_type in VALID_POWERPLAY_SALVAGE_TYPES:
            count = entry.get("Count", 1)
            remaining_count = count
            
            # Log significant PowerPlay cargo deliveries
            if count >= 10:
                logger.info(f"Large PowerPlay cargo delivery: {count}x {cargo_type}")
            
            # Initialisiere das Dictionary für diesen PowerPlay SAR-Run
            if this.lastSARCounts is None:
                this.lastSARCounts = {}
                this.lastSARSystems = []
            
            # Track delivery to current system (will get reduced merits)
            #this.lastPowerPlayDeliverySystem = this.currentSystemFlying.StarSystem if this.currentSystemFlying else None
            
            # Sort systems alphabetically
            sorted_systems = sorted(salvageInventory.keys())
           
            # Try to remove cargo from each system until count is satisfied
            for system_name in sorted_systems:
                if remaining_count <= 0:
                    break
                if salvageInventory[system_name].has_cargo(cargo_type):
                    removed = salvageInventory[system_name].remove_cargo(cargo_type, remaining_count)
                    remaining_count -= removed
                    
                    # Speichere die Anzahl der Items pro System
                    if system_name not in this.lastSARCounts:
                        this.lastSARCounts[system_name] = 0
                        this.lastSARSystems.append(system_name)
                    this.lastSARCounts[system_name] += removed
    if entry['event'] in ['Powerplay']:
        logger.info(f"PowerPlay status changed - Power: {entry.get('Power', 'Unknown')}")
        pledgedPower.__init__(eventEntry=entry)  # NEU: re-initialisiere das Singleton-Objekt
        trackerFrame.update_display(this.currentSystemFlying)
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
            if this.currentSystemFlying and this.currentSystemFlying.StarSystem in systems:
                if systems[this.currentSystemFlying.StarSystem].Merits >= retroactive_correction:
                    systems[this.currentSystemFlying.StarSystem].Merits -= retroactive_correction
                    logger.info(f"Corrected system merits for {this.currentSystemFlying.StarSystem}: -{retroactive_correction}")
        
        # Process the valid PowerplayMerits event
        merits_gained = entry.get('MeritsGained', 0)

        # Check DeliverPowerMicroResources first (backpack hand-in at power contact)
        if this.lastDeliveryCounts:
            total_items = sum(this.lastDeliveryCounts.values())
            if total_items > 0:
                merits_per_item = merits_gained / total_items
                for system_name, item_count in this.lastDeliveryCounts.items():
                    system_merits = int(merits_per_item * item_count)
                    update_system_merits_for_collection(system_merits, system_name)
            this.lastDeliveryCounts = None
        elif this.lastSARCounts is not None and this.lastSARSystems:
            total_items = sum(this.lastSARCounts.values())
            if total_items > 0:
                merits_per_item = merits_gained / total_items
                for system_name, item_count in this.lastSARCounts.items():
                    system_merits = int(merits_per_item * item_count)
                    update_system_merits_sar(system_merits, system_name)
            this.lastSARCounts = None
            this.lastSARSystems = []
        else:
            update_system_merits(merits_gained)
        
        pledgedPower.Merits = entry.get('TotalMerits', pledgedPower.Merits)
        pledgedPower.Power = entry.get('Power', pledgedPower.Power)
    if entry['event'] in ['FSDJump', 'Location'] or (entry['event'] in ['CarrierJump'] and entry['Docked'] == True):
        nameSystem = entry.get('StarSystem',"Nomansland")
        if (not systems or len(systems)==0 or nameSystem not in systems):
            new_system = StarSystem(eventEntry=entry)
            new_system.setReported(False)  # Set reported status after creation
            systems[new_system.StarSystem] = new_system
        else:
            systems[nameSystem].updateSystem(eventEntry=entry)
        updateSystemTracker(this.currentSystemFlying,systems[nameSystem])
        trackerFrame.update_display(this.currentSystemFlying)

def updateSystemTracker(oldSystem, newSystem):
    if (oldSystem != None) :
        systems[oldSystem.StarSystem].Active = False
    systems[newSystem.StarSystem].Active = True
    this.currentSystemFlying = newSystem
    
    # Log only if system has meaningful merit activity
    if newSystem.Merits > 0 or (oldSystem and oldSystem.Merits > 0):
        logger.info(f"System changed: {oldSystem.StarSystem if oldSystem else 'None'} -> {newSystem.StarSystem} (Merits: {newSystem.Merits})")

def logdump(here:str, data:dict):
    if this.debug:
        #logger.debug(f"{here} - {json.dumps(data, indent=2)}")
        pass
