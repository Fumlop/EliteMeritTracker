"""
Tests for the PowerPlay merit ledger.

All scenarios are taken from real journals - the timestamps in the docstrings
point at the events they were built from.
"""
import pytest

from emt_core.duplicate import MeritLedger


def merits(gained, total, power="Felicia Winters"):
    return {"event": "PowerplayMerits", "Power": power, "MeritsGained": gained, "TotalMerits": total}


@pytest.fixture
def ledger():
    return MeritLedger()


class TestBaseline:
    def test_first_event_seeds_baseline_from_its_own_base(self, ledger):
        assert ledger.merits_delta(merits(56, 1000)) == (0, 56)
        assert ledger.baseline == 1000

    def test_snapshot_seeds_baseline_without_crediting(self, ledger):
        assert ledger.reconcile_snapshot({"Power": "Felicia Winters", "Merits": 6059891}) == 0
        assert ledger.baseline == 6059891

    def test_clean_run_credits_every_gain(self, ledger):
        ledger.reconcile_snapshot({"Merits": 6059891})
        assert ledger.merits_delta(merits(10, 6059901)) == (0, 10)
        assert ledger.merits_delta(merits(441, 6060342)) == (0, 441)
        assert ledger.merits_delta(merits(6820, 6067162)) == (0, 6820)


class TestDuplicates:
    def test_verbatim_resend_is_ignored(self, ledger):
        """Journal.2026-08-27T115928.01.log:841-844 - the same 56/6067442 four times."""
        assert ledger.merits_delta(merits(56, 6067442)) == (0, 56)
        for _ in range(3):
            assert ledger.merits_delta(merits(56, 6067442)) == (0, 0)
        assert ledger.baseline == 6067442

    def test_repeated_gain_with_advancing_total_is_credited_then_taken_back(self, ledger):
        """Journal.2026-08-27T185156.01.log:797-798,1541 - 15898 twice, only one landed."""
        ledger.merits_delta(merits(1893, 6112659))
        assert ledger.merits_delta(merits(15898, 6128557)) == (0, 15898)
        assert ledger.merits_delta(merits(15898, 6144455)) == (0, 15898)
        # the next event exposes the second one and still credits its own 3074
        assert ledger.merits_delta(merits(3074, 6131631)) == (15898, 3074)
        assert ledger.baseline == 6131631

    def test_gain_reported_but_total_frozen(self, ledger):
        """Journal.2026-01-15T110022.01.log:1851-2052 - 118520 gained, 0 credited.

        MeritsGained here would imply a base of 2086892, which is a lie: the
        server total never moved, so nothing is credited and nothing taken back.
        """
        ledger.merits_delta(merits(46184, 2205412))
        assert ledger.merits_delta(merits(118520, 2205412)) == (0, 0)
        assert ledger.baseline == 2205412


