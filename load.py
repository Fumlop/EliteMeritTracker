from imports import *
from system import *
from power import *
from power_info_window import show_power_info

this = sys.modules[__name__]  # For holding module globals
this.debug = False
this.dump_test = False
this.systems = {}
this.pledgedPower = PledgedPower()
this.currentSystemFlying = StarSystem()
this.station_ecos = []
this.trackedMerits = 0
this.version = 'v0.4.59.1.200'

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

def plugin_app(parent):
    this.frame = tk.Frame(parent)

    if this.newest == 1:
        this.updateButton = tk.Button(
            this.frame, text="Update Available", command=auto_update, fg="red"
        )
        this.updateButton.grid(row=5, column=0, padx=5, pady=5, sticky="w")

    return this.frame

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
    directory_name = os.path.basename(os.path.dirname(__file__))
    plugin_path = os.path.join(config.plugin_dir, directory_name)
    file_path = os.path.join(plugin_path, "power.json")
    systems_path = os.path.join(plugin_path, "systems.json")
  
    this.assetspath = f"{plugin_path}/assets"

    # Initialize discordText
    this.discordText = tk.StringVar(value=config.get_str("dText") or "@Leader Earned @MeritsValue merits in @System")
    this.saveSession = tk.BooleanVar(value=(config.get_str("saveSession") =="True" if config.get_str("saveSession") else True))
    default_system:StarSystem = StarSystem(eventEntry={},reported=False)
    default_pledgedPower:PledgedPower = PledgedPower(eventEntry={})
    
    this.newest = checkVersion()

    # JSON prüfen oder initialisieren
    if not os.path.exists(file_path):
        os.makedirs(plugin_path, exist_ok=True)
        with open(file_path, "w") as json_file:
            json.dump(default_pledgedPower.to_dict(), json_file, indent=4)
        this.pledgedPower = default_pledgedPower
    else:
        try:
            with open(file_path, "r") as json_file:
                this.pledgedPower.from_dict(json.load(json_file))
                if not this.pledgedPower:
                    this.pledgedPower = default_pledgedPower
        except json.JSONDecodeError:
            this.pledgedPower = default_pledgedPower
              
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
                    this.systems[name] = n
                    if n.Active == True:
                        this.currentSystemFlying = this.systems[name]
                    
        except json.JSONDecodeError:
            logger.error("Failed to load systems.json, using empty Systems data.")
            this.systems = {}
        
def dashboard_entry(cmdr: str, is_beta: bool, entry: Dict[str, Any]):
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
        for name, data in this.systems.items()
        if not data.reported and data.Merits > 0
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
    stateButton = tk.NORMAL if this.debug or len(this.systems)>0 else tk.DISABLED
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

    this.power = tk.Label(this.frame_row1, text=f"Pledged: {this.pledgedPower.Power} - Rank : {this.pledgedPower.Rank}".strip(), anchor="w", justify="left")
    this.powerMerits = tk.Label(this.frame_row2 ,text=f"Merits session: {this.pledgedPower.MeritsSession:,} - Total: {this.pledgedPower.Merits:,}".strip(), anchor="w", justify="left")
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
        command=lambda: show_power_info(parent, this.pledgedPower, this.systems, this.discordText.get()),
        state=stateButton,
        compound="center"
    )
    this.showButton.pack(side="left", expand=True, fill="both", padx=0, pady=2) 
     
    #if this.debug:
    #   update_display()
    return this.frame

def reset():
    # Initialisiere ein neues Dictionary für Systeme
    if this.currentSystemFlying:
       lastState = this.currentSystemFlying
       this.systems = {}
       this.systems[this.currentSystemFlying.StarSystem] = this.currentSystemFlying
    update_display()


