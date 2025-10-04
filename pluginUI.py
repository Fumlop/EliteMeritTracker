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
    def __init__(self, parent=None, newest=False):
        self.parent = parent
        self.newest = newest
        self.icondelete = None
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.assetspath = f"{self.plugin_dir}/assets"
        self.this = sys.modules[__name__]
        
        # Initialize all frame and widget references
        self.frame = None
        self.frames = {}  # Store all row frames
        self.widgets = {}  # Store all widgets
    
    def get_scale_factor(self, current_width: int, current_height: int, base_width: int = 2560, base_height: int = 1440) -> float:
        scale_x = current_width / base_width
        scale_y = current_height / base_height
        return min(scale_x, scale_y)

    def load_and_scale_image(self, path: str, scale: float) -> Image:
        image = Image.open(path)
        new_size = (int(image.width * scale), int(image.height * scale))
        try:
            resample_filter = Image.Resampling.LANCZOS
        except AttributeError:
            resample_filter = Image.LANCZOS
        return image.resize(new_size, resample_filter)

    def update_display(self, currentSystemFlying):
        if not currentSystemFlying:
            return
            
        # Update power information
        self.widgets['power']['text'] = f"Pledged: {pledgedPower.Power} - Rank: {pledgedPower.Rank}"
        self.widgets['powerMerits']['text'] = f"Merits session: {pledgedPower.MeritsSession:,} - total: {pledgedPower.Merits:,}"
        
        # Enable buttons if system is available
        if currentSystemFlying and currentSystemFlying.StarSystem:
            self.widgets['showButton'].config(state=tk.NORMAL)
            self.widgets['resetButton'].config(state=tk.NORMAL)
        else:
            logger.info("No Current System")
            return

        try:
            power = currentSystemFlying.getSystemStatePowerPlay(pledged=pledgedPower.Power)[0]
            powerprogress = currentSystemFlying.getSystemProgressNumber()
            powerprogress_percent = f"{powerprogress:.2f}%" if powerprogress is not None else "--%"

            self.widgets['currentSystemLabel']['text'] = f"'{currentSystemFlying.StarSystem}': {currentSystemFlying.Merits} merits gained"
            self.widgets['systemPowerLabel']['text'] = f"{currentSystemFlying.getSystemStateText()} ({powerprogress_percent}) by {power}"
            
            # Handle power cycle information
            systemPowerStatusText = ""
            if not currentSystemFlying.PowerplayConflictProgress:
                cycle_status = currentSystemFlying.getPowerPlayCycleNetStatusText()
                if cycle_status:
                    systemPowerStatusText = f"Powerplaycycle {cycle_status}"
            
            self.widgets['systemPowerStatusLabel']['text'] = systemPowerStatusText
            
        except KeyError as e:
            logger.debug(f"KeyError for current system '{currentSystemFlying}': {e}")
        
        self.widgets['currentSystemLabel'].grid()

    def create_tracker_frame(self, reset, auto_update):
        stateButton = tk.NORMAL if len(systems) > 0 else tk.DISABLED
        
        # Create main frame
        self.frame = tk.Frame(self.parent, name="eliteMeritTrackerComponentframe")
        
        # Create row frames
        for i in range(1, 8):
            frame_name = f"frame_row{i}"
            self.frames[frame_name] = tk.Frame(self.frame, name=f"eliteMeritTrackerComponentframe_row{i}")
            sticky = "we" if i == 6 else "w"
            pady = 2 if i == 6 else 0
            self.frames[frame_name].grid(row=i-1, column=0, columnspan=3, sticky=sticky, padx=0, pady=pady)

        # Create labels
        self.widgets['power'] = tk.Label(
            self.frames['frame_row1'],
            text=f"Pledged: {pledgedPower.Power} - Rank: {pledgedPower.Rank}",
            anchor="w", justify="left", name="eliteMeritTrackerComponentpower"
        )
        self.widgets['powerMerits'] = tk.Label(
            self.frames['frame_row2'],
            text=f"Merits session: {pledgedPower.MeritsSession:,} - Total: {pledgedPower.Merits:,}",
            anchor="w", justify="left", name="eliteMeritTrackerComponentpowerMerits"
        )
        self.widgets['currentSystemLabel'] = tk.Label(
            self.frames['frame_row3'], text="Waiting for Events",
            anchor="w", justify="left", name="eliteMeritTrackerComponentcurrentSystemLabel"
        )
        self.widgets['systemPowerLabel'] = tk.Label(
            self.frames['frame_row4'], text="Powerplay Status",
            anchor="w", justify="left", name="eliteMeritTrackerComponentsystemPowerLabel"
        )
        self.widgets['systemPowerStatusLabel'] = tk.Label(
            self.frames['frame_row5'], text="Net progress",
            anchor="w", justify="left", name="eliteMeritTrackerComponentsystemPowerStatusLabel"
        )

        # Load and scale icon
        scale = self.get_scale_factor(self.parent.winfo_toplevel().winfo_screenwidth(), 
                                      self.parent.winfo_toplevel().winfo_screenheight())
        imagedelete = self.load_and_scale_image(f"{self.assetspath}/delete.png", scale)
        self.icondelete = ImageTk.PhotoImage(imagedelete)

        # Grid all labels
        for widget in ['systemPowerLabel', 'systemPowerStatusLabel', 'currentSystemLabel']:
            self.widgets[widget].grid(row=0, column=0, sticky='w', padx=0, pady=0)
        for widget in ['power', 'powerMerits']:
            self.widgets[widget].grid(row=0, column=0, columnspan=3, sticky='w', padx=0, pady=0)

        # Create buttons
        self.widgets['resetButton'] = tk.Button(
            self.frames['frame_row6'], image=self.icondelete, command=reset,
            state=stateButton, name="eliteMeritTrackerComponentresetButton"
        )
        self.widgets['resetButton'].pack(side="right", padx=0, pady=2)

        # Update button (if needed)
        if self.newest == 1:
            self.widgets['updateButton'] = tk.Button(
                self.frames['frame_row6'], text="Update Available", command=auto_update,
                fg="red", font=("Arial", 10, "bold"), state=tk.NORMAL,
                compound="right", name="eliteMeritTrackerComponentupdateButton"
            )
            self.widgets['updateButton'].pack(side="left", padx=0, pady=2)

        # Show button
        self.widgets['showButton'] = tk.Button(
            self.frames['frame_row6'], text="Overview",
            command=lambda: show_power_info(self.parent, pledgedPower, systems, self),
            state=stateButton, compound="center", name="eliteMeritTrackerComponentshowButton"
        )
        self.widgets['showButton'].pack(side="left", expand=True, fill="both", padx=0, pady=2)
    
    def updateButtonText(self):
        if 'updateButton' in self.widgets:
            self.widgets['updateButton'].config(text="Please Restart EDMC")
            self.update_display(self.this.currentSystemFlying)

    def destroy_tracker_frame(self):
        # Destroy all widgets
        for widget in self.widgets.values():
            if widget is not None:
                if hasattr(widget, 'config'):
                    widget.config(command=None)
                if hasattr(widget, 'pack_forget'):
                    widget.pack_forget()
                widget.destroy()
        self.widgets.clear()
        
        # Clean up icon
        if self.icondelete is not None:
            del self.icondelete
            self.icondelete = None
            
        # Destroy frames
        for frame in self.frames.values():
            if frame is not None:
                frame.destroy()
        self.frames.clear()
        
        # Destroy main frame and parent
        if self.frame is not None:
            self.frame.destroy()
            self.frame = None
        if self.parent is not None:
            self.parent.destroy()
            self.parent = None
