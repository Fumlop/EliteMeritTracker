# trackerUI.py

import tkinter as tk
from PIL import Image, ImageTk
from power import pledgedPower
from system import systems
from power_info_window import show_power_info

def create_tracker_frame(parent, this, get_scale_factor, load_and_scale_image, reset, auto_update):
    stateButton = tk.NORMAL if this.debug or len(systems) > 0 else tk.DISABLED
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
    this.frame_row7 = tk.Frame(this.frame)
    this.frame_row7.grid(row=6, column=0, columnspan=3, sticky="w")

    this.power = tk.Label(
        this.frame_row1,
        text=f"Pledged: {pledgedPower.Power} - Rank : {pledgedPower.Rank}".strip(),
        anchor="w", justify="left"
    )
    this.powerMerits = tk.Label(
        this.frame_row2,
        text=f"Merits session: {pledgedPower.MeritsSession:,} - Total: {pledgedPower.Merits:,}".strip(),
        anchor="w", justify="left"
    )
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
    this.power.grid(row=0, column=0, columnspan=3, sticky='w', padx=0, pady=0)
    this.powerMerits.grid(row=0, column=0, columnspan=3, sticky='w', padx=0, pady=0)

    this.resetButton = tk.Button(
        this.frame_row6,
        image=this.frame.icondelete,
        command=reset,
        state=stateButton
    )
    this.resetButton.pack(side="right", padx=0, pady=2)

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
