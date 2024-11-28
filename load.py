import os
import tkinter as tk
import sys
import json
import requests
import myNotebook as nb
from typing import Dict, Any
import re
from power_info_window import show_power_info
from ttkHyperlinkLabel import HyperlinkLabel
from os import path
from companion import CAPIData, SERVER_LIVE, SERVER_LEGACY, SERVER_BETA
from config import config, appname
import logging
from datetime import datetime, timedelta

this = sys.modules[__name__]  # For holding module globals
this.debug = False
if (this.debug):
    this.powerInfo = {}
    this.currentSysPP = {"sessionMerits":0,"state":"stronghold", "power":"Felicia Winters"}
    this.currentSystem = "Rhea" 
    this.trackedMerits = 1750
    this.newest = 0
    this.powerInfo = {
        "PowerName": "Felica Winters",
        "Merits": 42424242,
        "Rank": 99,
        "LastUpdate": "",
        "AccumulatedMerits": 500,
        "AccumulatedSince": "",
        "Systems":{
        "Rhea":{"sessionMerits":0,"state":"stronghold", "power":"Felicia Winters"},
        "BD-01 1707":{"sessionMerits":250,"state":"stronghold", "power":"Felicia Winters"},
        "Urks":{"sessionMerits":1500,"state":"stronghold", "power":"Felicia Winters"}}
    }
else:
    this.powerInfo = {}
    this.currentSysPP = {}
    this.currentSystem = "" 
    this.trackedMerits = 0
this.version = 'v0.2.6'
# This could also be returned from plugin_start3()
plugin_name = os.path.basename(os.path.dirname(__file__))

# A Logger is used per 'found' plugin to make it easy to include the plugin's
# folder name in the logging output format.
# NB: plugin_name here *must* be the plugin's folder name as per the preceding
#     code, else the logger won't be properly set up.
logger = logging.getLogger(f'{appname}.{plugin_name}')

# If the Logger has handlers then it was already set up by the core code, else
# it needs setting up here.
if not logger.hasHandlers():
    level = logging.INFO  # So logger.info(...) is equivalent to print()

    logger.setLevel(level)
    logger_channel = logging.StreamHandler()
    logger_formatter = logging.Formatter(f'%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d:%(funcName)s: %(message)s')
    logger_formatter.default_time_format = '%Y-%m-%d %H:%M:%S'
    logger_formatter.default_msec_format = '%s.%03d'
    logger_channel.setFormatter(logger_formatter)
    logger.addHandler(logger_channel)

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

    try:
        data = req.json()
        if data['tag_name'] == this.version:
            return 0  # Newest
        return 1  # Newer version available
    except Exception as e:
        # JSON-Parsing-Fehler loggen
        logger.exception('Error while parsing the JSON response')
        return -1

def plugin_start3(plugin_dir):
    directory_name = path.basename(path.dirname(__file__))
    plugin_path = path.join(config.plugin_dir, directory_name)
    file_path = path.join(plugin_path, "power.json")

    # Initialize discordText
    this.discordText = tk.StringVar(value=config.get("dText", "@Leader Earned @MertitsValue merits in @System"))
    if (this.debug == False):
        # Default-Datenstruktur
        default_data = {
            "PowerName": "",
            "Merits": 0,
            "Rank": 0,
            "LastUpdate": "",
            "AccumulatedMerits": 0,
            "AccumulatedSince": "",
            "Systems":{}
        }

        this.newest = checkVersion()

        # JSON prüfen oder initialisieren
        if not path.exists(file_path):
            os.makedirs(plugin_path, exist_ok=True)
            with open(file_path, "w") as json_file:
                json.dump(default_data, json_file, indent=4)
            this.powerInfo = default_data
        else:
            try:
                with open(file_path, "r") as json_file:
                    this.powerInfo = json.load(json_file)
                    if not this.powerInfo:
                        this.powerInfo = default_data
            except json.JSONDecodeError:
                this.powerInfo = default_data

def dashboard_entry(cmdr: str, is_beta: bool, entry: Dict[str, Any]):
    this.currentSystem = entry.get('StarSystem', this.currentSystem)
    if "Systems" not in this.powerInfo:
        this.powerInfo["Systems"] = {}
    if this.currentSystem not in this.powerInfo["Systems"]:
        # Neues System zu powerInfo hinzufügen
        this.powerInfo["Systems"][this.currentSystem] = {
            "sessionMerits": 0,
            "state": entry.get('PowerplayState', ""),
            "power": entry.get('ControllingPower', "")
        }
        this.currentSysPP = this.powerInfo["Systems"][this.currentSystem]
    else:
        this.currentSysPP = this.powerInfo["Systems"][this.currentSystem]
    update_display()

