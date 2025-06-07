# trackerUI.py

import tkinter as tk
from PIL import Image, ImageTk
from power import pledgedPower
from system import systems
import os
import sys
from config import config
from log import logger
from pluginDetailsUI import show_power_info


class TrackerFrame:
    def __init__(self, parent=None,newest=False):
        self.parent = parent
        self.newest = newest
        self.icondelete = None
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.assetspath = f"{self.plugin_dir}/assets"
        self.this = sys.modules[__name__]
        self.frame = None
        self.frame_row1 = None
        self.frame_row2 = None     
        self.frame_row3 = None
        self.frame_row4 = None
        self.frame_row5 = None
        self.frame_row6 = None
        self.frame_row7 = None
        self.power = None
        self.powerMerits = None   
        self.currentSystemLabel = None
        self.systemPowerLabel = None
        self.systemPowerStatusLabel = None
        self.station_eco_label = None
        self.resetButton = None
        self.updateButton = None
        self.showButton = None
    
    def get_scale_factor(self,current_width: int, current_height: int, base_width: int = 2560, base_height: int = 1440) -> float:
        scale_x = current_width / base_width
        scale_y = current_height / base_height
        return min(scale_x, scale_y)  

    def load_and_scale_image(self,path: str, scale: float) -> Image:
        image = Image.open(path)
        new_size = (int(image.width * scale), int(image.height * scale))
        try:
            # Pillow 10.0.0 and later
            resample_filter = Image.Resampling.LANCZOS
        except AttributeError:
            # Older Pillow versions
            resample_filter = Image.LANCZOS

        return image.resize(new_size, resample_filter)

    def update_display(self, currentSystemFlying):
        if (not currentSystemFlying):
            return
        self.power["text"] = f"Pledged: {pledgedPower.Power} - Rank : {pledgedPower.Rank}"
        self.powerMerits["text"] = f"Merits session: {pledgedPower.MeritsSession:,} - total: {pledgedPower.Merits:,}".strip()
        if currentSystemFlying != None and currentSystemFlying.StarSystem != "":
                self.showButton.config(state=tk.NORMAL)
                self.resetButton.config(state=tk.NORMAL)
        else:
            logger.info("No Current System")

        try:
            #logger.debug(system_data)
            power = currentSystemFlying.getSystemStatePowerPlay(pledged=pledgedPower.Power)[0]
            #logger.debug("ZEFIX")
            powerprogress = currentSystemFlying.getSystemProgressNumber()

            if powerprogress is None:
                powerprogress_percent = "--%"
            else:
                powerprogress_percent = f"{powerprogress:.2f}%".rstrip('0').rstrip('.')

            self.currentSystemLabel["text"] = f"'{currentSystemFlying.StarSystem}' : {currentSystemFlying.Merits} merits gained".strip()
            self.systemPowerLabel["text"] = f"{currentSystemFlying.getSystemStateText()} ({powerprogress_percent}) by {power}  ".strip()
            powercycle = currentSystemFlying.getPowerplayCycleNetValue()
            
            if powercycle is None:
                systemPowerStatusText = ""
            else:
                reinforcement = powercycle[0]
                undermining = powercycle[1]

                if not currentSystemFlying.PowerplayConflictProgress:
                    systemPowerStatusText = f"Powerplaycycle {currentSystemFlying.getPowerPlayCycleNetStatusText()}"
                else:
                    systemPowerStatusText = ""

            self.systemPowerStatusLabel["text"] = systemPowerStatusText.strip()
        except KeyError as e:
            logger.debug(f"KeyError for current system '{currentSystemFlying}': {e}")
        self.currentSystemLabel.grid()

    def create_tracker_frame(self, reset, auto_update):
        stateButton = tk.NORMAL if len(systems) > 0 else tk.DISABLED
        self.frame = tk.Frame(self.parent,name="eliteMeritTrackerComponentframe")
        self.frame_row1 = tk.Frame(self.frame,name="eliteMeritTrackerComponentframe_row1")
        self.frame_row1.grid(row=0, column=0, columnspan=3, sticky="w")
        self.frame_row2 = tk.Frame(self.frame,name="eliteMeritTrackerComponentframe_row2")
        self.frame_row2.grid(row=1, column=0, columnspan=3, sticky="w")
        self.frame_row3 = tk.Frame(self.frame,name="eliteMeritTrackerComponentframe_row3")
        self.frame_row3.grid(row=2, column=0, columnspan=3, sticky="w")
        self.frame_row4 = tk.Frame(self.frame,name="eliteMeritTrackerComponentframe_row4")
        self.frame_row4.grid(row=3, column=0, columnspan=3, sticky="w")
        self.frame_row5 = tk.Frame(self.frame,name="eliteMeritTrackerComponentframe_row5")
        self.frame_row5.grid(row=4, column=0, columnspan=3, sticky="w")
        self.frame_row6 = tk.Frame(self.frame,name="eliteMeritTrackerComponentframe_row6")
        self.frame_row6.grid(row=5, column=0, columnspan=3, sticky="we", padx=0, pady=2)
        self.frame_row7 = tk.Frame(self.frame,name="eliteMeritTrackerComponentframe_row7")
        self.frame_row7.grid(row=6, column=0, columnspan=3, sticky="w")

        self.power = tk.Label(
            self.frame_row1,
            text=f"Pledged: {pledgedPower.Power} - Rank : {pledgedPower.Rank}".strip(),
            anchor="w", justify="left",name="eliteMeritTrackerComponentpower"
        )
        self.powerMerits = tk.Label(
            self.frame_row2,
            text=f"Merits session: {pledgedPower.MeritsSession:,} - Total: {pledgedPower.Merits:,}".strip(),
            anchor="w", justify="left",name="eliteMeritTrackerComponentpowerMerits"
        )
        self.currentSystemLabel = tk.Label(self.frame_row3, text="Waiting for Events".strip(), anchor="w", justify="left",name="eliteMeritTrackerComponentcurrentSystemLabel")
        self.systemPowerLabel = tk.Label(self.frame_row4, text="Powerplay Status", anchor="w", justify="left",name="eliteMeritTrackerComponentsystemPowerLabel")
        self.systemPowerStatusLabel = tk.Label(self.frame_row5, text="Net progress", anchor="w", justify="left",name="eliteMeritTrackerComponentsystemPowerStatusLabel")

        scale = self.get_scale_factor(self.parent.winfo_toplevel().winfo_screenwidth(), self.parent.winfo_toplevel().winfo_screenheight())
        imagedelete = self.load_and_scale_image(f"{self.assetspath}/delete.png", scale)
        self.icondelete = ImageTk.PhotoImage(imagedelete)

        self.systemPowerLabel.grid(row=0, column=0, sticky='w', padx=0, pady=0)
        self.systemPowerStatusLabel.grid(row=0, column=0, sticky='w', padx=0, pady=0)
        self.currentSystemLabel.grid(row=0, column=0, sticky='w', padx=0, pady=0)
        self.power.grid(row=0, column=0, columnspan=3, sticky='w', padx=0, pady=0)
        self.powerMerits.grid(row=0, column=0, columnspan=3, sticky='w', padx=0, pady=0)

        self.resetButton = tk.Button(
            self.frame_row6,
            image=self.icondelete,
            command=reset,
            state=stateButton,name="eliteMeritTrackerComponentresetButton"
        )
        self.resetButton.pack(side="right", padx=0, pady=2)
        self.updateButton = None
        if self.newest == 1:
            self.updateButton = tk.Button(
                self.frame_row6, text="Update Available",
                command=lambda: auto_update(),
                fg="red",
                font=("Arial", 10, "bold"),
                state=tk.NORMAL,
                compound="right",name="eliteMeritTrackerComponentupdateButton"
            )
            self.updateButton.pack(side="left", padx=0, pady=2)

        self.showButton = tk.Button(
            self.frame_row6,
            text="Overview",
            command=lambda: show_power_info(self.parent, pledgedPower, systems),
            state=stateButton,
            compound="center",name="eliteMeritTrackerComponentshowButton"
        )
        self.showButton.pack(side="left", expand=True, fill="both", padx=0, pady=2)
    
    def updateButtonText(self):
        if self.updateButton is not None:
            self.updateButton.config(text="Please Restart EDMC")
            self.update_display(self.this.currentSystemFlying)

        for widget in [self.power, self.powerMerits, self.currentSystemLabel, self.systemPowerLabel, self.systemPowerStatusLabel]:
            if widget is not None:
                widget.destroy()
        if self.resetButton is not None:
            self.resetButton.config(command=None)
            self.resetButton.pack_forget()
            self.resetButton.destroy()
            logger.debug("Reset Button destroyed")
        if self.updateButton is not None:
            self.updateButton.config(command=None)
            self.updateButton.pack_forget()
            self.updateButton.destroy()
            logger.debug("Update Button destroyed")
        if self.showButton is not None:
            self.showButton.config(command=None)
            self.showButton.pack_forget()
            self.showButton.destroy()
            logger.debug("Show Button destroyed")
        if self.icondelete is not None:
            del self.icondelete
            self.icondelete = None
            logger.debug("Icon delete destroyed")
        if self.frame is not None:
            self.frame.destroy()
            self.frame = None
            logger.debug("Frame destroyed")
        if self.parent is not None:
            self.parent.destroy()
            self.parent = None
            logger.debug("Parent destroyed")
