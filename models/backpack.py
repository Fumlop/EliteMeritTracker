# models/backpack.py - Player Backpack for tracking PowerPlay data collection
from core.logging import logger
from core.storage import load_json, save_json
from ppdata.undermining import is_valid_um_data, get_um_display_name
from ppdata.reinforcement import is_valid_reinf_data, get_reinf_display_name
from ppdata.acquisition import is_valid_acq_data, get_acq_display_name


class Bag:
    """Generic bag for storing items per system - tracks item_type -> system -> count"""
    def __init__(self, name: str):
        self.name = name
        # Structure: {item_name: {system_name: count}}
        self.items = {}

    def add_item(self, name: str, count: int, system: str = None, controlling_power: str = None):
        """Add item to bag, tracking per system"""
        if count <= 0:
            return
        name_lower = name.lower()
        system_key = system or "unknown"

        if name_lower not in self.items:
            self.items[name_lower] = {}
        if system_key not in self.items[name_lower]:
            self.items[name_lower][system_key] = 0
        self.items[name_lower][system_key] += count

    def remove_item(self, name: str, count: int) -> dict:
        """Remove item from bag, alphabetically by system.
        Returns dict of {system: removed_count} for merit distribution."""
        name_lower = name.lower()
        if name_lower not in self.items:
            return {}

        systems_data = self.items[name_lower]
        if not systems_data:
            return {}

        removed_per_system = {}
        remaining = count

        # Sort systems alphabetically and remove in order
        for system in sorted(systems_data.keys()):
            if remaining <= 0:
                break
            available = systems_data[system]
            if available <= 0:
                continue

            to_remove = min(available, remaining)
            systems_data[system] -= to_remove
            removed_per_system[system] = to_remove
            remaining -= to_remove

            # Clean up empty system
            if systems_data[system] <= 0:
                del systems_data[system]

        # Clean up empty item
        if not systems_data:
            del self.items[name_lower]

        return removed_per_system

    def get_count(self, name: str) -> int:
        """Get total count of specific item across all systems"""
        name_lower = name.lower()
        if name_lower not in self.items:
            return 0
        return sum(self.items[name_lower].values())

    def get_count_by_system(self, name: str) -> dict:
        """Get count of specific item per system"""
        name_lower = name.lower()
        return dict(self.items.get(name_lower, {}))

    def get_total(self) -> int:
        """Get total count of all items across all systems"""
        total = 0
        for systems in self.items.values():
            total += sum(systems.values())
        return total

    def get_systems_summary(self) -> dict:
        """Get summary of items per system: {system: total_count}"""
        summary = {}
        for item_systems in self.items.values():
            for system, count in item_systems.items():
                summary[system] = summary.get(system, 0) + count
        return summary

    def clear(self):
        """Clear all items"""
        self.items.clear()

    def to_dict(self) -> dict:
        """Serialize to dict for JSON storage"""
        return dict(self.items)

    def from_dict(self, data: dict):
        """Deserialize from dict"""
        self.items.clear()

        # Handle both old and new formats
        if isinstance(data, dict):
            if "items" in data:
                # New format (ignore cp_values if present)
                for name, systems_data in data.get("items", {}).items():
                    if isinstance(systems_data, dict):
                        self.items[name] = dict(systems_data)
            else:
                # Old format: {item: {system: count}}
                for name, systems_data in data.items():
                    if isinstance(systems_data, dict):
                        self.items[name] = dict(systems_data)
                    else:
                        # Legacy format: {item: BackpackItem.to_dict()}
                        legacy_system = systems_data.get("system", "unknown")
                        legacy_count = systems_data.get("count", 0)
                        if legacy_count > 0:
                            self.items[name] = {legacy_system: legacy_count}


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

    def remove_item(self, name: str, count: int) -> dict:
        """Remove PowerPlay data from appropriate bag(s).
        Returns dict of {system: removed_count} for merit distribution."""
        name_lower = name.lower()
        total_removed = 0
        removed_from = []
        all_systems_removed = {}  # Aggregated {system: count} across all bags

        # Try to remove from each bag, tracking actual removed amounts per system
        if is_valid_um_data(name_lower):
            systems_removed = self.umbag.remove_item(name_lower, count)
            if systems_removed:
                bag_total = sum(systems_removed.values())
                total_removed += bag_total
                removed_from.append(f"UM:{bag_total}")
                for system, cnt in systems_removed.items():
                    all_systems_removed[system] = all_systems_removed.get(system, 0) + cnt

        if is_valid_reinf_data(name_lower):
            systems_removed = self.reinfbag.remove_item(name_lower, count)
            if systems_removed:
                bag_total = sum(systems_removed.values())
                total_removed += bag_total
                removed_from.append(f"Reinf:{bag_total}")
                for system, cnt in systems_removed.items():
                    all_systems_removed[system] = all_systems_removed.get(system, 0) + cnt

        if is_valid_acq_data(name_lower):
            systems_removed = self.acqbag.remove_item(name_lower, count)
            if systems_removed:
                bag_total = sum(systems_removed.values())
                total_removed += bag_total
                removed_from.append(f"Acq:{bag_total}")
                for system, cnt in systems_removed.items():
                    all_systems_removed[system] = all_systems_removed.get(system, 0) + cnt

        if total_removed > 0:
            display_name = get_um_display_name(name_lower) if is_valid_um_data(name_lower) else get_acq_display_name(name_lower)
            systems_str = ", ".join(f"{s}:{c}" for s, c in all_systems_removed.items())
            logger.info(f"Backpack [{'/'.join(removed_from)}]: -{total_removed} {display_name} from [{systems_str}]")

        # Warn if requested count exceeds what we had tracked
        if total_removed < count:
            logger.warning(f"Backpack: Requested removal of {count} {name_lower} but only had {total_removed} tracked")

        return all_systems_removed

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
    save_json("backpack.json", playerBackpack.to_dict())


def load_backpack():
    """Load backpack from JSON file"""
    data = load_json("backpack.json")
    if data:
        playerBackpack.from_dict(data)
        logger.info(f"Loaded backpack - UM: {len(playerBackpack.umbag.items)}, Reinf: {len(playerBackpack.reinfbag.items)}, Acq: {len(playerBackpack.acqbag.items)}")
