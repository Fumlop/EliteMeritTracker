# trackerUI.py

import tkinter as tk
from PIL import Image, ImageTk
from power import pledgedPower
from system import systems
import os
import sys
from config import config
from log import logger
from power_info_window import show_power_info


class TrackerFrame:
    def __init__(self, parent=None,newest=False):
        self.parent = parent
        self.newest = newest
        self.frame = None
        self.power = None
        self.powerMerits = None
        self.currentSystemLabel = None
        self.systemPowerLabel = None
        self.systemPowerStatusLabel = None
        self.station_eco_label = None
        self.resetButton = None
        self.updateButton = None
        self.showButton = None
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.assetspath = f"{self.plugin_dir}/assets"
        self.this = sys.modules[__name__]

    
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
        self.this.power["text"] = f"Pledged: {pledgedPower.Power} - Rank : {pledgedPower.Rank}"
        self.this.powerMerits["text"] = f"Merits session: {pledgedPower.MeritsSession:,} - total: {pledgedPower.Merits:,}".strip()
        if self.this.currentSystemFlying != None and self.this.currentSystemFlying.StarSystem != "":
                self.this.showButton.config(state=tk.NORMAL)
                self.this.resetButton.config(state=tk.NORMAL)
        else:
            logger.info("No Current System")

        try:
            #logger.debug(system_data)
            power = self.this.currentSystemFlying.getSystemStatePowerPlay(pledged=pledgedPower.Power)[0]
            #logger.debug("ZEFIX")
            powerprogress = self.this.currentSystemFlying.getSystemProgressNumber()

            if powerprogress is None:
                powerprogress_percent = "--%"
            else:
                powerprogress_percent = f"{powerprogress:.2f}%".rstrip('0').rstrip('.')

            self.this.currentSystemLabel["text"] = f"'{self.this.currentSystemFlying.StarSystem}' : {self.this.currentSystemFlying.Merits} merits gained".strip()
            self.this.systemPowerLabel["text"] = f"{self.this.currentSystemFlying.getSystemStateText()} ({powerprogress_percent}) by {power}  ".strip()
            powercycle = self.this.currentSystemFlying.getPowerplayCycleNetValue()
            
            if powercycle is None:
                systemPowerStatusText = ""
            else:
                reinforcement = powercycle[0]
                undermining = powercycle[1]

                if not self.this.currentSystemFlying.PowerplayConflictProgress:
                    systemPowerStatusText = f"Powerplaycycle {self.this.currentSystemFlying.getPowerPlayCycleNetStatusText()}"
                else:
                    systemPowerStatusText = ""

            self.this.systemPowerStatusLabel["text"] = systemPowerStatusText.strip()
        except KeyError as e:
            logger.debug(f"KeyError for current system '{self.this.currentSystemFlying}': {e}")
        self.this.currentSystemLabel.grid()

    def create_tracker_frame(self, reset, auto_update):
        stateButton = tk.NORMAL if len(systems) > 0 else tk.DISABLED
        self.this.frame = tk.Frame(self.parent)
        self.this.frame_row1 = tk.Frame(self.this.frame)
        self.this.frame_row1.grid(row=0, column=0, columnspan=3, sticky="w")
        self.this.frame_row2 = tk.Frame(self.this.frame)
        self.this.frame_row2.grid(row=1, column=0, columnspan=3, sticky="w")
        self.this.frame_row3 = tk.Frame(self.this.frame)
        self.this.frame_row3.grid(row=2, column=0, columnspan=3, sticky="w")
        self.this.frame_row4 = tk.Frame(self.this.frame)
        self.this.frame_row4.grid(row=3, column=0, columnspan=3, sticky="w")
        self.this.frame_row5 = tk.Frame(self.this.frame)
        self.this.frame_row5.grid(row=4, column=0, columnspan=3, sticky="w")
        self.this.frame_row6 = tk.Frame(self.this.frame)
        self.this.frame_row6.grid(row=5, column=0, columnspan=3, sticky="we", padx=0, pady=2)
        self.this.frame_row7 = tk.Frame(self.this.frame)
        self.this.frame_row7.grid(row=6, column=0, columnspan=3, sticky="w")

        self.this.power = tk.Label(
            self.this.frame_row1,
            text=f"Pledged: {pledgedPower.Power} - Rank : {pledgedPower.Rank}".strip(),
            anchor="w", justify="left"
        )
        self.this.powerMerits = tk.Label(
            self.this.frame_row2,
            text=f"Merits session: {pledgedPower.MeritsSession:,} - Total: {pledgedPower.Merits:,}".strip(),
            anchor="w", justify="left"
        )
        self.this.currentSystemLabel = tk.Label(self.this.frame_row3, text="Waiting for Events".strip(), anchor="w", justify="left")
        self.this.systemPowerLabel = tk.Label(self.this.frame_row4, text="Powerplay Status", anchor="w", justify="left")
        self.this.systemPowerStatusLabel = tk.Label(self.this.frame_row5, text="Net progress", anchor="w", justify="left")
        self.this.station_eco_label = tk.Label(self.this.frame_row7, text="", anchor="w", justify="left")

        self.parent.root = tk.Tk()
        self.parent.root.withdraw()  # Hide the main window

        scale = self.get_scale_factor(self.parent.root.winfo_screenwidth(), self.parent.root.winfo_screenheight())
        imagedelete = self.load_and_scale_image(f"{self.assetspath}/delete.png", scale)
        self.this.frame.icondelete = ImageTk.PhotoImage(imagedelete)

        self.this.systemPowerLabel.grid(row=0, column=0, sticky='w', padx=0, pady=0)
        self.this.systemPowerStatusLabel.grid(row=0, column=0, sticky='w', padx=0, pady=0)
        self.this.station_eco_label.grid(row=0, column=0, sticky='w', padx=0, pady=0)
        self.this.currentSystemLabel.grid(row=0, column=0, sticky='w', padx=0, pady=0)
        self.this.power.grid(row=0, column=0, columnspan=3, sticky='w', padx=0, pady=0)
        self.this.powerMerits.grid(row=0, column=0, columnspan=3, sticky='w', padx=0, pady=0)

        self.this.resetButton = tk.Button(
            self.this.frame_row6,
            image=self.this.frame.icondelete,
            command=reset,
            state=stateButton
        )
        self.this.resetButton.pack(side="right", padx=0, pady=2)

        if self.newest == 1:
            self.this.updateButton = tk.Button(
                self.this.frame_row6, text="Update Available",
                command=lambda: auto_update(),
                fg="red",
                font=("Arial", 10, "bold"),
                state=tk.NORMAL,
                compound="right"
            )
            self.this.updateButton.pack(side="left", padx=0, pady=2)

        self.this.showButton = tk.Button(
            self.this.frame_row6,
            text="Overview",
            command=lambda: show_power_info(self.parent, pledgedPower, systems),
            state=stateButton,
            compound="center"
        )
        self.this.showButton.pack(side="left", expand=True, fill="both", padx=0, pady=2)

        return self.this.frame
