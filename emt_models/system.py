import json
from emt_core.logging import logger
from emt_core.storage import load_json, save_json, get_file_path

# PowerPlay CP thresholds for calculating progress percentages
STRONGHOLD_CP_THRESHOLD = 120000
FORTIFIED_CP_THRESHOLD = 120000
EXPLOITED_CP_THRESHOLD = 60000

# Max CP per system type used for decay calculation (EDIntel formula)
_MAX_CP = {
    'Stronghold': 1_000_000,
    'Fortified': 650_000,
    'Exploited': 350_000,
}

# Piecewise linear interpolation points: (progress_percent, decay_percent)
# Decay differs per system type. Source: EDIntel decay formula analysis.
_DECAY_POINTS = {
    'Exploited': [
        (0, 0.0), (25, 0.5), (26, 0.624), (27.5, 0.923), (28.5, 1.194),
        (29.5, 1.443), (31, 1.806), (33.5, 2.245), (36.5, 2.775), (39, 3.091),
        (42.5, 3.444), (47.5, 3.913), (55, 4.469), (65, 5.099), (75, 5.475),
        (85, 5.713), (95, 5.177), (125, 2.291),
    ],
    'Fortified': [
        (0, 0.0), (25, 0.4), (26, 0.541), (27.5, 1.472), (28.5, 2.128),
        (29.5, 2.672), (31, 3.557), (33.5, 4.634), (36.5, 6.061), (39, 6.874),
        (42.5, 7.834), (47.5, 9.072), (55, 9.473), (65, 12.358), (75, 11.881),
        (85, 8.382), (100, 12.356),
    ],
    'Stronghold': [
        (0, 0.0), (25, 0.8), (26, 1.036), (27.5, 2.288), (28.5, 3.099),
        (29.5, 3.761), (31, 4.705), (33.5, 6.145), (36.5, 7.524), (39, 8.716),
        (42.5, 9.872), (47.5, 10.609), (55, 13.200), (65, 14.788), (75, 16.311),
        (85, 17.094), (95, 16.117), (125, 11.419),
    ],
}


def _interpolate_decay(progress_pct: float, system_type: str) -> float:
    """Return decay percent via piecewise linear interpolation. Decay only above 25%."""
    points = _DECAY_POINTS.get(system_type)
    if not points or progress_pct <= 25.0:
        return 0.0
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        if x1 <= progress_pct <= x2:
            if x2 == x1:
                return y1
            return y1 + (y2 - y1) * (progress_pct - x1) / (x2 - x1)
    return points[-1][1]


def _calc_real_undermining(raw_um: int, raw_reinf: int, progress_pct: float, system_type: str) -> int:
    """Return real (decay-subtracted) undermining CP. Formula from EDIntel."""
    max_cp = _MAX_CP.get(system_type)
    if not max_cp or raw_um == 0:
        return raw_um
    current_cp = max_cp * (progress_pct / 100.0)
    last_cycle_cp = current_cp + raw_um - raw_reinf
    last_cycle_pct = (last_cycle_cp / max_cp) * 100.0
    decay_pct = _interpolate_decay(last_cycle_pct, system_type)
    decay_amount = last_cycle_cp * (decay_pct / 100.0)
    return max(0, int(raw_um - decay_amount))

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
            'RealUndermining': 0,
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
        self.RealUndermining = _calc_real_undermining(
            self.PowerplayStateUndermining,
            self.PowerplayStateReinforcement,
            self.getSystemProgressNumber(),
            self.PowerplayState,
        )

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
        """Parse security level from game formats like '$SYSTEM_SECURITY_low;' or '$galaxy_map_info_state_anarchy;'"""
        if not security_string:
            return None
        for prefix in ("$SYSTEM_SECURITY_", "$galaxy_map_info_state_"):
            if prefix in security_string:
                security = security_string.replace(prefix, "").replace(";", "").strip()
                return security.capitalize() if security else None
        # Already a plain string (e.g. loaded from saved data)
        if not security_string.startswith("$"):
            return security_string
        return None

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
        """Get reinforcement and real undermining values as list"""
        if self.PowerplayState in ['Stronghold', 'Fortified', 'Exploited']:
            undermining = self.RealUndermining if len(self.Powers) > 1 else 0
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
            "RealUndermining": self.RealUndermining,
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
        """Get formatted status text showing real undermining vs reinforcement"""
        reinf = self.PowerplayStateReinforcement
        real_um = self.RealUndermining
        decay = self.PowerplayStateUndermining - real_um
        if reinf == 0 and real_um == 0:
            return ""
        decay_str = f" ({decay:,} decay)" if decay > 0 else ""
        return f"UM: {real_um:,}{decay_str} | Reinf: {reinf:,}"

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
            'Controlled': 'Controlled',  # Acquisition completed (>100%)
            'Contested': 'Contested',   # Acquisition in progress (30-100%)
            'Unoccupied': 'Unoccupied',  # Acquisition in progress (<30%)
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