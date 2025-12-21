"""
Test script to simulate system jumps and verify economy/security loading from journal events.

This script simulates the journal entry processing that happens when jumping to
different systems, and verifies that economy and security data is properly
extracted from FSDJump events and displayed.
"""

import sys
import os
import json
from unittest.mock import MagicMock

# Mock the EDMC and tkinter dependencies before importing our modules
sys.modules['config'] = MagicMock()

# Create a simple mock for tkinter StringVar
class MockStringVar:
    def __init__(self, value=None):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value

# Mock tkinter
tk_mock = MagicMock()
tk_mock.StringVar = MockStringVar
sys.modules['tkinter'] = tk_mock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from emt_models.system import StarSystem


def print_separator():
    """Print a visual separator"""
    print("\n" + "="*80 + "\n")


def test_system_jump(system_name: str, fsd_event: dict, test_num: int):
    """
    Simulate a system jump and verify economy/security data extraction.

    Args:
        system_name: Name of the system to test
        fsd_event: FSDJump event data
        test_num: Test number for display
    """
    print(f"TEST {test_num}: Simulating jump to '{system_name}'")
    print("-" * 80)

    # Step 1: Display FSDJump event data
    print("\n1. FSDJump event data:")
    print(f"     Primary Economy: {fsd_event.get('SystemEconomy_Localised', 'N/A')}")
    print(f"     Secondary Economy: {fsd_event.get('SystemSecondEconomy_Localised', 'N/A')}")
    print(f"     System Security: {fsd_event.get('SystemSecurity', 'N/A')}")

    # Step 2: Create StarSystem instance (simulates what happens in load.py)
    print("\n2. Creating StarSystem instance from FSDJump event...")
    star_system = StarSystem(eventEntry=fsd_event)

    print(f"   Primary Economy: {getattr(star_system, 'PrimaryEconomy', 'NOT SET')}")
    print(f"   Secondary Economy: {getattr(star_system, 'SecondaryEconomy', 'NOT SET')}")
    print(f"   System Security: {getattr(star_system, 'SystemSecurity', 'NOT SET')}")
    print(f"   System Allegiance: {getattr(star_system, 'SystemAllegiance', 'NOT SET')}")
    print(f"   System Government: {getattr(star_system, 'SystemGovernment', 'NOT SET')}")
    print(f"   Population: {getattr(star_system, 'Population', 'NOT SET')}")

    # Step 3: Verify all fields are set
    print("\n3. Verification:")
    success = True

    if hasattr(star_system, 'PrimaryEconomy') and star_system.PrimaryEconomy:
        print(f"   [OK] PrimaryEconomy: {star_system.PrimaryEconomy}")
    else:
        print(f"   [X] PrimaryEconomy: NOT SET")
        success = False

    if hasattr(star_system, 'SecondaryEconomy'):
        if star_system.SecondaryEconomy and star_system.SecondaryEconomy != "None":
            print(f"   [OK] SecondaryEconomy: {star_system.SecondaryEconomy}")
        else:
            print(f"   [i] SecondaryEconomy: None (system may not have secondary)")
    else:
        print(f"   [X] SecondaryEconomy: NOT SET")
        success = False

    if hasattr(star_system, 'SystemSecurity') and star_system.SystemSecurity:
        print(f"   [OK] SystemSecurity: {star_system.SystemSecurity}")
    else:
        print(f"   [X] SystemSecurity: NOT SET")
        success = False

    # Step 4: Test serialization (to_dict / from_dict)
    print("\n4. Testing serialization (to_dict / from_dict)...")

    # Serialize to dict
    system_dict = star_system.to_dict()
    print(f"   Serialized data keys: {list(system_dict.keys())}")

    if 'PrimaryEconomy' in system_dict:
        print(f"   [OK] PrimaryEconomy in dict: {system_dict['PrimaryEconomy']}")
    else:
        print(f"   [X] PrimaryEconomy missing from dict")
        success = False

    if 'SecondaryEconomy' in system_dict:
        print(f"   [OK] SecondaryEconomy in dict: {system_dict['SecondaryEconomy']}")

    if 'SystemSecurity' in system_dict:
        print(f"   [OK] SystemSecurity in dict: {system_dict['SystemSecurity']}")

    # Deserialize from dict
    restored_system = StarSystem()
    restored_system.from_dict(system_dict)

    print(f"\n   After from_dict restoration:")
    print(f"     PrimaryEconomy: {getattr(restored_system, 'PrimaryEconomy', 'NOT SET')}")
    print(f"     SecondaryEconomy: {getattr(restored_system, 'SecondaryEconomy', 'NOT SET')}")
    print(f"     SystemSecurity: {getattr(restored_system, 'SystemSecurity', 'NOT SET')}")

    # Step 5: Simulate UI display
    print("\n5. Simulating UI display logic...")

    # Row 6: Economy and Security
    primary = getattr(star_system, 'PrimaryEconomy', None)
    secondary = getattr(star_system, 'SecondaryEconomy', None)
    security = getattr(star_system, 'SystemSecurity', None)

    parts = []
    if primary:
        if secondary and secondary != "None":
            parts.append(f"{primary} / {secondary}")
        else:
            parts.append(f"{primary}")

    if security:
        parts.append(f"Security: {security}")

    if parts:
        economy_security_text = " - ".join(parts)
        print(f"   Row 6 (Economy/Security): '{economy_security_text}'")
    else:
        print(f"   Row 6 (Economy/Security): (empty)")

    # Row 7: Allegiance, Government, Population
    allegiance = getattr(star_system, 'SystemAllegiance', None)
    government = getattr(star_system, 'SystemGovernment', None)
    population = getattr(star_system, 'Population', None)

    parts = []
    if allegiance:
        if government:
            parts.append(f"{allegiance} ({government})")
        else:
            parts.append(f"{allegiance}")

    if population and population > 0:
        if population >= 1_000_000_000:
            pop_str = f"Pop: {population / 1_000_000_000:.1f}B"
        elif population >= 1_000_000:
            pop_str = f"Pop: {population / 1_000_000:.1f}M"
        elif population >= 100_000:
            pop_str = f"Pop: {population / 1_000:.1f}K"
        else:
            pop_str = f"Pop: {population:,}"
        parts.append(pop_str)

    if parts:
        allegiance_text = " - ".join(parts)
        print(f"   Row 7 (Allegiance/Gov/Pop): '{allegiance_text}'")
    else:
        print(f"   Row 7 (Allegiance/Gov/Pop): (empty)")

    print("\n" + ("="*80))
    print(f"TEST {test_num} RESULT: {'[PASS]' if success else '[FAIL]'}")
    print("="*80)
    print_separator()

    return success


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("ELITE MERIT TRACKER - SYSTEM JUMP SIMULATION TESTS")
    print("="*80)

    # Test systems with simulated FSDJump events
    test_cases = [
        {
            "name": "Antliae Sector KR-W b1-7",
            "event": {
                "event": "FSDJump",
                "StarSystem": "Antliae Sector KR-W b1-7",
                "SystemEconomy": "$economy_Industrial;",
                "SystemEconomy_Localised": "Industrial",
                "SystemSecondEconomy": "$economy_HighTech;",
                "SystemSecondEconomy_Localised": "High Tech",
                "SystemSecurity": "$SYSTEM_SECURITY_low;",
                "SystemAllegiance": "Independent",
                "SystemGovernment_Localised": "Corporate",
                "Population": 191707078,
                "PowerplayState": "Unoccupied",
                "Powers": ["Felicia Winters", "Zemina Torval"],
                "PowerplayConflictProgress": [
                    {"Power": "Felicia Winters", "ConflictProgress": 0.198150},
                    {"Power": "Zemina Torval", "ConflictProgress": 0.032750}
                ]
            }
        },
        {
            "name": "Col 285 Sector BA-P c6-18",
            "event": {
                "event": "FSDJump",
                "StarSystem": "Col 285 Sector BA-P c6-18",
                "SystemEconomy": "$economy_Refinery;",
                "SystemEconomy_Localised": "Refinery",
                "SystemSecondEconomy": "$economy_Tourism;",
                "SystemSecondEconomy_Localised": "Tourism",
                "SystemSecurity": "$SYSTEM_SECURITY_medium;",
                "SystemAllegiance": "Federation",
                "SystemGovernment_Localised": "Democracy",
                "Population": 4091441,
                "PowerplayState": "Exploited",
                "ControllingPower": "Felicia Winters",
                "Powers": ["Felicia Winters"],
                "PowerplayStateReinforcement": 91021,
                "PowerplayStateUndermining": 0,
                "PowerplayStateControlProgress": 0.260629
            }
        }
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        result = test_system_jump(test_case["name"], test_case["event"], i)
        results.append((test_case["name"], result))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    for system_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {system_name}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*80 + "\n")

    return all(result for _, result in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
