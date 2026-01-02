"""
Test Suite for StarSystem Model (emt_models/system.py)

Target Coverage: 99%
"""
import pytest
from emt_models.system import StarSystem, PowerConflictEntry, PowerConflict


class TestStarSystemCreation:
    """Test StarSystem object creation and initialization"""

    def test_create_empty_system(self):
        """Test creating system with no data"""
        system = StarSystem()
        assert system.StarSystem == "unknown system"
        assert system.Merits == 0
        assert system.Active == False
        assert system.PowerplayState == "no PP connection"
        assert system.ControllingPower == "no power"

    def test_create_from_fsdjump(self, sample_fsdjump_event):
        """Test creating system from FSDJump event"""
        system = StarSystem(sample_fsdjump_event, "TestCMDR")
        assert system.StarSystem == "Hyades Sector KC-U c3-9"
        assert system.PowerplayState == "Unoccupied"
        assert system.Population == 2070564
        assert system.SystemAllegiance == "Independent"
        assert system.SystemGovernment == "Corporate"
        assert system.PrimaryEconomy == "Military"
        assert system.SecondaryEconomy == "Extraction"
        assert system.SystemSecurity == "Low"

    def test_create_fortified_system(self, sample_fortified_system):
        """Test creating fortified system"""
        system = StarSystem(sample_fortified_system, "TestCMDR")
        assert system.StarSystem == "Czerno"
        assert system.PowerplayState == "Fortified"
        assert system.ControllingPower == "Felicia Winters"
        assert system.PowerplayStateReinforcement == 905
        assert system.PowerplayStateUndermining == 0


class TestAcquisitionSystems:
    """Test acquisition system handling"""

    def test_acquisition_single_power(self, sample_fsdjump_event):
        """Test acquisition system with one power"""
        system = StarSystem(sample_fsdjump_event, "TestCMDR")
        assert system.PowerplayState == "Unoccupied"
        assert len(system.PowerplayConflictProgress) == 1
        assert system.PowerplayConflictProgress[0].power == "Felicia Winters"
        assert system.PowerplayConflictProgress[0].progress == 0.306875

    def test_acquisition_controlling_power_from_conflict(self, sample_fsdjump_event):
        """Test that ControllingPower is derived from conflict progress for Unoccupied"""
        system = StarSystem(sample_fsdjump_event, "TestCMDR")
        # For Unoccupied systems, ControllingPower should be set from first conflict entry
        assert system.ControllingPower == "Felicia Winters"

    def test_acquisition_multi_power(self, sample_multi_power_acquisition):
        """Test acquisition system with multiple competing powers"""
        system = StarSystem(sample_multi_power_acquisition, "TestCMDR")
        assert len(system.PowerplayConflictProgress) == 2
        assert system.PowerplayConflictProgress[0].power == "Felicia Winters"
        assert system.PowerplayConflictProgress[0].progress == 0.4523
        assert system.PowerplayConflictProgress[1].power == "Arissa Lavigny-Duval"
        assert system.PowerplayConflictProgress[1].progress == 0.2543
        # Should be sorted by progress (highest first)
        assert system.PowerplayConflictProgress[0].progress > system.PowerplayConflictProgress[1].progress

    def test_acquisition_controlling_power_is_leading(self, sample_multi_power_acquisition):
        """Test that ControllingPower is the leading power in acquisition"""
        system = StarSystem(sample_multi_power_acquisition, "TestCMDR")
        assert system.ControllingPower == "Felicia Winters"


