"""
Tests for the merit_events log and for parked awards surviving a restart.

The log is what lets DUPE_MIN_MERITS be re-checked against real play - it was
tuned on 5 journals / 84 events. The parked awards are a correctness fix: a
large award rejected as a resend only gets its merits back when a later event
proves the server held it, and closing EDMC in between used to lose them.
"""
import pytest

from emt_core import database
from emt_core.duplicate import MeritLedger, DUPE_MIN_MERITS


def award(total, gained, stamp="2026-09-20T12:00:00Z", power="Felicia Winters"):
    return {"timestamp": stamp, "event": "PowerplayMerits", "Power": power,
            "TotalMerits": total, "MeritsGained": gained}


class TestMeritEventLog:
    def test_a_row_survives_the_round_trip(self):
        database.record_merit_event(
            stamp="2026-09-20T12:00:00Z", commander="Fumlop",
            power="Felicia Winters", total=1000, gained=120, delta=120,
            system="Eme", verdict="credited")
        events = database.merit_events()
        assert len(events) == 1
        assert events[0]["total"] == 1000
        assert events[0]["gained"] == 120
        assert events[0]["delta"] == 120
        assert events[0]["system"] == "Eme"
        assert events[0]["verdict"] == "credited"

    def test_events_come_back_oldest_first(self):
        for total in (100, 200, 300):
            database.record_merit_event(
                stamp="2026-09-20T12:00:00Z", commander="", power="P",
                total=total, gained=100, delta=100, system="Eme",
                verdict="credited")
        assert [e["total"] for e in database.merit_events()] == [100, 200, 300]

    def test_a_limit_keeps_the_newest_but_still_reads_forward(self):
        for total in (100, 200, 300):
            database.record_merit_event(
                stamp="s", commander="", power="P", total=total, gained=100,
                delta=100, system=None, verdict="credited")
        assert [e["total"] for e in database.merit_events(limit=2)] == [200, 300]

    def test_it_can_be_filtered_by_commander(self):
        for name, total in (("A", 100), ("B", 200)):
            database.record_merit_event(
                stamp="s", commander=name, power="P", total=total, gained=1,
                delta=1, system=None, verdict="credited")
        assert [e["total"] for e in database.merit_events(commander="A")] == [100]

    def test_a_system_of_none_is_allowed(self):
        assert database.record_merit_event(
            stamp="s", commander="", power="P", total=1, gained=1, delta=1,
            system=None, verdict="ignored") is True
        assert database.merit_events()[0]["system"] is None

    def test_a_failed_write_is_not_fatal(self, tmp_path):
        broken = tmp_path / "broken.db"
        broken.write_bytes(b"not a database at all")
        # A lost log line must never cost the award it describes.
        assert database.record_merit_event(
            stamp="s", commander="", power="P", total=1, gained=1, delta=1,
            system=None, verdict="credited", db=str(broken)) is False

    def test_a_failed_read_is_empty(self, tmp_path):
        broken = tmp_path / "broken.db"
        broken.write_bytes(b"not a database at all")
        assert database.merit_events(db=str(broken)) == []


class TestPendingSurvivesARestart:
    def test_a_parked_award_is_exported(self):
        ledger = MeritLedger()
        ledger.merits_delta(award(10000, DUPE_MIN_MERITS), "Eme")
        # The same large award again inside the window is rejected and parked.
        ledger.merits_delta(award(11000, DUPE_MIN_MERITS), "Eme")
        assert ledger.export_state()["pending"] == [[DUPE_MIN_MERITS, 11000, "Eme"]]

    def test_import_puts_it_back_and_it_can_still_be_restored(self):
        first = MeritLedger()
        first.merits_delta(award(10000, DUPE_MIN_MERITS), "Eme")
        first.merits_delta(award(11000, DUPE_MIN_MERITS), "Eme")
        saved = first.export_state()
        assert saved["pending"]

        # EDMC restarts. The baseline travels with the parked award: without it
        # _resolve_pending has no room and can never give the merits back.
        second = MeritLedger()
        assert second.import_state(saved) == 1
        assert second.baseline == first.baseline

        # The server's own snapshot proves it held the award after all.
        _delta, restored = second.reconcile_snapshot(
            {"Power": "Felicia Winters", "Merits": 11000})
        assert restored == [("Eme", DUPE_MIN_MERITS)]

    def test_export_is_a_copy_not_the_live_list(self):
        ledger = MeritLedger()
        ledger.pending.append([1000, 2000, "Eme"])
        exported = ledger.export_state()["pending"]
        exported[0][0] = 9999
        assert ledger.pending[0][0] == 1000

    def test_importing_nothing_is_a_no_op(self):
        ledger = MeritLedger()
        assert ledger.import_state(None) == 0
        assert ledger.import_state({}) == 0
        assert ledger.import_state("nonsense") == 0
        assert ledger.pending == []

    @pytest.mark.parametrize("row", [
        "not a list", [1, 2], [1, 2, 3, 4], ["gained", 2000, "Eme"],
        [1000, "total", "Eme"], None, {},
    ])
    def test_a_malformed_row_is_dropped_not_raised(self, row):
        # These come off disk; a bad one must not stop the plugin loading.
        ledger = MeritLedger()
        ledger.import_state({"pending": [row]})
        assert ledger.pending == []

    def test_a_non_string_system_becomes_none(self):
        ledger = MeritLedger()
        ledger.import_state({"pending": [[1000, 2000, 17]]})
        assert ledger.pending == [[1000, 2000, None]]

    def test_the_import_respects_the_cap(self):
        from emt_core.duplicate import PENDING_LIMIT
        ledger = MeritLedger()
        ledger.import_state({"pending": [[1000, 2000, "Eme"]] * (PENDING_LIMIT + 10)})
        assert len(ledger.pending) == PENDING_LIMIT

    def test_a_round_trip_through_the_database(self):
        ledger = MeritLedger()
        ledger.baseline = 3000
        ledger.pending.append([1500, 4000, "Eme"])
        database.save_meta("ledger", ledger.export_state())

        after = MeritLedger()
        after.import_state(database.load_meta("ledger"))
        assert after.pending == [[1500, 4000, "Eme"]]
        assert after.baseline == 3000
