import json
import os
from merit_log import logger
from system import StarSystem
from ppcargo import Cargo

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
    try:
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        salvage_path = os.path.join(plugin_dir, "salvage.json")
        
        data = {name: salvage.to_dict() for name, salvage in salvageInventory.items()}
        
        with open(salvage_path, "w") as f:
            json.dump(data, f, indent=4)
            
    except Exception as e:
        logger.error(f"Failed to save salvage inventory: {e}")

def load_salvage():
    try:
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        salvage_path = os.path.join(plugin_dir, "salvage.json")
        
        if not os.path.exists(salvage_path):
            #logger.debug("No salvage.json found, starting with empty inventory")
            return
            
        with open(salvage_path, "r") as f:
            data = json.load(f)
            #logger.debug(f"Loading salvage.json content: {json.dumps(data, indent=4)}")
            
        for system_name, salvage_data in data.items():
            salvageInventory[system_name] = Salvage.from_dict(salvage_data)
            #logger.debug(f"Loaded salvage for system {system_name}: {json.dumps(salvage_data, indent=4)}")
            
        #logger.debug(f"Loaded salvage inventory for {len(salvageInventory)} systems")    
    except Exception as e:
        logger.error(f"Failed to load salvage inventory: {e}", exc_info=True)

# Global inventory of all salvage by system
salvageInventory = {}