class TestSystemProgress:
    """Test system progress calculations"""

    def test_progress_acquisition_system(self, sample_fsdjump_event):
        """Test progress calculation for acquisition system"""
        system = StarSystem(sample_fsdjump_event, "TestCMDR")
        progress = system.getSystemProgressNumber()
        # 0.306875 * 100 = 30.6875
        assert progress == pytest.approx(30.6875, rel=0.01)

    def test_progress_fortified_system(self, sample_fortified_system):
        """Test progress calculation for fortified system"""
        system = StarSystem(sample_fortified_system, "TestCMDR")
        progress = system.getSystemProgressNumber()
        # 0.134008 * 100 = 13.4008
        assert progress == pytest.approx(13.4008, rel=0.01)

    def test_progress_stronghold_system(self, sample_stronghold_system):
        """Test progress calculation for stronghold system"""
        system = StarSystem(sample_stronghold_system, "TestCMDR")
        progress = system.getSystemProgressNumber()
        # Stronghold: 0.85 * 100 = 85.0
        assert progress == pytest.approx(85.0, rel=0.01)

    def test_progress_exploited_system(self, sample_exploited_system):
        """Test progress calculation for exploited system"""
        system = StarSystem(sample_exploited_system, "TestCMDR")
        progress = system.getSystemProgressNumber()
        # Exploited: 0.42 * 100 = 42.0
        assert progress == pytest.approx(42.0, rel=0.01)


class TestSystemStateText:
    """Test system state text generation"""

    def test_state_text_unoccupied_low_progress(self):
        """Test state text for unoccupied system with <30% progress"""
        event = {
            "event": "FSDJump",
            "StarSystem": "Test",
            "PowerplayState": "Unoccupied",
            "Powers": ["Felicia Winters"],
            "PowerplayConflictProgress": [{"Power": "Felicia Winters", "ConflictProgress": 0.25}]
        }
        system = StarSystem(event, "TestCMDR")
        assert system.getSystemStateText() == "Unoccupied"

    def test_state_text_contested(self):
        """Test state text for contested system (30-100%)"""
        event = {
            "event": "FSDJump",
            "StarSystem": "Test",
            "PowerplayState": "Unoccupied",
            "Powers": ["Felicia Winters"],
            "PowerplayConflictProgress": [{"Power": "Felicia Winters", "ConflictProgress": 0.50}]
        }
        system = StarSystem(event, "TestCMDR")
        assert system.getSystemStateText() == "Contested"

    def test_state_text_controlled(self):
        """Test state text for controlled system (>100%)"""
        event = {
            "event": "FSDJump",
            "StarSystem": "Test",
            "PowerplayState": "Unoccupied",
            "Powers": ["Felicia Winters"],
            "PowerplayConflictProgress": [{"Power": "Felicia Winters", "ConflictProgress": 1.05}]
        }
        system = StarSystem(event, "TestCMDR")
        assert system.getSystemStateText() == "Controlled"

    def test_state_text_fortified(self, sample_fortified_system):
        """Test state text for fortified system"""
        system = StarSystem(sample_fortified_system, "TestCMDR")
        assert system.getSystemStateText() == "Fortified"

    def test_state_text_stronghold(self, sample_stronghold_system):
        """Test state text for stronghold system"""
        system = StarSystem(sample_stronghold_system, "TestCMDR")
        assert system.getSystemStateText() == "Stronghold"

    def test_state_text_exploited(self, sample_exploited_system):
        """Test state text for exploited system"""
        system = StarSystem(sample_exploited_system, "TestCMDR")
        assert system.getSystemStateText() == "Exploited"


