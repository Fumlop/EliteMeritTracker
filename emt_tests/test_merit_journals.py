"""
End-to-end merit tracking: one generated journal per scenario, replayed through
the real load.journal_entry.

Each journal contains only the entries its case needs. Ground truth comes from
the builder, which tracks what the server actually credited, so every scenario
asserts both the per-system split and the final total.
"""
import json
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

import load
from emt_core.duplicate import merit_ledger
from emt_core.state import state
from emt_models.power import pledgedPower
from emt_models.system import systems
from emt_tests.journal_builder import JournalBuilder

load.trackerFrame = MagicMock()
load.dumpSystems = lambda *a, **k: None


@pytest.fixture
def replay(tmp_path):
    """Write a builder journal to disk, read it back, feed it to the plugin."""
    def _run(builder, name):
        path = builder.write(tmp_path / f"Journal.{name}.01.log")
        merit_ledger.reset()
        systems.clear()
        pledgedPower.MeritsSession = 0
        pledgedPower.Merits = 0
        state.current_system = None
        state.reset_delivery_tracking()
        state.reset_sar_tracking()
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    entry = json.loads(line)
                    load.journal_entry("CMDR", False, entry.get("StarSystem"), None, entry, {})
        return {key: value.Merits for key, value in systems.items()}
    return _run


def assert_matches(builder, tracked):
    expected = {k: v for k, v in builder.earned.items() if v}
    assert {k: v for k, v in tracked.items() if v} == expected
    assert sum(tracked.values()) == sum(builder.earned.values())
    assert all(v >= 0 for v in tracked.values())


def test_clean_run(replay):
    """No phantoms: every award lands where it was earned."""
    b = JournalBuilder()
    b.load_game(); b.jump("Aramo"); b.real(600); b.real(1200)
    b.jump("Orgen"); b.real(400)
    assert_matches(b, replay(b, "clean"))


def test_phantom_same_system(replay):
    """Award dropped by the server, exposed by the next award in the same system."""
    b = JournalBuilder()
    b.load_game(); b.jump("Aramo"); b.real(600); b.phantom(15898); b.real(3074)
    tracked = replay(b, "phantom_same_system")
    assert tracked["Aramo"] == 3674
    assert_matches(b, tracked)


def test_phantom_exposed_after_jumping_away(replay):
    """Correction must hit the system that got the merits, not the current one."""
    b = JournalBuilder()
    b.load_game(); b.jump("Aramo"); b.real(1000); b.phantom(14749)
    b.jump("Col 285 Sector HL-L b9-0"); b.real(3657)
    tracked = replay(b, "phantom_after_jump")
    assert tracked["Aramo"] == 1000
    assert tracked["Col 285 Sector HL-L b9-0"] == 3657
    assert_matches(b, tracked)


def test_round_trip_without_earning_in_between(replay):
    """A earns, phantom in A, B/C/D pass through empty, correction lands back on A."""
    b = JournalBuilder()
    b.load_game(); b.jump("A"); b.real(600); b.phantom(400)
    b.jump("B"); b.jump("C"); b.jump("D"); b.jump("A"); b.real(50)
    tracked = replay(b, "round_trip_empty")
    assert tracked["A"] == 650
    assert_matches(b, tracked)


def test_round_trip_earning_everywhere(replay):
    """A B C D all earn, the award in D is dropped, exposed back in A."""
    b = JournalBuilder()
    b.load_game(); b.jump("A"); b.real(1000); b.real(500)
    b.jump("B"); b.real(200)
    b.jump("C"); b.real(300)
    b.jump("D"); b.phantom(400)
    b.jump("A"); b.real(60)
    tracked = replay(b, "round_trip_earning")
    assert tracked["A"] == 1560 and tracked["D"] == 0
    assert_matches(b, tracked)


def test_verbatim_resend_is_ignored(replay):
    """Journal.2026-08-27T115928.01.log:841-844 - the same line four times."""
    b = JournalBuilder()
    b.load_game(); b.jump("Aramo"); b.real(56)
    b.resend(); b.resend(); b.resend()
    tracked = replay(b, "resend_burst")
    assert tracked["Aramo"] == 56
    assert_matches(b, tracked)


def test_resend_across_a_jump_stays_on_the_earning_system(replay):
    b = JournalBuilder()
    b.load_game(); b.jump("Aramo"); b.real(500)
    b.jump("Orgen"); b.resend()
    tracked = replay(b, "resend_across_jump")
    assert tracked["Aramo"] == 500
    assert tracked.get("Orgen", 0) == 0
    assert_matches(b, tracked)


