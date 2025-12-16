from core.logging import logger
from core.storage import load_json, save_json
from .system import StarSystem
from .ppcargo import Cargo

# Valid cargo types that can be salvaged
VALID_POWERPLAY_SALVAGE_TYPES = {
    "usscargoblackbox": "Black Box",
    "wreckagecomponents": "Wreckage Components"
}

class Salvage:
    def __init__(self, system_name: str):
        self.system_name = system_name
        self.inventory = {}  # Dict[str, Cargo]

    def add_cargo(self, cargo_name: str, count: int = 1):
        cargo_name_lower = cargo_name.lower()
        if cargo_name_lower not in VALID_POWERPLAY_SALVAGE_TYPES:
            logger.error(f"Invalid salvage type: {cargo_name}")
            return
        if cargo_name_lower not in self.inventory:
            self.inventory[cargo_name_lower] = Cargo(cargo_name_lower)
        self.inventory[cargo_name_lower].add(count)
        
        # Log significant cargo collections
        total_count = self.inventory[cargo_name_lower].count
        if total_count >= 50:
            logger.info(f"Large salvage collection in {self.system_name}: {total_count}x {cargo_name}")
    
    def has_cargo(self, cargo_name: str) -> bool:
        cargo_name_lower = cargo_name.lower()
        return cargo_name_lower in self.inventory and self.inventory[cargo_name_lower].count > 0
        
    def remove_cargo(self, cargo_name: str, count: int = 1) -> int:
        cargo_name_lower = cargo_name.lower()
        if cargo_name_lower not in VALID_POWERPLAY_SALVAGE_TYPES:
            logger.error(f"Invalid salvage type: {cargo_name}")
            return 0
        if cargo_name_lower in self.inventory:
            actual_count = min(count, self.inventory[cargo_name_lower].count)
            self.inventory[cargo_name_lower].remove(actual_count)
            if self.inventory[cargo_name_lower].count <= 0:
                del self.inventory[cargo_name_lower]
            return actual_count
        return 0
    
    def to_dict(self):
        return {
            "system_name": self.system_name,
            "inventory": {name: cargo.to_dict() for name, cargo in self.inventory.items()}
        }
    
    @staticmethod
    def from_dict(data: dict):
        salvage = Salvage(data.get("system_name", "Unknown"))
        for name, cargo_data in data.get("inventory", {}).items():
            salvage.inventory[name] = Cargo.from_dict(cargo_data)
        return salvage

    @staticmethod
    def process_collect_cargo(event_entry: dict, star_system: StarSystem):
        if event_entry.get('event') != 'CollectCargo':
            logger.error("Not a CollectCargo event")
            return
            
        system_name = star_system.StarSystem
        cargo_type = event_entry.get("Type", "Unknown")
        cargo_count = event_entry.get("Count", 1)
        
        if system_name not in salvageInventory:
            salvageInventory[system_name] = Salvage(system_name)
            
        salvageInventory[system_name].add_cargo(cargo_type, cargo_count)
        logger.debug(f"Added {cargo_count} {cargo_type} to {system_name}")

def save_salvage():
    """Save salvage inventory to JSON file"""
    data = {name: salvage.to_dict() for name, salvage in salvageInventory.items()}
    save_json("salvage.json", data)


def load_salvage():
    """Load salvage inventory from JSON file"""
    data = load_json("salvage.json")
    if data:
        for system_name, salvage_data in data.items():
            salvageInventory[system_name] = Salvage.from_dict(salvage_data)

# Global inventory of all salvage by system
salvageInventory = {}