class TestSystemStatusShort:
    """Test @SystemStatus variable abbreviations"""

    def test_status_short_acquisition(self, sample_fsdjump_event):
        """Test that acquisition systems return 'ACQ'"""
        system = StarSystem(sample_fsdjump_event, "TestCMDR")
        assert system.getSystemStatusShort() == "ACQ"

    def test_status_short_fortified(self, sample_fortified_system):
        """Test that fortified systems return 'Fort'"""
        system = StarSystem(sample_fortified_system, "TestCMDR")
        assert system.getSystemStatusShort() == "Fort"

    def test_status_short_stronghold(self, sample_stronghold_system):
        """Test that stronghold systems return 'Stronghold'"""
        system = StarSystem(sample_stronghold_system, "TestCMDR")
        assert system.getSystemStatusShort() == "Stronghold"

    def test_status_short_exploited(self, sample_exploited_system):
        """Test that exploited systems return 'Exploited'"""
        system = StarSystem(sample_exploited_system, "TestCMDR")
        assert system.getSystemStatusShort() == "Exploited"

    def test_status_short_contested(self):
        """Test that contested systems return 'ACQ'"""
        event = {
            "event": "FSDJump",
            "StarSystem": "Test",
            "PowerplayState": "Unoccupied",
            "Powers": ["Felicia Winters"],
            "PowerplayConflictProgress": [{"Power": "Felicia Winters", "ConflictProgress": 0.50}]
        }
        system = StarSystem(event, "TestCMDR")
        assert system.getSystemStatusShort() == "ACQ"

    def test_status_short_controlled(self):
        """Test that controlled systems return 'ACQ'"""
        event = {
            "event": "FSDJump",
            "StarSystem": "Test",
            "PowerplayState": "Unoccupied",
            "Powers": ["Felicia Winters"],
            "PowerplayConflictProgress": [{"Power": "Felicia Winters", "ConflictProgress": 1.05}]
        }
        system = StarSystem(event, "TestCMDR")
        assert system.getSystemStatusShort() == "ACQ"


class TestPopulationFormatting:
    """Test population number formatting"""

    def test_population_under_100k(self):
        """Test population < 100K shows complete number"""
        event = {
            "event": "FSDJump",
            "StarSystem": "Test",
            "Population": 45678
        }
        system = StarSystem(event, "TestCMDR")
        # Population formatting happens in UI, but we store the raw value
        assert system.Population == 45678

    def test_population_100k_to_1m(self):
        """Test population 100K-999K"""
        event = {
            "event": "FSDJump",
            "StarSystem": "Test",
            "Population": 567890
        }
        system = StarSystem(event, "TestCMDR")
        assert system.Population == 567890

    def test_population_millions(self, sample_fsdjump_event):
        """Test population in millions"""
        system = StarSystem(sample_fsdjump_event, "TestCMDR")
        assert system.Population == 2070564

    def test_population_billions(self, sample_multi_power_acquisition):
        """Test population in billions"""
        system = StarSystem(sample_multi_power_acquisition, "TestCMDR")
        assert system.Population == 5000000000


class TestPowerPlayCycleStatus:
    """Test PowerPlay cycle status calculations"""

    def test_cycle_net_positive(self, sample_exploited_system):
        """Test NET calculation when reinforcement > undermining"""
        system = StarSystem(sample_exploited_system, "TestCMDR")
        net_text = system.getPowerPlayCycleNetStatusText()
        # 8500 reinforcement, 2300 undermining
        # NET = (8500 - 2300) / (8500 + 2300) * 100 = 6200 / 10800 * 100 = 57.41%
        assert "NET +" in net_text
        assert "57" in net_text

    def test_cycle_net_negative(self):
        """Test NET calculation when undermining > reinforcement"""
        event = {
            "event": "FSDJump",
            "StarSystem": "Test",
            "PowerplayState": "Exploited",
            "ControllingPower": "Felicia Winters",
            "Powers": ["Felicia Winters", "Zemina Torval"],
            "PowerplayStateReinforcement": 2000,
            "PowerplayStateUndermining": 5000
        }
        system = StarSystem(event, "TestCMDR")
        net_text = system.getPowerPlayCycleNetStatusText()
        # NET = (2000 - 5000) / (2000 + 5000) * 100 = -3000 / 7000 * 100 = -42.86%
        assert "NET -" in net_text or "NET " in net_text  # Could be "NET -42" or "NET -42"
        assert "42" in net_text

    def test_cycle_neutral(self):
        """Test NET calculation when both are 0"""
        event = {
            "event": "FSDJump",
            "StarSystem": "Test",
            "PowerplayState": "Exploited",
            "ControllingPower": "Felicia Winters",
            "Powers": ["Felicia Winters"],
            "PowerplayStateReinforcement": 0,
            "PowerplayStateUndermining": 0
        }
        system = StarSystem(event, "TestCMDR")
        net_text = system.getPowerPlayCycleNetStatusText()
        assert net_text == "Neutral"


