# test_backpack.py - Standalone Test driver for Backpack system
# Run this without EDMC dependencies

import json

# ============================================================
# Inline copies of data types (to avoid EDMC dependencies)
# ============================================================

VALID_UNDERMINING_DATA_TYPES = {
    "poweremployeedata": "Power Association Data",
    "powerclassifieddata": "Power Classified Data",
    "powerfinancialrecords": "Power Industrial Data",
    "powerpropagandadata": "Power Political Data",
    "powerresearchdata": "Power Research Data"
}

VALID_REINFORCEMENT_DATA_TYPES = {
    "poweremployeedata": "Power Association Data",
    "powerclassifieddata": "Power Classified Data",
    "powerpropagandadata": "Power Political Data"
}

VALID_ACQUISITION_DATA_TYPES = {
    "poweremployeedata": "Power Association Data",
    "powerclassifieddata": "Power Classified Data",
    "powerfinancialrecords": "Power Industrial Data",
    "powerpropagandadata": "Power Political Data",
    "powerresearchdata": "Power Research Data"
}

def is_valid_um_data(name): return name.lower() in VALID_UNDERMINING_DATA_TYPES
def is_valid_reinf_data(name): return name.lower() in VALID_REINFORCEMENT_DATA_TYPES
def is_valid_acq_data(name): return name.lower() in VALID_ACQUISITION_DATA_TYPES
def get_um_display_name(name): return VALID_UNDERMINING_DATA_TYPES.get(name.lower(), name)
def get_acq_display_name(name): return VALID_ACQUISITION_DATA_TYPES.get(name.lower(), name)

# ============================================================
# Inline Backpack classes (simplified for testing)
# ============================================================

class Bag:
    """Bag tracks items per system: {item_name: {system_name: count}}"""
    def __init__(self, name):
        self.name = name
        self.items = {}  # {item_name: {system_name: count}}

    def add_item(self, name, count, system=None, controlling_power=None):
        if count <= 0:
            return
        name_lower = name.lower()
        system_key = system or "unknown"

        if name_lower not in self.items:
            self.items[name_lower] = {}
        if system_key not in self.items[name_lower]:
            self.items[name_lower][system_key] = 0
        self.items[name_lower][system_key] += count

    def remove_item(self, name, count):
        """Remove item alphabetically by system. Returns {system: removed_count}."""
        name_lower = name.lower()
        if name_lower not in self.items:
            return {}

        systems_data = self.items[name_lower]
        if not systems_data:
            return {}

        removed_per_system = {}
        remaining = count

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

            if systems_data[system] <= 0:
                del systems_data[system]

        if not systems_data:
            del self.items[name_lower]

        return removed_per_system

    def get_count(self, name):
        name_lower = name.lower()
        if name_lower not in self.items:
            return 0
        return sum(self.items[name_lower].values())

    def get_total(self):
        total = 0
        for systems in self.items.values():
            total += sum(systems.values())
        return total

    def get_systems_summary(self):
        """Returns {system: total_count}"""
        summary = {}
        for item_systems in self.items.values():
            for system, count in item_systems.items():
                summary[system] = summary.get(system, 0) + count
        return summary


class Backpack:
    def __init__(self):
        self.umbag = Bag("undermining")
        self.reinfbag = Bag("reinforcement")
        self.acqbag = Bag("acquisition")

    def add_item(self, name, count, system=None, controlling_power=None, pledged_power=None):
        name_lower = name.lower()
        added_to = []

        is_neutral = not controlling_power or controlling_power == "no power" or controlling_power == ""
        is_own_power = not is_neutral and pledged_power and controlling_power == pledged_power
        is_enemy_power = not is_neutral and pledged_power and controlling_power != pledged_power

        if is_valid_um_data(name_lower) and is_enemy_power:
            self.umbag.add_item(name_lower, count, system, controlling_power)
            added_to.append("UM")

        if is_valid_reinf_data(name_lower) and is_own_power:
            self.reinfbag.add_item(name_lower, count, system, controlling_power)
            added_to.append("Reinf")

        if is_valid_acq_data(name_lower) and is_neutral:
            self.acqbag.add_item(name_lower, count, system, controlling_power)
            added_to.append("Acq")

        if added_to:
            print(f"  -> Added to [{'/'.join(added_to)}]: +{count} {name_lower} from {system}")

    def remove_item(self, name, count):
        """Remove item and return {system: removed_count} for merit distribution."""
        name_lower = name.lower()
        all_systems_removed = {}
        removed_from = []

        if is_valid_um_data(name_lower):
            systems_removed = self.umbag.remove_item(name_lower, count)
            if systems_removed:
                removed_from.append(f"UM:{sum(systems_removed.values())}")
                for s, c in systems_removed.items():
                    all_systems_removed[s] = all_systems_removed.get(s, 0) + c

        if is_valid_reinf_data(name_lower):
            systems_removed = self.reinfbag.remove_item(name_lower, count)
            if systems_removed:
                removed_from.append(f"Reinf:{sum(systems_removed.values())}")
                for s, c in systems_removed.items():
                    all_systems_removed[s] = all_systems_removed.get(s, 0) + c

        if is_valid_acq_data(name_lower):
            systems_removed = self.acqbag.remove_item(name_lower, count)
            if systems_removed:
                removed_from.append(f"Acq:{sum(systems_removed.values())}")
                for s, c in systems_removed.items():
                    all_systems_removed[s] = all_systems_removed.get(s, 0) + c

        if all_systems_removed:
            systems_str = ", ".join(f"{s}:{c}" for s, c in all_systems_removed.items())
            print(f"  -> Removed [{'/'.join(removed_from)}]: -{sum(all_systems_removed.values())} {name_lower} from [{systems_str}]")

        return all_systems_removed


