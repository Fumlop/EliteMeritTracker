# ui/main.py - Main tracker UI

import tkinter as tk
from PIL import Image, ImageTk
from models.power import pledgedPower
from models.system import systems
import os
from config import config
from theme import theme
from core.logging import logger
from ui.details import show_power_info
from core.state import state


def get_theme_colors():
    """Get EDMC theme colors with fallbacks"""
    try:
        return {
            'bg': theme.current.get('background', '#000000'),
            'fg': theme.current.get('foreground', '#ff8c00'),
            'highlight': theme.current.get('highlight', '#ff8c00'),
        }
    except Exception:
        return {'bg': '#000000', 'fg': '#ff8c00', 'highlight': '#ff8c00'}


class TrackerFrame:
    def __init__(self, parent=None, newest=False):
        self.parent = parent
        self.newest = newest
        self.icondelete = None
        self.plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assetspath = os.path.join(self.plugin_dir, "assets")

        # Initialize all frame and widget references
        self.frame = None
        self.frames = {}  # Store all row frames
        self.widgets = {}  # Store all widgets
    
    def get_scale_factor(self, current_width: int, current_height: int, base_width: int = 2560, base_height: int = 1440) -> float:
        scale_x = current_width / base_width
        scale_y = current_height / base_height
        return min(scale_x, scale_y)

    def _get_dim_color(self, hex_color):
        """Get a dimmer version of the color (50% towards background)"""
        try:
            colors = get_theme_colors()
            bg = colors['bg'].lstrip('#')
            fg = hex_color.lstrip('#')
            # Parse colors
            bg_r, bg_g, bg_b = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
            fg_r, fg_g, fg_b = int(fg[0:2], 16), int(fg[2:4], 16), int(fg[4:6], 16)
            # Blend 50% towards background
            r = int(fg_r * 0.5 + bg_r * 0.5)
            g = int(fg_g * 0.5 + bg_g * 0.5)
            b = int(fg_b * 0.5 + bg_b * 0.5)
            return f'#{r:02x}{g:02x}{b:02x}'
        except Exception:
            return '#888888'

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

        colors = get_theme_colors()

        # Update power information with split labels
        self.widgets['powerValue']['text'] = f"{pledgedPower.Power}"
        self.widgets['rankValue']['text'] = f"{pledgedPower.Rank}"
        self.widgets['sessionValue']['text'] = f"{pledgedPower.MeritsSession:,}"
        self.widgets['totalValue']['text'] = f"{pledgedPower.Merits:,}"

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

            # System name with merits - highlight merits if > 0
            merits = currentSystemFlying.Merits
            if merits > 0:
                self.widgets['currentSystemLabel']['text'] = f"'{currentSystemFlying.StarSystem}'"
                self.widgets['meritsGainedLabel']['text'] = f"+{merits:,} merits"
                self.widgets['meritsGainedLabel']['fg'] = '#00ff00'  # Green for positive
            else:
                self.widgets['currentSystemLabel']['text'] = f"'{currentSystemFlying.StarSystem}'"
                self.widgets['meritsGainedLabel']['text'] = "0 merits"
                self.widgets['meritsGainedLabel']['fg'] = colors['fg']

            # System state with progress - colored state word
            state_text = currentSystemFlying.getSystemStateText()

            # State text - use theme color for all states
            self.widgets['stateWord']['text'] = f"{state_text}"
            self.widgets['stateDetails']['text'] = f" ({powerprogress_percent}) by {power}"

            # Handle power cycle information with color coding
            if not currentSystemFlying.PowerplayConflictProgress:
                cycle_status = currentSystemFlying.getPowerPlayCycleNetStatusText()
                if cycle_status:
                    # Parse the NET value to determine color
                    try:
                        # Extract percentage from text like "NET -52.02%"
                        net_str = cycle_status.replace("NET", "").replace("%", "").strip()
                        net_value = float(net_str)
                        if net_value > 0:
                            net_color = '#00ff00'  # Green for positive
                            arrow = chr(0x25B2)  # Up arrow
                        elif net_value < 0:
                            net_color = '#ff4444'  # Red for negative
                            arrow = chr(0x25BC)  # Down arrow
                        else:
                            net_color = colors['fg']
                            arrow = ""
                        self.widgets['netLabel']['text'] = f"Cycle NET {net_value:+.2f}% {arrow}"
                        self.widgets['netLabel']['fg'] = net_color
                    except (ValueError, IndexError):
                        self.widgets['netLabel']['text'] = f"Cycle {cycle_status}"
                        self.widgets['netLabel']['fg'] = colors['fg']
                else:
                    self.widgets['netLabel']['text'] = ""
            else:
                self.widgets['netLabel']['text'] = "Conflict in progress"
                self.widgets['netLabel']['fg'] = '#ffaa00'  # Orange for conflict

        except KeyError as e:
            logger.debug(f"KeyError for current system '{currentSystemFlying}': {e}")

        self.widgets['currentSystemLabel'].grid()

    def create_tracker_frame(self, reset, auto_update):
        stateButton = tk.NORMAL if len(systems) > 0 else tk.DISABLED
        colors = get_theme_colors()

        # Dim color for labels (50% opacity effect)
        dim_color = self._get_dim_color(colors['fg'])

        # Create main frame
        self.frame = tk.Frame(self.parent, name="eliteMeritTrackerComponentframe")

        # Create row frames
        for i in range(1, 8):
            frame_name = f"frame_row{i}"
            self.frames[frame_name] = tk.Frame(self.frame, name=f"eliteMeritTrackerComponentframe_row{i}")
            sticky = "we" if i == 6 else "w"
            pady = 2 if i == 6 else 0
            self.frames[frame_name].grid(row=i-1, column=0, columnspan=3, sticky=sticky, padx=0, pady=pady)

        # Row 1: "Pledged:" (dim) + Power name (bright) + "Rank:" (dim) + rank value (bright)
        self.widgets['pledgedLabel'] = tk.Label(
            self.frames['frame_row1'], text="Pledged:", fg=dim_color,
            anchor="w", justify="left", name="eliteMeritTrackerComponentpledgedLabel"
        )
        self.widgets['powerValue'] = tk.Label(
            self.frames['frame_row1'], text=f"{pledgedPower.Power}", fg=colors['fg'],
            anchor="w", justify="left", name="eliteMeritTrackerComponentpowerValue"
        )
        self.widgets['rankLabel'] = tk.Label(
            self.frames['frame_row1'], text="Rank:", fg=dim_color,
            anchor="w", justify="left", name="eliteMeritTrackerComponentrankLabel"
        )
        self.widgets['rankValue'] = tk.Label(
            self.frames['frame_row1'], text=f"{pledgedPower.Rank}", fg=colors['fg'],
            anchor="w", justify="left", name="eliteMeritTrackerComponentrankValue"
        )
        # Keep original for compatibility
        self.widgets['power'] = tk.Label(
            self.frames['frame_row1'], text="", anchor="w", justify="left",
            name="eliteMeritTrackerComponentpower"
        )

        # Row 2: "Session:" (dim) + value (bright) + "Total:" (dim) + value (highlight)
        self.widgets['sessionLabel'] = tk.Label(
            self.frames['frame_row2'], text="Session:", fg=dim_color,
            anchor="w", justify="left", name="eliteMeritTrackerComponentsessionLabel"
        )
        self.widgets['sessionValue'] = tk.Label(
            self.frames['frame_row2'], text=f"{pledgedPower.MeritsSession:,}", fg=colors['fg'],
            anchor="w", justify="left", name="eliteMeritTrackerComponentsessionValue"
        )
        self.widgets['totalLabel'] = tk.Label(
            self.frames['frame_row2'], text="Total:", fg=dim_color,
            anchor="w", justify="left", name="eliteMeritTrackerComponenttotalLabel"
        )
        self.widgets['totalValue'] = tk.Label(
            self.frames['frame_row2'], text=f"{pledgedPower.Merits:,}", fg=colors['fg'],
            anchor="w", justify="left", name="eliteMeritTrackerComponenttotalValue"
        )
        # Keep original for compatibility
        self.widgets['powerMerits'] = tk.Label(
            self.frames['frame_row2'], text="", anchor="w", justify="left",
            name="eliteMeritTrackerComponentpowerMerits"
        )

        # Row 3: System name + merits gained (side by side)
        self.widgets['currentSystemLabel'] = tk.Label(
            self.frames['frame_row3'], text="Waiting for Events",
            anchor="w", justify="left", name="eliteMeritTrackerComponentcurrentSystemLabel"
        )
        self.widgets['meritsGainedLabel'] = tk.Label(
            self.frames['frame_row3'], text="",
            anchor="w", justify="left", name="eliteMeritTrackerComponentmeritsGainedLabel"
        )

        # Row 4: System state (Stronghold, etc.) - split for colored state word
        self.widgets['stateWord'] = tk.Label(
            self.frames['frame_row4'], text="Powerplay",
            anchor="w", justify="left", name="eliteMeritTrackerComponentstateWord"
        )
        self.widgets['stateDetails'] = tk.Label(
            self.frames['frame_row4'], text="Status",
            anchor="w", justify="left", name="eliteMeritTrackerComponentstateDetails"
        )
        # Keep original for compatibility
        self.widgets['systemPowerLabel'] = tk.Label(
            self.frames['frame_row4'], text="",
            anchor="w", justify="left", name="eliteMeritTrackerComponentsystemPowerLabel"
        )

        # Row 5: NET progress with color coding
        self.widgets['netLabel'] = tk.Label(
            self.frames['frame_row5'], text="",
            anchor="w", justify="left", name="eliteMeritTrackerComponentnetLabel"
        )

        # Keep old label for compatibility but hide it
        self.widgets['systemPowerStatusLabel'] = tk.Label(
            self.frames['frame_row5'], text="",
            anchor="w", justify="left", name="eliteMeritTrackerComponentsystemPowerStatusLabel"
        )

        # Load and scale icon
        scale = self.get_scale_factor(self.parent.winfo_toplevel().winfo_screenwidth(),
                                      self.parent.winfo_toplevel().winfo_screenheight())
        imagedelete = self.load_and_scale_image(f"{self.assetspath}/delete.png", scale)
        self.icondelete = ImageTk.PhotoImage(imagedelete)

        # Grid Row 1: Pledged + Power + Rank
        self.widgets['pledgedLabel'].grid(row=0, column=0, sticky='w', padx=0, pady=0)
        self.widgets['powerValue'].grid(row=0, column=1, sticky='w', padx=(2, 8), pady=0)
        self.widgets['rankLabel'].grid(row=0, column=2, sticky='w', padx=0, pady=0)
        self.widgets['rankValue'].grid(row=0, column=3, sticky='w', padx=(2, 0), pady=0)

        # Grid Row 2: Session + Total
        self.widgets['sessionLabel'].grid(row=0, column=0, sticky='w', padx=0, pady=0)
        self.widgets['sessionValue'].grid(row=0, column=1, sticky='w', padx=(2, 8), pady=0)
        self.widgets['totalLabel'].grid(row=0, column=2, sticky='w', padx=0, pady=0)
        self.widgets['totalValue'].grid(row=0, column=3, sticky='w', padx=(2, 0), pady=0)

        # Grid Row 3-5
        self.widgets['currentSystemLabel'].grid(row=0, column=0, sticky='w', padx=0, pady=0)
        self.widgets['meritsGainedLabel'].grid(row=0, column=1, sticky='w', padx=(5, 0), pady=0)
        self.widgets['stateWord'].grid(row=0, column=0, sticky='w', padx=0, pady=0)
        self.widgets['stateDetails'].grid(row=0, column=1, sticky='w', padx=0, pady=0)
        self.widgets['netLabel'].grid(row=0, column=0, sticky='w', padx=0, pady=0)

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
            self.update_display(state.current_system)

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