class TestSerialization:
    """Test system serialization (to_dict/from_dict)"""

    def test_to_dict_acquisition(self, sample_fsdjump_event):
        """Test serializing acquisition system to dict"""
        system = StarSystem(sample_fsdjump_event, "TestCMDR")
        data = system.to_dict()

        assert data["StarSystem"] == "Hyades Sector KC-U c3-9"
        assert data["PowerplayState"] == "Unoccupied"
        assert data["ControllingPower"] == "Felicia Winters"
        assert len(data["PowerplayConflictProgress"]) == 1
        assert data["Population"] == 2070564
        assert data["SystemAllegiance"] == "Independent"

    def test_from_dict_reconstruction(self, sample_fsdjump_event):
        """Test reconstructing system from dict"""
        system1 = StarSystem(sample_fsdjump_event, "TestCMDR")
        data = system1.to_dict()

        system2 = StarSystem()
        system2.from_dict(data)

        assert system2.StarSystem == system1.StarSystem
        assert system2.PowerplayState == system1.PowerplayState
        assert system2.ControllingPower == system1.ControllingPower
        assert system2.Population == system1.Population

    def test_roundtrip_serialization(self, sample_multi_power_acquisition):
        """Test full roundtrip: object -> dict -> object"""
        system1 = StarSystem(sample_multi_power_acquisition, "TestCMDR")
        system1.Merits = 5000
        system1.Active = True

        data = system1.to_dict()

        system2 = StarSystem()
        system2.from_dict(data)

        assert system2.StarSystem == system1.StarSystem
        assert system2.Merits == system1.Merits
        assert system2.Active == system1.Active
        assert len(system2.PowerplayConflictProgress) == len(system1.PowerplayConflictProgress)


class TestPowerConflictEntry:
    """Test PowerConflictEntry model"""

    def test_create_conflict_entry(self):
        """Test creating conflict entry"""
        entry = PowerConflictEntry("Felicia Winters", 0.5)
        assert entry.power == "Felicia Winters"
        assert entry.progress == 0.5

    def test_conflict_entry_type_conversion(self):
        """Test type conversion in conflict entry"""
        entry = PowerConflictEntry("Test Power", "0.75")
        assert entry.power == "Test Power"
        assert entry.progress == 0.75


class TestPowerConflict:
    """Test PowerConflict model"""

    def test_create_from_dict_list(self):
        """Test creating PowerConflict from dict list"""
        data = [
            {"Power": "Felicia Winters", "ConflictProgress": 0.6},
            {"Power": "Arissa Lavigny-Duval", "ConflictProgress": 0.3}
        ]
        conflict = PowerConflict(data)

        assert len(conflict.entries) == 2
        # Should be sorted by progress (highest first)
        assert conflict.entries[0].power == "Felicia Winters"
        assert conflict.entries[0].progress == 0.6
        assert conflict.entries[1].power == "Arissa Lavigny-Duval"
        assert conflict.entries[1].progress == 0.3

    def test_create_from_lowercase_keys(self):
        """Test creating from dict with lowercase keys"""
        data = [
            {"power": "Test Power", "progress": 0.5}
        ]
        conflict = PowerConflict(data)

        assert len(conflict.entries) == 1
        assert conflict.entries[0].power == "Test Power"
        assert conflict.entries[0].progress == 0.5

    def test_empty_conflict_data(self):
        """Test creating PowerConflict with empty data"""
        conflict = PowerConflict([])
        assert len(conflict.entries) == 0

    def test_none_conflict_data(self):
        """Test creating PowerConflict with None"""
        conflict = PowerConflict(None)
        assert len(conflict.entries) == 0


