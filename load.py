import os
import sys
import requests
import shutil
import zipfile
import myNotebook as nb
import io
import re
from typing import Dict, Any

from report import report
from system import systems, StarSystem, loadSystems, dumpSystems
from salvage import Salvage, salvageInventory, save_salvage, load_salvage, VALID_SALVAGE_TYPES
from power import pledgedPower
from pluginUI import TrackerFrame
from pluginConfig import configPlugin
from log import logger
from config import config, appname
from pluginConfigUI import create_config_frame

# Module globals
this = sys.modules[__name__]
trackerFrame = None

# System state
this.currentSystemFlying = None
this.commander = ""

# UI state  
this.crow = -1
this.mainframerow = -1
this.parent = None
this.assetpath = ""

# SAR (Search and Rescue) tracking
this.lastSARCounts = None
this.lastSARSystems = []
def _get_github_release_data():
    """Fetch latest GitHub release data"""
    try:
        response = requests.get('https://api.github.com/repos/Fumlop/EliteMeritTracker/releases/latest')
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        logger.exception('Error fetching GitHub release data')
        return None


def _download_and_extract_update(zip_url):
    """Download and extract update ZIP"""
    try:
        zip_response = requests.get(zip_url)
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
    if this.currentSystemFlying:
       systems.clear() 
       this.currentSystemFlying.MeritsSession = 0
       systems[this.currentSystemFlying.StarSystem] = this.currentSystemFlying
    trackerFrame.update_display(this.currentSystemFlying)

def plugin_prefs(parent, cmdr, is_beta):
    return create_config_frame(parent, nb)

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

def journal_entry(cmdr, is_beta, system, station, entry, state):
    global trackerFrame
    if entry['event'] in ['LoadGame']:
        this.commander = entry.get('Commander', "Ganimed ")
    if entry['event'] in ['CollectCargo']:
        # Process cargo collection with new Salvage system
        Salvage.process_collect_cargo(entry, this.currentSystemFlying)
    if entry['event'] in ['SearchAndRescue']:
        # Remove cargo when delivered to Search and Rescue - from any system
        cargo_type = entry.get("Name", "Unknown").lower()  # Use Name field from SearchAndRescue event
        if cargo_type in VALID_SALVAGE_TYPES:
            count = entry.get("Count", 1)
            remaining_count = count
            
            # Log significant salvage deliveries
            if count >= 10:
                logger.info(f"Large salvage delivery: {count}x {cargo_type}")
            
            # Initialisiere das Dictionary für diesen SAR-Run
            if this.lastSARCounts is None:
                this.lastSARCounts = {}
                this.lastSARSystems = []
            
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
        merits_gained = entry.get('MeritsGained', 0)
        if merits_gained > 0:
            logger.info(f"PowerPlay merits gained: {merits_gained} (Total: {entry.get('TotalMerits', pledgedPower.Merits)})")
        if this.lastSARCounts is not None and this.lastSARSystems:
            total_items = sum(this.lastSARCounts.values())
            if total_items > 0:
                merits_per_item = merits_gained / total_items
                for system_name, item_count in this.lastSARCounts.items():
                    system_merits = int(merits_per_item * item_count)
                    update_system_merits_sar(system_merits, system_name)
            this.lastSARCounts = None
            this.lastSARSystems = []
        else:
            #logger.debug(f"Processing normal PowerplayMerits in current system")
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
