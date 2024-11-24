import os
import tkinter as tk
import sys
import json
import re
from os import path
from config import config
from datetime import datetime, timedelta

this = sys.modules[__name__]  # For holding module globals

this.powerInfo = {}
this.version = 'v0.0.9'

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
        "AccumulatedSince": ""
    }

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

def plugin_app(parent):
    # Adds to the main page UI
    this.frame = tk.Frame(parent)
    this.title = tk.Label(this.frame, text="Powerplay and Merits".strip(), anchor="w", justify="left")
    this.power = tk.Label(this.frame, text=f"Pledged Power : {this.powerInfo['PowerName']}".strip(), anchor="w", justify="left")
    this.powerrank = tk.Label(this.frame, text=f"Rank : {this.powerInfo['Rank']}".strip(), anchor="w", justify="left")
    this.currMerits = tk.Label(this.frame, text=f"Current Merits : {this.powerInfo['Merits']}".strip(), anchor="w", justify="left")
    this.meritsLastSession = tk.Label(this.frame, text=f"LastSession Merits : {this.powerInfo['AccumulatedMerits']}".strip(), anchor="w", justify="left")

    # Positionierung der Labels
    this.title.grid(row=0, column=0, sticky='we')
    this.power.grid(row=1, column=0, sticky='we')
    this.powerrank.grid(row=2, column=0, sticky='we')
    this.currMerits.grid(row=3, column=0, sticky='we')
    this.meritsLastSession.grid(row=4, column=0, sticky='we')
    
    return this.frame


def plugin_prefs(parent, cmdr, is_beta):
	frame = nb.Frame(parent)
	return frame

def prefs_changed(cmdr, is_beta):
	# Saves settings
	update_display()

def update_json_file():
    """Schreibt die aktuelle powerInfo-Datenstruktur in die JSON-Datei."""
    directory_name = path.basename(path.dirname(__file__))
    plugin_path = path.join(config.plugin_dir, directory_name)
    file_path = path.join(plugin_path, "power.json")

    with open(file_path, "w") as json_file:
        json.dump(this.powerInfo, json_file, indent=4)

def journal_entry(cmdr, is_beta, system, station, entry, state):
    print("Event:", entry['event'])
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

        # Dump ins Log
        print("Updated powerInfo:", json.dumps(this.powerInfo, indent=4))

        # Update UI
        update_display()

def update_display():
    this.title["text"] = "Powerplay and Merits".strip()
    this.title.grid()

    this.power["text"] = f"Pledged Power: {this.powerInfo['PowerName'].strip()}".strip()
    this.power.grid()

    this.powerrank["text"] = f"Rank: {str(this.powerInfo['Rank']).strip()}".strip()
    this.powerrank.grid()

    this.currMerits["text"] = f"Current Merits: {str(this.powerInfo['Merits']).strip()}".strip()
    this.currMerits.grid()

    this.meritsLastSession["text"] = f"LastSession Merits : {str(this.powerInfo['AccumulatedMerits']).strip()}".strip()
    this.meritsLastSession.grid()