class TestSystemEdgeCases:
    """Test edge cases for 100% coverage"""

    def test_parse_security_level_empty_string(self):
        """Test _parse_security_level with empty string"""
        system = StarSystem()
        result = system._parse_security_level("")
        assert result is None

    def test_parse_security_level_none(self):
        """Test _parse_security_level with None"""
        system = StarSystem()
        result = system._parse_security_level(None)
        assert result is None

    def test_safe_list_with_non_list(self):
        """Test _safe_list with non-list input"""
        system = StarSystem()
        assert system._safe_list("not a list") == []
        assert system._safe_list(None) == []
        assert system._safe_list(123) == []
        assert system._safe_list(["valid", "list"]) == ["valid", "list"]

    def test_update_system_method(self):
        """Test updateSystem method"""
        initial_event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Exploited",
            "ControllingPower": "Felicia Winters",
            "Powers": ["Felicia Winters"],
            "PowerplayStateReinforcement": 100
        }
        system = StarSystem(initial_event, "TestCMDR")
        assert system.Active == False

        # Update with new data
        update_event = {
            "event": "FSDJump",
            "PowerplayStateReinforcement": 500,
            "PowerplayStateUndermining": 200
        }
        system.updateSystem(update_event)
        assert system.Active == True
        assert system.PowerplayStateReinforcement == 500
        assert system.PowerplayStateUndermining == 200

    def test_add_merits_method(self):
        """Test addMerits method"""
        system = StarSystem()
        system.Merits = 100
        system.addMerits(50)
        assert system.Merits == 150
        system.addMerits(0)
        assert system.Merits == 150
        system.addMerits(-30)
        assert system.Merits == 120

    def test_set_reported_method(self):
        """Test setReported method"""
        system = StarSystem()
        assert system.reported == False
        system.setReported(True)
        assert system.reported == True
        system.setReported(False)
        assert system.reported == False
        system.setReported(1)  # Test with truthy value
        assert system.reported == True

    def test_get_powerplay_cycle_net_value_single_power(self):
        """Test getPowerplayCycleNetValue with single power (no undermining)"""
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Exploited",
            "ControllingPower": "Felicia Winters",
            "Powers": ["Felicia Winters"],  # Single power
            "PowerplayStateReinforcement": 5000,
            "PowerplayStateUndermining": 300  # Should be ignored
        }
        system = StarSystem(event, "TestCMDR")
        result = system.getPowerplayCycleNetValue()
        assert result == [5000, 0]  # Undermining should be 0 for single power

    def test_get_powerplay_cycle_net_value_multi_power(self):
        """Test getPowerplayCycleNetValue with multiple powers"""
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Exploited",
            "ControllingPower": "Felicia Winters",
            "Powers": ["Felicia Winters", "Arissa Lavigny-Duval"],  # Multiple powers
            "PowerplayStateReinforcement": 5000,
            "PowerplayStateUndermining": 300
        }
        system = StarSystem(event, "TestCMDR")
        result = system.getPowerplayCycleNetValue()
        assert result == [5000, 300]  # Undermining should be included

    def test_get_powerplay_cycle_net_value_no_conflict_progress(self):
        """Test getPowerplayCycleNetValue with no conflict progress"""
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Unoccupied",
            "Powers": ["Felicia Winters"],
            "PowerplayConflictProgress": []  # Empty conflict progress
        }
        system = StarSystem(event, "TestCMDR")
        result = system.getPowerplayCycleNetValue()
        assert result == [0, 0]

    def test_get_powerplay_cycle_net_value_acquisition(self):
        """Test getPowerplayCycleNetValue for acquisition system"""
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Unoccupied",
            "Powers": ["Felicia Winters"],
            "PowerplayConflictProgress": [{"Power": "Felicia Winters", "ConflictProgress": 0.4523}]
        }
        system = StarSystem(event, "TestCMDR")
        result = system.getPowerplayCycleNetValue()
        assert result == [45.23, 0]  # Percentage conversion

    def test_get_system_progress_stronghold_large_cp(self):
        """Test getSystemProgressNumber for Stronghold with large CP value"""
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Stronghold",
            "PowerplayStateControlProgress": 90000  # Large CP value
        }
        system = StarSystem(event, "TestCMDR")
        result = system.getSystemProgressNumber()
        assert result == pytest.approx((90000 / 120000) * 100, rel=0.01)

    def test_get_system_progress_fortified_large_cp(self):
        """Test getSystemProgressNumber for Fortified with large CP value"""
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Fortified",
            "PowerplayStateControlProgress": 60000  # Large CP value
        }
        system = StarSystem(event, "TestCMDR")
        result = system.getSystemProgressNumber()
        assert result == pytest.approx((60000 / 120000) * 100, rel=0.01)

    def test_get_system_progress_exploited_large_cp(self):
        """Test getSystemProgressNumber for Exploited with large CP value"""
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Exploited",
            "PowerplayStateControlProgress": 30000  # Large CP value
        }
        system = StarSystem(event, "TestCMDR")
        result = system.getSystemProgressNumber()
        assert result == pytest.approx((30000 / 60000) * 100, rel=0.01)

    def test_get_powerplay_cycle_net_status_neutral_zero_both(self):
        """Test getPowerPlayCycleNetStatusText when both are zero"""
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Exploited",
            "PowerplayStateReinforcement": 0,
            "PowerplayStateUndermining": 0
        }
        system = StarSystem(event, "TestCMDR")
        result = system.getPowerPlayCycleNetStatusText()
        assert result == "Neutral"

    def test_get_powerplay_cycle_net_status_equal_values(self):
        """Test getPowerPlayCycleNetStatusText when reinforcement equals undermining"""
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Exploited",
            "PowerplayStateReinforcement": 5000,
            "PowerplayStateUndermining": 5000
        }
        system = StarSystem(event, "TestCMDR")
        result = system.getPowerPlayCycleNetStatusText()
        assert result == "NET 0%"

    def test_get_system_state_text_unoccupied_no_conflict(self):
        """Test getSystemStateText for Unoccupied with no conflict progress"""
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Unoccupied",
            "PowerplayConflictProgress": []
        }
        system = StarSystem(event, "TestCMDR")
        result = system.getSystemStateText()
        assert result == "Unoccupied"

    def test_get_system_state_text_unknown_state(self):
        """Test getSystemStateText for unknown PowerplayState"""
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "SomeUnknownState"
        }
        system = StarSystem(event, "TestCMDR")
        result = system.getSystemStateText()
        assert result == "SomeUnknownState"

    def test_get_system_state_powerplay_unoccupied_no_conflict(self):
        """Test getSystemStatePowerPlay for Unoccupied with no conflict"""
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Unoccupied",
            "PowerplayConflictProgress": []
        }
        system = StarSystem(event, "TestCMDR")
        result = system.getSystemStatePowerPlay("Felicia Winters")
        assert result == ["NoPower", ""]

    def test_get_system_state_powerplay_unoccupied_single_power(self):
        """Test getSystemStatePowerPlay for Unoccupied with single power"""
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Unoccupied",
            "PowerplayConflictProgress": [{"Power": "Felicia Winters", "ConflictProgress": 0.45}]
        }
        system = StarSystem(event, "TestCMDR")
        result = system.getSystemStatePowerPlay("Felicia Winters")
        assert result == ["Felicia Winters", ""]

    def test_get_system_state_powerplay_unoccupied_multi_power(self):
        """Test getSystemStatePowerPlay for Unoccupied with multiple powers"""
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Unoccupied",
            "PowerplayConflictProgress": [
                {"Power": "Felicia Winters", "ConflictProgress": 0.45},
                {"Power": "Arissa Lavigny-Duval", "ConflictProgress": 0.25}
            ]
        }
        system = StarSystem(event, "TestCMDR")
        result = system.getSystemStatePowerPlay("Felicia Winters")
        assert result == ["Felicia Winters", "Arissa Lavigny-Duval"]

    def test_get_system_state_powerplay_exploited_single_power(self):
        """Test getSystemStatePowerPlay for Exploited with single power"""
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Exploited",
            "ControllingPower": "Felicia Winters",
            "Powers": ["Felicia Winters"]
        }
        system = StarSystem(event, "TestCMDR")
        result = system.getSystemStatePowerPlay("Felicia Winters")
        assert result == ["Felicia Winters", ""]

    def test_get_system_state_powerplay_exploited_multi_power(self):
        """Test getSystemStatePowerPlay for Exploited with multiple powers"""
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Exploited",
            "ControllingPower": "Felicia Winters",
            "Powers": ["Felicia Winters", "Arissa Lavigny-Duval"]
        }
        system = StarSystem(event, "TestCMDR")
        result = system.getSystemStatePowerPlay("Felicia Winters")
        assert result == ["Felicia Winters", "Arissa Lavigny-Duval"]

    def test_get_system_state_text_no_state(self):
        """Test getSystemStateText with no PowerplayState"""
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem"
        }
        system = StarSystem(event, "TestCMDR")
        system.PowerplayState = None
        result = system.getSystemStateText()
        assert result == "NoState"

    def test_power_conflict_non_dict_in_list(self):
        """Test PowerConflict with non-dict items in list"""
        data = [
            {"Power": "Valid Power", "ConflictProgress": 0.5},
            "InvalidString",
            123,
            None,
            {"Power": "Another Power", "ConflictProgress": 0.3}
        ]
        conflict = PowerConflict(data)
        # Only valid dict entries should be processed
        assert len(conflict.entries) == 2

    def test_get_system_state_powerplay_default_case(self):
        """Test getSystemStatePowerPlay for state that doesn't match any condition"""
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "UnknownState"
        }
        system = StarSystem(event, "TestCMDR")
        result = system.getSystemStatePowerPlay("Felicia Winters")
        assert result == ["NoPower", ""]

    def test_get_powerplay_cycle_net_status_impossible_total_zero(self):
        """Test getPowerPlayCycleNetStatusText when total is 0 but individual values are not

        This is a mathematical edge case that shouldn't occur in practice
        (e.g., negative reinforcement), but we test it for 100% coverage.
        """
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Exploited",
            "PowerplayStateReinforcement": 100,
            "PowerplayStateUndermining": 0
        }
        system = StarSystem(event, "TestCMDR")
        # Manually set to impossible state for edge case coverage
        system.PowerplayStateReinforcement = 100
        system.PowerplayStateUndermining = -100  # Impossible but tests line 202
        result = system.getPowerPlayCycleNetStatusText()
        # Total = 100 + (-100) = 0, should return "Neutral"
        assert result == "Neutral"

    def test_get_system_state_powerplay_unoccupied_conflict_without_power_attr(self):
        """Test getSystemStatePowerPlay with conflict entries missing 'power' attribute

        This tests the hasattr(item, 'power') check in line 270.
        """
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Unoccupied",
            "PowerplayConflictProgress": []
        }
        system = StarSystem(event, "TestCMDR")

        # Manually create conflict entries, one without 'power' attribute
        from emt_models.system import PowerConflictEntry
        entry1 = PowerConflictEntry("Felicia Winters", 0.5)
        entry2 = object()  # Object without 'power' attribute

        system.PowerplayConflictProgress = [entry1, entry2]
        result = system.getSystemStatePowerPlay("Felicia Winters")
        # Should only get the valid entry
        assert result == ["Felicia Winters", ""]


