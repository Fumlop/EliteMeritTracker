import os
import tkinter as tk
import sys
import json
import requests
import myNotebook as nb
import re
from power_info_window import show_power_info
from ttkHyperlinkLabel import HyperlinkLabel
from os import path
from config import config
import logging
from config import appname
from datetime import datetime, timedelta

this = sys.modules[__name__]  # For holding module globals

this.powerInfo = {}
this.currentSysPP = {"":{"merits":0}}
this.lastSysPP = {"":{"merits":0}}
this.currentSystem = "" 
this.lastSystem = ""
this.version = 'v0.2.3'
this.discordText = ""
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
        logger.debug('Starting request to check version')
        req = requests.get(url='https://api.github.com/repos/Fumlop/EliteMeritTracker/releases/latest')
        logger.debug('Request completed with status code: %s', req.status_code)
    except Exception as e:
        # Exception mit vollständigem Stacktrace loggen
        logger.exception('An error occurred while checking the version')
        return -1

    if req.status_code != requests.codes.ok:
        logger.error('Request failed with status code: %s', req.status_code)
        return -1  # Error

    try:
        data = req.json()
        logger.debug('Response JSON: %s', data)
        logger.debug('Current version: %s', this.version)
        if data['tag_name'] == this.version:
            logger.debug('Latest version is up-to-date: %s', data['tag_name'])
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

