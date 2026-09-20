"""
Tests for following the commander: rows saved before the pilot is named, and
two commanders sharing one install.

plugin_start3 reads the models before EDMC replays a single journal line, so
they are always read under '' or under whoever saved last. load._follow_commander
is what puts that right when LoadGame finally names the pilot.
"""
import pytest

import load
from emt_core import database
from emt_core.state import state
from emt_models.backpack import playerBackpack, save_backpack
from emt_models.salvage import Salvage, salvageInventory, save_salvage
from emt_models.system import StarSystem, systems, dumpSystems, loadSystems


@pytest.fixture(autouse=True)
def clean():
    saved = (dict(systems), dict(salvageInventory), state.commander,
             state.current_system, database.loaded_commander())
    systems.clear()
    salvageInventory.clear()
    for bag in (playerBackpack.umbag, playerBackpack.reinfbag, playerBackpack.acqbag):
        bag.items.clear()
    state.commander = ""
    state.current_system = None
    database.mark_loaded(None)

    yield

    systems.clear()
    systems.update(saved[0])
    salvageInventory.clear()
    salvageInventory.update(saved[1])
    state.commander, state.current_system = saved[2], saved[3]
    database.mark_loaded(saved[4])


def add_system(name, merits=100):
    system = StarSystem({"event": "FSDJump", "StarSystem": name,
                         "PowerplayState": "Fortified",
                         "ControllingPower": "Felicia Winters",
                         "Powers": ["Felicia Winters"]}, "cmdr")
    system.Merits = merits
    systems[name] = system
    return system


def save_everything_as(commander):
    state.commander = commander
    dumpSystems()
    save_backpack()
    save_salvage()


class TestAdopt:
    def test_moves_unowned_rows_to_the_name(self):
        add_system("Eme", merits=293529)
        playerBackpack.umbag.items["powerclassifieddata"] = {"Eme": 4}
        save_everything_as("")

        assert database.adopt("Fumlop") is True
        assert database.load_systems("Fumlop")[0]["Merits"] == 293529
        assert database.load_inventory("umbag", "Fumlop") == [("powerclassifieddata", "Eme", 4)]
        assert database.load_systems("") == []

    def test_pins_the_name_for_the_next_start(self):
        add_system("Eme")
        save_everything_as("")
        database.adopt("Fumlop")
        assert database.load_meta("commander") == "Fumlop"

    def test_a_commander_who_already_owns_rows_takes_nothing(self):
        # Written straight through database, because commander() falls back to
        # meta['commander'] - once a name is stored you cannot make '' rows
        # through dumpSystems() any more.
        theirs = add_system("Theirs")
        database.save_systems([database.system_row(theirs, "Fumlop")], "Fumlop")
        systems.clear()
        unowned = add_system("Unowned")
        database.save_systems([database.system_row(unowned, "")], "")

        assert database.adopt("Fumlop") is False
        assert [row["StarSystem"] for row in database.load_systems("Fumlop")] == ["Theirs"]
        assert [row["StarSystem"] for row in database.load_systems("")] == ["Unowned"]

    def test_an_empty_name_adopts_nothing(self):
        add_system("Eme")
        save_everything_as("")
        assert database.adopt("") is False
        assert database.load_systems("") != []

    def test_nothing_to_adopt_is_not_an_error(self):
        assert database.adopt("Fumlop") is False


class TestFollowCommander:
    def test_the_first_start_after_the_import_keeps_the_merits(self):
        """Rows land under '' when power.json has no Commander. LoadGame then
        names the pilot, and the merits must not vanish."""
        add_system("Eme", merits=293529)
        save_everything_as("")

        # plugin_start3: nothing named yet.
        systems.clear()
        state.commander = ""
        loadSystems()
        assert systems["Eme"].Merits == 293529

        # LoadGame arrives.
        state.commander = "Fumlop"
        load._follow_commander()

        assert systems["Eme"].Merits == 293529
        assert database.loaded_commander() == "Fumlop"
        # And it survives the next save and restart.
        dumpSystems()
        systems.clear()
        loadSystems()
        assert systems["Eme"].Merits == 293529

    def test_a_second_commander_does_not_inherit_the_first(self):
        add_system("Eme", merits=293529)
        save_everything_as("")
        state.commander = "First"
        load._follow_commander()
        dumpSystems()

        # Second pilot, same install. plugin_start3 reads First's rows.
        systems.clear()
        state.commander = ""
        loadSystems()
        assert "Eme" in systems

        state.commander = "Second"
        load._follow_commander()
        assert systems == {}, "Second must not hold First's systems"

        add_system("Kaushpoos", merits=10)
        dumpSystems()

        # First's merits are untouched.
        systems.clear()
        state.commander = "First"
        loadSystems()
        assert systems["Eme"].Merits == 293529
        assert "Kaushpoos" not in systems

    def test_the_same_commander_does_not_reload(self):
        add_system("Eme", merits=10)
        save_everything_as("Fumlop")
        systems.clear()
        loadSystems()

        systems["Eme"].Merits = 999          # unsaved, in memory only
        state.commander = "Fumlop"
        load._follow_commander()
        assert systems["Eme"].Merits == 999, "a needless reload threw away live merits"

    def test_the_current_system_is_re_pointed_after_a_reload(self):
        add_system("Eme")
        save_everything_as("")
        systems.clear()
        loadSystems()
        state.current_system = systems["Eme"]

        state.commander = "Fumlop"
        load._follow_commander()

        # The old object was dropped by systems.clear(); a stale one makes
        # updateSystemTracker raise on the next journal line.
        assert state.current_system is systems["Eme"]

    def test_a_reload_that_finds_nothing_clears_the_current_system(self):
        add_system("Eme")
        save_everything_as("First")
        systems.clear()
        loadSystems()
        state.current_system = systems.get("Eme")

        state.commander = "Second"
        load._follow_commander()
        assert state.current_system is None

    def test_the_shiplocker_follows_too(self):
        playerBackpack.umbag.items["powerclassifieddata"] = {"Eme": 4}
        salvage = Salvage("Cerno")
        salvage.add_cargo("wreckagecomponents", 3)
        salvageInventory["Cerno"] = salvage
        save_everything_as("")

        state.commander = "Fumlop"
        load._follow_commander()

        assert playerBackpack.umbag.items == {"powerclassifieddata": {"Eme": 4}}
        assert salvageInventory["Cerno"].inventory["wreckagecomponents"].count == 3