def plugin_prefs(parent, cmdr, is_beta):
    config_frame = nb.Frame(parent)

    # Label für die Beschreibung
    tk.Label(config_frame, text="Copy paste text value - Text must contain @MeritsValue and @System for replacement").grid(row=0, column=0, sticky="w", padx=5, pady=5)

    # Textfeld für die Eingabe
    text_entry = tk.Entry(config_frame, textvariable=this.discordText, width=50)
    text_entry.grid(row=1, column=0, padx=5, pady=5, sticky="we")
    tk.Label(config_frame, text="Save non-reported system merits on exiting edmc").grid(row=3, column=0, sticky="w", padx=5, pady=5)
    bool_entry = tk.Checkbutton(config_frame, variable=this.saveSession)
    bool_entry.grid(row=3, column=3, sticky="w", padx=5, pady=5)
    
    tk.Label(config_frame, text="Optional place holder @CPOppositon, @CPPledged").grid(row=5, column=0, sticky="w", padx=5, pady=5)
    
    tk.Label(config_frame, text=f"Version {this.version}").grid(row=10, column=0, sticky="w", padx=5, pady=5)
    return config_frame

def update_system_merits(merits_value, total):
    try:
        merits = int(merits_value)
        this.pledgedPower.MeritsSession += merits
        # Aktualisiere Merits im aktuellen System
        if this.currentSystemFlying.StarSystem in this.systems:
            this.systems[this.currentSystemFlying.StarSystem].Merits += merits
        else:
            this.systems[this.currentSystemFlying.StarSystem]= this.currentSystemFlying
            this.systems[this.currentSystemFlying.StarSystem].Merits = merits
        # Direkte Aktualisierung der Anzeige
        this.pledgedPower.Merits = int(total)
        update_display()
    except ValueError:
        logger.debug("Invalid merits value. Please enter a number.")

def prefs_changed(cmdr, is_beta):
    # Speichere den aktuellen Wert der StringVar in die Konfiguration
    config.set("dText", this.discordText.get())
    config.set("saveSession", str(this.saveSession.get()))
    logger.info(str(this.saveSession.get()))
    update_display()
           
def update_json_file():
    if (this.debug == False):
        directory_name = os.path.basename(os.path.dirname(__file__))
        plugin_path = os.path.join(config.plugin_dir, directory_name)
        file_path = os.path.join(plugin_path, "power.json")
        with open(file_path, "w") as json_file:
            json.dump(this.pledgedPower.to_dict(), json_file, indent=4)

def journal_entry(cmdr, is_beta, system, station, entry, state):
    if entry['event'] in ['Powerplay']:
        this.pledgedPower = PledgedPower(eventEntry=entry)
        update_display()
    if entry['event'] in ['PowerplayMerits']:
        merits = entry.get('MeritsGained')
        total = entry.get('TotalMerits')
        update_system_merits(merits,total)
    if entry['event'] in ['FSDJump', 'Location','SupercruiseEntry','SupercruiseExit']:
        
        nameSystem = entry.get('StarSystem',"Nomansland")
        if (not this.systems or len(this.systems)==0 or nameSystem not in this.systems):
            new_system = StarSystem(eventEntry=entry)
            logger.debug(f"Created new system- {nameSystem}")
            logger.debug(f"Existing systems- {len(this.systems)}")
            this.systems[new_system.StarSystem] = new_system
            logger.debug(new_system.to_dict())
        updateSystemTracker(this.currentSystemFlying,this.systems[nameSystem])
        
        update_display()

def updateSystemTracker(oldSystem, newSystem):
    this.systems[oldSystem.StarSystem].Active = False
    this.systems[newSystem.StarSystem].Active = True
    this.currentSystemFlying = newSystem
    

def update_display():
    this.power["text"] = f"Pledged: {this.pledgedPower.Power} - Rank : {this.pledgedPower.Rank}"
    this.powerMerits["text"] = f"Merits session: {this.pledgedPower.MeritsSession:,} - total: {this.pledgedPower.Merits:,}".strip()
    if this.currentSystemFlying.StarSystem != "":
            this.showButton.config(state=tk.NORMAL)
            this.resetButton.config(state=tk.NORMAL)
    else:
        logger.info("No Current System")

    try:
        #logger.debug(system_data)
        power = this.currentSystemFlying.getSystemStatePowerPlay(pledged=this.pledgedPower.Power)[0]
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
    if len(this.station_ecos) > 0:
        this.station_eco_label["text"] = "\n".join(this.station_ecos)
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
