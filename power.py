from imports import *

class PledgedPower:
    def __init__(self, eventEntry:dict = {}, reported: bool = False):
        self.Power: str = eventEntry.get("Power","")
        self.Merits: int = eventEntry.get("Merits",0)
        self.MeritsSession: int = eventEntry.get("MeritsSession",0)
        self.Rank: str = eventEntry.get("Rank","")

    def to_dict(self):
        return {
            "Power": self.Power,
            "Merits": self.Merits,
            "Rank": self.Rank
        }
    
    def from_dict(self, data:dict={}):
        self.Power = data.get("Power") or data.get("PowerName","")
        self.Merits = data.get("Merits",0)
        self.Rank = data.get("Rank","")
    
