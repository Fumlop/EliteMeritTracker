"""
Builds Elite Dangerous journal files for merit-tracking tests.

The builder keeps the real server-side merit total alongside what it writes, so
each scenario knows its own ground truth by construction:

    real(n)     the server credits n merits    -> TotalMerits advances
    phantom(n)  the game reports n merits the server drops. TotalMerits is the
                stale server total plus n, which is what the game actually
                writes (Journal.2026-08-27T185156.01.log:798).
    resend()    the previous line again, byte for byte
"""
import json
from datetime import datetime, timedelta

POWER = "Felicia Winters"


class JournalBuilder:
    def __init__(self, start_total: int = 1_000_000, start: str = "2026-08-28T12:00:00Z"):
        self.server_total = start_total
        self.clock = datetime.fromisoformat(start.replace("Z", "+00:00"))
        self.lines = []
        self.last = None
        self.system = None
        self.earned = {}          # system -> merits the server actually credited

    def _stamp(self, seconds=3):
        self.clock += timedelta(seconds=seconds)
        return self.clock.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _emit(self, event, seconds=3, **fields):
        entry = {"timestamp": self._stamp(seconds), "event": event}
        entry.update(fields)
        self.lines.append(entry)
        return entry

    # --- movement -------------------------------------------------------
    def jump(self, system, seconds=30):
        self.system = system
        self.earned.setdefault(system, 0)
        return self._emit("FSDJump", seconds, StarSystem=system, SystemAddress=1, StarPos=[0, 0, 0],
                          Powers=[POWER], PowerplayState="Exploited")

    def dock(self, system=None, seconds=30):
        self.system = system or self.system
        self.earned.setdefault(self.system, 0)
        return self._emit("Docked", seconds, StarSystem=self.system, StationName="Test", MarketID=1)

    # --- powerplay ------------------------------------------------------
    def load_game(self, seconds=60):
        """Game start: Location plus the authoritative Powerplay snapshot."""
        self._emit("Location", seconds, StarSystem=self.system or "Origin", Docked=True,
                   StationName="Test", MarketID=1, Powers=[POWER], PowerplayState="Exploited")
        self.last = None
        return self._emit("Powerplay", 0, Power=POWER, Rank=100,
                          Merits=self.server_total, TimePledged=1000)

    def real(self, merits, seconds=3):
        self.server_total += merits
        self.earned[self.system] = self.earned.get(self.system, 0) + merits
        self.last = self._emit("PowerplayMerits", seconds, Power=POWER,
                               MeritsGained=merits, TotalMerits=self.server_total)
        return self.last

    def phantom(self, merits, seconds=3):
        """Reported to the player, never applied by the server."""
        self.last = self._emit("PowerplayMerits", seconds, Power=POWER,
                               MeritsGained=merits, TotalMerits=self.server_total + merits)
        return self.last

    def resend(self, seconds=1):
        assert self.last is not None, "nothing to resend"
        copy = dict(self.last)
        copy["timestamp"] = self._stamp(seconds)
        self.lines.append(copy)
        return copy

    def scan(self, seconds=5):
        """Unrelated journal traffic between merit events."""
        return self._emit("Scan", seconds, BodyName="Test A", ScanType="AutoScan")

    # --- output ---------------------------------------------------------
    def write(self, path):
        with open(path, "w", encoding="utf-8") as fh:
            for entry in self.lines:
                fh.write(json.dumps(entry) + "\n")
        return path
