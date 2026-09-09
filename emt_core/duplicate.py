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

That correction only lands once a *later* event exposes the phantom. A player who
stops earning right after a big hand-in never gets one, and reports the doubled
number. Large awards are therefore also checked on arrival: an identical large
MeritsGained for the same power inside a short window is rejected outright. Across
5 journals holding merit events / 84 events, all 4 awards >= 1000 merits carrying
that signature were phantom and all 11 without it were real; the largest
legitimately repeated award seen was 112 merits (test/Journal.2026-02-16T133244
.01.log, four in a row at 20:25:46-20:27:29).

The threshold is the whole safety margin and the sample is small, so a rejection
is provisional rather than final. The rejected award is parked with the system it
would have gone to; the next event's base decides its fate. A base at or above the
total the rejected event claimed proves the server did hold it, and it is given
back to the system that earned it - the mirror of the unwind that takes a phantom
off one. Two rules keep a restore honest: an award whose own base is already below
the tracked baseline is never parked, because the server has demonstrably moved
past it without it; and no more is ever given back than the base exceeds the
baseline by, because that difference is exactly what is owed.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from emt_core.logging import logger

# An identical award this size or larger, repeated for the same power inside the
# window, is a server resend rather than a second hand-in.
DUPE_MIN_MERITS = 1000
DUPE_WINDOW_SECONDS = 60.0
# Rejections only stack inside a resend burst; the cap is a safety net
PENDING_LIMIT = 32