class TestAttribution:
    def test_correction_hits_the_system_that_got_the_merits(self, ledger):
        """Journal.2026-08-27T185156.01.log:1544,3620 - phantom in Col 285 HL-L
        exposed two hours later while the player is in Aramo."""
        ledger.merits_delta(merits(14749, 6146380))
        ledger.record("Col 285 Sector HL-L b9-0", 14749)
        ledger.merits_delta(merits(14749, 6161129))
        ledger.record("Col 285 Sector HL-L b9-0", 14749)
        # player jumps to Aramo, the next event exposes the second 14749
        uncredited, credited = ledger.merits_delta(merits(3657, 6150037))
        assert (uncredited, credited) == (14749, 3657)
        assert ledger.unwind(uncredited, "Aramo") == [("Col 285 Sector HL-L b9-0", 14749)]

    def test_correction_spans_several_systems_newest_first(self, ledger):
        ledger.record("Aramo", 100)
        ledger.record("Orgen", 50)
        assert ledger.unwind(120, "Kuwembaa") == [("Orgen", 50), ("Aramo", 70)]
        assert ledger.credits == [["Aramo", 30]]

    def test_correction_beyond_history_falls_back_to_current_system(self, ledger):
        ledger.record("Aramo", 40)
        assert ledger.unwind(100, "Orgen") == [("Aramo", 40), ("Orgen", 60)]

    def test_correction_without_history_or_current_system_is_dropped(self, ledger):
        assert ledger.unwind(100, None) == []

    def test_banked_credits_absorb_a_correction_without_refunding(self, ledger):
        """A reported system must not be clawed back after its merits were submitted."""
        ledger.record("Aramo", 1000)
        ledger.forget("Aramo")
        ledger.record("Orgen", 200)
        assert ledger.unwind(700, "Orgen") == [("Orgen", 200)]

    def test_forget_all_banks_everything(self, ledger):
        ledger.record("Aramo", 100)
        ledger.record("Orgen", 100)
        ledger.forget_all()
        assert ledger.unwind(200, None) == []

    def test_history_is_capped(self):
        ledger = MeritLedger(history_size=4)
        for i in range(10):
            ledger.record(f"S{i}", 10)
        assert [c[0] for c in ledger.credits] == ["S6", "S7", "S8", "S9"]


class TestEdgeCases:
    def test_power_change_resets_tracking(self, ledger):
        ledger.merits_delta(merits(100, 900000, power="Felicia Winters"))
        ledger.record("Aramo", 100)
        assert ledger.merits_delta(merits(50, 50, power="Nakato Kaine")) == (0, 50)
        assert ledger.credits == []

    def test_missing_total_falls_back_to_reported_gain(self, ledger):
        assert ledger.merits_delta({"Power": "Felicia Winters", "MeritsGained": 10}) == (0, 10)

    def test_leave_and_return_keeps_merits_on_the_earning_system(self, ledger):
        """Journal.2026-01-15T110022.01.log - Ross 444 earns, player hops to
        Parapa where a 118520 award is reported but never credited, then returns."""
        for gain, total in ((49232, 2136124), (10224, 2146348), (12880, 2159228), (46184, 2205412)):
            uncredited, credited = ledger.merits_delta(merits(gain, total))
            assert (uncredited, credited) == (0, gain)
            ledger.record("Ross 444", credited)
        assert ledger.merits_delta(merits(118520, 2205412)) == (0, 0)   # in Parapa
        assert ledger.merits_delta(merits(9988, 2215400)) == (0, 9988)  # back in Ross 444
        assert sum(c[1] for c in ledger.credits if c[0] == "Ross 444") == 118520

    def test_missing_gain_credits_the_total_difference(self, ledger):
        ledger.merits_delta(merits(100, 500))
        assert ledger.merits_delta({"Power": "Felicia Winters", "TotalMerits": 600}) == (0, 100)

    def test_snapshot_takes_back_an_uncredited_tail_event(self, ledger):
        """Journal.2026-08-28T115835.01.log - snapshot 6162503 after a 333/6162836 event."""
        ledger.reconcile_snapshot({"Merits": 6162503 - 333})
        ledger.merits_delta(merits(333, 6162836))
        assert ledger.reconcile_snapshot({"Merits": 6162503}) == -333

    def test_snapshot_clears_the_resend_guard(self, ledger):
        ledger.merits_delta(merits(56, 1000))
        ledger.reconcile_snapshot({"Merits": 1000})
        assert ledger.merits_delta(merits(56, 1056)) == (0, 56)

    def test_reset_clears_everything(self, ledger):
        ledger.merits_delta(merits(56, 1000))
        ledger.record("Aramo", 56)
        ledger.reset()
        assert ledger.baseline is None and ledger.credits == [] and ledger.last_event is None

    def test_total_ahead_of_baseline_is_credited(self, ledger):
        """Journal.2026-07-10T191931.01.log:1700 - server total jumped past what we tracked."""
        ledger.merits_delta(merits(1299, 5430665))
        assert ledger.merits_delta(merits(1865, 5450751)) == (0, 20086)