# ============================================================
# Test Functions
# ============================================================

def test_backpack():
    print("=" * 70)
    print("BACKPACK TEST DRIVER - PowerPlay Data Collection & Hand-in")
    print("=" * 70)

    pledged_power = "Zachary Hudson"
    enemy_power = "Aisling Duval"
    neutral_power = "no power"

    enemy_system = "Cubeo"
    own_system = "Sol"
    neutral_system = "Merope"

    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 1: UNDERMINING - Collect in ENEMY territory")
    print("=" * 70)
    print(f"Player pledged to: {pledged_power}")
    print(f"Current system: {enemy_system} (controlled by {enemy_power})")
    print()

    bp = Backpack()
    um_items = ["poweremployeedata", "powerclassifieddata", "powerfinancialrecords", "powerpropagandadata", "powerresearchdata"]

    for item in um_items:
        print(f"Collecting: {item}")
        bp.add_item(item, 3, enemy_system, enemy_power, pledged_power)

    print(f"\nResult: UM={bp.umbag.get_total()}, Reinf={bp.reinfbag.get_total()}, Acq={bp.acqbag.get_total()}")
    assert bp.umbag.get_total() == 15 and bp.reinfbag.get_total() == 0 and bp.acqbag.get_total() == 0
    print("[OK] PASS")

    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 2: REINFORCEMENT - Collect in OWN territory")
    print("=" * 70)
    print(f"Player pledged to: {pledged_power}")
    print(f"Current system: {own_system} (controlled by {pledged_power})")
    print()

    bp2 = Backpack()
    reinf_items = ["poweremployeedata", "powerclassifieddata", "powerpropagandadata"]

    for item in reinf_items:
        print(f"Collecting: {item}")
        bp2.add_item(item, 2, own_system, pledged_power, pledged_power)

    print(f"\nTrying UM-only items (should be ignored):")
    bp2.add_item("powerfinancialrecords", 2, own_system, pledged_power, pledged_power)
    bp2.add_item("powerresearchdata", 2, own_system, pledged_power, pledged_power)

    print(f"\nResult: UM={bp2.umbag.get_total()}, Reinf={bp2.reinfbag.get_total()}, Acq={bp2.acqbag.get_total()}")
    assert bp2.reinfbag.get_total() == 6 and bp2.umbag.get_total() == 0 and bp2.acqbag.get_total() == 0
    print("[OK] PASS")

    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 3: ACQUISITION - Collect in NEUTRAL territory")
    print("=" * 70)
    print(f"Player pledged to: {pledged_power}")
    print(f"Current system: {neutral_system} (controlled by: {neutral_power})")
    print()

    bp3 = Backpack()
    for item in um_items:
        print(f"Collecting: {item}")
        bp3.add_item(item, 4, neutral_system, neutral_power, pledged_power)

    print(f"\nResult: UM={bp3.umbag.get_total()}, Reinf={bp3.reinfbag.get_total()}, Acq={bp3.acqbag.get_total()}")
    assert bp3.acqbag.get_total() == 20 and bp3.umbag.get_total() == 0 and bp3.reinfbag.get_total() == 0
    print("[OK] PASS")

    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 4: HAND-IN via DeliverPowerMicroResources")
    print("=" * 70)

    bp4 = Backpack()
    # Collect 10 items in enemy territory
    bp4.add_item("powerfinancialrecords", 10, enemy_system, enemy_power, pledged_power)
    print(f"After collection: UM={bp4.umbag.get_total()}")

    # Simulate DeliverPowerMicroResources event
    deliver_event = {
        "timestamp": "2025-12-02T12:55:14Z",
        "event": "DeliverPowerMicroResources",
        "TotalCount": 3,
        "MicroResources": [
            {"Name": "powerfinancialrecords", "Count": 3}
        ]
    }

    print(f"\nDeliverPowerMicroResources event: hand in 3 items")
    for item in deliver_event.get('MicroResources', []):
        bp4.remove_item(item['Name'], item['Count'])

    print(f"After hand-in: UM={bp4.umbag.get_total()}")
    assert bp4.umbag.get_total() == 7
    print("[OK] PASS")

    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 5: BackpackChange events (Add & Remove)")
    print("=" * 70)

    bp5 = Backpack()

    # Simulate BackpackChange Add event
    add_event = {
        "timestamp": "2025-12-02T12:29:26Z",
        "event": "BackpackChange",
        "Added": [{"Name": "poweremployeedata", "Count": 1}]
    }

    print("BackpackChange Add event:")
    for item in add_event.get('Added', []):
        bp5.add_item(item['Name'], item['Count'], enemy_system, enemy_power, pledged_power)

    print(f"After add: UM={bp5.umbag.get_total()}")

    # Simulate BackpackChange Remove event
    remove_event = {
        "timestamp": "2025-12-02T12:39:44Z",
        "event": "BackpackChange",
        "Removed": [{"Name": "poweremployeedata", "Count": 1}]
    }

    print("\nBackpackChange Remove event:")
    for item in remove_event.get('Removed', []):
        bp5.remove_item(item['Name'], item['Count'])

    print(f"After remove: UM={bp5.umbag.get_total()}")
    assert bp5.umbag.get_total() == 0
    print("[OK] PASS")

    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 6: ShipLocker sync with multiple entries for same item")
    print("=" * 70)

    bp6 = Backpack()
    # Track 15 items in enemy territory
    bp6.add_item("poweremployeedata", 10, enemy_system, enemy_power, pledged_power)
    bp6.add_item("poweremployeedata", 5, enemy_system, enemy_power, pledged_power)
    print(f"Tracked in backpack: UM={bp6.umbag.get_total()}")

    # Simulate ShipLocker event with MULTIPLE entries for same item (same OwnerID scenario)
    shiplocker_event = {
        "timestamp": "2025-12-02T13:00:00Z",
        "event": "ShipLocker",
        "Data": [
            {"Name": "poweremployeedata", "OwnerID": 123456, "Count": 8},
            {"Name": "poweremployeedata", "OwnerID": 123456, "Count": 4},  # Same item, same owner!
            {"Name": "poweremployeedata", "OwnerID": 789012, "Count": 3},  # Same item, different owner
        ]
    }

    print(f"\nShipLocker event has 3 entries for poweremployeedata:")
    for item in shiplocker_event["Data"]:
        print(f"  - OwnerID={item['OwnerID']}, Count={item['Count']}")

    # Aggregate like sync_from_shiplocker does
    game_counts = {}
    for item in shiplocker_event["Data"]:
        name = item.get('Name', '').lower()
        count = item.get('Count', 0)
        if is_valid_um_data(name) or is_valid_reinf_data(name) or is_valid_acq_data(name):
            game_counts[name] = game_counts.get(name, 0) + count

    print(f"\nAggregated game state: {game_counts}")
    assert game_counts["poweremployeedata"] == 15, f"Expected 15, got {game_counts['poweremployeedata']}"

    # Check that tracked total matches aggregated game state
    tracked_total = bp6.umbag.get_total() + bp6.reinfbag.get_total() + bp6.acqbag.get_total()
    print(f"Tracked total: {tracked_total}, Game total: {game_counts['poweremployeedata']}")
    assert tracked_total == game_counts["poweremployeedata"], "Mismatch between tracked and game state!"
    print("[OK] PASS - Aggregation works correctly")

    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 7: ShipLocker sync detects mismatch")
    print("=" * 70)

    bp7 = Backpack()
    # Track only 10 items but game has 15
    bp7.add_item("powerclassifieddata", 10, enemy_system, enemy_power, pledged_power)
    print(f"Tracked in backpack: UM={bp7.umbag.get_total()}")

    shiplocker_mismatch = {
        "Data": [
            {"Name": "powerclassifieddata", "OwnerID": 111, "Count": 8},
            {"Name": "powerclassifieddata", "OwnerID": 222, "Count": 7},
        ]
    }

    game_counts2 = {}
    for item in shiplocker_mismatch["Data"]:
        name = item.get('Name', '').lower()
        count = item.get('Count', 0)
        if is_valid_um_data(name) or is_valid_reinf_data(name) or is_valid_acq_data(name):
            game_counts2[name] = game_counts2.get(name, 0) + count

    tracked_total2 = bp7.umbag.get_total()
    game_total2 = game_counts2.get("powerclassifieddata", 0)
    print(f"Tracked: {tracked_total2}, Game: {game_total2}")

    if tracked_total2 != game_total2:
        print(f"[OK] Mismatch detected as expected: tracked={tracked_total2} vs game={game_total2}")
    else:
        print("[FAIL] Should have detected mismatch!")
        assert False

    print("[OK] PASS - Mismatch detection works")

    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 8: Merit Distribution - Multiple Collection Systems")
    print("=" * 70)
    print("Scenario: Collect items from multiple enemy systems, then hand in all")
    print()

    bp8 = Backpack()
    enemy_power2 = "Felicia Winters"

    # Collect from multiple enemy systems (alphabetically: Achenar, Cubeo, Eotienses)
    print("Collecting powerfinancialrecords from 3 enemy systems:")
    bp8.add_item("powerfinancialrecords", 10, "Cubeo", enemy_power, pledged_power)      # 10 from Cubeo
    bp8.add_item("powerfinancialrecords", 5, "Achenar", enemy_power, pledged_power)     # 5 from Achenar
    bp8.add_item("powerfinancialrecords", 8, "Eotienses", enemy_power2, pledged_power)  # 8 from Eotienses

    total = bp8.umbag.get_total()
    print(f"\nTotal in UM bag: {total}")
    print(f"Per system: {bp8.umbag.get_systems_summary()}")
    assert total == 23, f"Expected 23, got {total}"

    # Hand in 15 items - should come alphabetically: Achenar(5), Cubeo(10)
    print(f"\nHanding in 15 items (alphabetically: Achenar first, then Cubeo):")
    systems_removed = bp8.remove_item("powerfinancialrecords", 15)

    print(f"Systems that got merits: {systems_removed}")
    assert systems_removed.get("Achenar", 0) == 5, f"Achenar should get 5, got {systems_removed.get('Achenar', 0)}"
    assert systems_removed.get("Cubeo", 0) == 10, f"Cubeo should get 10, got {systems_removed.get('Cubeo', 0)}"
    assert "Eotienses" not in systems_removed, "Eotienses should not be touched yet"

    print(f"\nRemaining in bag: {bp8.umbag.get_total()}")
    print(f"Remaining per system: {bp8.umbag.get_systems_summary()}")
    assert bp8.umbag.get_total() == 8, f"Expected 8 remaining, got {bp8.umbag.get_total()}"

    # Hand in remaining 8 - should come from Eotienses
    print(f"\nHanding in remaining 8 items:")
    systems_removed2 = bp8.remove_item("powerfinancialrecords", 8)

    print(f"Systems that got merits: {systems_removed2}")
    assert systems_removed2.get("Eotienses", 0) == 8, f"Eotienses should get 8, got {systems_removed2.get('Eotienses', 0)}"
    assert bp8.umbag.get_total() == 0, "Bag should be empty now"

    print("[OK] PASS - Merit distribution works correctly")

    # ============================================================
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED!")
    print("=" * 70)

    print("""
SUMMARY - Bag Assignment Rules:
===============================

| Bag      | Collect in           | Valid Data Types              | Hand-in at              |
|----------|----------------------|-------------------------------|-------------------------|
| umbag    | Enemy Power System   | All 5 types                   | Own Power System        |
| reinfbag | Own Power System     | employee, classified, propag. | Same System             |
| acqbag   | Neutral System       | All 5 types                   | Own Power System        |

Events:
- BackpackChange (Added)    -> add_item() (data collection)
- DeliverPowerMicroResources -> remove_item() (hand-in at power contact for merits)
- ShipLocker                 -> sync_from_shiplocker() (cross-check game state)
""")


if __name__ == "__main__":
    test_backpack()
