import json
from imports import logger
from power import PowerConflict, PowerConflictEntry
class StarSystem:
    def __init__(self, eventEntry=None, reported: bool = False):
        self.debug = False
        if eventEntry is None:
            self._init_defaults()
            return

        self.StarSystem = str(eventEntry.get("StarSystem", "Nomansland"))
        self.Merits = int(eventEntry.get("Merits", 0))
        self.Active = False
        self.PowerplayState = str(eventEntry.get("PowerplayState", "stateless"))
        self.ControllingPower = str(eventEntry.get("ControllingPower", "Mr.Nobody"))
        self.Powers = self._safe_list(eventEntry.get("Powers", []))
        self.Opposition = [p for p in self.Powers if p != self.ControllingPower]
        conflict_data = eventEntry.get("PowerplayConflictProgress", [])
        self.PowerplayConflictProgress = sorted(
            PowerConflict(conflict_data).entries, 
            key=lambda p: getattr(p, "progress", 0), 
            reverse=True
        )
        self.PowerplayStateControlProgress = float(eventEntry.get("PowerplayStateControlProgress", 0.0))
        self.PowerplayStateReinforcement = int(eventEntry.get("PowerplayStateReinforcement", 0))
        self.PowerplayStateUndermining = int(eventEntry.get("PowerplayStateUndermining", 0))
        self.reported = bool(reported)

    def _init_defaults(self):
        self.StarSystem = "Nomansland"
        self.Merits = 0
        self.Active = False
        self.PowerplayState = "stateless"
        self.ControllingPower = "Mr.Nobody"
        self.Powers = []
        self.Opposition = []
        self.PowerplayConflictProgress = []
        self.PowerplayStateControlProgress = 0.0
        self.PowerplayStateReinforcement = 0
        self.PowerplayStateUndermining = 0
        self.reported = False

    def _safe_list(self, val):
        if isinstance(val, list):
            return val
        return []

    def getPowerplayCycleNetValue(self):
        if self.PowerplayState in ['Stronghold', 'Fortified', 'Exploited']:
            if len(self.Powers) > 1:
                return [self.PowerplayStateReinforcement, self.PowerplayStateUndermining]
            return [self.PowerplayStateReinforcement, 0]
        if not self.PowerplayConflictProgress:
            return [0, 0]
        return [self.PowerplayConflictProgress[0].progress, 0, 0]

    def updateSystem(self, eventEntry: dict = {}):
        self.Active = True
        self.PowerplayState = str(eventEntry.get("PowerplayState", "stateless"))
        self.ControllingPower = str(eventEntry.get("ControllingPower", "Mr.Nobody"))
        self.Powers = self._safe_list(eventEntry.get("Powers", []))
        self.Opposition = [p for p in self.Powers if p != self.ControllingPower]
        conflict_data = eventEntry.get("PowerplayConflictProgress", [])
        self.PowerplayConflictProgress = sorted(
            PowerConflict(conflict_data).entries, 
            key=lambda p: getattr(p, "progress", 0), 
            reverse=True
        )
        self.PowerplayStateControlProgress = float(eventEntry.get("PowerplayStateControlProgress", 0.0))
        self.PowerplayStateReinforcement = int(eventEntry.get("PowerplayStateReinforcement", 0))
        self.PowerplayStateUndermining = int(eventEntry.get("PowerplayStateUndermining", 0))

    def addMerits(self, gained=0):
        self.Merits += int(gained)

    def setReported(self, value=False):
        self.reported = bool(value)

    def getSystemProgressNumber(self):
        if self.PowerplayState in ['Stronghold', 'Fortified', 'Exploited']:
            return self.PowerplayStateControlProgress * 100
        if not self.PowerplayConflictProgress:
            return 0
        return self.PowerplayConflictProgress[0].progress * 100

    def to_dict(self):
        return {
            "StarSystem": self.StarSystem,
            "Merits": self.Merits,
            "Active": self.Active,
            "PowerplayState": self.PowerplayState,
            "ControllingPower": self.ControllingPower,
            "Powers": self.Powers,
            "Opposition": self.Opposition,
            "PowerplayConflictProgress": [vars(p) for p in self.PowerplayConflictProgress],
            "PowerplayStateControlProgress": self.PowerplayStateControlProgress,
            "PowerplayStateReinforcement": self.PowerplayStateReinforcement,
            "PowerplayStateUndermining": self.PowerplayStateUndermining,
            "reported": self.reported
        }

    def from_dict(self, data: dict = {}):
        self.StarSystem = str(data.get("StarSystem", "Nomansland"))
        self.Merits = int(data.get("Merits", 0))
        self.Active = bool(data.get("Active", False))
        self.PowerplayState = str(data.get("PowerplayState", "stateless"))
        self.ControllingPower = str(data.get("ControllingPower", "Mr.Nobody"))
        self.Powers = self._safe_list(data.get("Powers", []))
        self.Opposition = self._safe_list(data.get("Opposition", []))
        conflict_data = data.get("PowerplayConflictProgress", [])
        self.PowerplayConflictProgress = sorted(
            PowerConflict(conflict_data).entries, 
            key=lambda p: getattr(p, "progress", 0), 
            reverse=True
        )
        self.PowerplayStateControlProgress = float(data.get("PowerplayStateControlProgress", 0.0))
        self.PowerplayStateReinforcement = int(data.get("PowerplayStateReinforcement", 0))
        self.PowerplayStateUndermining = int(data.get("PowerplayStateUndermining", 0))
        self.reported = bool(data.get("reported", False))

    def getPowerPlayCycleNetStatusText(self):
        if self.PowerplayStateReinforcement == 0 and self.PowerplayStateUndermining == 0:
            return "Neutral"
        total = self.PowerplayStateReinforcement + self.PowerplayStateUndermining
        if total == 0:
            return "Neutral"
        if self.PowerplayStateReinforcement > self.PowerplayStateUndermining:
            return f"NET +{(self.PowerplayStateReinforcement / total) * 100:.2f}%"
        return f"NET -{(self.PowerplayStateUndermining / total) * 100:.2f}%"

    def getSystemStateText(self):
        if not self.PowerplayState:
            return "NoState"
        if self.PowerplayState in ['Stronghold', 'Fortified', 'Exploited']:
            return self.PowerplayState
        if self.PowerplayState == 'Unoccupied':
            if not self.PowerplayConflictProgress:
                return 'Unoccupied'
            progress = self.PowerplayConflictProgress[0].progress * 100
            if progress < 30:
                return f"Unoccupied {progress} {self.PowerplayConflictProgress[0].power}"
            if progress < 100:
                return f"Contested {progress} {self.PowerplayConflictProgress[0].power}"
            return 'Controlled'
        return self.PowerplayState

    def getSystemStatePowerPlay(self, pledged):
        if self.PowerplayState in ['Stronghold', 'Fortified', 'Exploited']:
            if len(self.Powers) > 1:
                return [self.ControllingPower, next((p for p in self.Powers if p != pledged), "")]
            return [self.ControllingPower, ""]
        if self.PowerplayState == 'Unoccupied':
            if len(self.PowerplayConflictProgress) == 1:
                return [self.PowerplayConflictProgress[0].power, ""]
            if len(self.PowerplayConflictProgress) > 1:
                arr = [item.power for item in self.PowerplayConflictProgress if hasattr(item, 'power')]
                if len(arr) >= 2:
                    return [arr[0], arr[1]]
                if len(arr) == 1:
                    return [arr[0], ""]
            return ["NoPower", ""]
        return ["NoPower", ""]

    def getFromOldDict(self, name: str, data: dict = {}):
        self.StarSystem = str(name)
        self.Merits = int(data.get("sessionMerits", 0))
        self.PowerplayState = str(data.get("state", "stateless"))
        self.ControllingPower = str(data.get("power", "Mr.Nobody"))
        self.Powers = self._safe_list(data.get("powerCompetition", []))
        self.PowerplayConflictProgress = []
        self.PowerplayStateControlProgress = float(data.get("progress", 0.0))
        self.PowerplayStateReinforcement = int(data.get("statereinforcement", 0))
        self.PowerplayStateUndermining = int(data.get("stateundermining", 0))
        self.reported = bool(data.get("reported", False))

class PowerConflictEntry:
    def __init__(self, power, progress):
        self.power = str(power)
        self.progress = float(progress)

class PowerConflict:
    def __init__(self, data):
        self.entries = []
        if not data or not isinstance(data, list):
            return
        for item in data:
            if isinstance(item, dict):
                power = item.get("Power") or item.get("power")
                progress = item.get("ConflictProgress") or item.get("progress")
                if power is not None and progress is not None:
                    self.entries.append(PowerConflictEntry(power, progress))

class SystemEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, StarSystem):
            return o.__dict__
        return super().default(o)
