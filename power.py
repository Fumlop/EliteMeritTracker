import json
import os
from config import config
from log import logger, plugin_name

class PledgedPower:
    def __init__(self, eventEntry: dict = {}, reported: bool = False, commander: str = "Ganimed"):
        assert isinstance(eventEntry, dict), "eventEntry must be a dictionary"
        self.Power = str(eventEntry.get("Power", ""))
        self.Merits = int(eventEntry.get("Merits", 0))
        self.MeritsSession = int(eventEntry.get("MeritsSession", 0))
        self.Rank = str(eventEntry.get("Rank", ""))
        self.TimePledged = int(eventEntry.get("TimePledged", 0))
        self.TimePledgedStr = ""
        self.Commander = commander
        days, remainder = divmod(self.TimePledged, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)

    def from_dict(self, data: dict = {}):
        self.Power = str(data.get("Power") or data.get("PowerName", ""))
        self.Merits = int(data.get("Merits", 0))
        self.Rank = str(data.get("Rank", ""))
        self.TimePledged = int(data.get("TimePledged", 0))
        self.Commander = str(data.get("Commander", ""))

        seconds = self.TimePledged
        years, seconds = divmod(seconds, 31536000)   # 1 year = 31536000 seconds
        days, seconds = divmod(seconds, 86400)
        hours, _ = divmod(seconds, 3600)

        self.TimePledgedStr = f"{years}y {days}d {hours}h"
    
    def dumpJson(self):
        directory_name = os.path.basename(os.path.dirname(__file__))
        plugin_path = os.path.join(config.plugin_dir, directory_name)
        file_path = os.path.join(plugin_path, "power.json")
        with open(file_path, "w") as json_file:
            json.dump(self, json_file, indent=4, cls=PowerEncoder)

    def loadPower(self):
        directory_name = os.path.basename(os.path.dirname(__file__))
        logger.debug(f"Loading power data from {directory_name}")
        plugin_path = os.path.join(config.plugin_dir, directory_name)
        logger.debug(f"Loading power data from {plugin_path}")
        file_path = os.path.join(plugin_path, "power.json")
        if not os.path.exists(file_path):
            with open(file_path, "w") as json_file:
                pledgedPower.__init__()
                json.dump(pledgedPower, json_file, indent=4, cls=PowerEncoder)
            pledgedPower.from_dict({}) 
        else:
            try:
                with open(file_path, "r") as json_file:
                    pledgedPower.from_dict(json.load(json_file)) 
            except json.JSONDecodeError:
                pledgedPower.__init__() 

class PowerEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, PledgedPower):
            # Optional: Nur gewünschte Attribute serialisieren
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