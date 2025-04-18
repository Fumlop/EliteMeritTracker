from imports import *

class PledgedPower:
    def __init__(self, eventEntry:dict = {}, reported: bool = False):
        self.Power: str = eventEntry.get("Power","")
        self.Merits: int = eventEntry.get("Merits",0)
        self.MeritsSession: int = eventEntry.get("MeritsSession",0)
        self.Rank: str = eventEntry.get("Rank","")
        self.TimePledged: int = eventEntry.get("TimePledged",0)
        seconds = eventEntry.get("TimePledged", 0)
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        self.TimePledgedStr: str = f"{days}d {hours}h {minutes}m"

    def to_dict(self):
        return {
            "Power": self.Power,
            "Merits": self.Merits,
            "Rank": self.Rank,
            "TimePledged": self.TimePledged
        }
    
    def from_dict(self, data:dict={}):
        self.Power = data.get("Power") or data.get("PowerName","")
        self.Merits = data.get("Merits",0)
        self.Rank = data.get("Rank","")
        self.TimePledged = data.get("TimePledged","")
    
