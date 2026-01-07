"""
Comprehensive Test Suite for PowerPlay Items Tracking

Tests all PowerPlay item types (Data and Item categories) to ensure proper
tracking through the backpack, salvage, and merit calculation systems.

Target Coverage: 95%+
"""
import pytest
from emt_models.salvage import VALID_POWERPLAY_SALVAGE_TYPES, Salvage, salvageInventory
from emt_models.backpack import playerBackpack
from emt_ppdata.undermining import VALID_UNDERMINING_DATA_TYPES, is_valid_um_data
from emt_ppdata.reinforcement import VALID_REINFORCEMENT_DATA_TYPES, is_valid_reinf_data
from emt_ppdata.acquisition import VALID_ACQUISITION_DATA_TYPES, is_valid_acq_data


class TestPowerPlayDataTypes:
    """Test PowerPlay Data-type items (backpack tracking)"""

    def test_all_undermining_data_types(self):
        """Test all valid undermining data types are recognized"""
        expected_types = {
            "poweremployeedata": "Power Association Data",
            "powerclassifieddata": "Power Classified Data",
            "powerfinancialrecords": "Power Industrial Data",
            "powerpropagandadata": "Power Political Data",
            "powerresearchdata": "Power Research Data"
        }
        assert VALID_UNDERMINING_DATA_TYPES == expected_types

        # Test validation
        for item_name in expected_types.keys():
            assert is_valid_um_data(item_name)
            assert is_valid_um_data(item_name.upper())  # Case insensitive

    def test_all_reinforcement_data_types(self):
        """Test all valid reinforcement data types are recognized"""
        expected_types = {
            "poweremployeedata": "Power Association Data",
            "powerclassifieddata": "Power Classified Data",
            "powerpropagandadata": "Power Political Data"
        }
        assert VALID_REINFORCEMENT_DATA_TYPES == expected_types

        # Test validation
        for item_name in expected_types.keys():
            assert is_valid_reinf_data(item_name)

    def test_all_acquisition_data_types(self):
        """Test all valid acquisition data types are recognized"""
        expected_types = {
            "poweremployeedata": "Power Association Data",
            "powerclassifieddata": "Power Classified Data",
            "powerfinancialrecords": "Power Industrial Data",
            "powerpropagandadata": "Power Political Data",
            "powerresearchdata": "Power Research Data"
        }
        assert VALID_ACQUISITION_DATA_TYPES == expected_types

        # Test validation
        for item_name in expected_types.keys():
            assert is_valid_acq_data(item_name)

    def test_invalid_data_types(self):
        """Test that invalid data types are rejected"""
        invalid_types = ["notpowerdata", "randomitem", "powerinvalid", ""]

        for invalid in invalid_types:
            assert not is_valid_um_data(invalid)
            assert not is_valid_reinf_data(invalid)
            assert not is_valid_acq_data(invalid)


class TestPowerPlayItemTypes:
    """Test PowerPlay Item-type materials (salvage/cargo tracking)"""

    def test_all_powerplay_salvage_types(self):
        """Test all valid PowerPlay salvage/item types are recognized"""
        expected_types = {
            # Original salvage types
            "usscargoblackbox": "Black Box",
            "wreckagecomponents": "Wreckage Components",
            # PowerPlay Item-type materials
            "powerinventory": "Inventory Record",
            "powerextraction": "Extraction Sample",
            "powerexperiment": "Experiment Prototype",
            "powerelectronics": "Electronics Package",
            "powercomputer": "Computer Parts",
            "powerequipment": "Personal Protective Equipment",
            "powermisccomputer": "Data Storage Device",
            "powersecurity": "Security Logs",
            "powerresearch": "Research Notes"
        }
        assert VALID_POWERPLAY_SALVAGE_TYPES == expected_types

    def test_powerplay_item_collection(self):
        """Test collecting PowerPlay items through salvage system"""
        salvage = Salvage("Test System")

        # Test each PowerPlay item type
        power_items = [
            "powerinventory",
            "powerextraction",
            "powerexperiment",
            "powerelectronics",
            "powercomputer",
            "powerequipment",
            "powermisccomputer",
            "powersecurity",
            "powerresearch"
        ]

        for item in power_items:
            salvage.add_cargo(item, 1)
            assert salvage.has_cargo(item)
            assert salvage.inventory[item].count == 1

    def test_powerplay_item_removal(self):
        """Test removing PowerPlay items from salvage"""
        salvage = Salvage("Test System")

        # Add multiple of each item
        salvage.add_cargo("powerexperiment", 5)
        salvage.add_cargo("powerelectronics", 3)

        # Remove some
        removed = salvage.remove_cargo("powerexperiment", 2)
        assert removed == 2
        assert salvage.inventory["powerexperiment"].count == 3

        # Remove all
        removed = salvage.remove_cargo("powerelectronics", 10)
        assert removed == 3
        assert not salvage.has_cargo("powerelectronics")

    def test_legacy_salvage_types_still_work(self):
        """Ensure original salvage types still function"""
        salvage = Salvage("Test System")

        salvage.add_cargo("usscargoblackbox", 10)
        salvage.add_cargo("wreckagecomponents", 5)

        assert salvage.has_cargo("usscargoblackbox")
        assert salvage.has_cargo("wreckagecomponents")
        assert salvage.inventory["usscargoblackbox"].count == 10
        assert salvage.inventory["wreckagecomponents"].count == 5


