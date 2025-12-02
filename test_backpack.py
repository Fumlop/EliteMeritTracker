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

class BackpackItem:
    def __init__(self, name, count=0, system=None, controlling_power=None):
        self.name = name.lower()
        self.count = count
        self.system = system
        self.controlling_power = controlling_power

    def add(self, amount, system=None, controlling_power=None):
        if amount <= 0: return
        self.count += amount
        if system: self.system = system
        if controlling_power: self.controlling_power = controlling_power

    def remove(self, amount):
        if amount <= 0: return 0
        actual = min(amount, self.count)
        self.count -= actual
        return actual

    def to_dict(self):
        return {"name": self.name, "count": self.count, "system": self.system, "controlling_power": self.controlling_power}


class Bag:
    def __init__(self, name):
        self.name = name
        self.items = {}

    def add_item(self, name, count, system=None, controlling_power=None):
        name_lower = name.lower()
        if name_lower not in self.items:
            self.items[name_lower] = BackpackItem(name_lower, 0, system, controlling_power)
        self.items[name_lower].add(count, system, controlling_power)

    def remove_item(self, name, count):
        name_lower = name.lower()
        if name_lower not in self.items: return 0
        removed = self.items[name_lower].remove(count)
        if self.items[name_lower].count <= 0:
            del self.items[name_lower]
        return removed

    def get_total(self):
        return sum(item.count for item in self.items.values())

    def to_dict(self):
        return {name: item.to_dict() for name, item in self.items.items()}


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
            print(f"  -> Added to [{'/'.join(added_to)}]: +{count} {name_lower}")

    def remove_item(self, name, count):
        name_lower = name.lower()
        removed = 0
        removed_from = []

        if is_valid_um_data(name_lower):
            r = self.umbag.remove_item(name_lower, count)
            if r > 0: removed = r; removed_from.append("UM")

        if is_valid_reinf_data(name_lower):
            r = self.reinfbag.remove_item(name_lower, count)
            if r > 0: removed = r; removed_from.append("Reinf")

        if is_valid_acq_data(name_lower):
            r = self.acqbag.remove_item(name_lower, count)
            if r > 0: removed = r; removed_from.append("Acq")

        if removed > 0:
            print(f"  -> Removed from [{'/'.join(removed_from)}]: -{removed} {name_lower}")

        return removed


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