class TestFileIOFunctions:
    """Test file I/O functions for system storage"""

    def test_dump_and_load_systems(self):
        """Test dumpSystems and loadSystems functions"""
        from emt_models.system import systems, dumpSystems, loadSystems, StarSystem

        # Clear existing systems
        systems.clear()

        # Create test systems
        event1 = {
            "event": "FSDJump",
            "StarSystem": "TestSystem1",
            "PowerplayState": "Exploited",
            "ControllingPower": "Felicia Winters",
            "Powers": ["Felicia Winters"],
            "PowerplayStateReinforcement": 5000
        }
        system1 = StarSystem(event1, "TestCMDR")
        system1.Merits = 3000
        system1.Active = True
        systems["TestSystem1_TestCMDR"] = system1

        event2 = {
            "event": "FSDJump",
            "StarSystem": "TestSystem2",
            "PowerplayState": "Fortified",
            "ControllingPower": "Felicia Winters",
            "Powers": ["Felicia Winters"],
            "PowerplayStateReinforcement": 800
        }
        system2 = StarSystem(event2, "TestCMDR")
        system2.Merits = 500
        system2.reported = False
        systems["TestSystem2_TestCMDR"] = system2

        # Save systems (with backup)
        dumpSystems(create_backup=True)

        # Clear and reload
        systems.clear()
        loadSystems()

        # Verify systems were loaded
        assert "TestSystem1_TestCMDR" in systems
        assert systems["TestSystem1_TestCMDR"].Merits == 3000
        assert systems["TestSystem1_TestCMDR"].Active == True

    def test_dump_systems_filters_reported(self):
        """Test that dumpSystems filters out reported systems with no merits"""
        from emt_models.system import systems, dumpSystems, StarSystem

        systems.clear()

        # Create reported system with 0 merits (should be filtered out)
        event = {
            "event": "FSDJump",
            "StarSystem": "ReportedSystem",
            "PowerplayState": "Exploited"
        }
        system = StarSystem(event, "TestCMDR")
        system.Merits = 0
        system.reported = True
        system.Active = False
        systems["ReportedSystem_TestCMDR"] = system

        # This should not fail even though all systems are filtered
        dumpSystems(create_backup=False)

    def test_load_systems_with_empty_file(self):
        """Test loadSystems when file returns None/empty"""
        from emt_models.system import systems, loadSystems

        # This will call load_json which may return None if file doesn't exist
        # Should not crash
        systems.clear()
        loadSystems()  # Should handle None gracefully


