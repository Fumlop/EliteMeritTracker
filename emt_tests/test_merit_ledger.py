"""
Tests for the PowerPlay merit ledger.

All scenarios are taken from real journals - the timestamps in the docstrings
point at the events they were built from.
"""
import pytest

from datetime import timedelta

from emt_core.duplicate import MeritLedger, _parse_timestamp


def merits(gained, total, power="Felicia Winters", timestamp=None):
    entry = {"event": "PowerplayMerits", "Power": power, "MeritsGained": gained, "TotalMerits": total}
    if timestamp:
        entry["timestamp"] = timestamp
    return entry


@pytest.fixture
def ledger():
    return MeritLedger()


class TestBaseline:
    def test_first_event_seeds_baseline_from_its_own_base(self, ledger):
        assert ledger.merits_delta(merits(56, 1000)) == (0, [], 56)
        assert ledger.baseline == 1000

    def test_snapshot_seeds_baseline_without_crediting(self, ledger):
        assert ledger.reconcile_snapshot({"Power": "Felicia Winters", "Merits": 6059891}) == (0, [])
        assert ledger.baseline == 6059891

    def test_clean_run_credits_every_gain(self, ledger):
        ledger.reconcile_snapshot({"Merits": 6059891})
        assert ledger.merits_delta(merits(10, 6059901)) == (0, [], 10)
        assert ledger.merits_delta(merits(441, 6060342)) == (0, [], 441)
        assert ledger.merits_delta(merits(6820, 6067162)) == (0, [], 6820)


class TestDuplicates:
    def test_verbatim_resend_is_ignored(self, ledger):
        """Journal.2026-08-27T115928.01.log:841-844 - the same 56/6067442 four times."""
        assert ledger.merits_delta(merits(56, 6067442)) == (0, [], 56)
        for _ in range(3):
            assert ledger.merits_delta(merits(56, 6067442)) == (0, [], 0)
        assert ledger.baseline == 6067442

    def test_repeated_gain_with_advancing_total_is_credited_then_taken_back(self, ledger):
        """Journal.2026-08-27T185156.01.log:797-798,1541 - 15898 twice, only one landed."""
        ledger.merits_delta(merits(1893, 6112659))
        assert ledger.merits_delta(merits(15898, 6128557)) == (0, [], 15898)
        assert ledger.merits_delta(merits(15898, 6144455)) == (0, [], 15898)
        # the next event exposes the second one and still credits its own 3074
        assert ledger.merits_delta(merits(3074, 6131631)) == (15898, [], 3074)
        assert ledger.baseline == 6131631

    def test_gain_reported_but_total_frozen(self, ledger):
        """Journal.2026-01-15T110022.01.log:1851-2052 - 118520 gained, 0 credited.

        MeritsGained here would imply a base of 2086892, which is a lie: the
        server total never moved, so nothing is credited and nothing taken back.
        """
        ledger.merits_delta(merits(46184, 2205412))
        assert ledger.merits_delta(merits(118520, 2205412)) == (0, [], 0)
        assert ledger.baseline == 2205412


