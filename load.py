import os
import sys
import json
import tkinter as tk
import requests
import shutil
import zipfile
import myNotebook as nb
import io
import re
from PIL import Image, ImageTk
from typing import Dict, Any

from imports import pledgedPower, plugin_name, configPlugin, logger
from system import StarSystem
from power import PledgedPower,PowerEncoder
from report import Report
from history import PowerPlayHistory
from power_info_window import show_power_info
from config import config, appname
from configPlugin import ConfigEncoder
from imports import logger, configPlugin,report, history, systems

this = sys.modules[__name__]  # For holding module globals
this.debug = False
this.dump_test = False

this.currentSystemFlying = None
this.version = 'v0.4.70.1.200'
this.crow = -1
this.mainframerow = -1
this.copyText = tk.StringVar(value=configPlugin.copyText if isinstance(configPlugin.copyText, str) else configPlugin.copyText.get())
this.discordHook = tk.StringVar(value=configPlugin.discordHook if isinstance(configPlugin.discordHook, str) else configPlugin.discordHook.get())
this.reportOnFSDJump = tk.BooleanVar(value=configPlugin.reportOnFSDJump if isinstance(configPlugin.reportOnFSDJump, bool) else False)
this.assetpath = ""
def auto_update():
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
        this.updateButton.config(text="Close EDMC", command=restart_edmc)
    
    except Exception as e:
        logger.exception("Error occurred during auto-update.")

def restart_edmc():
    logger.info("Restarting EDMC...")
    this.frame.quit()
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
        current_version = parse_version(this.version)
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
    directory_name = os.path.basename(os.path.dirname(__file__))
    plugin_path = os.path.join(config.plugin_dir, directory_name)
    file_path = os.path.join(plugin_path, "power.json")
    systems_path = os.path.join(plugin_path, "systems.json")
  
    this.assetspath = f"{plugin_path}/assets"

    if configPlugin.never == True:
        logger.debug("new config mode")
        logger.debug(json.dumps(configPlugin, ensure_ascii=False, indent=4, cls=ConfigEncoder))
    else:
        this.discordText = tk.StringVar(value=config.get_str("dText") or "@Leader Earned @MeritsValue merits in @System")
        this.saveSession = tk.BooleanVar(value=(config.get_str("saveSession") =="True" if config.get_str("saveSession") else True))
        configPlugin.never = True
        configPlugin.reportSave = this.saveSession
        configPlugin.copyText = this.discordText
    
    this.newest = checkVersion()

    if not os.path.exists(file_path):
        os.makedirs(plugin_path, exist_ok=True)
        with open(file_path, "w") as json_file:
            json.dump(pledgedPower, json_file, indent=4, cls=PowerEncoder)
        pledgedPower.from_dict({})  # NEU: auf die existierende Instanz schreiben
    else:
        try:
            with open(file_path, "r") as json_file:
                pledgedPower.from_dict(json.load(json_file))  # KORREKT
        except json.JSONDecodeError:
            pledgedPower.from_dict({})  # NEU: leeren Dict in Singleton laden

              
    # Laden der gespeicherten Systeme
    if os.path.exists(systems_path):
        try:
            with open(systems_path, "r") as json_file:
                tmp = json.load(json_file)
                for name, system_data in tmp.items():
                    if not isinstance(system_data, dict):
                        continue
                    n = StarSystem()
                    n.from_dict(system_data)
                    systems[name] = n
                    if n.Active == True:
                        this.currentSystemFlying = systems[name]
                    
        except json.JSONDecodeError:
            logger.error("Failed to load systems.json, using empty Systems data.")
            systems.__init__()  # NEU: leeres Dict in Singleton laden
            this.currentSystemFlying = StarSystem()
            this.currentSystemFlying.meInit()
            systems[this.currentSystemFlying.StarSystem] = this.currentSystemFlying
        
def dashboard_entry(cmdr: str, is_beta: bool, entry: Dict[str, Any]):
    if (this.currentSystemFlying):
        update_display()