def test_consecutive_phantoms(replay):
    """Several dropped awards in a row, all exposed by one later award."""
    b = JournalBuilder()
    b.load_game(); b.jump("Aramo"); b.real(1000)
    b.phantom(300); b.phantom(700); b.phantom(150)
    b.real(80)
    tracked = replay(b, "consecutive_phantoms")
    assert tracked["Aramo"] == 1080
    assert_matches(b, tracked)


def test_phantom_exposed_by_game_restart(replay):
    """Nothing follows the phantom - only the next Powerplay snapshot exposes it."""
    b = JournalBuilder()
    b.load_game(); b.jump("Aramo"); b.real(2000); b.phantom(2305)
    b.load_game()
    tracked = replay(b, "phantom_by_snapshot")
    assert tracked["Aramo"] == 2000
    assert_matches(b, tracked)


def test_phantom_exposed_by_restart_in_another_system(replay):
    """Player quits in B; the snapshot on restart must correct A, not B."""
    b = JournalBuilder()
    b.load_game(); b.jump("A"); b.real(5000); b.phantom(1200)
    b.jump("B")
    b.load_game()
    b.real(90)
    tracked = replay(b, "phantom_by_snapshot_elsewhere")
    assert tracked["A"] == 5000
    assert tracked["B"] == 90
    assert_matches(b, tracked)


def test_unrelated_traffic_between_awards(replay):
    b = JournalBuilder()
    b.load_game(); b.jump("Aramo")
    b.real(400); b.scan(); b.scan(); b.phantom(700); b.scan(); b.real(120)
    tracked = replay(b, "interleaved_traffic")
    assert tracked["Aramo"] == 520
    assert_matches(b, tracked)


def test_deep_unwind_after_many_later_awards(replay):
    """Phantom in A followed by a long run of awards in B before it is exposed."""
    b = JournalBuilder()
    b.load_game(); b.jump("A"); b.real(5000); b.phantom(3000)
    b.jump("B")
    for _ in range(40):
        b.real(10)
    tracked = replay(b, "deep_unwind")
    assert tracked["A"] == 5000
    assert tracked["B"] == 400
    assert_matches(b, tracked)


def test_award_larger_than_the_dropped_one(replay):
    """Correction and a genuine award collide: the server total is still matched."""
    b = JournalBuilder()
    b.load_game(); b.jump("A"); b.real(100); b.phantom(50)
    b.jump("B"); b.real(5000)
    tracked = replay(b, "big_award_after_phantom")
    assert sum(tracked.values()) == b.server_total - 1_000_000
    assert all(v >= 0 for v in tracked.values())


def test_power_change_starts_a_new_total(replay):
    """Repledging resets the server total; no giant negative correction."""
    b = JournalBuilder(900_000)
    b.load_game(); b.jump("Aramo"); b.real(100)
    b.server_total = 50
    b.lines.append({"timestamp": "2026-08-29T10:00:00Z", "event": "PowerplayMerits",
                    "Power": "Nakato Kaine", "MeritsGained": 50, "TotalMerits": 50})
    b.earned["Aramo"] += 50
    tracked = replay(b, "power_change")
    assert tracked["Aramo"] == 150


def test_merits_before_any_location_are_not_attributed(replay):
    """Known gap: with no system yet, there is nowhere to book the merits."""
    b = JournalBuilder()
    b.lines.append({"timestamp": "2026-08-28T12:00:00Z", "event": "PowerplayMerits",
                    "Power": "Felicia Winters", "MeritsGained": 250, "TotalMerits": 1_000_250})
    b.server_total = 1_000_250
    tracked = replay(b, "no_location")
    assert sum(tracked.values()) == 0


def test_large_resend_is_dropped_with_nothing_after_it(replay):
    """The bug the threshold exists for: a phantom big award and then the player
    stops earning, so no later event ever exposes it."""
    b = JournalBuilder()
    b.load_game(); b.jump("Aramo"); b.real(127735); b.phantom(127735)
    tracked = replay(b, "large_resend_tail")
    assert tracked["Aramo"] == 127735
    assert sum(tracked.values()) == b.server_total - 1_000_000


def test_two_genuine_large_awards_are_restored_to_their_system(replay):
    """False positive of the threshold: both hand-ins are real. The second is
    rejected, then the next award's base proves it landed and it goes back to
    Aramo - not to Orgen, where the player is by then."""
    b = JournalBuilder()
    b.load_game(); b.jump("Aramo"); b.real(2000); b.real(2000)
    b.jump("Orgen"); b.real(50)
    tracked = replay(b, "large_resend_false_positive")
    assert_matches(b, tracked)


def test_two_genuine_large_awards_are_restored_on_relog(replay):
    """Same, but the proof is the snapshot at the next game start."""
    b = JournalBuilder()
    b.load_game(); b.jump("Aramo"); b.real(2000); b.real(2000)
    b.load_game()
    tracked = replay(b, "large_resend_restored_on_relog")
    assert_matches(b, tracked)
