from imports import *

class StarSystem:
    def __init__(self, eventEntry:dict = {}, reported: bool = False):
        self.debug = False
        
        self.StarSystem: str = eventEntry.get("StarSystem", "Nomansland")
        self.Merits: int = 0
        self.Active: bool = False
        self.PowerplayState: str = eventEntry.get("PowerplayState", "stateless")
        self.ControllingPower: str = eventEntry.get("ControllingPower", "Mr.Nobody")
        self.Powers: list[str] = eventEntry.get("Powers", [])
        self.Opposition: list[str] = [p for p in self.Powers if p != self.ControllingPower]
        self.PowerplayConflictProgress: list[PowerConflictEntry] = sorted(
            PowerConflict(eventEntry.get("PowerplayConflictProgress", [])).entries,
            key=lambda p: p.progress,
            reverse=True  # absteigend sortiert
        )
        self.PowerplayStateControlProgress: float = eventEntry.get("PowerplayStateControlProgress", 0.0)
        self.PowerplayStateReinforcement: int = eventEntry.get("PowerplayStateReinforcement", 0)
        self.PowerplayStateUndermining: int = eventEntry.get("PowerplayStateUndermining", 0)
        self.reported: bool = reported

    def getPowerplayCycleNetValue(self):
        if self.PowerplayState in ['Stronghold', 'Fortified', 'Exploited']:
            if len(self.Powers) > 1:
                return [self.PowerplayStateReinforcement, self.PowerplayStateUndermining]
            else:
                return [self.PowerplayStateReinforcement, 0]
        else:
            if not self.PowerplayConflictProgress:
                return [0, 0]
            return [self.PowerplayConflictProgress[0].progress, 0, 0]
        
    def updateSystem(self, eventEntry:dict = {}):
        self.Active: bool = True
        self.PowerplayState: str = eventEntry.get("PowerplayState", "stateless")
        self.ControllingPower: str = eventEntry.get("ControllingPower", "Mr.Nobody")
        self.Powers: list[str] = eventEntry.get("Powers", [])
        self.Opposition: list[str] = [p for p in self.Powers if p != self.ControllingPower]
        self.PowerplayConflictProgress: list[PowerConflictEntry] = sorted(
            PowerConflict(eventEntry.get("PowerplayConflictProgress", [])).entries,
            key=lambda p: p.progress,
            reverse=True  # absteigend sortiert
        )
        self.PowerplayStateControlProgress: float = eventEntry.get("PowerplayStateControlProgress", 0.0)
        self.PowerplayStateReinforcement: int = eventEntry.get("PowerplayStateReinforcement", 0)
        self.PowerplayStateUndermining: int = eventEntry.get("PowerplayStateUndermining", 0)
    
    def addMerits(self, gained=0):
        self.Merits += gained
        
    def setReported(self, value=False):
        self.reported = value
        
    def getSystemProgressNumber(self):
        #logger.debug(f"get_system_state_power.{system_state}")
        if self.PowerplayState in ['Stronghold', 'Fortified', 'Exploited']:
            return  self.PowerplayStateControlProgress * 100
        if self.PowerplayConflictProgress is None or not self.PowerplayConflictProgress:
            return 0
        return self.PowerplayConflictProgress[0].progress*100

    def to_dict(self):
        return {
            "StarSystem": self.StarSystem,
            "Merits": self.Merits,
            "Active": self.Active,
            "PowerplayState": self.PowerplayState,
            "ControllingPower": self.ControllingPower,
            "Powers": self.Powers,
            "Opposition": self.Opposition,
            "PowerplayConflictProgress":  [vars(p) for p in self.PowerplayConflictProgress],
            "PowerplayStateControlProgress": self.PowerplayStateControlProgress,
            "PowerplayStateReinforcement": self.PowerplayStateReinforcement,
            "PowerplayStateUndermining": self.PowerplayStateUndermining,
            "reported": self.reported
        }
    
    def from_dict(self, data:dict={}):
        self.StarSystem: str = data.get("StarSystem", None)
        self.Merits: int = data.get("Merits", None)
        self.Active: bool = data.get("Active", False)
        self.PowerplayState: str = data.get("PowerplayState", "stateless")
        self.ControllingPower: str = data.get("ControllingPower", "Mr.Nobody")
        self.Powers: list[str] = data.get("Powers", [])
        self.Opposition: list[str] = data.get("Opposition", [])
        self.PowerplayConflictProgress: list[PowerConflictEntry] = sorted(
            PowerConflict(data.get("PowerplayConflictProgress",[])).entries,
            key=lambda p: p.progress,
            reverse=True  
        )
        self.PowerplayStateControlProgress: float = data.get("PowerplayStateControlProgress", 0.0)
        self.PowerplayStateReinforcement: int = data.get("PowerplayStateReinforcement", 0)
        self.PowerplayStateUndermining: int = data.get("PowerplayStateUndermining", 0)
        self.reported: bool = data.get("reported",False)
        
    def getPowerPlayCycleNetStatusText(self):
        if self.PowerplayStateReinforcement == 0 and self.PowerplayStateUndermining == 0:
            return "Neutral"  # If both are 0, show neutral
        total = self.PowerplayStateReinforcement + self.PowerplayStateUndermining  # Total value
        # Calculate actual percentage share
        reinforcement_percentage = (self.PowerplayStateReinforcement / total) * 100
        undermining_percentage = (self.PowerplayStateUndermining / total) * 100

        if self.PowerplayStateReinforcement > self.PowerplayStateUndermining:
            return f"NET +{reinforcement_percentage:.2f}%"
        else:
            return f"NET -{undermining_percentage:.2f}%"

    def getSystemStateText(self):
        if not self.PowerplayState:
            return "NoState"

        if self.PowerplayState in ['Stronghold', 'Fortified', 'Exploited']:
            return self.PowerplayState

        if self.PowerplayState == 'Unoccupied':
            logger.debug(self.PowerplayConflictProgress)
            if not self.PowerplayConflictProgress:
                return 'Unoccupied'  # Kein Konflikt erkennbar

            progress = self.PowerplayConflictProgress[0].progress * 100
            if progress < 30:
                return f"Unoccupied {progress} {self.PowerplayConflictProgress[0].power}"
            if progress < 100:
                return f"Contested {progress} {self.PowerplayConflictProgress[0].power}"
            return 'Controlled'

        return self.PowerplayState  # Fallback
    
    def getSystemStatePowerPlay(self, pledged):
        # Fälle mit klarer Kontrolle
        if self.PowerplayState in ['Stronghold', 'Fortified', 'Exploited']:
            if len(self.Powers) > 1:
                # Zwei Mächte im System – Opposition ermitteln
                return [self.ControllingPower, next((p for p in self.Powers if p != pledged), "")]
            else:
                return [self.ControllingPower, ""]

        # Konfliktzone – unbesetzt
        if self.PowerplayState == 'Unoccupied':
            if len(self.PowerplayConflictProgress) == 1:
                return [self.PowerplayConflictProgress[0].power, ""]
            elif len(self.PowerplayConflictProgress) > 1:
                arr = [item.power for item in self.PowerplayConflictProgress if item.power]
                if len(arr) >= 2:
                    return [arr[0], arr[1]]
                elif len(arr) == 1:
                    return [arr[0], ""]
            return ["NoPower", ""]

        # Kein Powerplay-Status
        return ["NoPower", ""]

    
    def getFromOldDict(self, name:str, data:dict={}):
        self.StarSystem: str = name
        self.Merits = data.get("sessionMerits",0)
        self.PowerplayState: str = data.get("state", "stateless")
        self.ControllingPower: str = data.get("power", "Mr.Nobody")
        self.Powers: list[str] = data.get("powerCompetition", [])
        self.PowerplayConflictProgress = []
        self.PowerplayStateControlProgress: float = data.get("progress", 0.0)
        self.PowerplayStateReinforcement: int = data.get("statereinforcement", 0)
        self.PowerplayStateUndermining: int = data.get("stateundermining", 0)
        self.reported: bool = data.get("reported",False)
        
    def debug(self, what):
        if self.debug == True:
            logger.debug(what)
            
        
class PowerConflictEntry:
    def __init__(self, power: str, progress: float):
        self.power = power
        self.progress = progress

class PowerConflict:
    def __init__(self, data):
        self.entries: list[PowerConflictEntry] = []
        logger.debug(data)
        
        if len(data) == 0:
            return

        for item in data:
            if isinstance(item, dict) and "Power" in item and "ConflictProgress" in item:
                self.entries.append(PowerConflictEntry(item["Power"], item["ConflictProgress"]))
        
class SystemEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, StarSystem):
            return o.__dict__
        return super().default(o)
    