def position_button():
    entry_y = this.currentSystemEntry.winfo_y()
    entry_height = this.currentSystemEntry.winfo_height()
    button_y = entry_y + (entry_height // 2) - (this.currentSystemButton.winfo_height() // 2)
    this.currentSystemButton.place(x=this.currentSystemEntry.winfo_x() + this.currentSystemEntry.winfo_width() + 10, y=button_y)

def plugin_stop():
    # Sicherstellen, dass "Systems" existiert
    logger.info("Shutting down plugin.")
    update_json_file()
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    systems_path = os.path.join(plugin_dir, "systems.json")
    test_system_merits_path = os.path.join(plugin_dir, "systems_test.json")
    
    filtered_systems = {
        name: data.to_dict()
        for name, data in systems.items()
        if (not data.reported and data.Merits > 0) or data.Active == True
    }
    try:
        with open(systems_path, "w") as json_file:
            json.dump(filtered_systems, json_file, indent=4)
    except Exception as e:
        logger.error(f"Failed to save system merits: {e}")
            
    if this.dump_test:
        try:
            with open(test_system_merits_path, "w") as json_file_test:
                with open(test_system_merits_path, "w") as json_file_test:
                    json.dump(filtered_systems, json_file_test, indent=4)  # Leere JSON-Datei schreiben
        except Exception as e:
            logger.error(f"Failed to save system merits: {e}")
            
    this.frame.quit()
    logger.info("Shutting down plugin.")
    

def plugin_app(parent):
    # Adds to the main page UI
    stateButton = tk.NORMAL if this.debug or len(systems)>0 else tk.DISABLED
    this.frame = tk.Frame(parent)
    this.frame_row1 = tk.Frame(this.frame)
    this.frame_row1.grid(row=0, column=0, columnspan=3, sticky="w")
    this.frame_row2 = tk.Frame(this.frame)
    this.frame_row2.grid(row=1, column=0, columnspan=3, sticky="w")
    this.frame_row3 = tk.Frame(this.frame)
    this.frame_row3.grid(row=2, column=0, columnspan=3, sticky="w")
    this.frame_row4 = tk.Frame(this.frame)
    this.frame_row4.grid(row=3, column=0, columnspan=3, sticky="w")
    this.frame_row5 = tk.Frame(this.frame)
    this.frame_row5.grid(row=4, column=0, columnspan=3, sticky="w")
    this.frame_row6 = tk.Frame(this.frame)
    this.frame_row6.grid(row=5, column=0, columnspan=3, sticky="we", padx=0, pady=2)
    this.frame_row7= tk.Frame(this.frame)
    this.frame_row7.grid(row=6, column=0, columnspan=3, sticky="w")

    this.power = tk.Label(this.frame_row1, text=f"Pledged: {pledgedPower.Power} - Rank : {pledgedPower.Rank}".strip(), anchor="w", justify="left")
    this.powerMerits = tk.Label(this.frame_row2 ,text=f"Merits session: {pledgedPower.MeritsSession:,} - Total: {pledgedPower.Merits:,}".strip(), anchor="w", justify="left")
    this.currentSystemLabel = tk.Label(this.frame_row3, text="Waiting for Events".strip(), anchor="w", justify="left")
    this.systemPowerLabel = tk.Label(this.frame_row4, text="Powerplay Status", anchor="w", justify="left")
    this.systemPowerStatusLabel = tk.Label(this.frame_row5, text="Net progress", anchor="w", justify="left")
    this.station_eco_label = tk.Label(this.frame_row7, text="", anchor="w", justify="left")

    parent.root = tk.Tk()
    parent.root.withdraw()  # Hide the main window

    scale = get_scale_factor(parent.root.winfo_screenwidth(), parent.root.winfo_screenheight())

    imagedelete = load_and_scale_image(f"{this.assetspath}/delete.png", scale)
    this.frame.icondelete = ImageTk.PhotoImage(imagedelete)

    this.systemPowerLabel.grid(row=0, column=0, sticky='w', padx=0, pady=0)
    this.systemPowerStatusLabel.grid(row=0, column=0, sticky='w', padx=0, pady=0)
    this.station_eco_label.grid(row=0, column=0, sticky='w', padx=0, pady=0)
    this.currentSystemLabel.grid(row=0, column=0, sticky='w', padx=0, pady=0)
    # Positionierung der Labels
    this.power.grid(row=0, column=0, columnspan=3, sticky='w', padx=0, pady=0)
    this.powerMerits.grid(row=0, column=0, columnspan=3, sticky='w', padx=0, pady=0)
    # Button zum Anzeigen der Power Info
    this.resetButton = tk.Button(
        this.frame_row6,
        image=this.frame.icondelete,
        command=reset,
        state=stateButton
    )
    this.resetButton.pack(side="right", padx=0, pady=2)  # Rechtsbündig platzieren
    if this.newest == 1:
        this.updateButton = tk.Button(
            this.frame_row6, text="Update Available", 
            command=lambda: auto_update(), 
            fg="red", 
            font=("Arial", 10, "bold"),
            state=tk.NORMAL,
            compound="right"
        )
        this.updateButton.pack(side="left", padx=0, pady=2)   
    this.showButton = tk.Button(
        this.frame_row6,
        text="Overview",
        command=lambda: show_power_info(parent, pledgedPower, systems),
        state=stateButton,
        compound="center"
    )
    this.showButton.pack(side="left", expand=True, fill="both", padx=0, pady=2) 

    return this.frame

def reset():
    # Initialisiere ein neues Dictionary für Systeme
    if this.currentSystemFlying:
       lastState = this.currentSystemFlying
       systems.__init__()  # Leeres Dict in Singleton laden
       systems[this.currentSystemFlying.StarSystem] = this.currentSystemFlying
    update_display()


def plugin_prefs(parent, cmdr, is_beta):
    config_frame = nb.Frame(parent)
    config_frame.columnconfigure(1, weight=1)
    config_frame.grid(sticky=tk.EW)
    # Label für die Beschreibung
    nb.Label(config_frame, text="Copy paste text value - Text must contain @MeritsValue and @System for replacement").grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=5)
    # Textfeld für die Eingabe
    nb.Label(config_frame, text="@MeritsValue,@System,@CPOppositon,@CPControlling").grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=5)
    text_entry = nb.Entry(config_frame, textvariable=this.copyText, width=50)
    text_entry.grid(row=next_config_row(), column=0, padx=5, pady=5, sticky="we")
    nb.Label(config_frame, text="").grid(row=next_config_row(), column=0,sticky="w", padx=5, pady=5)
    nb.Label(config_frame, text="Discordwebhook URL").grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=5)
    text_entry = nb.Entry(config_frame, textvariable=this.discordHook, width=50)
    text_entry.grid(row=next_config_row(), column=0, padx=5, pady=5, sticky="we")
    nb.Checkbutton(config_frame, text="Report merits from source system to discord on FSDJump", variable=this.reportOnFSDJump).grid(
            row=next_config_row(), columnspan=2, sticky=tk.W)
    nb.Label(config_frame, text="").grid(row=next_config_row(), column=0,sticky="w", padx=5, pady=5)
    nb.Label(config_frame, text=f"Version {this.version}").grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=5)
    return config_frame

