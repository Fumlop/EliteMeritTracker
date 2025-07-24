import json
import os
from log import logger

class StarSystem:
    def __init__(self, eventEntry=None, commander: str = "Ganimed"):
        if eventEntry is None:
            self._init_defaults()
            return
            
        self.StarSystem = str(eventEntry.get("StarSystem", "unknown system"))
        self.idSystem = f"{self.StarSystem}_{commander}"
        self.Merits = int(eventEntry.get("Merits", 0))
        self.Active = False
        self.reported = False
        self._update_from_entry(eventEntry)

    def _init_defaults(self):
        """Initialize with default values"""
        defaults = {
            'StarSystem': "unknown system",
            'Merits': 0,
            'Active': False,
            'PowerplayState': "stateless",
            'ControllingPower': "no controlling power",
            'Powers': [],
            'Opposition': [],
            'PowerplayConflictProgress': [],
            'PowerplayStateControlProgress': 0.0,
            'PowerplayStateReinforcement': 0,
            'PowerplayStateUndermining': 0,
            'reported': False
        }
        for key, value in defaults.items():
            setattr(self, key, value)

    def _update_from_entry(self, eventEntry):
        """Update system data from event entry"""
        self.PowerplayState = str(eventEntry.get("PowerplayState", "stateless"))
        self.ControllingPower = str(eventEntry.get("ControllingPower", "no controlling power"))
        self.Powers = self._safe_list(eventEntry.get("Powers", []))
        self.Opposition = [p for p in self.Powers if p != self.ControllingPower]
        
        conflict_data = eventEntry.get("PowerplayConflictProgress", [])
        self.PowerplayConflictProgress = self._process_conflict_data(conflict_data)
        self.PowerplayStateControlProgress = float(eventEntry.get("PowerplayStateControlProgress", 0.0))
        self.PowerplayStateReinforcement = int(eventEntry.get("PowerplayStateReinforcement", 0))
        self.PowerplayStateUndermining = int(eventEntry.get("PowerplayStateUndermining", 0))

    def _process_conflict_data(self, conflict_data):
        """Process and sort conflict progress data"""
        return sorted(
            PowerConflict(conflict_data).entries,
            key=lambda p: getattr(p, "progress", 0),
            reverse=True
        )

    def _safe_list(self, val):
        """Ensure value is a list"""
        return val if isinstance(val, list) else []

    def getPowerplayCycleNetValue(self):
        """Get reinforcement and undermining values as list"""
        if self.PowerplayState in ['Stronghold', 'Fortified', 'Exploited']:
            undermining = self.PowerplayStateUndermining if len(self.Powers) > 1 else 0
            return [self.PowerplayStateReinforcement, undermining]
        
        if self.PowerplayConflictProgress:
            return [self.PowerplayConflictProgress[0].progress, 0]
        return [0, 0]

    def updateSystem(self, eventEntry: dict = {}):
        """Update system with new event data"""
        self.Active = True
        self._update_from_entry(eventEntry)

    def addMerits(self, gained=0):
        """Add merits to current total"""
        self.Merits += int(gained)

    def setReported(self, value=False):
        """Set reported status"""
        self.reported = bool(value)

    def getSystemProgressNumber(self):
        """Get system progress as percentage"""
        if self.PowerplayState in ['Stronghold', 'Fortified', 'Exploited']:
            return self.PowerplayStateControlProgress * 100
        
        if self.PowerplayConflictProgress:
            return self.PowerplayConflictProgress[0].progress * 100
        return 0

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
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
        """Load from dictionary"""
        self.StarSystem = str(data.get("StarSystem", "unknown system"))
        self.Merits = int(data.get("Merits", 0))
        self.Active = bool(data.get("Active", False))
        self.reported = bool(data.get("reported", False))
        self._update_from_entry(data)
        self.Opposition = self._safe_list(data.get("Opposition", []))

    def getPowerPlayCycleNetStatusText(self):
        """Get formatted net status text"""
        if self.PowerplayStateReinforcement == 0 and self.PowerplayStateUndermining == 0:
            return "Neutral"
            
        total = self.PowerplayStateReinforcement + self.PowerplayStateUndermining
        if total == 0:
            return "Neutral"
            
        if self.PowerplayStateReinforcement > self.PowerplayStateUndermining:
            percentage = (self.PowerplayStateReinforcement / total) * 100
            return f"NET +{percentage:.2f}%"
        else:
            percentage = (self.PowerplayStateUndermining / total) * 100
            return f"NET -{percentage:.2f}%"

    def getSystemStateText(self):
        """Get readable system state"""
        if not self.PowerplayState:
            return "NoState"
            
        if self.PowerplayState in ['Stronghold', 'Fortified', 'Exploited']:
            return self.PowerplayState
            
        if self.PowerplayState == 'Unoccupied':
            if not self.PowerplayConflictProgress:
                return 'Unoccupied'
                
            progress = self.PowerplayConflictProgress[0].progress * 100
            if progress > 100.00:
                return 'Controlled'
            elif progress < 30.00 and progress > 0.00:
                return 'Exploited'
            else:
                return 'Contested'
                
        return self.PowerplayState

    def getSystemStatePowerPlay(self, pledged):
        """Get powerplay state powers"""
        if self.PowerplayState in ['Stronghold', 'Fortified', 'Exploited']:
            opposition = next((p for p in self.Powers if p != pledged), "") if len(self.Powers) > 1 else ""
            return [self.ControllingPower, opposition]
            
        if self.PowerplayState == 'Unoccupied':
            if not self.PowerplayConflictProgress:
                return ["NoPower", ""]
                
            if len(self.PowerplayConflictProgress) == 1:
                return [self.PowerplayConflictProgress[0].power, ""]
                
            if len(self.PowerplayConflictProgress) > 1:
                arr = [item.power for item in self.PowerplayConflictProgress if hasattr(item, 'power')]
                if len(arr) >= 2:
                    return [arr[0], arr[1]]
                elif len(arr) == 1:
                    return [arr[0], ""]
                    
        return ["NoPower", ""]


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
        if isinstance(o, (StarSystem, PowerConflictEntry)):
            return o.__dict__
        return super().default(o)

def _get_systems_path():
    """Get path to systems.json file"""
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(plugin_dir, "systems.json")


def dumpSystems():
    """Save systems to JSON file"""
    systems_path = _get_systems_path()
    
    filtered_systems = {
        name: data.to_dict()
        for name, data in systems.items()
        if (not data.reported and data.Merits > 0) or data.Active
    }
    
    try:
        with open(systems_path, "w") as json_file:
            json.dump(filtered_systems, json_file, cls=SystemEncoder, indent=4)
    except Exception as e:
        logger.error(f"Failed to save systems: {e}")


def loadSystems():
    """Load systems from JSON file"""
    systems_path = _get_systems_path()
    
    if not os.path.exists(systems_path):
        return
        
    try:
        with open(systems_path, "r") as json_file:
            tmp = json.load(json_file)
            for name, system_data in tmp.items():
                if isinstance(system_data, dict):
                    system = StarSystem()
                    system.from_dict(system_data)
                    systems[name] = system
    except json.JSONDecodeError:
        logger.error("Failed to load systems.json, using empty systems data.")
        systems.clear()


systems = {} 