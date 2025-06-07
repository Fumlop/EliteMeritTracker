import os
import sys
import json
import tkinter as tk
import requests
import gc
import shutil
import zipfile
import myNotebook as nb
import io
import re
from PIL import Image, ImageTk
from typing import Dict, Any

from report import report
from system import systems, StarSystem, loadSystems, dumpSystems
from power import pledgedPower, PowerEncoder
from pluginUI import TrackerFrame
from pluginConfig import configPlugin, ConfigEncoder
from log import logger, plugin_name
from pluginDetailsUI import show_power_info
from config import config, appname
from pluginConfigUI import create_config_frame

this = sys.modules[__name__]  # For holding module globals
trackerFrame = None
this.currentSystemFlying = None
this.crow = -1
this.mainframerow = -1
this.parent = None
this.assetpath = ""
def auto_update():
    global trackerFrame
    try:
        url = 'https://api.github.com/repos/Fumlop/EliteMeritTracker/releases/latest'
        response = requests.get(url)
        if response.status_code != 200:
            logger.error("Failed to fetch latest release information.")
            return
        
        data = response.json()
        zip_url = data.get("zipball_url")  # Holt die ZIP-URL

        if not zip_url:
            logger.error("No ZIP file found in latest release.")
            return
        
        logger.info(f"Downloading update from {zip_url}")
        zip_response = requests.get(zip_url)
        if zip_response.status_code != 200:
            logger.error("Failed to download update ZIP.")
            return
        
        plugin_dir = os.path.dirname(os.path.abspath(__file__))  # Plugin-Verzeichnis
        temp_dir = os.path.join(plugin_dir, "temp_update")  # Temporärer Ordner für Entpacken
        
        # Vorheriges Update-Verzeichnis löschen, falls vorhanden
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        os.makedirs(temp_dir, exist_ok=True)

        # ZIP entpacken
        with zipfile.ZipFile(io.BytesIO(zip_response.content), 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Suche das entpackte Unterverzeichnis (beginnt mit "Fumlop-EliteMeritTracker-")
        extracted_subdir = None
        for item in os.listdir(temp_dir):
            if item.startswith("Fumlop-EliteMeritTracker-"):
                extracted_subdir = os.path.join(temp_dir, item)
                break

        if not extracted_subdir or not os.path.isdir(extracted_subdir):
            logger.error("Extracted directory not found.")
            return

        # Kopiere die entpackten Dateien ins Plugin-Verzeichnis
        for item in os.listdir(extracted_subdir):
            src_path = os.path.join(extracted_subdir, item)
            dest_path = os.path.join(plugin_dir, item)

            if os.path.isdir(src_path):
                if os.path.exists(dest_path):
                    shutil.rmtree(dest_path)  # Vorheriges Verzeichnis löschen
                shutil.copytree(src_path, dest_path)
            else:
                shutil.copy2(src_path, dest_path)

        # Update abgeschlossen
        logger.info("Update successfully installed. Restart required.")
        
        # Lösche das temp_update-Verzeichnis nach dem Update
        try:
            shutil.rmtree(temp_dir)
            logger.info("Temporary update folder deleted successfully.")
        except Exception as e:
            logger.warning(f"Failed to delete temp_update folder: {e}")
        
        # Ändere den Button-Text und die Funktion auf "Restart EDMC"
        trackerFrame.updateButtonText()
        
    
    except Exception as e:
        logger.exception("Error occurred during auto-update.")

def restart_edmc():
    logger.info("Restarting EDMC...")
    global trackerFrame
    trackerFrame.destroy_tracker_frame()
    os._exit(0)  # Beendet das aktuelle Python-Programm

def parse_version(version_str):
    return tuple(int(part) for part in re.findall(r'\d+', version_str))

def report_on_FSD(sourceSystem):
    if not configPlugin.discordHook or configPlugin.reportOnFSDJump == False:
        return
    dcText = f"{this.copyText.replace('@MeritsValue', sourceSystem.Merits).replace('@System', sourceSystem.StarSystem)}"
    if '@CPOpposition' in dcText:
        dcText = dcText.replace('@CPOpposition', str(sourceSystem.PowerplayStateUndermining))

    if '@CPPledged' in dcText:
        dcText = dcText.replace('@CPPledged', str(sourceSystem.PowerplayStateReinforcement))
    systems[sourceSystem.StarSystem].Merits = 0
    report.send_to_discord(dcText)

def checkVersion():
    try:
        req = requests.get(url='https://api.github.com/repos/Fumlop/EliteMeritTracker/releases/latest')
    except Exception as e:
        # Exception mit vollständigem Stacktrace loggen
        logger.exception('An error occurred while checking the version')
        return -1

    if req.status_code != requests.codes.ok:
        logger.error('Request failed with status code: %s', req.status_code)
        return -1  # Error
    else:
        logger.info('Request sucess with status code: %s', req.status_code)

    try:
        data = req.json()
        latest_version = parse_version(data['tag_name'])
        logger.info('latest_version: %s', latest_version)
        current_version = parse_version(configPlugin.version)
        logger.info('current_version: %s', current_version)

        if current_version >= latest_version:
            return 0  # Newest
        else:
            return 1
    except Exception as e:
        # JSON-Parsing-Fehler loggen
        logger.exception('Error while parsing the JSON response')
        return -1

def plugin_start3(plugin_dir):
    configPlugin.loadConfig()
    logger.debug(json.dumps(configPlugin, ensure_ascii=False, indent=4, cls=ConfigEncoder))    
    this.newest = checkVersion()
    loadSystems()  # Lädt die Systeme aus der JSON-Datei
    for system in systems.values():
        if (system.Active):
            this.currentSystemFlying = system
    pledgedPower.loadPower()  # Lädt die Power-Daten aus der JSON-Datei
        
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
    return trackerFrame.frame

def reset():
    global trackerFrame
    if this.currentSystemFlying:
       systems.clear() 
       systems[this.currentSystemFlying.StarSystem] = this.currentSystemFlying
    trackerFrame.update_display(this.currentSystemFlying)

def plugin_prefs(parent, cmdr, is_beta):
    return create_config_frame(parent, nb)

def update_system_merits(merits_value, total):
    global trackerFrame
    try:
        merits = int(merits_value)
        total_merits = int(total)
    except (ValueError, TypeError):
        logger.debug("Invalid merits value or total.")
        return

    pledgedPower.MeritsSession += merits

    sys_name = getattr(this.currentSystemFlying, "StarSystem", None)
    if sys_name:
        current = systems.get(sys_name, this.currentSystemFlying)
        current.Merits += merits
        systems[sys_name] = current

    pledgedPower.Merits = total_merits
    trackerFrame.update_display(this.currentSystemFlying)

def prefs_changed(cmdr, is_beta):
    configPlugin.dumpConfig()
           
def update_json_file():
    pledgedPower.dumpJson()  
    dumpSystems()

def journal_entry(cmdr, is_beta, system, station, entry, state):
    global trackerFrame
    if entry['event'] in ['Powerplay']:
        pledgedPower.__init__(eventEntry=entry)  # NEU: re-initialisiere das Singleton-Objekt
        trackerFrame.update_display(this.currentSystemFlying)
    if entry['event'] in ['PowerplayMerits']:
        update_system_merits(entry.get('MeritsGained'),entry.get('TotalMerits'))
    if entry['event'] in ['FSDJump', 'Location']:
        nameSystem = entry.get('StarSystem',"Nomansland")
        if (not systems or len(systems)==0 or nameSystem not in systems):
            new_system = StarSystem(eventEntry=entry, reported=False)
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

def logdump(here:str, data:dict):
    if this.debug:
        logger.debug(f"{here} - {json.dumps(data, indent=2)}")
