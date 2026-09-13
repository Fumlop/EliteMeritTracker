"""EDMC names the system on every journal line. The tracker follows it.

Before this, the system came only from FSDJump, Location, CarrierJump and
Docked. Start EDMC with the game already running and the tracker restored
whichever system was Active at the last shutdown - the wrong one, if you
jumped while it was closed - and kept showing it until one of those four
events happened. The plugin's own comment called the fix "jump to another
system or dock to trigger system update".
"""
import sys
from unittest.mock import MagicMock

import pytest

import emt_tests.mocks  # noqa: F401  installs the EDMC/tkinter mocks

sys.modules.setdefault("myNotebook", MagicMock())
sys.modules.setdefault("requests", MagicMock())
import tkinter as _tk
for _name in ("ttk", "filedialog", "messagebox", "font", "simpledialog"):
    setattr(_tk, _name, MagicMock())
    sys.modules.setdefault("tkinter." + _name, getattr(_tk, _name))

import load                                            # noqa: E402
from emt_core import state                             # noqa: E402


@pytest.fixture(autouse=True)
def clean_tracker():
    """Each case starts with no systems and no panel, the way a fresh EDMC
    start does."""
    load.systems.clear()
    state.current_system = None
    frame, load.trackerFrame = load.trackerFrame, None
    yield
    load.systems.clear()
    state.current_system = None
    load.trackerFrame = frame


def test_a_name_is_enough_to_switch():
    load.follow_edmc_system("Andel")
    assert state.current_system is not None
    assert state.current_system.StarSystem == "Andel"


def test_the_system_is_marked_active():
    load.follow_edmc_system("Andel")
    assert load.systems["Andel"].Active


def test_switching_deactivates_the_old_one():
    load.follow_edmc_system("Andel")
    load.follow_edmc_system("Loha")
    assert not load.systems["Andel"].Active
    assert load.systems["Loha"].Active
    assert state.current_system.StarSystem == "Loha"


def test_the_same_name_again_changes_nothing():
    load.follow_edmc_system("Andel")
    first = state.current_system
    load.follow_edmc_system("Andel")
    assert state.current_system is first


@pytest.mark.parametrize("name", [None, "", "Nomansland"])
def test_nothing_useful_is_ignored(name):
    """"Nomansland" is what this plugin already uses for "no idea", so it must
    not become a system anyone can be in."""
    load.follow_edmc_system(name)
    assert state.current_system is None
    assert not load.systems


def test_a_known_system_keeps_its_data():
    """A name carries no PowerPlay data, so switching to a system that already
    has some must not replace it with a blank one."""
    load.follow_edmc_system("Andel")
    known = load.systems["Andel"]
    known.Merits = 500
    load.follow_edmc_system("Loha")
    load.follow_edmc_system("Andel")
    assert load.systems["Andel"] is known
    assert load.systems["Andel"].Merits == 500


def test_it_survives_having_no_panel_yet():
    """journal_entry fires during the startup replay, which is before
    plugin_app has built anything to update."""
    load.trackerFrame = None
    load.follow_edmc_system("Andel")
    assert state.current_system.StarSystem == "Andel"


def test_the_panel_is_told_when_there_is_one():
    load.trackerFrame = MagicMock()
    load.follow_edmc_system("Andel")
    load.trackerFrame.update_display.assert_called_once()


def test_journal_entry_follows_it_on_any_event():
    """The point of the whole thing: a line that says nothing about where you
    are still carries where you are."""
    load.trackerFrame = MagicMock()
    load.journal_entry("Cmdr", False, "Andel", None,
                       {"event": "Music", "MusicTrack": "DockingComputer"}, {})
    assert state.current_system.StarSystem == "Andel"


def test_the_plugin_exposes_its_version():
    """The EDMC plugin registry reads a VERSION constant or a __version__
    dunder off the plugin, and the plugin is load.py - not the config object
    three imports down where the number lives."""
    from emt_core.config import configPlugin
    assert load.VERSION == configPlugin.version
    assert load.__version__ == configPlugin.version