def position_button():
    entry_y = this.currentSystemEntry.winfo_y()
    entry_height = this.currentSystemEntry.winfo_height()
    button_y = entry_y + (entry_height // 2) - (this.currentSystemButton.winfo_height() // 2)
    this.currentSystemButton.place(x=this.currentSystemEntry.winfo_x() + this.currentSystemEntry.winfo_width() + 10, y=button_y)

def plugin_app(parent):
    # Adds to the main page UI
    this.currentSystem = "BD-01 1707"
    this.lastSystem = "Rhea"
    this.currentSysPP = { "TEST" :{"sessionMerits":500}}
    this.lastSysPP = { "LAST" :{"sessionMerits":150}}

    this.frame = tk.Frame(parent)
    this.power = tk.Label(this.frame, text=f"Pledged power : {this.powerInfo['PowerName']} - Rank : {this.powerInfo['Rank']}".strip(), anchor="w", justify="left")
    this.currMerits = tk.Label(this.frame, text=f"Current merits : {this.powerInfo['Merits']}".strip(), anchor="w", justify="left")
    this.meritsLastSession = tk.Label(this.frame, text=f"Last session merits : {this.powerInfo['AccumulatedMerits']}".strip(), anchor="w", justify="left")
    this.currentSystemLabel = tk.Label(this.frame, text=f"'{this.currentSystem}'".strip(), anchor="w", justify="left")
    this.currentSystemEntry = tk.Entry(this.frame, width=10)
    
    this.currentSystemButton = tk.Button(this.frame, text="add merits", command=lambda: [update_system_merits(this.currentSystem, this.currentSystemEntry.get()), update_display()])

    this.currentSystemLabel.grid(row=3, column=0, sticky='we')
    this.currentSystemEntry.grid(row=3, column=1, padx=5, sticky='we')
    this.currentSystemButton.grid(row=3, column=2, padx=3, sticky='w')
    this.lastSystemLabel = tk.Label(this.frame, text=f"'{this.lastSystem}'".strip(), anchor="w", justify="left")

    # Positionierung der Labels
    this.power.grid(row=0, column=0, sticky='we')
    this.currMerits.grid(row=1, column=0, sticky='we')
    this.meritsLastSession.grid(row=2, column=0, sticky='we')
    this.currentSystemLabel.grid(row=3, column=0, sticky='we')
    this.lastSystemLabel.grid(row=4, column=0, sticky='we')
    # Button zum Anzeigen der Power Info
    this.showButton = tk.Button(
        this.frame,  # Button wird zu `this.frame` hinzugefügt
        text="Show Merits",
        command=lambda: show_power_info(parent, this.powerInfo, this.discordText)
    )
    this.showButton.grid(row=5, column=0, sticky='we', pady=10)
    #this.reset = tk.Button(
    #    this.frame,  # Button wird zu `this.frame` hinzugefügt
    #    text="Reset",
    #    command=lambda: reset_power(parent, this.powerInfo)
    #)
    #this.reset.grid(row=5, column=1, sticky='we', pady=10)
    this.updateIndicator = HyperlinkLabel(this.frame, text="Update available", anchor=tk.W, url='https://github.com/Fumlop/EliteMeritTracker/releases')
    logger.debug('this.newest: %s', this.newest)
    if this.newest == 1:
        this.updateIndicator.grid(padx = 5, row = 6, column = 0)
    return this.frame
    
def plugin_prefs(parent, cmdr, is_beta):
    config_frame = nb.Frame(parent)
    # Label mit Beschreibung
    tk.Label(config_frame, text="Copy paste text value - Text must contain @MeritsValue and @System for replacement").grid(row=0, column=0, sticky="w", padx=5, pady=5)

    # Textfeld für die Eingabe
    this.discordText = tk.StringVar(value=config.get("dText", "@Leader Earned @MertitsValue merits in @System"))  # Initialisiere mit gespeichertem Wert oder leerem String
    text_entry = tk.Entry(config_frame, textvariable=this.discordText, width=50)
    text_entry.grid(row=1, column=0, padx=5, pady=5, sticky="we")
    logger.debug('this.discordText: %s', this.discordText)    

    return config_frame


def update_system_merits(current_system, merits_value):
    logger.debug('update_merits_value: %s', merits_value)    
    logger.debug('update_current_system: %s', current_system)    
    try:
        merits = int(merits_value)

        # Initialisiere das Systems-Objekt in powerInfo, falls es nicht existiert
        if "Systems" not in this.powerInfo:
            this.powerInfo["Systems"] = {}

        # Aktualisiere Merits im aktuellen System
        if current_system in this.powerInfo["Systems"]:
            this.powerInfo["Systems"][current_system]["sessionMerits"] += merits
        else:
            this.powerInfo["Systems"][current_system] = {"sessionMerits": merits}
        
        logger.debug(f"Updated system '{current_system}': {this.powerInfo['Systems'][current_system]}")

        # Direkte Aktualisierung der Anzeige
        update_display()
    except ValueError:
        logger.debug("Invalid merits value. Please enter a number.")

def prefs_changed(cmdr, is_beta):
	config.set("dText", this.discordText.get())
	update_display()

def update_json_file():
    logger.debug("update_json_file")
    directory_name = path.basename(path.dirname(__file__))
    plugin_path = path.join(config.plugin_dir, directory_name)
    file_path = path.join(plugin_path, "power.json")
    power_info_copy = this.powerInfo.copy()
    if "Systems" in power_info_copy:
        del power_info_copy["Systems"]

    with open(file_path, "w") as json_file:
        json.dump(power_info_copy, json_file, indent=4)

def journal_entry(cmdr, is_beta, system, station, entry, state):
    logger.debug("Event %s", entry['event'])
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
        this.powerInfo.update({
            "PowerName": power_name,
            "Merits": current_merits,
            "Rank": rank,
            "LastUpdate": timestamp,
            "AccumulatedMerits": accumulated_merits,
            "AccumulatedSince": accumulated_since.strftime("%Y-%m-%dT%H:%M:%SZ")
        })

        # JSON aktualisieren
        update_json_file()

        # Block to prepare sytsem merits
        # this.currentSysPP[this.currentSystem]["merits"] += event.merits
        # this.currentSysPP[this.currentSystem]["influence"] += (event.merits/4)
        # Block to prepare sytsem merits
        # Update UI
        update_display()
    if entry['event'] == 'SupercruiseExit':
        logger.debug("SupercruiseExit")
        this.lastSysPP = this.currentSysPP
        this.lastSystem = this.currentSystem
        this.currentSystem = entry.get('StarSystem',"")
        logger.debug(this.currentSystem)
        if "Systems" not in this.powerInfo:
            this.powerInfo["Systems"] = {}
            logger.debug('Initialized "Systems" in powerInfo')
        if this.currentSystem not in this.powerInfo["Systems"]:
            # Neues System zu powerInfo hinzufügen
            this.powerInfo["Systems"][this.currentSystem] = {
                "sessionMerits": 0,
                "state": entry.get('PowerplayState', ""),
                "power": entry.get('ControllingPower', "")
            }
            this.currentSysPP = this.powerInfo["Systems"][this.currentSystem]
            logger.debug(f"Added new system to powerInfo: {this.currentSystem}")
        else:
            this.currentSysPP = this.powerInfo["Systems"][this.currentSystem]
        update_display()
    if entry['event'] == 'Location':
        logger.debug("Location")
        this.currentSystem = entry.get('StarSystem', "")
        logger.debug(this.currentSystem)
        if "Systems" not in this.powerInfo:
            this.powerInfo["Systems"] = {}
            logger.debug('Initialized "Systems" in powerInfo')
        if this.currentSystem not in this.powerInfo["Systems"]:
            # Neues System zu powerInfo hinzufügen
            this.powerInfo["Systems"][this.currentSystem] = {
                "sessionMerits": 0,
                "state": entry.get('PowerplayState', ""),
                "power": entry.get('ControllingPower', "")
            }
            this.currentSysPP = this.powerInfo["Systems"][this.currentSystem]
            logger.debug(f"Added new system to powerInfo: {this.currentSystem}")
        else:
            # Vorhandenes System laden
            this.currentSysPP = this.powerInfo["Systems"][this.currentSystem]

        # Aktualisiere die Anzeige
        update_display()


def update_display():
    logger.debug("update_display called")
    logger.debug(f"Current system: {this.currentSystem}")
    logger.debug(f"Last system: {this.lastSystem}")
    logger.debug("Systems data:")

    this.currMerits["text"] = f"Current merits: {str(this.powerInfo['Merits']).strip()}".strip()
    this.currMerits.grid()

    this.meritsLastSession["text"] = f"Last session merits : {str(this.powerInfo['AccumulatedMerits']).strip()}".strip()
    this.meritsLastSession.grid()

    try:
        # Aktuelle Merits aus Systems abrufen
        curr_system_merits = this.powerInfo["Systems"][this.currentSystem]["sessionMerits"]
        logger.debug(f"Merits for current system '{this.currentSystem}': {curr_system_merits}")
        this.currentSystemLabel["text"] = f"'{this.currentSystem}' (Merits: {curr_system_merits})".strip()
    except KeyError as e:
        logger.debug(f"KeyError for current system '{this.currentSystem}': {e}")

    this.currentSystemLabel.grid()

    try:
        last_system_merits = this.powerInfo["Systems"][this.lastSystem]["sessionMerits"]
        logger.debug(f"'{this.lastSystem}': {last_system_merits}")
        this.lastSystemLabel["text"] = f"'{this.lastSystem}' (Merits: {last_system_merits})".strip()
    except KeyError as e:
        logger.debug(f"KeyError for last system '{this.lastSystem}': {e}")
        this.lastSystemLabel["text"] = f"'{this.lastSystem}' (Merits: N/A)".strip()

    this.lastSystemLabel.grid()
