import json
from imports import logger


class PledgedPower:
    def __init__(self, eventEntry: dict = {}, reported: bool = False):
        self.Power = str(eventEntry.get("Power", ""))
        self.Merits = int(eventEntry.get("Merits", 0))
        self.MeritsSession = int(eventEntry.get("MeritsSession", 0))
        self.Rank = str(eventEntry.get("Rank", ""))
        self.TimePledged = int(eventEntry.get("TimePledged", 0))
        days, remainder = divmod(self.TimePledged, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        self.TimePledgedStr = f"{days}d {hours}h {minutes}m"

    def from_dict(self, data: dict = {}):
        self.Power = str(data.get("Power") or data.get("PowerName", ""))
        self.Merits = int(data.get("Merits", 0))
        self.Rank = str(data.get("Rank", ""))
        self.TimePledged = int(data.get("TimePledged", 0))

        seconds = self.TimePledged
        years, seconds = divmod(seconds, 31536000)   # 1 year = 31536000 seconds
        days, seconds = divmod(seconds, 86400)
        hours, _ = divmod(seconds, 3600)

        self.TimePledgedStr = f"{years}y {days}d {hours}h"

class PowerEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, PledgedPower):
            # Optional: Nur gewünschte Attribute serialisieren
            return {
                "Power": o.Power,
                "Merits": o.Merits,
                "MeritsSession": o.MeritsSession,
                "Rank": o.Rank,
                "TimePledged": o.TimePledged,
                "TimePledgedStr": o.TimePledgedStr,
            }
        return super().default(o)