class TestSystemEncoder:
    """Test SystemEncoder JSON serialization"""

    def test_system_encoder_with_starsystem(self):
        """Test SystemEncoder with StarSystem object"""
        import json
        from emt_models.system import SystemEncoder, StarSystem

        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Exploited"
        }
        system = StarSystem(event, "TestCMDR")
        system.Merits = 100

        # Encode to JSON
        json_str = json.dumps(system, cls=SystemEncoder)
        assert "TestSystem" in json_str
        assert "100" in json_str

    def test_system_encoder_with_powerconflictentry(self):
        """Test SystemEncoder with PowerConflictEntry object"""
        import json
        from emt_models.system import SystemEncoder, PowerConflictEntry

        entry = PowerConflictEntry("Felicia Winters", 0.5)
        json_str = json.dumps(entry, cls=SystemEncoder)
        assert "Felicia Winters" in json_str
        assert "0.5" in json_str

    def test_system_encoder_with_regular_object(self):
        """Test SystemEncoder falls back to default for non-system objects"""
        import json
        from emt_models.system import SystemEncoder

        # Regular dict should work fine
        data = {"key": "value"}
        json_str = json.dumps(data, cls=SystemEncoder)
        assert "value" in json_str

    def test_system_encoder_fallback_to_super(self):
        """Test SystemEncoder calls super().default() for non-serializable objects"""
        import json
        from emt_models.system import SystemEncoder

        # Create a non-serializable object (not StarSystem or PowerConflictEntry)
        class CustomObject:
            pass

        obj = CustomObject()

        # This should raise TypeError because super().default() will be called
        # and it can't serialize CustomObject
        with pytest.raises(TypeError):
            json.dumps(obj, cls=SystemEncoder)
