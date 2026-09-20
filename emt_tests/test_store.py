"""
Tests for the SQLite cutover: the four models saving and loading through
emt_core/database.py instead of data/*.json.
"""
import pytest

from emt_core import database
from emt_core.state import state
from emt_models.backpack import playerBackpack, save_backpack, load_backpack
from emt_models.power import pledgedPower
from emt_models.salvage import Salvage, salvageInventory, save_salvage, load_salvage
from emt_models.system import StarSystem, systems, dumpSystems, loadSystems


@pytest.fixture(autouse=True)
def clean_models():
    """Empty models and no commander, restored afterwards."""
    saved = (dict(systems), dict(salvageInventory), state.commander,
             {kind: dict(bag.items) for kind, bag in _bags()})
    systems.clear()
    salvageInventory.clear()
    for _kind, bag in _bags():
        bag.items.clear()
    state.commander = ""

    yield

    systems.clear()
    systems.update(saved[0])
    salvageInventory.clear()
    salvageInventory.update(saved[1])
    state.commander = saved[2]
    for kind, bag in _bags():
        bag.items.clear()
        bag.items.update(saved[3][kind])


def _bags():
    return (("umbag", playerBackpack.umbag),
            ("reinfbag", playerBackpack.reinfbag),
            ("acqbag", playerBackpack.acqbag))


def add_system(name, merits=100, power="Felicia Winters"):
    system = StarSystem({"event": "FSDJump", "StarSystem": name,
                         "PowerplayState": "Fortified",
                         "ControllingPower": power,
                         "Powers": [power]}, "cmdr")
    system.Merits = merits
    systems[name] = system
    return system


class TestCommander:
    def test_the_live_journal_name_wins(self):
        state.commander = "Fumlop"
        database.remember_commander("Someone Else")
        assert database.commander() == "Fumlop"

    def test_falls_back_to_the_stored_name(self):
        state.commander = ""
        database.remember_commander("Fumlop")
        assert database.commander() == "Fumlop"

    def test_empty_when_nothing_is_known(self):
        assert database.commander() == ""

    def test_remembering_nothing_stores_nothing(self):
        database.remember_commander("")
        assert database.load_meta("commander") is None


class TestSystems:
    def test_round_trip(self):
        add_system("Eme", merits=293529)
        dumpSystems()
        systems.clear()
        loadSystems()
        assert systems["Eme"].Merits == 293529

    def test_saving_remembers_the_commander(self):
        state.commander = "Fumlop"
        add_system("Eme")
        dumpSystems()
        assert database.load_meta("commander") == "Fumlop"

    def test_two_commanders_do_not_see_each_other(self):
        state.commander = "First"
        add_system("Eme", merits=10)
        dumpSystems()

        systems.clear()
        state.commander = "Second"
        add_system("Eme", merits=20)
        dumpSystems()

        systems.clear()
        state.commander = "First"
        loadSystems()
        assert systems["Eme"].Merits == 10

        systems.clear()
        state.commander = "Second"
        loadSystems()
        assert systems["Eme"].Merits == 20

    def test_a_second_save_replaces_rather_than_duplicates(self):
        system = add_system("Eme", merits=10)
        dumpSystems()
        system.Merits = 20
        dumpSystems()
        systems.clear()
        loadSystems()
        assert len(systems) == 1
        assert systems["Eme"].Merits == 20

    def test_loading_does_not_clear_what_is_already_there(self):
        # loadSystems merges, as it always has: plugin_start3 calls it into an
        # empty dict, and nothing else calls it.
        add_system("Eme")
        dumpSystems()
        systems.clear()
        add_system("Kaushpoos")
        loadSystems()
        assert sorted(systems) == ["Eme", "Kaushpoos"]


