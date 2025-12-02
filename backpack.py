# backpack.py - Player Backpack for tracking PowerPlay data collection
import json
import os
from log import logger
from umdata import is_valid_um_data, get_um_display_name
from reinfdata import is_valid_reinf_data, get_reinf_display_name
from acqdata import is_valid_acq_data, get_acq_display_name


class BackpackItem:
    """Single item in the backpack with collection metadata"""
    def __init__(self, name: str, count: int = 0, system: str = None, controlling_power: str = None):
        self.name = name.lower()
        self.count = count
        self.system = system  # System where data was collected
        self.controlling_power = controlling_power  # Power controlling the system

    def add(self, amount: int, system: str = None, controlling_power: str = None):
        """Add items, updating collection system if provided"""
        if amount <= 0:
            return
        self.count += amount
        if system:
            self.system = system
        if controlling_power:
            self.controlling_power = controlling_power

    def remove(self, amount: int) -> int:
        """Remove items, returns actual amount removed"""
        if amount <= 0:
            return 0
        actual = min(amount, self.count)
        self.count -= actual
        return actual

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "count": self.count,
            "system": self.system,
            "controlling_power": self.controlling_power
        }

    @staticmethod
    def from_dict(data: dict) -> 'BackpackItem':
        return BackpackItem(
            name=data.get("name", "unknown"),
            count=data.get("count", 0),
            system=data.get("system"),
            controlling_power=data.get("controlling_power")
        )


class Bag:
    """Generic bag for storing items of a specific type"""
    def __init__(self, name: str):
        self.name = name
        self.items = {}  # Dict[str, BackpackItem]

    def add_item(self, name: str, count: int, system: str = None, controlling_power: str = None):
        """Add item to bag"""
        name_lower = name.lower()
        if name_lower not in self.items:
            self.items[name_lower] = BackpackItem(name_lower, 0, system, controlling_power)
        self.items[name_lower].add(count, system, controlling_power)

    def remove_item(self, name: str, count: int) -> int:
        """Remove item from bag, returns actual amount removed"""
        name_lower = name.lower()
        if name_lower not in self.items:
            return 0
        removed = self.items[name_lower].remove(count)
        if self.items[name_lower].count <= 0:
            del self.items[name_lower]
        return removed

    def get_count(self, name: str) -> int:
        """Get count of specific item"""
        item = self.items.get(name.lower())
        return item.count if item else 0

    def get_total(self) -> int:
        """Get total count of all items"""
        return sum(item.count for item in self.items.values())

    def clear(self):
        """Clear all items"""
        self.items.clear()

    def to_dict(self) -> dict:
        return {name: item.to_dict() for name, item in self.items.items()}

    def from_dict(self, data: dict):
        self.items.clear()
        for name, item_data in data.items():
            self.items[name] = BackpackItem.from_dict(item_data)