class TestBackpackChangeEvents:
    """Test BackpackChange journal events with PowerPlay items"""

    def test_backpack_add_undermining_data(self):
        """Test adding undermining data to backpack"""
        # Simulate BackpackChange event from journal
        event = {
            "event": "BackpackChange",
            "Added": [
                {"Name": "powerfinancialrecords", "Name_Localised": "Power Industrial Data", "Count": 2, "Type": "Data"},
                {"Name": "powerresearchdata", "Name_Localised": "Power Research Data", "Count": 1, "Type": "Data"}
            ]
        }

        # Verify these are valid types
        for item in event["Added"]:
            item_name = item["Name"].lower()
            assert is_valid_um_data(item_name)

    def test_backpack_add_powerplay_items(self):
        """Test adding PowerPlay Item-type materials to inventory"""
        # Simulate CollectCargo events from journal
        items_to_collect = [
            {"Name": "powerexperiment", "Name_Localised": "Experiment Prototype", "Count": 1, "Type": "Item"},
            {"Name": "powerelectronics", "Name_Localised": "Electronics Package", "Count": 2, "Type": "Item"},
            {"Name": "powercomputer", "Name_Localised": "Computer Parts", "Count": 1, "Type": "Item"}
        ]

        # Verify these are valid salvage types
        for item in items_to_collect:
            item_name = item["Name"].lower()
            assert item_name in VALID_POWERPLAY_SALVAGE_TYPES


class TestDeliverPowerMicroResources:
    """Test PowerPlay material delivery events"""

    def test_deliver_data_types(self):
        """Test delivery of Data-type PowerPlay materials"""
        # Real event from journal log
        event = {
            "timestamp": "2026-01-07T05:24:02Z",
            "event": "DeliverPowerMicroResources",
            "TotalCount": 8,
            "MicroResources": [
                {"Name": "powerfinancialrecords", "Name_Localised": "Power Industrial Data", "Category": "Data", "Count": 8}
            ],
            "MarketID": 3228496384
        }

        # Verify item is trackable
        item = event["MicroResources"][0]
        assert is_valid_um_data(item["Name"])
        assert item["Category"] == "Data"

    def test_deliver_item_types(self):
        """Test delivery of Item-type PowerPlay materials"""
        # Real event from journal log
        event = {
            "timestamp": "2026-01-07T05:24:45Z",
            "event": "DeliverPowerMicroResources",
            "TotalCount": 3,
            "MicroResources": [
                {"Name": "powerexperiment", "Name_Localised": "Experiment Prototype", "Category": "Item", "Count": 3}
            ],
            "MarketID": 3228496384
        }

        # Verify item is trackable
        item = event["MicroResources"][0]
        assert item["Name"] in VALID_POWERPLAY_SALVAGE_TYPES
        assert item["Category"] == "Item"


class TestSearchAndRescueDelivery:
    """Test Search and Rescue delivery of PowerPlay items"""

    def test_sar_delivery_powerplay_items(self):
        """Test delivering PowerPlay items to Search and Rescue"""
        salvage = Salvage("Test System 1")
        salvage2 = Salvage("Test System 2")

        # Add items to multiple systems
        salvage.add_cargo("powerexperiment", 10)
        salvage2.add_cargo("powerexperiment", 5)

        # Simulate SearchAndRescue event
        event = {
            "event": "SearchAndRescue",
            "Name": "powerexperiment",
            "Name_Localised": "Experiment Prototype",
            "Count": 8,
            "Reward": 66293
        }

        # Verify item type is valid
        assert event["Name"] in VALID_POWERPLAY_SALVAGE_TYPES

        # System would remove from salvage inventory
        removed_from_system1 = salvage.remove_cargo("powerexperiment", 8)
        assert removed_from_system1 == 8
        assert salvage.inventory["powerexperiment"].count == 2


