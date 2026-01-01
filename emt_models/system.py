import json
from emt_core.logging import logger
from emt_core.storage import load_json, save_json, get_file_path

# PowerPlay CP thresholds for calculating progress percentages
STRONGHOLD_CP_THRESHOLD = 120000
FORTIFIED_CP_THRESHOLD = 120000
EXPLOITED_CP_THRESHOLD = 60000

class StarSystem:
    def __init__(self, eventEntry=None, commander: str = ""):
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
            'PowerplayState': "no PP connection",
            'ControllingPower': "no power",
            'Powers': [],
            'Opposition': [],
            'PowerplayConflictProgress': [],
            'PowerplayStateControlProgress': 0.0,
            'PowerplayStateReinforcement': 0,
            'PowerplayStateUndermining': 0,
            'reported': False,
            'PrimaryEconomy': None,
            'SecondaryEconomy': None,
            'SystemSecurity': None,
            'SystemAllegiance': None,
            'SystemGovernment': None,
            'Population': None
        }
        for key, value in defaults.items():
            setattr(self, key, value)

    def _update_from_entry(self, eventEntry):
        """Update system data from event entry"""
        self.PowerplayState = str(eventEntry.get("PowerplayState", "no PP connection"))
        self.ControllingPower = str(eventEntry.get("ControllingPower", "no power"))
        self.Powers = self._safe_list(eventEntry.get("Powers", []))

        conflict_data = eventEntry.get("PowerplayConflictProgress", [])
        self.PowerplayConflictProgress = self._process_conflict_data(conflict_data)

        # For Unoccupied systems with conflict progress, set ControllingPower from leading power
        if self.PowerplayState == "Unoccupied" and self.PowerplayConflictProgress and len(self.PowerplayConflictProgress) > 0:
            self.ControllingPower = self.PowerplayConflictProgress[0].power

        self.Opposition = [p for p in self.Powers if p != self.ControllingPower]
        self.PowerplayStateControlProgress = float(eventEntry.get("PowerplayStateControlProgress", 0.0))
        self.PowerplayStateReinforcement = int(eventEntry.get("PowerplayStateReinforcement", 0))
        self.PowerplayStateUndermining = int(eventEntry.get("PowerplayStateUndermining", 0))

        # Extract economy and security from FSDJump/Location events
        self.PrimaryEconomy = eventEntry.get("SystemEconomy_Localised")
        self.SecondaryEconomy = eventEntry.get("SystemSecondEconomy_Localised")

        # Extract security level (parse from "$SYSTEM_SECURITY_low;" format)
        system_security = eventEntry.get("SystemSecurity", "")
        if system_security:
            # Extract just the security level (e.g., "low", "medium", "high")
            self.SystemSecurity = self._parse_security_level(system_security)

        # Extract allegiance, government, and population
        self.SystemAllegiance = eventEntry.get("SystemAllegiance")
        self.SystemGovernment = eventEntry.get("SystemGovernment_Localised")
        self.Population = eventEntry.get("Population")

    def _parse_security_level(self, security_string):
        """Parse security level from game format like '$SYSTEM_SECURITY_low;'"""
        if not security_string:
            return None
        # Remove prefix and suffix, capitalize first letter
        security = security_string.replace("$SYSTEM_SECURITY_", "").replace(";", "").strip()
        return security.capitalize() if security else None

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
            # Convert decimal to percentage
            return [self.PowerplayConflictProgress[0].progress * 100, 0]
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
        if self.PowerplayState == 'Stronghold':
            # If value is already a decimal percentage (0 < x <= 1), convert to percentage
            if -10 < self.PowerplayStateControlProgress <= 10:
                return self.PowerplayStateControlProgress * 100
            return (self.PowerplayStateControlProgress / STRONGHOLD_CP_THRESHOLD) * 100
        elif self.PowerplayState == 'Fortified':
            # If value is already a decimal percentage (0 < x <= 1), convert to percentage
            if -10 < self.PowerplayStateControlProgress <= 10:
                return self.PowerplayStateControlProgress * 100
            return (self.PowerplayStateControlProgress / FORTIFIED_CP_THRESHOLD) * 100
        elif self.PowerplayState == 'Exploited':
            # If value is already a decimal percentage (0 < x <= 1), convert to percentage
            if -10 < self.PowerplayStateControlProgress <= 10:
                return self.PowerplayStateControlProgress * 100
            return (self.PowerplayStateControlProgress / EXPLOITED_CP_THRESHOLD) * 100

        if self.PowerplayConflictProgress:
            # Conflict progress is provided as decimal (0.0-1.0), convert to percentage
            return self.PowerplayConflictProgress[0].progress * 100
        return 0

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        result = {
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
        # Include economy, security, allegiance, government, and population if they exist
        if hasattr(self, 'PrimaryEconomy') and self.PrimaryEconomy:
            result["PrimaryEconomy"] = self.PrimaryEconomy
        if hasattr(self, 'SecondaryEconomy') and self.SecondaryEconomy:
            result["SecondaryEconomy"] = self.SecondaryEconomy
        if hasattr(self, 'SystemSecurity') and self.SystemSecurity:
            result["SystemSecurity"] = self.SystemSecurity
        if hasattr(self, 'SystemAllegiance') and self.SystemAllegiance:
            result["SystemAllegiance"] = self.SystemAllegiance
        if hasattr(self, 'SystemGovernment') and self.SystemGovernment:
            result["SystemGovernment"] = self.SystemGovernment
        if hasattr(self, 'Population') and self.Population:
            result["Population"] = self.Population
        return result

    def from_dict(self, data: dict = {}):
        """Load from dictionary"""
        self.StarSystem = str(data.get("StarSystem", "unknown system"))
        self.Merits = int(data.get("Merits", 0))
        self.Active = bool(data.get("Active", False))
        self.reported = bool(data.get("reported", False))
        self._update_from_entry(data)
        self.Opposition = self._safe_list(data.get("Opposition", []))
        # Load economy, security, allegiance, government, and population if they were saved
        self.PrimaryEconomy = data.get("PrimaryEconomy", None)
        self.SecondaryEconomy = data.get("SecondaryEconomy", None)
        self.SystemSecurity = data.get("SystemSecurity", None)
        self.SystemAllegiance = data.get("SystemAllegiance", None)
        self.SystemGovernment = data.get("SystemGovernment", None)
        self.Population = data.get("Population", None)

    def getPowerPlayCycleNetStatusText(self):
        """Get formatted net status text showing difference between reinforcement and undermining"""
        if self.PowerplayStateReinforcement == 0 and self.PowerplayStateUndermining == 0:
            return "Neutral"

        total = self.PowerplayStateReinforcement + self.PowerplayStateUndermining
        if total == 0:
            return "Neutral"

        # NET is the difference between reinforcement and undermining as percentage of total
        net_difference = self.PowerplayStateReinforcement - self.PowerplayStateUndermining
        percentage = (net_difference / total) * 100

        if net_difference > 0:
            return f"NET +{percentage:.2f}%"
        elif net_difference < 0:
            return f"NET {percentage:.2f}%"
        else:
            return "NET 0%"

    def getSystemStateText(self):
        """Get readable system state"""
        if not self.PowerplayState:
            return "NoState"

        if self.PowerplayState in ['Stronghold', 'Fortified', 'Exploited']:
            return self.PowerplayState

        if self.PowerplayState == 'Unoccupied':
            if not self.PowerplayConflictProgress:
                return 'Unoccupied'

            # Convert decimal (0.0-1.0) to percentage for threshold comparison
            progress = self.PowerplayConflictProgress[0].progress * 100
            if progress > 100.00:
                return 'Controlled'
            elif progress >= 30.00:
                return 'Contested'
            else:
                # Below contested threshold, still unoccupied
                return 'Unoccupied'

        return self.PowerplayState

    def getSystemStatusShort(self):
        """Get short abbreviation for system status (for @SystemStatus variable)"""
        state = self.getSystemStateText()

        # Map full state names to short abbreviations
        status_map = {
            'Stronghold': 'Stronghold',
            'Fortified': 'Fort',
            'Exploited': 'Exploited',
            'Controlled': 'ACQ',  # Acquisition completed (>100%)
            'Contested': 'ACQ',   # Acquisition in progress (30-100%)
            'Unoccupied': 'ACQ',  # Acquisition in progress (<30%)
            'NoState': 'None'
        }

        return status_map.get(state, state)

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


def dumpSystems(create_backup=False):
    """Save systems to JSON file

    Args:
        create_backup: If True, creates .backup file (only during updates)
    """
    filtered_systems = {
        name: data.to_dict()
        for name, data in systems.items()
        if (not data.reported and data.Merits > 0) or data.Active
    }
    save_json("systems.json", filtered_systems, encoder=SystemEncoder, create_backup=create_backup)


def loadSystems():
    """Load systems from JSON file"""
    data = load_json("systems.json")
    if data:
        for name, system_data in data.items():
            if isinstance(system_data, dict):
                system = StarSystem()
                system.from_dict(system_data)
                systems[name] = system


systems = {} 