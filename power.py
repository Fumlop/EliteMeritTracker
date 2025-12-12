import json
from merit_log import logger
from storage import load_json, save_json

class PledgedPower:
    def __init__(self, eventEntry: dict = {}, commander: str = "Ganimed"):
        self.Power = str(eventEntry.get("Power", ""))
        self.Merits = int(eventEntry.get("Merits", 0))
        self.MeritsSession = int(eventEntry.get("MeritsSession", 0))
        self.Rank = str(eventEntry.get("Rank", ""))
        self.TimePledged = int(eventEntry.get("TimePledged", 0))
        self.Commander = commander
        self._update_time_pledged_str()

    def _update_time_pledged_str(self):
        """Convert TimePledged seconds to readable format"""
        seconds = self.TimePledged
        years, seconds = divmod(seconds, 31536000)
        days, seconds = divmod(seconds, 86400)
        hours, _ = divmod(seconds, 3600)
        self.TimePledgedStr = f"{years}y {days}d {hours}h"

    def from_dict(self, data: dict = {}):
        """Load power data from dictionary"""
        self.Power = str(data.get("Power") or data.get("PowerName", ""))
        self.Merits = int(data.get("Merits", 0))
        self.Rank = str(data.get("Rank", ""))
        self.TimePledged = int(data.get("TimePledged", 0))
        self.Commander = str(data.get("Commander", ""))
        self._update_time_pledged_str()

    def dumpJson(self):
        """Save power data to JSON file"""
        save_json("power.json", self, encoder=PowerEncoder)

    def loadPower(self):
        """Load power data from JSON file"""
        data = load_json("power.json")
        if data:
            self.from_dict(data)
        else:
            # Create new file with current data
            self.dumpJson()
            self.from_dict({}) 

class PowerEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, PledgedPower):
            return {
                "Power": o.Power,
                "Commander": o.Commander,
                "Merits": o.Merits,
                "MeritsSession": o.MeritsSession,
                "Rank": o.Rank,
                "TimePledged": o.TimePledged,
                "TimePledgedStr": o.TimePledgedStr,
            }
        return super().default(o)

pledgedPower = PledgedPower()