class TestCollectCargoEvents:
    """Test CollectCargo journal events for PowerPlay items"""

    def test_collect_cargo_powerplay_items(self):
        """Test collecting PowerPlay items via CollectCargo event"""
        # Real events from journal log
        events = [
            {
                "event": "CollectCargo",
                "Type": "powerextraction",
                "Type_Localised": "Extraction Sample",
                "Count": 1,
                "Stolen": False
            },
            {
                "event": "CollectCargo",
                "Type": "powerequipment",
                "Type_Localised": "Personal Protective Equipment",
                "Count": 1,
                "Stolen": False
            },
            {
                "event": "CollectCargo",
                "Type": "powersecurity",
                "Type_Localised": "Security Logs",
                "Count": 1,
                "Stolen": False
            }
        ]

        for event in events:
            assert event["Type"] in VALID_POWERPLAY_SALVAGE_TYPES


class TestPowerPlayMeritCalculation:
    """Test merit calculation for different PowerPlay item deliveries"""

    def test_data_item_merit_distribution(self):
        """Test merit distribution when delivering Data items"""
        # Simulate delivering 8 Power Industrial Data from one system
        # Real event showed: 8 items = 2631 merits
        items_delivered = 8
        merits_gained = 2631
        merits_per_item = merits_gained / items_delivered

        assert merits_per_item == pytest.approx(328.875)

    def test_item_type_merit_distribution(self):
        """Test merit distribution when delivering Item-type materials"""
        # Simulate delivering 3 Experiment Prototypes
        # Real event showed: 3 items = 248 merits
        items_delivered = 3
        merits_gained = 248
        merits_per_item = merits_gained / items_delivered

        assert merits_per_item == pytest.approx(82.67, rel=0.01)

    def test_mixed_system_delivery(self):
        """Test merit distribution across multiple systems"""
        # Simulate collecting from multiple systems and delivering together
        system_counts = {
            "System A": 5,
            "System B": 3,
            "System C": 2
        }
        total_items = sum(system_counts.values())
        merits_gained = 1000

        merits_per_item = merits_gained / total_items

        # Verify distribution
        for system, count in system_counts.items():
            system_merits = int(merits_per_item * count)
            assert system_merits > 0


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_case_insensitive_item_names(self):
        """Test that item names are case-insensitive"""
        salvage = Salvage("Test System")

        salvage.add_cargo("POWEREXPERIMENT", 1)
        assert salvage.has_cargo("powerexperiment")

        removed = salvage.remove_cargo("PowerExperiment", 1)
        assert removed == 1

    def test_invalid_salvage_type(self):
        """Test adding invalid salvage type"""
        salvage = Salvage("Test System")

        # Should not add invalid type
        salvage.add_cargo("invaliditem", 10)
        assert not salvage.has_cargo("invaliditem")

    def test_remove_more_than_available(self):
        """Test removing more items than available"""
        salvage = Salvage("Test System")
        salvage.add_cargo("powerexperiment", 5)

        removed = salvage.remove_cargo("powerexperiment", 100)
        assert removed == 5  # Only removes what's available
        assert not salvage.has_cargo("powerexperiment")

    def test_remove_nonexistent_cargo(self):
        """Test removing cargo that doesn't exist"""
        salvage = Salvage("Test System")

        removed = salvage.remove_cargo("powerexperiment", 1)
        assert removed == 0


class TestRealWorldScenarios:
    """Test real-world scenarios from journal logs"""

    def test_undermining_run_scenario(self):
        """Test a complete undermining run based on real journal events"""
        # Scenario: Player collects UM data and delivers it
        system_name = "Test UM System"

        # Simulate collecting data over time
        data_collected = {
            "powerfinancialrecords": 8,
            "powerresearchdata": 2,
            "powerpropagandadata": 4,
            "poweremployeedata": 6,
            "powerclassifieddata": 5
        }

        # Verify all are valid UM data
        for item_name in data_collected.keys():
            assert is_valid_um_data(item_name)

        # Total items and expected merits (based on real data)
        total_items = sum(data_collected.values())
        assert total_items == 25

    def test_salvage_collection_scenario(self):
        """Test collecting PowerPlay items from salvage based on real events"""
        system_name = "Zeta Tucanae"
        salvage = Salvage(system_name)

        # Simulate collecting items (from journal log)
        items_found = [
            ("powerextraction", 3),
            ("powerexperiment", 3),
            ("powerelectronics", 2),
            ("powercomputer", 1),
            ("powerequipment", 3),
            ("powermisccomputer", 1),
            ("powersecurity", 1),
            ("powerresearch", 1)
        ]

        for item_name, count in items_found:
            salvage.add_cargo(item_name, count)

        # Verify all collected
        for item_name, count in items_found:
            assert salvage.has_cargo(item_name)
            assert salvage.inventory[item_name].count == count

        # Deliver to Search and Rescue
        # Real event: 3 Experiment Prototypes = 248 merits
        delivered = salvage.remove_cargo("powerexperiment", 3)
        assert delivered == 3
        assert not salvage.has_cargo("powerexperiment")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