class TestLargeResend:
    """MeritsGained >= DUPE_MIN_MERITS repeated inside the window is rejected on
    arrival, so the doubled number never shows up even if nothing follows it."""

    def test_same_second_resend_is_rejected(self, ledger):
        """Journal.2026-09-08T072628.01.log:1395-1398 - 127735 twice at 10:27:22."""
        assert ledger.merits_delta(merits(127735, 7515770, timestamp="2026-09-08T10:27:22Z")) == (0, [], 127735)
        assert ledger.merits_delta(merits(127735, 7643505, timestamp="2026-09-08T10:27:22Z")) == (0, [], 0)
        assert ledger.baseline == 7515770
        # the event that used to be needed to expose it now just credits its own 90
        assert ledger.merits_delta(merits(90, 7515860, timestamp="2026-09-08T10:27:28Z")) == (0, [], 90)

    def test_resend_44s_later_is_rejected(self, ledger):
        """Journal.2026-09-07T192004.01.log - 35005 at 17:33:11 and 17:33:55."""
        ledger.merits_delta(merits(16390, 7204799, timestamp="2026-09-07T17:33:11Z"))
        assert ledger.merits_delta(merits(35005, 7239804, timestamp="2026-09-07T17:33:11Z")) == (0, [], 35005)
        assert ledger.merits_delta(merits(35005, 7274809, timestamp="2026-09-07T17:33:55Z")) == (0, [], 0)
        assert ledger.baseline == 7239804

    def test_resend_survives_small_awards_in_between(self, ledger):
        """Journal.2026-09-07T192004.01.log - 111648 at 20:12:35 and 20:13:12 with
        two 77s in between, so the check cannot look at the previous event only."""
        ledger.merits_delta(merits(77, 7240127, timestamp="2026-09-07T20:12:35Z"))
        assert ledger.merits_delta(merits(111648, 7351775, timestamp="2026-09-07T20:12:35Z")) == (0, [], 111648)
        ledger.merits_delta(merits(77, 7351852, timestamp="2026-09-07T20:12:35Z"))
        ledger.merits_delta(merits(77, 7351929, timestamp="2026-09-07T20:12:35Z"))
        assert ledger.merits_delta(merits(111648, 7463423, timestamp="2026-09-07T20:13:12Z")) == (0, [], 0)
        assert ledger.baseline == 7351929

    def test_small_awards_repeat_legitimately(self, ledger):
        """Journal.2026-09-07T192004.01.log:21:33:41-59 - 45 merits seven times.

        test/Journal.2026-02-16T133244.01.log has the same shape at 112 merits
        (four in a row, gaps 58/33/12 s) and at 10, 89. Small awards repeat
        constantly, which is why the threshold exists."""
        total = 7387765
        for second in (41, 44, 46, 48, 50, 58, 59):
            total += 45
            stamp = f"2026-09-07T21:33:{second:02d}Z"
            assert ledger.merits_delta(merits(45, total, timestamp=stamp)) == (0, [], 45)
        assert ledger.baseline == 7388080

    def test_repeat_outside_the_window_is_credited(self, ledger):
        ledger.merits_delta(merits(35005, 7239804, timestamp="2026-09-07T17:33:11Z"))
        assert ledger.merits_delta(merits(35005, 7274809, timestamp="2026-09-07T17:35:00Z")) == (0, [], 35005)

    def test_a_power_change_drops_the_window(self, ledger):
        """Not the `p == power` clause: _check_power resets the whole ledger, so
        the window is empty by the time the comparison runs."""
        ledger.merits_delta(merits(35005, 7239804, timestamp="2026-09-07T17:33:11Z"))
        assert ledger.merits_delta(
            merits(35005, 35005, power="Nakato Kaine", timestamp="2026-09-07T17:33:55Z")
        ) == (0, [], 35005)
        assert [p for _, _, p in ledger.recent] == ["Nakato Kaine"]

    def test_rejection_leaves_the_credit_history_alone(self, ledger):
        """Journal.2026-09-07T192004.01.log 21:33:39-21:34:05. Dropping the resend
        must not touch what the genuine award was booked against."""
        ledger.merits_delta(merits(35969, 7387765, timestamp="2026-09-07T21:33:39Z"))
        ledger.record("Aramo", 35969)
        assert ledger.merits_delta(merits(35969, 7424004, timestamp="2026-09-07T21:34:04Z")) == (0, [], 0)
        assert ledger.merits_delta(merits(45, 7387810, timestamp="2026-09-07T21:34:05Z")) == (0, [], 45)
        assert ledger.credits == [["Aramo", 35969]]

    def test_a_real_phantom_after_a_rejection_still_unwinds(self, ledger):
        """The rejection must not disarm the correction path for a later drop."""
        ledger.merits_delta(merits(2000, 5000, timestamp="2026-09-07T20:00:00Z"))
        ledger.record("Aramo", 2000)
        assert ledger.merits_delta(merits(2000, 7000, timestamp="2026-09-07T20:00:10Z")) == (0, [], 0)
        ledger.merits_delta(merits(300, 5300, timestamp="2026-09-07T20:05:00Z"))
        ledger.record("Orgen", 300)
        # 20:05 was itself dropped: the next base is back at 5000
        assert ledger.merits_delta(merits(40, 5040, timestamp="2026-09-07T20:06:00Z")) == (300, [], 40)
        assert ledger.unwind(300, "Orgen") == [("Orgen", 300)]

    def test_a_genuine_repeat_after_a_rejection_is_still_credited(self, ledger):
        """A rejected resend carries the same (gain, total) the genuine award will
        carry, because the baseline did not move. It must not arm the verbatim guard."""
        assert ledger.merits_delta(merits(35005, 7239804, timestamp="2026-09-07T17:33:11Z")) == (0, [], 35005)
        assert ledger.merits_delta(merits(35005, 7274809, timestamp="2026-09-07T17:33:55Z")) == (0, [], 0)
        assert ledger.merits_delta(merits(35005, 7274809, timestamp="2026-09-07T17:45:00Z")) == (0, [], 35005)
        assert ledger.baseline == 7274809

    def test_the_window_does_not_grow_on_a_trickle(self, ledger):
        total = 1000
        for i in range(500):
            total += 5
            ledger.merits_delta(merits(5, total, timestamp="2026-09-07T17:33:11Z"))
        assert ledger.recent == []

    def test_a_timestamp_without_a_zone_is_read_as_utc(self, ledger):
        """A replayed journal may lose the Z; local time would skew the window by
        the machine's UTC offset, so assert the zone rather than the outcome -
        the outcome alone passes on a UTC runner with the fix removed."""
        assert _parse_timestamp("2026-09-07T17:33:11").utcoffset() == timedelta(0)
        ledger.merits_delta(merits(35005, 7239804, timestamp="2026-09-07T17:33:11"))
        assert ledger.merits_delta(merits(35005, 7274809, timestamp="2026-09-07T17:33:55Z")) == (0, [], 0)

    def test_a_wrong_rejection_is_given_back_to_the_system_that_earned_it(self, ledger):
        """Two genuine identical hand-ins in Aramo 20s apart. The second is
        rejected, then the server base proves it landed - it goes back to Aramo,
        not to Orgen where the player is by the time that proof arrives."""
        assert ledger.merits_delta(merits(2000, 5000, timestamp="2026-09-09T20:00:00Z"), "Aramo") == (0, [], 2000)
        assert ledger.merits_delta(merits(2000, 7000, timestamp="2026-09-09T20:00:20Z"), "Aramo") == (0, [], 0)
        assert ledger.merits_delta(merits(50, 7050, timestamp="2026-09-09T20:05:00Z"), "Orgen") == (0, [("Aramo", 2000)], 50)
        assert ledger.baseline == 7050

    def test_a_correct_rejection_gives_nothing_back(self, ledger):
        """Journal.2026-09-08T072628.01.log:1395-1398 - the server base stays at
        7515770, below the 7643505 the resend claimed, so the rejection stands."""
        ledger.merits_delta(merits(127735, 7515770, timestamp="2026-09-08T10:27:22Z"), "Aramo")
        ledger.merits_delta(merits(127735, 7643505, timestamp="2026-09-08T10:27:22Z"), "Aramo")
        assert ledger.merits_delta(merits(90, 7515860, timestamp="2026-09-08T10:27:28Z"), "Orgen") == (0, [], 90)
        assert ledger.pending == []

    def test_a_wrong_rejection_is_given_back_on_relog(self, ledger):
        """No further award, just a game restart: the snapshot is proof enough."""
        ledger.merits_delta(merits(2000, 5000, timestamp="2026-09-09T20:00:00Z"), "Aramo")
        ledger.merits_delta(merits(2000, 7000, timestamp="2026-09-09T20:00:20Z"), "Aramo")
        assert ledger.reconcile_snapshot({"Power": "Felicia Winters", "Merits": 7000}) == (0, [("Aramo", 2000)])
        assert ledger.baseline == 7000

    def test_a_correct_rejection_still_shows_as_a_snapshot_drop(self, ledger):
        ledger.merits_delta(merits(2000, 5000, timestamp="2026-09-09T20:00:00Z"), "Aramo")
        ledger.merits_delta(merits(2000, 7000, timestamp="2026-09-09T20:00:20Z"), "Aramo")
        assert ledger.reconcile_snapshot({"Power": "Felicia Winters", "Merits": 5000}) == (0, [])

    def test_a_rejection_without_a_system_falls_back_to_the_lump(self, ledger):
        """Nothing to park the award against, so it stays in the credited lump and
        lands on the current system. The total is right, the split may not be."""
        ledger.merits_delta(merits(2000, 5000, timestamp="2026-09-09T20:00:00Z"))
        ledger.merits_delta(merits(2000, 7000, timestamp="2026-09-09T20:00:20Z"))
        assert ledger.merits_delta(merits(50, 7050, timestamp="2026-09-09T20:05:00Z")) == (0, [], 2050)

    def test_a_resend_carrying_a_stale_base_is_never_restored(self, ledger):
        """The resend claims a total below what the server already holds, so it
        is one the server demonstrably never applied. Parking it would hand it
        back on the next event that happens to clear that stale number."""
        ledger.merits_delta(merits(1000, 1001000, timestamp="2026-09-09T20:00:33Z"), "Aramo")
        ledger.merits_delta(merits(9000, 1010000, timestamp="2026-09-09T20:00:36Z"), "Aramo")
        assert ledger.merits_delta(merits(1000, 1002000, timestamp="2026-09-09T20:00:39Z"), "Aramo") == (0, [], 0)
        assert ledger.pending == []
        assert ledger.reconcile_snapshot({"Power": "Felicia Winters", "Merits": 1010000}) == (0, [])

    def test_a_restore_never_drives_the_credited_amount_negative(self, ledger):
        ledger.merits_delta(merits(1000, 1001000, timestamp="2026-09-09T20:00:33Z"), "Aramo")
        ledger.merits_delta(merits(9000, 1010000, timestamp="2026-09-09T20:00:36Z"), "Aramo")
        ledger.merits_delta(merits(1000, 1002000, timestamp="2026-09-09T20:00:39Z"), "Aramo")
        assert ledger.merits_delta(merits(90, 1002090, timestamp="2026-09-09T20:00:45Z"), "Aramo") == (8000, [], 90)

    def test_two_rejections_each_go_back_to_their_own_system(self, ledger):
        """A single pending slot booked the first award to wherever the player
        had moved by the time the proof arrived."""
        ledger.merits_delta(merits(2000, 1002000, timestamp="2026-09-09T20:00:00Z"), "Aramo")
        ledger.merits_delta(merits(2000, 1004000, timestamp="2026-09-09T20:00:10Z"), "Aramo")
        ledger.merits_delta(merits(2000, 1006000, timestamp="2026-09-09T20:00:20Z"), "Orgen")
        assert ledger.merits_delta(merits(90, 1006090, timestamp="2026-09-09T20:00:30Z"), "Zed") == (
            0, [("Aramo", 2000), ("Orgen", 2000)], 90)

    def test_two_rejections_claiming_the_same_base_restore_only_one(self, ledger):
        """The server base accounts for one of them, so only one is owed."""
        ledger.merits_delta(merits(2000, 5000, timestamp="2026-09-09T20:00:00Z"), "Aramo")
        ledger.merits_delta(merits(2000, 7000, timestamp="2026-09-09T20:00:10Z"), "Aramo")
        ledger.merits_delta(merits(2000, 7000, timestamp="2026-09-09T20:00:20Z"), "Orgen")
        assert ledger.merits_delta(merits(50, 7050, timestamp="2026-09-09T20:00:30Z"), "Zed") == (
            0, [("Aramo", 2000)], 50)

    def test_a_frozen_total_decides_nothing_and_keeps_the_award_parked(self, ledger):
        ledger.merits_delta(merits(2000, 5000, timestamp="2026-09-09T20:00:00Z"), "Aramo")
        ledger.merits_delta(merits(2000, 7000, timestamp="2026-09-09T20:00:20Z"), "Aramo")
        assert ledger.merits_delta(merits(500, 5000, timestamp="2026-09-09T20:00:30Z"), "Orgen") == (0, [], 0)
        assert ledger.pending == [[2000, 7000, "Aramo"]]
        assert ledger.merits_delta(merits(50, 7050, timestamp="2026-09-09T20:05:00Z"), "Orgen") == (
            0, [("Aramo", 2000)], 50)

    def test_an_award_against_a_frozen_total_does_not_arm_the_window(self, ledger):
        """Journal.2026-01-15T110022.01.log:2052 - 118520 reported, nothing
        credited. A genuine repeat of it must not then be rejected."""
        ledger.merits_delta(merits(46184, 2205412, timestamp="2026-01-15T11:00:00Z"))
        assert ledger.merits_delta(merits(118520, 2205412, timestamp="2026-01-15T11:00:10Z")) == (0, [], 0)
        assert [g for _, g, _ in ledger.recent] == [46184]
        assert ledger.merits_delta(merits(118520, 2323932, timestamp="2026-01-15T11:00:20Z")) == (0, [], 118520)

    def test_snapshot_clears_the_resend_window(self, ledger):
        ledger.merits_delta(merits(35005, 7239804, timestamp="2026-09-07T17:33:11Z"))
        ledger.reconcile_snapshot({"Merits": 7239804})
        assert ledger.merits_delta(merits(35005, 7274809, timestamp="2026-09-07T17:33:55Z")) == (0, [], 35005)