def _parse_timestamp(value: Any) -> Optional[datetime]:
    """Parse an Elite journal timestamp, or None if it is missing/unusable."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    # Elite always emits UTC; a replayed journal may have lost the marker, and a
    # naive value would otherwise be read as local time and skew the window
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


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
        self.recent: List[Tuple[datetime, int, str]] = []
        self.pending: List[List[Any]] = []
        self.credits: List[List[Any]] = []

    def _check_power(self, power: str) -> None:
        """Reset tracking when the pledged power changes - totals are per power."""
        if power and self.power and power != self.power:
            logger.info(f"Power changed {self.power} -> {power}, resetting merit baseline")
            self.reset()
        if power:
            self.power = power

    def _is_large_resend(self, when: Optional[datetime], gained: int, power: str) -> bool:
        """True if this is a large award already seen for the same power just now.

        Suppressed events are deliberately not remembered, so a run of resends is
        always measured against the one genuine award that started it.
        """
        if when is None or gained < DUPE_MIN_MERITS:
            return False
        cutoff = when.timestamp() - DUPE_WINDOW_SECONDS
        self.recent = [r for r in self.recent if r[0].timestamp() >= cutoff]
        return any(g == gained and p == power for _, g, p in self.recent)

    def _resolve_pending(self, base: int) -> List[Tuple[str, int]]:
        """Decide every rejected award's fate from the server's own base.

        A rejection stands while the server base is below the total that award
        claimed. Once the base reaches it the server really did hold it, so it
        goes back to the system it was parked against - the mirror of `unwind`,
        which takes a phantom back off a system.

        The base also caps the total: it exceeds the baseline by exactly the
        merits this ledger has not credited, so nothing beyond `base - baseline`
        can be owed. Without that cap two awards claiming the same base would
        both be restored, and `credited` would go negative.
        """
        pending, self.pending = self.pending, []
        room = base - (self.baseline or 0)
        restored: List[Tuple[str, int]] = []
        for gained, claimed_total, system in pending:
            if base < claimed_total:
                continue
            if gained > room:
                logger.warning(f"Not restoring {gained} merits: server base {base} only accounts for {room}")
                continue
            room -= gained
            logger.warning(f"Rejected award of {gained} merits was genuine after all (server base {base} >= claimed {claimed_total})")
            if system:
                restored.append((system, gained))
            else:
                logger.warning(f"Cannot restore {gained} merits: the rejected award had no system")
        return restored

    def reconcile_snapshot(self, entry: Dict[str, Any]) -> Tuple[int, List[Tuple[str, int]]]:
        """Fold a Powerplay snapshot (game load) into the baseline.

        Returns (delta to apply, merits to give back to a wrongly rejected award).
        The delta is always 0 on the first snapshot seen.
        """
        total = entry.get("Merits")
        if total is None:
            return 0, []
        self._check_power(entry.get("Power", ""))
        if self.baseline is None:
            self.baseline = total
            return 0, self._resolve_pending(total)
        restored = self._resolve_pending(total)
        delta = total - self.baseline - sum(m for _, m in restored)
        self.baseline = total
        if delta:
            logger.info(f"Server merit snapshot {total} disagrees with tracked {total - delta}: {delta:+}")
        self.last_event = None
        self.recent = []
        return delta, restored

    def merits_delta(self, entry: Dict[str, Any], system: Optional[str] = None) -> Tuple[int, List[Tuple[str, int]], int]:
        """Split a PowerplayMerits event into (uncredited, restored, credited).

        `uncredited` is what earlier events were given but the server never
        applied - it has to be taken back off whichever systems received it.
        `restored` is [(system, merits)] for an award this ledger rejected as a
        resend that the server turns out to have held after all.
        `credited` is what this event added and belongs to the current system.

        `system` is where a rejected award would have gone, so it can be given
        back to the right place if the rejection turns out to be wrong.

        TotalMerits is authoritative. If it has not moved, the server applied
        nothing and the event is ignored outright - Journal.2026-01-15T110022.01
        .log:2052 reports 118520 merits against a frozen total, so MeritsGained
        cannot be trusted to describe what happened. Once the total has moved,
        MeritsGained tells us how much of the move belongs to this event, which
        is what keeps a correction and a genuine award from cancelling out.
        """
        total = entry.get("TotalMerits")
        gained = entry.get("MeritsGained", 0)
        if total is None:
            return 0, [], gained
        power = entry.get("Power", "")
        self._check_power(power)

        # A verbatim resend is the one unambiguous duplicate: same award, same total
        if self.last_event == (gained, total):
            logger.warning(f"Duplicate PowerplayMerits ignored: {gained} merits, total {total}")
            return 0, [], 0

        # A large award repeated within the window advances TotalMerits by exactly
        # its own size, so nothing later in this method can tell it from a real one.
        # Reject it without touching the baseline: the next genuine event still
        # reconciles against the total the server actually holds.
        when = _parse_timestamp(entry.get("timestamp"))
        if self._is_large_resend(when, gained, power):
            logger.warning(f"Large PowerplayMerits resend ignored: {gained} merits repeated within {DUPE_WINDOW_SECONDS:.0f}s (total {total})")
            # Provisional: park it with the system it would have gone to, in case
            # the next event's base proves the server held it after all. Only
            # worth parking if the award would sit on top of what we already
            # track - a resend carrying a base below the baseline is one the
            # server demonstrably never applied.
            if self.baseline is None or total - gained >= self.baseline:
                self.pending.append([gained, total, system])
                del self.pending[:-PENDING_LIMIT]
            return 0, [], 0
        self.last_event = (gained, total)

        if self.baseline is None:
            self.baseline = total - gained

        # What the server believed the total was before this award
        claimed_base = total - gained

        if total == self.baseline:
            logger.warning(f"Server credited none of the reported {gained} merits (total still {total})")
            return 0, [], 0

        # Only awards at or above the threshold can ever match, so only they are
        # kept - otherwise a long trickle grows the window list without bound.
        # An award against a frozen total never gets here: the server applied
        # nothing, so a genuine repeat of it must not be rejected.
        if when is not None and gained >= DUPE_MIN_MERITS:
            self.recent.append((when, gained, power))

        restored = self._resolve_pending(claimed_base)
        uncredited = 0
        if claimed_base < self.baseline:
            uncredited = self.baseline - claimed_base
            logger.warning(f"Server never credited {uncredited} earlier merits (base {claimed_base} < tracked {self.baseline})")
            self.baseline = claimed_base

        credited = total - self.baseline - sum(m for _, m in restored)
        self.baseline = total
        if credited != gained:
            logger.warning(f"MeritsGained {gained} but server credited {credited} (total {total})")
        return uncredited, restored, credited

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
