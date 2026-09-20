"""
Tests for saving on every event that moves merits, instead of on a timer.

The two things that make this more than "write the current system": a server
correction takes merits off systems other than the one you are in, and the
ledger's baseline and parked awards have to reach disk with them - a crash
that kept the merits but lost the ledger would hand a parked award back twice
or never.
"""
import pytest

import load
from emt_core import database
from emt_core.duplicate import merit_ledger
from emt_core.state import state
from emt_models.system import StarSystem, systems, loadSystems


@pytest.fixture(autouse=True)
def clean():
    saved = (dict(systems), state.commander, state.current_system)
    systems.clear()
    load._dirty.clear()
    merit_ledger.reset()
    state.commander = ""
    state.current_system = None

    yield

    systems.clear()
    systems.update(saved[0])
    state.commander, state.current_system = saved[1], saved[2]
    load._dirty.clear()
    merit_ledger.reset()


def add(name, merits):
    system = StarSystem({"event": "FSDJump", "StarSystem": name,
                         "PowerplayState": "Fortified",
                         "ControllingPower": "Felicia Winters",
                         "Powers": ["Felicia Winters"]}, "cmdr")
    system.Merits = merits
    systems[name] = system
    return system


def on_disk(name):
    """The merits stored for `name`, or None."""
    for entry in database.load_systems(database.commander()):
        if entry["StarSystem"] == name:
            return entry["Merits"]
    return None


class TestOnlyTheChangedRows:
    def test_crediting_a_system_writes_it(self):
        add("Eme", 0)
        load._add_merits_to_system("Eme", 500)
        load._save_now()
        assert on_disk("Eme") == 500

    def test_an_untouched_system_is_not_rewritten(self):
        add("Eme", 100)
        add("Kaushpoos", 200)
        load._touch("Eme", "Kaushpoos")
        load._save_now()

        # Change one in memory without marking it; only the marked one moves.
        systems["Eme"].Merits = 999
        systems["Kaushpoos"].Merits = 888
        load._touch("Kaushpoos")
        load._save_now()

        assert on_disk("Eme") == 100
        assert on_disk("Kaushpoos") == 888

    def test_the_dirty_set_is_emptied(self):
        add("Eme", 1)
        load._touch("Eme")
        load._save_now()
        assert load._dirty == set()

    def test_saving_nothing_is_a_no_op(self):
        load._save_now()          # must not raise on an empty dirty set

    def test_a_system_dropped_from_memory_is_skipped(self):
        load._touch("Ghost")      # never in `systems`
        load._save_now()          # must not raise


class TestCorrectionReachesDisk:
    def test_a_correction_writes_the_systems_it_took_merits_off(self):
        """The correction hits the system that earned them, not the one you
        are standing in."""
        add("Eme", 1000)
        add("Kaushpoos", 0)
        state.current_system = systems["Kaushpoos"]
        merit_ledger.record("Eme", 1000)
        load._touch("Eme", "Kaushpoos")
        load._save_now()
        assert on_disk("Eme") == 1000

        load.apply_merit_correction(400)
        load._save_now()

        assert systems["Eme"].Merits == 600
        assert on_disk("Eme") == 600, "the corrected system never reached disk"

    def test_a_correction_spread_over_several_systems_writes_all_of_them(self):
        add("First", 300)
        add("Second", 300)
        state.current_system = systems["Second"]
        merit_ledger.record("First", 300)
        merit_ledger.record("Second", 300)
        load._touch("First", "Second")
        load._save_now()

        load.apply_merit_correction(400)      # 300 off Second, 100 off First
        load._save_now()

        assert on_disk("Second") == 0
        assert on_disk("First") == 200

    def test_a_restore_writes_the_system_it_gave_merits_back_to(self):
        add("Eme", 0)
        state.current_system = systems["Eme"]
        load.apply_merit_restore([("Eme", 1500)])
        load._save_now()
        assert on_disk("Eme") == 1500


class TestTheLedgerTravelsWithTheMerits:
    def test_the_baseline_is_written_with_the_systems(self):
        add("Eme", 100)
        merit_ledger.baseline = 54321
        load._touch("Eme")
        load._save_now()
        assert database.load_meta("ledger")["baseline"] == 54321

    def test_a_parked_award_is_written_with_the_systems(self):
        add("Eme", 100)
        merit_ledger.pending.append([1500, 4000, "Eme"])
        load._touch("Eme")
        load._save_now()
        assert database.load_meta("ledger")["pending"] == [[1500, 4000, "Eme"]]

    def test_the_merits_and_the_ledger_land_together(self):
        """One transaction: a crash cannot keep the merits and lose the
        ledger that explains them."""
        add("Eme", 0)
        load._add_merits_to_system("Eme", 750)
        merit_ledger.baseline = 750
        load._save_now()

        systems.clear()
        loadSystems()
        stored = database.load_meta("ledger")
        assert systems["Eme"].Merits == 750
        assert stored["baseline"] == 750


class TestNoTimer:
    def test_the_autosave_timer_is_gone(self):
        # Saving happens per event now; the timer raced the journal thread on
        # the `systems` dict.
        assert not hasattr(load, "_schedule_autosave")
        assert not hasattr(load, "_autosave_data")
        assert not hasattr(load, "autosave_timer")
