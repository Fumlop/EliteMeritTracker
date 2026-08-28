"""
PowerPlay merit ledger.

Elite reports TotalMerits in a PowerplayMerits event as a stale server-side read
plus MeritsGained. Concurrent awards clobber each other under server lag, so a
reported MeritsGained is frequently never credited - the following event exposes
it by reusing the same base (TotalMerits - MeritsGained).

TotalMerits is therefore the only authoritative number and merits are tracked as
its delta. Verified against 388 journals / 2732 PowerplayMerits events: delta
tracking reproduces the server total exactly, summing MeritsGained overcounts by
5.6%.

A delta can be negative when the previous event turns out to have been dropped
server-side. Because the player may have changed system in between, credits are
kept in a small LIFO history so the correction is taken off the system that
actually received it.
"""

from typing import Any, Dict, List, Optional, Tuple
from emt_core.logging import logger


class MeritLedger:
    """Tracks the authoritative PowerPlay merit total and per-system credits."""

    def __init__(self, history_size: int = 128):
        self.history_size = history_size
        self.reset()

    def reset(self) -> None:
        """Drop the baseline and the credit history."""
        self.baseline: Optional[int] = None
        self.power: str = ""
        self.last_event: Optional[Tuple[int, int]] = None
        self.credits: List[List[Any]] = []

    def _check_power(self, power: str) -> None:
        """Reset tracking when the pledged power changes - totals are per power."""
        if power and self.power and power != self.power:
            logger.info(f"Power changed {self.power} -> {power}, resetting merit baseline")
            self.reset()
        if power:
            self.power = power

    def reconcile_snapshot(self, entry: Dict[str, Any]) -> int:
        """Fold a Powerplay snapshot (game load) into the baseline.

        Returns the delta to apply. Always 0 on the first snapshot seen.
        """
        total = entry.get("Merits")
        if total is None:
            return 0
        self._check_power(entry.get("Power", ""))
        if self.baseline is None:
            self.baseline = total
            return 0
        delta = total - self.baseline
        self.baseline = total
        if delta:
            logger.info(f"Server merit snapshot {total} disagrees with tracked {total - delta}: {delta:+}")
        self.last_event = None
        return delta

    def merits_delta(self, entry: Dict[str, Any]) -> Tuple[int, int]:
        """Split a PowerplayMerits event into (uncredited, credited) merits.

        Only TotalMerits is trusted. MeritsGained is regularly reported for
        awards the server dropped, so it is used for nothing but the resend
        check and logging.

        `uncredited` is what earlier events were given but the server never
        applied - it has to be taken back off whichever systems received it.
        `credited` is what the server total actually advanced by and belongs to
        the current system. Both zero means the event changed nothing.
        """
        total = entry.get("TotalMerits")
        gained = entry.get("MeritsGained", 0)
        if total is None:
            return 0, gained
        self._check_power(entry.get("Power", ""))

        # A verbatim resend is the one unambiguous duplicate: same award, same total
        if self.last_event == (gained, total):
            logger.warning(f"Duplicate PowerplayMerits ignored: {gained} merits, total {total}")
            return 0, 0
        self.last_event = (gained, total)

        if self.baseline is None:
            self.baseline = total - gained

        delta = total - self.baseline
        self.baseline = total
        if delta != gained:
            logger.warning(f"MeritsGained {gained} but server total moved {delta} (to {total})")
        if delta < 0:
            return -delta, 0
        return 0, delta

    def record(self, system: str, merits: int) -> None:
        """Remember that `merits` were credited to `system`."""
        if not system or merits <= 0:
            return
        self.credits.append([system, merits])
        if len(self.credits) > self.history_size:
            del self.credits[:len(self.credits) - self.history_size]

    def forget(self, system: str) -> None:
        """Mark a system's credits as banked - reported or manually cleared.

        The entries stay in the history so they still absorb their share of a
        later correction, but nothing is subtracted from the system any more.
        """
        for credit in self.credits:
            if credit[0] == system:
                credit[0] = None

    def forget_all(self) -> None:
        """Mark every tracked credit as banked."""
        for credit in self.credits:
            credit[0] = None

    def unwind(self, merits: int, fallback_system: Optional[str] = None) -> List[Tuple[str, int]]:
        """Take `merits` back off the most recent credits first.

        Returns [(system, merits)] to subtract. Credits already banked absorb
        their share without producing a refund. Anything left over once the
        history is exhausted falls back to `fallback_system`.
        """
        refunds: List[Tuple[str, int]] = []
        remaining = merits
        while remaining > 0 and self.credits:
            system, credited = self.credits[-1]
            take = min(credited, remaining)
            if system:
                refunds.append((system, take))
            remaining -= take
            if take == credited:
                self.credits.pop()
            else:
                self.credits[-1][1] = credited - take
        if remaining > 0:
            if fallback_system:
                refunds.append((fallback_system, remaining))
            else:
                logger.warning(f"Cannot unwind {remaining} merits: no credit history and no current system")
        return refunds


merit_ledger = MeritLedger()


def reset_merit_tracking() -> None:
    """Reset all merit tracking state."""
    merit_ledger.reset()
