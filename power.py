import json
import os
from config import config
from log import logger

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

    def _get_file_path(self):
        """Get the path to power.json file"""
        directory_name = os.path.basename(os.path.dirname(__file__))
        plugin_path = os.path.join(config.plugin_dir, directory_name)
        return os.path.join(plugin_path, "power.json")
    
    def dumpJson(self):
        """Save power data to JSON file"""
        file_path = self._get_file_path()
        with open(file_path, "w") as json_file:
            json.dump(self, json_file, indent=4, cls=PowerEncoder)

    def loadPower(self):
        """Load power data from JSON file"""
        file_path = self._get_file_path()
        if not os.path.exists(file_path):
            # Create new file with current data
            self.dumpJson()
            self.from_dict({})
        else:
            try:
                with open(file_path, "r") as json_file:
                    self.from_dict(json.load(json_file))
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in {file_path}, resetting to defaults")
                self.__init__() 

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