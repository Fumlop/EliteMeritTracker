from emt_core.logging import logger
from emt_core import database
from .system import StarSystem
from .ppcargo import Cargo

# Valid cargo types that can be salvaged (including PowerPlay items)
VALID_POWERPLAY_SALVAGE_TYPES = {
    "usscargoblackbox": "Black Box",
    "wreckagecomponents": "Wreckage Components",
    # PowerPlay Goods (Item-type materials)
    "poweragriculture": "Agricultural Sample",
    "powercomputer": "Computer Parts",
    "powermisccomputer": "Data Storage Device",
    "powerelectronics": "Electronics Package",
    "powerpower": "Energy Regulator",
    "powerexperiment": "Experiment Prototype",
    "powerextraction": "Extraction Sample",
    "powerindustrial": "Industrial Component",
    "powermiscindust": "Industrial Machinery",
    "powerinventory": "Inventory Record",
    "powermedical": "Medical Sample",
    "powerplaymilitary": "Military Schematic",
    "powerequipment": "Personal Protective Equipment",
    "powerresearch": "Research Notes",
    "powersecurity": "Security Logs"
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
            # At 0: add() below puts the collected amount on. Cargo's own
            # default of 1 counted every first pickup twice.
            self.inventory[cargo_name_lower] = Cargo(cargo_name_lower, 0)
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
    """Write the salvage hold to the database, under the current commander."""
    rows = [(item, system_name, cargo.count)
            for system_name, salvage in salvageInventory.items()
            for item, cargo in salvage.inventory.items()]
    database.save_inventory("salvage", database.commander(), rows)


def load_salvage():
    """Read the salvage hold from the database, replacing what is in memory."""
    salvageInventory.clear()
    for item, system_name, count in database.load_inventory("salvage", database.commander()):
        salvage = salvageInventory.setdefault(system_name, Salvage(system_name))
        salvage.inventory[item] = Cargo(item, count)

# Global inventory of all salvage by system
salvageInventory = {}