def position_button():
    entry_y = this.currentSystemEntry.winfo_y()
    entry_height = this.currentSystemEntry.winfo_height()
    button_y = entry_y + (entry_height // 2) - (this.currentSystemButton.winfo_height() // 2)
    this.currentSystemButton.place(x=this.currentSystemEntry.winfo_x() + this.currentSystemEntry.winfo_width() + 10, y=button_y)

def plugin_app(parent):
    # Adds to the main page UI
    stateButton = tk.NORMAL if this.debug else tk.DISABLED
    this.frame = tk.Frame(parent)
    this.power = tk.Label(this.frame, text=f"Pledged power : {this.powerInfo['PowerName']} - Rank : {this.powerInfo['Rank']}".strip(), anchor="w", justify="left")
    this.currMerits = tk.Label(this.frame, text=f"Total merits : {this.powerInfo['Merits']} | Last Session : {this.powerInfo['AccumulatedMerits']}".strip(), anchor="w", justify="left")
    this.meritsTrackedLabel = tk.Label(this.frame, text=f"Tracked merits : {this.trackedMerits}".strip(), anchor="w", justify="left")
    this.systemPowerLabel = tk.Label(this.frame, text="Status : ", anchor="w", justify="left")
    this.currentSystemLabel = tk.Label(this.frame, text="Waiting for Events".strip(),width=15, anchor="w", justify="left")
    this.currentSystemEntry = tk.Entry(this.frame, width=6 )
    this.currentSystemButton = tk.Button(
        this.frame, text="add merits", 
        command=lambda: [update_system_merits(this.currentSystem, this.currentSystemEntry.get()), 
        update_display()],
        state=stateButton)
    this.systemPowerLabel.grid(row=4, column=0, sticky='we')
    this.currentSystemLabel.grid(row=3, column=0, sticky='we')
    this.currentSystemEntry.grid(row=3, column=1, padx=5, sticky='we')
    this.currentSystemButton.grid(row=3, column=2, padx=3, sticky='w')

    # Positionierung der Labels
    this.power.grid(row=0, column=0,columnspan=3, sticky='we')
    this.currMerits.grid(row=1, column=0, sticky='we')
    this.meritsTrackedLabel.grid(row=2, column=0, sticky='we')
    # Button zum Anzeigen der Power Info
    this.showButton = tk.Button(
        this.frame,
        text="Show Merits",
        command=lambda: show_power_info(parent, this.powerInfo, this.discordText.get()),
        state=stateButton
    )
    this.showButton.grid(row=5, column=0, sticky='we', pady=10)
    this.resetButton = tk.Button(
        this.frame,
        text="Reset",
        command=lambda: reset(),
        state=stateButton
    )
    this.resetButton.grid(row=5, column=2, sticky='we', pady=10)
    this.updateIndicator = HyperlinkLabel(this.frame, text="Update available", anchor=tk.W, url='https://github.com/Fumlop/EliteMeritTracker/releases')
    this.version = tk.Label(this.frame, text=f"Version: {this.version}".strip(),width=15, anchor="w", justify="left")
    if this.newest == 1:
        this.updateIndicator.grid(padx = 5, row = 6, column = 0)
    else :
        this.version.grid(padx = 5, row = 6, column = 0)
    return this.frame
    
def reset():
    # Initialisiere ein neues Dictionary für Systeme
    this.powerInfo["Systems"] = {}
    # Prüfe, ob currentSysPP gültig ist und aktuelle Systemdaten enthält
    if this.currentSystem and this.currentSysPP:
        lastState = this.currentSysPP
        # Füge das aktuelle System mit den letzten bekannten Daten hinzu
        this.powerInfo["Systems"][this.currentSystem] = {
            "sessionMerits": 0,
            "state": lastState.get("PowerplayState", ""),
            "power": lastState.get("ControllingPower", "")
        }
        this.currentSysPP = this.powerInfo["Systems"][this.currentSystem]
    else:
        logger.debug("No valid data in currentSysPP for the current system.")

    # Aktualisiere die Anzeige
    update_display()


def plugin_prefs(parent, cmdr, is_beta):
    config_frame = nb.Frame(parent)

    # Label für die Beschreibung
    tk.Label(config_frame, text="Copy paste text value - Text must contain @MeritsValue and @System for replacement").grid(row=0, column=0, sticky="w", padx=5, pady=5)

    # Textfeld für die Eingabe
    text_entry = tk.Entry(config_frame, textvariable=this.discordText, width=50)
    text_entry.grid(row=1, column=0, padx=5, pady=5, sticky="we")

    return config_frame

def update_system_merits(current_system, merits_value):
    try:
        merits = int(merits_value)
        this.trackedMerits += merits
        # Initialisiere das Systems-Objekt in powerInfo, falls es nicht existiert
        if "Systems" not in this.powerInfo:
            this.powerInfo["Systems"] = {}
        this.currentSystemEntry.delete(0, tk.END)
        # Aktualisiere Merits im aktuellen System
        if current_system in this.powerInfo["Systems"]:
            this.powerInfo["Systems"][current_system]["sessionMerits"] += merits
        else:
            this.powerInfo["Systems"][current_system] = {"sessionMerits": merits}
        # Direkte Aktualisierung der Anzeige
        update_display()
    except ValueError:
        logger.debug("Invalid merits value. Please enter a number.")

def prefs_changed(cmdr, is_beta):
    # Speichere den aktuellen Wert der StringVar in die Konfiguration
    config.set("dText", this.discordText.get())
    update_display()

def update_json_file():
    if (this.debug == False):
        directory_name = path.basename(path.dirname(__file__))
        plugin_path = path.join(config.plugin_dir, directory_name)
        file_path = path.join(plugin_path, "power.json")
        power_info_copy = this.powerInfo.copy()
        if "Systems" in power_info_copy:
            del power_info_copy["Systems"]

        with open(file_path, "w") as json_file:
            json.dump(power_info_copy, json_file, indent=4)

def journal_entry(cmdr, is_beta, system, station, entry, state):
    if entry['event'] == 'Powerplay':
        current_merits = entry.get('Merits', this.powerInfo.get("Merits", 0))
        last_merits = this.powerInfo.get("Merits", 0)
        earned_merits = current_merits - last_merits
        rank = entry.get("Rank", this.powerInfo.get("Rank", 0))
        power_name = entry.get("Power", this.powerInfo.get("PowerName", ""))
        timestamp = entry.get("timestamp", this.powerInfo.get("LastUpdate", ""))

        
        # Konvertiere Timestamp
        current_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        accumulated_since_str = this.powerInfo.get("AccumulatedSince", "")
        if accumulated_since_str:
            accumulated_since = datetime.strptime(accumulated_since_str, "%Y-%m-%dT%H:%M:%SZ")
        else:
            accumulated_since = current_time
        
        # Berechnung der akkumulierten Merits über 24 Stunden
        accumulated_merits = this.powerInfo.get("AccumulatedMerits", 0)
        accumulated_merits = earned_merits
        #if (current_time - accumulated_since) > timedelta(hours=1440):
        #    accumulated_merits = earned_merits
        #    accumulated_since = current_time
        #else:
        #    accumulated_merits += earned_merits

        # Aktualisiere PowerInfo-Daten
        this.powerInfo["PowerName"] = power_name
        this.powerInfo["Merits"] = current_merits
        this.powerInfo["Rank"] = rank
        this.powerInfo["LastUpdate"] = timestamp
        this.powerInfo["AccumulatedMerits"] = accumulated_merits
        this.powerInfo["AccumulatedSince"] = accumulated_since.strftime("%Y-%m-%dT%H:%M:%SZ")

        # JSON aktualisieren
        update_json_file()

        # Block to prepare sytsem merits
        # this.currentSysPP[this.currentSystem]["merits"] += event.merits
        # this.currentSysPP[this.currentSystem]["influence"] += (event.merits/4)
        # Block to prepare sytsem merits
        # Update UI
        update_display()
    if entry['event'] in ['FSDJump', 'Location']:
        this.currentSystem = entry.get('StarSystem',"")
        if "Systems" not in this.powerInfo:
            this.powerInfo["Systems"] = {}
        if this.currentSystem not in this.powerInfo["Systems"]:
            # Neues System zu powerInfo hinzufügen
            this.powerInfo["Systems"][this.currentSystem] = {
                "sessionMerits": 0,
                "state": entry.get('PowerplayState', ""),
                "power": entry.get('ControllingPower', "")
            }
            this.currentSysPP = this.powerInfo["Systems"][this.currentSystem]
        else:
            this.currentSysPP = this.powerInfo["Systems"][this.currentSystem]
        update_display()


def update_display():
    this.currMerits["text"] = f"Total merits : {str(this.powerInfo['Merits'])} | Last Session : {str(this.powerInfo['AccumulatedMerits'])}".strip()
    this.currMerits.grid()

    this.meritsTrackedLabel["text"] = f"Tracked merits : {str(this.trackedMerits)}".strip().strip()
    this.meritsTrackedLabel.grid()

    if this.currentSystem and this.currentSysPP:
            this.currentSystemButton.config(state=tk.NORMAL)
            this.showButton.config(state=tk.NORMAL)
            this.resetButton.config(state=tk.NORMAL)
    else:
        raise KeyError("No valid data for currentSystem or currentSysPP")

    try:
        # Aktuelle Merits aus Systems abrufen
        curr_system_merits = this.powerInfo["Systems"][this.currentSystem]["sessionMerits"]
        power = this.powerInfo["Systems"][this.currentSystem]["power"]
        powerstate = this.powerInfo["Systems"][this.currentSystem]["state"]
        this.currentSystemLabel["text"] = f"'{this.currentSystem}' : {curr_system_merits} merits".strip()
        this.systemPowerLabel["text"] = f"Status : {power} - {powerstate}".strip()
    except KeyError as e:
        logger.debug(f"KeyError for current system '{this.currentSystem}': {e}")

    this.currentSystemLabel.grid()