class TestAttribution:
    def test_correction_hits_the_system_that_got_the_merits(self, ledger):
        """Journal.2026-08-27T185156.01.log:1544,3620 - phantom in Col 285 HL-L
        exposed two hours later while the player is in Aramo."""
        ledger.merits_delta(merits(14749, 6146380))
        ledger.record("Col 285 Sector HL-L b9-0", 14749)
        ledger.merits_delta(merits(14749, 6161129))
        ledger.record("Col 285 Sector HL-L b9-0", 14749)
        # player jumps to Aramo, the next event exposes the second 14749
        uncredited, _, credited = ledger.merits_delta(merits(3657, 6150037))
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
        assert ledger.merits_delta(merits(50, 50, power="Nakato Kaine")) == (0, [], 50)
        assert ledger.credits == []

    def test_missing_total_falls_back_to_reported_gain(self, ledger):
        assert ledger.merits_delta({"Power": "Felicia Winters", "MeritsGained": 10}) == (0, [], 10)

    def test_leave_and_return_keeps_merits_on_the_earning_system(self, ledger):
        """Journal.2026-01-15T110022.01.log - Ross 444 earns, player hops to
        Parapa where a 118520 award is reported but never credited, then returns."""
        for gain, total in ((49232, 2136124), (10224, 2146348), (12880, 2159228), (46184, 2205412)):
            uncredited, _, credited = ledger.merits_delta(merits(gain, total))
            assert (uncredited, credited) == (0, gain)
            ledger.record("Ross 444", credited)
        assert ledger.merits_delta(merits(118520, 2205412)) == (0, [], 0)   # in Parapa
        assert ledger.merits_delta(merits(9988, 2215400)) == (0, [], 9988)  # back in Ross 444
        assert sum(c[1] for c in ledger.credits if c[0] == "Ross 444") == 118520

    def test_missing_gain_credits_the_total_difference(self, ledger):
        ledger.merits_delta(merits(100, 500))
        assert ledger.merits_delta({"Power": "Felicia Winters", "TotalMerits": 600}) == (0, [], 100)

    def test_snapshot_takes_back_an_uncredited_tail_event(self, ledger):
        """Journal.2026-08-28T115835.01.log - snapshot 6162503 after a 333/6162836 event."""
        ledger.reconcile_snapshot({"Merits": 6162503 - 333})
        ledger.merits_delta(merits(333, 6162836))
        assert ledger.reconcile_snapshot({"Merits": 6162503}) == (-333, [])

    def test_snapshot_clears_the_resend_guard(self, ledger):
        ledger.merits_delta(merits(56, 1000))
        ledger.reconcile_snapshot({"Merits": 1000})
        assert ledger.merits_delta(merits(56, 1056)) == (0, [], 56)

    def test_reset_clears_everything(self, ledger):
        ledger.merits_delta(merits(56, 1000))
        ledger.record("Aramo", 56)
        ledger.reset()
        assert ledger.baseline is None and ledger.credits == [] and ledger.last_event is None
        assert ledger.recent == [] and ledger.pending == []

    def test_total_ahead_of_baseline_is_credited(self, ledger):
        """Journal.2026-07-10T191931.01.log:1700 - server total jumped past what we tracked."""
        ledger.merits_delta(merits(1299, 5430665))
        assert ledger.merits_delta(merits(1865, 5450751)) == (0, [], 20086)