def current_config_row():
    return this.crow

def next_config_row():
    this.crow += 1
    return this.crow

def update_system_merits(merits_value, total):
    try:
        merits = int(merits_value)
        pledgedPower.MeritsSession += merits
        # Aktualisiere Merits im aktuellen System
        if this.currentSystemFlying.StarSystem in systems:
            systems[this.currentSystemFlying.StarSystem].Merits += merits
        else:
            systems[this.currentSystemFlying.StarSystem]= this.currentSystemFlying
            systems[this.currentSystemFlying.StarSystem].Merits = merits
        # Direkte Aktualisierung der Anzeige
        pledgedPower.Merits = int(total)
        update_display()
    except ValueError:
        logger.debug("Invalid merits value. Please enter a number.")

def prefs_changed(cmdr, is_beta):
    configPlugin.copyText = this.copyText.get()
    configPlugin.discordHook = this.discordHook.get()
    configPlugin.reportOnFSDJump = this.reportOnFSDJump.get()
    configPlugin.dumpConfig()
    logger.debug(json.dumps(configPlugin, ensure_ascii=False, indent=4, cls=ConfigEncoder))
    update_display()
           
def update_json_file():
    directory_name = os.path.basename(os.path.dirname(__file__))
    plugin_path = os.path.join(config.plugin_dir, directory_name)
    file_path = os.path.join(plugin_path, "power.json")
    with open(file_path, "w") as json_file:
        json.dump(pledgedPower, json_file, indent=4, cls=PowerEncoder)