class Backpack:
    """Player backpack with separate bags for UM, Reinf, and Acquisition"""
    def __init__(self):
        self.umbag = Bag("undermining")      # Undermining data
        self.reinfbag = Bag("reinforcement")  # Reinforcement data
        self.acqbag = Bag("acquisition")      # Acquisition data

    def add_item(self, name: str, count: int, system: str = None, controlling_power: str = None, pledged_power: str = None):
        """Add PowerPlay data to appropriate bag based on controlling vs pledged power"""
        name_lower = name.lower()
        added_to = []

        # Determine territory type (check neutral first to avoid false enemy detection)
        is_neutral = not controlling_power or controlling_power == "no power" or controlling_power == ""
        is_own_power = not is_neutral and pledged_power and controlling_power == pledged_power
        is_enemy_power = not is_neutral and pledged_power and controlling_power != pledged_power

        # UM: Valid if collected in enemy territory (controlling_power != pledged_power and has a power)
        if is_valid_um_data(name_lower) and is_enemy_power:
            self.umbag.add_item(name_lower, count, system, controlling_power)
            added_to.append("UM")

        # Reinf: Valid only if collected in own power territory (controlling_power == pledged_power)
        if is_valid_reinf_data(name_lower) and is_own_power:
            self.reinfbag.add_item(name_lower, count, system, controlling_power)
            added_to.append("Reinf")

        # Acq: Valid if collected in neutral territory (no controlling power)
        if is_valid_acq_data(name_lower) and is_neutral:
            self.acqbag.add_item(name_lower, count, system, controlling_power)
            added_to.append("Acq")

        if added_to:
            display_name = get_um_display_name(name_lower) if is_valid_um_data(name_lower) else get_acq_display_name(name_lower)
            logger.info(f"Backpack [{'/'.join(added_to)}]: +{count} {display_name} from {system} ({controlling_power})")

    def remove_item(self, name: str, count: int) -> int:
        """Remove PowerPlay data from appropriate bag(s). Returns actual amount removed."""
        name_lower = name.lower()
        total_removed = 0
        removed_from = []

        # Try to remove from each bag, tracking actual removed amounts
        if is_valid_um_data(name_lower):
            r = self.umbag.remove_item(name_lower, count)
            if r > 0:
                total_removed += r
                removed_from.append(f"UM:{r}")

        if is_valid_reinf_data(name_lower):
            r = self.reinfbag.remove_item(name_lower, count)
            if r > 0:
                total_removed += r
                removed_from.append(f"Reinf:{r}")

        if is_valid_acq_data(name_lower):
            r = self.acqbag.remove_item(name_lower, count)
            if r > 0:
                total_removed += r
                removed_from.append(f"Acq:{r}")

        if total_removed > 0:
            display_name = get_um_display_name(name_lower) if is_valid_um_data(name_lower) else get_acq_display_name(name_lower)
            logger.info(f"Backpack [{'/'.join(removed_from)}]: -{total_removed} {display_name}")

        # Warn if requested count exceeds what we had tracked
        if total_removed < count:
            logger.warning(f"Backpack: Requested removal of {count} {name_lower} but only had {total_removed} tracked")

        return total_removed

    def sync_from_shiplocker(self, data_items: list):
        """Cross-check backpack counts against ShipLocker event Data section.
        ShipLocker shows actual game state - we can only compare totals,
        not per-bag distribution (game tracks internally with OwnerID etc.)"""
        # Aggregate PP data from ShipLocker (multiple entries possible for same item)
        game_counts = {}
        for item in data_items:
            name = item.get('Name', '').lower()
            count = item.get('Count', 0)
            if is_valid_um_data(name) or is_valid_reinf_data(name) or is_valid_acq_data(name):
                game_counts[name] = game_counts.get(name, 0) + count

        # Compare tracked totals vs game state
        for name, game_count in game_counts.items():
            tracked_total = (
                self.umbag.get_count(name) +
                self.reinfbag.get_count(name) +
                self.acqbag.get_count(name)
            )
            if tracked_total != game_count:
                logger.warning(f"Backpack sync mismatch: {name} tracked={tracked_total} game={game_count}")

        if game_counts:
            logger.info(f"ShipLocker sync: {len(game_counts)} PP data types, totals: {dict(game_counts)}")

    def to_dict(self) -> dict:
        return {
            "umbag": self.umbag.to_dict(),
            "reinfbag": self.reinfbag.to_dict(),
            "acqbag": self.acqbag.to_dict()
        }

    def from_dict(self, data: dict):
        if "umbag" in data:
            self.umbag.from_dict(data["umbag"])
        if "reinfbag" in data:
            self.reinfbag.from_dict(data["reinfbag"])
        if "acqbag" in data:
            self.acqbag.from_dict(data["acqbag"])


# Singleton backpack instance
playerBackpack = Backpack()


def save_backpack():
    """Save backpack to JSON file"""
    try:
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        backpack_path = os.path.join(plugin_dir, "backpack.json")

        with open(backpack_path, "w") as f:
            json.dump(playerBackpack.to_dict(), f, indent=4)
    except Exception as e:
        logger.error(f"Failed to save backpack: {e}")


def load_backpack():
    """Load backpack from JSON file"""
    try:
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        backpack_path = os.path.join(plugin_dir, "backpack.json")

        if not os.path.exists(backpack_path):
            return

        with open(backpack_path, "r") as f:
            data = json.load(f)

        playerBackpack.from_dict(data)
        logger.info(f"Loaded backpack - UM: {len(playerBackpack.umbag.items)}, Reinf: {len(playerBackpack.reinfbag.items)}, Acq: {len(playerBackpack.acqbag.items)}")
    except Exception as e:
        logger.error(f"Failed to load backpack: {e}")
