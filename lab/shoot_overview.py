r"""Render the real Overview window and save a PNG of each tab.

Not a test and not shipped: it exists to keep docs\pic\*.png honest, drawn by
the same emt_ui/details.py the plugin runs rather than by a mockup.

EDMC's own modules are stubbed - config, theme, myNotebook, EDMCLogging,
ttkHyperlinkLabel - but tkinter is the real one, so the widgets are real. With
no theme module to read, palette falls back to EDMC's dark scheme.

    python lab/shoot_overview.py

Needs a desktop session: it opens a window, grabs it, and closes it.
"""
import os
import sys
import types
from unittest.mock import MagicMock

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLUGIN_DIR)

OUT_DIR = os.path.join(PLUGIN_DIR, "docs", "pic")
SHOTS = (("Session", "overview-session.png"),
         ("Systems", "overview-systems.png"),
         ("Shiplocker", "overview-shiplocker.png"))

# The window is drawn at a fixed size here rather than at the screen share, so
# the pictures come out the same on any machine.
WIDTH, HEIGHT = 1280, 800


def stub_edmc():
    """Everything the plugin imports from EDMC, minus tkinter."""
    class Config:
        def get_str(self, key, default=""):
            return default

        def get_int(self, key, default=0):
            return default

        def get_bool(self, key, default=False):
            return default

        def get_list(self, key, default=None):
            return default if default is not None else []

        def set(self, key, value):
            pass

    config_module = types.ModuleType("config")
    config_module.config = Config()
    config_module.appname = "EDMarketConnector"
    sys.modules["config"] = config_module
    sys.modules["EDMCLogging"] = MagicMock()
    sys.modules["myNotebook"] = MagicMock()
    sys.modules["ttkHyperlinkLabel"] = MagicMock()
    # No theme module at all: emt_ui.palette then uses its FALLBACK, which is
    # EDMC's dark scheme. A MagicMock here would hand back mock colour strings.


# Made-up data, never the commander's own: these pictures go in the README.
# The six systems are chosen to land one on each tag colour - danger, safe,
# warning, neutral - so the screenshots show the whole palette.
EXAMPLE_SYSTEMS = [
    # name, state, power, control progress 0-1, merits, reinforcement, undermining
    ("Sol", "Fortified", "Felicia Winters", 0.6407, 12480, 132832, 24958),
    ("Alioth", "Stronghold", "Felicia Winters", 0.9140, 8105, 94300, 1200),
    ("LHS 3447", "Fortified", "Zemina Torval", 0.8720, 1905, 41800, 30400),
    ("Beta Hydri", "Exploited", "Felicia Winters", 0.1260, 3240, 7600, 900),
    ("Kaushpoos", "Exploited", "Nakato Kaine", 0.4500, 520, 18200, 2100),
    ("Hyades Sector DB-X d1-112", "Unoccupied", None, 0.0, 640, 0, 0),
]

EXAMPLE_POWER = {
    "Power": "Felicia Winters",
    "Commander": "CMDR Example",
    "Merits": 1234567,
    "MeritsSession": 640,
    "Rank": "42",
    "TimePledged": 24192000,
}

EXAMPLE_SALVAGE = {
    "Beta Hydri": {"wreckagecomponents": 14, "usscargoblackbox": 6},
    "Kaushpoos": {"powerresearch": 3},
}

# Real data-item ids from emt_ppdata, so the Item column shows the display
# name rather than the raw key.
EXAMPLE_BACKPACK = {
    "umbag": {"powerclassifieddata": {"LHS 3447": 12},
              "powerfinancialrecords": {"LHS 3447": 5}},
    "reinfbag": {"poweremployeedata": {"Sol": 22},
                 "powerpropagandadata": {"Alioth": 8}},
    "acqbag": {"powerclassifieddata": {"Hyades Sector DB-X d1-112": 9}},
}


def load_example_data():
    """Fill the models with EXAMPLE_* above. Nothing is read from data/."""
    from emt_models.backpack import playerBackpack
    from emt_models.power import pledgedPower
    from emt_models.salvage import Salvage, salvageInventory
    from emt_models.system import StarSystem, systems

    all_powers = ["Felicia Winters", "Zemina Torval", "Nakato Kaine", "Jerome Archer"]

    for name, state, power, progress, merits, reinf, um in EXAMPLE_SYSTEMS:
        entry = {
            "StarSystem": name,
            "Merits": merits,
            "PowerplayState": state,
            "PowerplayStateControlProgress": progress,
            "PowerplayStateReinforcement": reinf,
            "PowerplayStateUndermining": um,
            "Powers": all_powers[:3] if power else [],
        }
        if power:
            entry["ControllingPower"] = power
            # from_dict takes Opposition from the entry, not from Powers, so it
            # has to be spelled out or the column comes out empty.
            entry["Opposition"] = [other for other in all_powers[:3] if other != power]
        system = StarSystem()
        system.from_dict(entry)
        systems[name] = system

    pledgedPower.from_dict(EXAMPLE_POWER)

    for name, items in EXAMPLE_SALVAGE.items():
        salvage = Salvage(name)
        for item, count in items.items():
            salvage.add_cargo(item, count)
        salvageInventory[name] = salvage

    for kind, items in EXAMPLE_BACKPACK.items():
        getattr(playerBackpack, kind).items.update(items)

    print(f"  example data: {len(systems)} systems, "
          f"{len(salvageInventory)} salvage systems, {pledgedPower.Power}")


def shoot(window, path):
    """Grab the window's own rectangle and write it to `path`."""
    from PIL import ImageGrab

    window.update_idletasks()
    window.update()
    x, y = window.winfo_rootx(), window.winfo_rooty()
    box = (x, y, x + window.winfo_width(), y + window.winfo_height())
    ImageGrab.grab(bbox=box).save(path)
    print(f"  {os.path.relpath(path, PLUGIN_DIR)}  {box[2] - box[0]}x{box[3] - box[1]}")


def make_dpi_aware():
    """Tk reports logical pixels and ImageGrab works in physical ones. On a
    scaled display (125 % here) the grab box lands off the window unless the
    process is per-monitor DPI aware, which makes the two agree."""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        pass


def main():
    stub_edmc()
    make_dpi_aware()
    import tkinter as tk

    # The root comes first: emt_core.config builds a tk.StringVar at import
    # time, and a Variable with no default root raises.
    root = tk.Tk()
    root.withdraw()

    from emt_ui import details

    load_example_data()
    os.makedirs(OUT_DIR, exist_ok=True)

    window = details.show_power_info(root)
    window.geometry(f"{WIDTH}x{HEIGHT}+60+60")
    window.attributes("-topmost", True)
    window.update_idletasks()
    window.update()

    for tab, filename in SHOTS:
        details._state["tab"] = tab
        if tab == "Systems":
            # One row open, so the picture shows what a fold looks like. Sol,
            # because it is the one with reinforcement, decay and opposition on
            # it - an empty system shows an empty fold.
            details._state["folded_open"] = {"Sol"}
        details._draw()
        window.update()
        shoot(window, os.path.join(OUT_DIR, filename))

    window.destroy()
    root.destroy()


if __name__ == "__main__":
    main()