def journal_entry(cmdr, is_beta, system, station, entry, state):
    if entry['event'] in ['Powerplay']:
        pledgedPower.__init__(eventEntry=entry)  # NEU: re-initialisiere das Singleton-Objekt
        update_display()
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
        update_display()

def updateSystemTracker(oldSystem, newSystem):
    if (oldSystem != None) :
        systems[oldSystem.StarSystem].Active = False

    systems[newSystem.StarSystem].Active = True
    this.currentSystemFlying = newSystem
    

def update_display():
    if (not this.currentSystemFlying):
        return
    this.power["text"] = f"Pledged: {pledgedPower.Power} - Rank : {pledgedPower.Rank}"
    this.powerMerits["text"] = f"Merits session: {pledgedPower.MeritsSession:,} - total: {pledgedPower.Merits:,}".strip()
    if this.currentSystemFlying != None and this.currentSystemFlying.StarSystem != "":
            this.showButton.config(state=tk.NORMAL)
            this.resetButton.config(state=tk.NORMAL)
    else:
        logger.info("No Current System")

    try:
        #logger.debug(system_data)
        power = this.currentSystemFlying.getSystemStatePowerPlay(pledged=pledgedPower.Power)[0]
        #logger.debug("ZEFIX")
        powerprogress = this.currentSystemFlying.getSystemProgressNumber()

        if powerprogress is None:
            powerprogress_percent = "--%"
        else:
            powerprogress_percent = f"{powerprogress:.2f}%".rstrip('0').rstrip('.')

        this.currentSystemLabel["text"] = f"'{this.currentSystemFlying.StarSystem}' : {this.currentSystemFlying.Merits} merits gained".strip()
        this.systemPowerLabel["text"] = f"{this.currentSystemFlying.getSystemStateText()} ({powerprogress_percent}) by {power}  ".strip()
        powercycle = this.currentSystemFlying.getPowerplayCycleNetValue()
        
        if powercycle is None:
            systemPowerStatusText = ""
        else:
            reinforcement = powercycle[0]
            undermining = powercycle[1]

            if not this.currentSystemFlying.PowerplayConflictProgress:
                systemPowerStatusText = f"Powerplaycycle {this.currentSystemFlying.getPowerPlayCycleNetStatusText()}"
            else:
                systemPowerStatusText = ""

        this.systemPowerStatusLabel["text"] = systemPowerStatusText.strip()
    except KeyError as e:
        logger.debug(f"KeyError for current system '{this.currentSystemFlying}': {e}")
    this.currentSystemLabel.grid()

def get_scale_factor(current_width: int, current_height: int, base_width: int = 2560, base_height: int = 1440) -> float:
    scale_x = current_width / base_width
    scale_y = current_height / base_height
    return min(scale_x, scale_y)  # Use the smaller factor to maintain the aspect ratio.

def load_and_scale_image(path: str, scale: float) -> Image:
    image = Image.open(path)
    new_size = (int(image.width * scale), int(image.height * scale))
    try:
        # Pillow 10.0.0 and later
        resample_filter = Image.Resampling.LANCZOS
    except AttributeError:
        # Older Pillow versions
        resample_filter = Image.LANCZOS

    return image.resize(new_size, resample_filter)

def logdump(here:str, data:dict):
    if this.debug:
        logger.debug(f"{here} - {json.dumps(data, indent=2)}")
