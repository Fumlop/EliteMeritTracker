import tkinter as tk
import myNotebook as nb
from pluginConfig import configPlugin
from log import logger, plugin_name

def create_config_frame(parent, nb):
    config_frame = nb.Frame(parent)
    config_frame.columnconfigure(1, weight=1)
    config_frame.grid(sticky=tk.EW)

    row = 0
    def next_config_row():
        nonlocal row
        row += 1
        return row

    nb.Label(
        config_frame,
        text="Copy paste text value - Text must contain @MeritsValue and @System for replacement"
    ).grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=5)

    nb.Label(
        config_frame,
        text="@MeritsValue, @System, @CPOpposition, @CPControlling"
    ).grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=5)
    logger.warning(f"config {configPlugin.copyText}")
    nb.Entry(
        config_frame,
        textvariable=configPlugin.copyText,
        width=50
    ).grid(row=next_config_row(), column=0, padx=5, pady=5, sticky="we")

    nb.Label(config_frame, text="").grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=5)

    nb.Label(config_frame, text="Discord webhook URL").grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=5)

    nb.Entry(
        config_frame,
        textvariable=configPlugin.discordHook,
        width=50
    ).grid(row=next_config_row(), column=0, padx=5, pady=5, sticky="we")

    nb.Checkbutton(
        config_frame,
        text="Report merits from source system to Discord on FSDJump",
        variable=configPlugin.reportOnFSDJump
    ).grid(row=next_config_row(), columnspan=2, sticky=tk.W)

    nb.Label(config_frame, text="").grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=5)

    nb.Label(
        config_frame,
        text=f"Version {configPlugin.version}"
    ).grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=5)

    return config_frame