class TestBackpack:
    def test_round_trip_of_all_three_bags(self):
        playerBackpack.umbag.items["powerresearch"] = {"Eme": 4, "Cerno": 2}
        playerBackpack.acqbag.items["powermedical"] = {"Eme": 7}
        save_backpack()

        for _kind, bag in _bags():
            bag.items.clear()
        load_backpack()

        assert playerBackpack.umbag.items["powerresearch"] == {"Eme": 4, "Cerno": 2}
        assert playerBackpack.acqbag.items["powermedical"] == {"Eme": 7}
        assert playerBackpack.reinfbag.items == {}

    def test_a_removed_item_does_not_come_back(self):
        playerBackpack.umbag.items["powerresearch"] = {"Eme": 4}
        save_backpack()
        del playerBackpack.umbag.items["powerresearch"]
        save_backpack()
        load_backpack()
        assert playerBackpack.umbag.items == {}

    def test_a_zero_count_is_not_stored(self):
        playerBackpack.umbag.items["powerresearch"] = {"Eme": 0, "Cerno": 3}
        save_backpack()
        load_backpack()
        assert playerBackpack.umbag.items["powerresearch"] == {"Cerno": 3}

    def test_the_bags_stay_apart(self):
        playerBackpack.umbag.items["same"] = {"Eme": 1}
        playerBackpack.reinfbag.items["same"] = {"Eme": 2}
        save_backpack()
        load_backpack()
        assert playerBackpack.umbag.items["same"] == {"Eme": 1}
        assert playerBackpack.reinfbag.items["same"] == {"Eme": 2}


class TestSalvage:
    def test_round_trip(self):
        salvage = Salvage("Psi-5 Aurigae")
        salvage.add_cargo("wreckagecomponents", 11)
        salvage.add_cargo("usscargoblackbox", 5)
        salvageInventory["Psi-5 Aurigae"] = salvage
        save_salvage()

        salvageInventory.clear()
        load_salvage()

        loaded = salvageInventory["Psi-5 Aurigae"]
        assert loaded.inventory["wreckagecomponents"].count == 11
        assert loaded.inventory["usscargoblackbox"].count == 5

    def test_loading_replaces_what_is_in_memory(self):
        salvageInventory["Stale"] = Salvage("Stale")
        load_salvage()
        assert "Stale" not in salvageInventory

    def test_several_systems(self):
        for name, count in (("Psi-5 Aurigae", 11), ("Cerno", 1)):
            salvage = Salvage(name)
            salvage.add_cargo("wreckagecomponents", count)
            salvageInventory[name] = salvage
        save_salvage()
        salvageInventory.clear()
        load_salvage()
        assert sorted(salvageInventory) == ["Cerno", "Psi-5 Aurigae"]


class TestPower:
    def test_round_trip(self):
        pledgedPower.Power = "Felicia Winters"
        pledgedPower.Commander = "Fumlop"
        pledgedPower.Merits = 9044583
        pledgedPower.Rank = "1133"
        pledgedPower.TimePledged = 59525785
        pledgedPower.dumpJson()

        pledgedPower.from_dict({})
        pledgedPower.loadPower()

        assert pledgedPower.Power == "Felicia Winters"
        assert pledgedPower.Merits == 9044583
        assert pledgedPower.Commander == "Fumlop"

    def test_saving_remembers_the_commander(self):
        pledgedPower.Commander = "Fumlop"
        pledgedPower.dumpJson()
        assert database.load_meta("commander") == "Fumlop"


class TestFailureIsEmptyNotFatal:
    def test_reads_answer_empty_when_the_file_is_not_a_database(self, tmp_path):
        broken = tmp_path / "broken.db"
        broken.write_bytes(b"not a database at all, not even close")
        assert database.load_systems("", str(broken)) == []
        assert database.load_inventory("umbag", "", str(broken)) == []
        assert database.load_meta("power", "fallback", str(broken)) == "fallback"

    def test_a_write_to_a_broken_file_returns_false(self, tmp_path):
        broken = tmp_path / "broken.db"
        broken.write_bytes(b"not a database at all, not even close")
        assert database.save_systems([], str(broken)) is False
        assert database.save_inventory("umbag", "", [], str(broken)) is False
        assert database.save_meta("power", {}, str(broken)) is False
