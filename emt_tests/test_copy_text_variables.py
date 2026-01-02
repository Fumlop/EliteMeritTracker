"""
Test Suite for Copy Text Variable Replacement

Tests @MeritsValue, @System, @SystemStatus, @CPControlling, @CPOpposition

Target Coverage: 99%
"""
import pytest
from emt_models.system import StarSystem


class TestCopyTextVariableReplacement:
    """Test all copy text variable replacements"""

    def test_basic_variables(self, sample_fsdjump_event):
        """Test @MeritsValue and @System replacement"""
        system = StarSystem(sample_fsdjump_event, "TestCMDR")
        system.Merits = 3000

        template = "@MeritsValue @System"
        result = template.replace('@MeritsValue', str(system.Merits))
        result = result.replace('@System', system.StarSystem)

        assert result == "3000 Hyades Sector KC-U c3-9"

    def test_system_status_variable(self, sample_fsdjump_event):
        """Test @SystemStatus variable for acquisition system"""
        system = StarSystem(sample_fsdjump_event, "TestCMDR")
        system.Merits = 3000

        template = "@MeritsValue @SystemStatus @System"
        result = template.replace('@MeritsValue', str(system.Merits))
        # IMPORTANT: @SystemStatus must be replaced BEFORE @System
        result = result.replace('@SystemStatus', system.getSystemStatusShort())
        result = result.replace('@System', system.StarSystem)

        assert result == "3000 ACQ Hyades Sector KC-U c3-9"
        assert "Status" not in result  # Ensure no remnant from wrong order

    def test_system_status_fortified(self, sample_fortified_system):
        """Test @SystemStatus for fortified system"""
        system = StarSystem(sample_fortified_system, "TestCMDR")
        system.Merits = 300

        template = "@MeritsValue @SystemStatus @System"
        result = template.replace('@MeritsValue', str(system.Merits))
        result = result.replace('@SystemStatus', system.getSystemStatusShort())
        result = result.replace('@System', system.StarSystem)

        assert result == "300 Fort Czerno"

    def test_controlling_power_acquisition_single(self, sample_fsdjump_event):
        """Test @CPControlling for acquisition system with single power"""
        system = StarSystem(sample_fsdjump_event, "TestCMDR")

        template = "@CPControlling"
        if system.PowerplayConflictProgress and len(system.PowerplayConflictProgress) > 0:
            progress = system.getSystemProgressNumber()
            result = template.replace('@CPControlling', f"{system.ControllingPower} {progress:.2f}%")
        else:
            result = template.replace('@CPControlling', f"{system.ControllingPower} {system.PowerplayStateReinforcement}")

        assert result == "Felicia Winters 30.69%"

    def test_controlling_power_fortified(self, sample_fortified_system):
        """Test @CPControlling for fortified system"""
        system = StarSystem(sample_fortified_system, "TestCMDR")

        template = "@CPControlling"
        if system.PowerplayConflictProgress and len(system.PowerplayConflictProgress) > 0:
            progress = system.getSystemProgressNumber()
            result = template.replace('@CPControlling', f"{system.ControllingPower} {progress:.2f}%")
        else:
            result = template.replace('@CPControlling', f"{system.ControllingPower} {system.PowerplayStateReinforcement}")

        assert result == "Felicia Winters 905"

    def test_opposition_acquisition_no_second_power(self, sample_fsdjump_event):
        """Test @CPOpposition for acquisition with only one power"""
        system = StarSystem(sample_fsdjump_event, "TestCMDR")

        template = "@CPOpposition"
        if system.PowerplayConflictProgress and len(system.PowerplayConflictProgress) > 1:
            second_power = system.PowerplayConflictProgress[1]
            progress = second_power.progress * 100
            result = template.replace('@CPOpposition', f"{second_power.power} {progress:.2f}%")
        else:
            result = template.replace('@CPOpposition', f"Opposition {system.PowerplayStateUndermining}")

        assert result == "Opposition 0"

    def test_opposition_acquisition_with_second_power(self, sample_multi_power_acquisition):
        """Test @CPOpposition for acquisition with multiple powers"""
        system = StarSystem(sample_multi_power_acquisition, "TestCMDR")

        template = "@CPOpposition"
        if system.PowerplayConflictProgress and len(system.PowerplayConflictProgress) > 1:
            second_power = system.PowerplayConflictProgress[1]
            progress = second_power.progress * 100
            result = template.replace('@CPOpposition', f"{second_power.power} {progress:.2f}%")
        else:
            result = template.replace('@CPOpposition', f"Opposition {system.PowerplayStateUndermining}")

        assert result == "Arissa Lavigny-Duval 25.43%"

    def test_opposition_exploited(self, sample_exploited_system):
        """Test @CPOpposition for exploited system"""
        system = StarSystem(sample_exploited_system, "TestCMDR")

        template = "@CPOpposition"
        if system.PowerplayConflictProgress and len(system.PowerplayConflictProgress) > 1:
            second_power = system.PowerplayConflictProgress[1]
            progress = second_power.progress * 100
            result = template.replace('@CPOpposition', f"{second_power.power} {progress:.2f}%")
        else:
            result = template.replace('@CPOpposition', f"Opposition {system.PowerplayStateUndermining}")

        assert result == "Opposition 2300"

    def test_full_template_acquisition_single(self, sample_fsdjump_event):
        """Test complete template for acquisition system with single power"""
        system = StarSystem(sample_fsdjump_event, "TestCMDR")
        system.Merits = 3000

        template = "@MeritsValue @SystemStatus @System - @CPControlling vs @CPOpposition"

        # Replace in correct order
        result = template.replace('@MeritsValue', str(system.Merits))
        result = result.replace('@SystemStatus', system.getSystemStatusShort())
        result = result.replace('@System', system.StarSystem)

        # @CPControlling
        if system.PowerplayConflictProgress and len(system.PowerplayConflictProgress) > 0:
            progress = system.getSystemProgressNumber()
            result = result.replace('@CPControlling', f"{system.ControllingPower} {progress:.2f}%")
        else:
            result = result.replace('@CPControlling', f"{system.ControllingPower} {system.PowerplayStateReinforcement}")

        # @CPOpposition
        if system.PowerplayConflictProgress and len(system.PowerplayConflictProgress) > 1:
            second_power = system.PowerplayConflictProgress[1]
            progress = second_power.progress * 100
            result = result.replace('@CPOpposition', f"{second_power.power} {progress:.2f}%")
        else:
            result = result.replace('@CPOpposition', f"Opposition {system.PowerplayStateUndermining}")

        expected = "3000 ACQ Hyades Sector KC-U c3-9 - Felicia Winters 30.69% vs Opposition 0"
        assert result == expected

    def test_full_template_acquisition_multi(self, sample_multi_power_acquisition):
        """Test complete template for acquisition with multiple powers"""
        system = StarSystem(sample_multi_power_acquisition, "TestCMDR")
        system.Merits = 5000

        template = "@MeritsValue @SystemStatus @System - @CPControlling vs @CPOpposition"

        # Replace in correct order
        result = template.replace('@MeritsValue', str(system.Merits))
        result = result.replace('@SystemStatus', system.getSystemStatusShort())
        result = result.replace('@System', system.StarSystem)

        # @CPControlling
        if system.PowerplayConflictProgress and len(system.PowerplayConflictProgress) > 0:
            progress = system.getSystemProgressNumber()
            result = result.replace('@CPControlling', f"{system.ControllingPower} {progress:.2f}%")
        else:
            result = result.replace('@CPControlling', f"{system.ControllingPower} {system.PowerplayStateReinforcement}")

        # @CPOpposition
        if system.PowerplayConflictProgress and len(system.PowerplayConflictProgress) > 1:
            second_power = system.PowerplayConflictProgress[1]
            progress = second_power.progress * 100
            result = result.replace('@CPOpposition', f"{second_power.power} {progress:.2f}%")
        else:
            result = result.replace('@CPOpposition', f"Opposition {system.PowerplayStateUndermining}")

        expected = "5000 ACQ Test Acquisition System - Felicia Winters 45.23% vs Arissa Lavigny-Duval 25.43%"
        assert result == expected

    def test_full_template_fortified(self, sample_fortified_system):
        """Test complete template for fortified system"""
        system = StarSystem(sample_fortified_system, "TestCMDR")
        system.Merits = 300

        template = "@MeritsValue @SystemStatus @System - @CPControlling vs @CPOpposition"

        # Replace in correct order
        result = template.replace('@MeritsValue', str(system.Merits))
        result = result.replace('@SystemStatus', system.getSystemStatusShort())
        result = result.replace('@System', system.StarSystem)

        # @CPControlling
        if system.PowerplayConflictProgress and len(system.PowerplayConflictProgress) > 0:
            progress = system.getSystemProgressNumber()
            result = result.replace('@CPControlling', f"{system.ControllingPower} {progress:.2f}%")
        else:
            result = result.replace('@CPControlling', f"{system.ControllingPower} {system.PowerplayStateReinforcement}")

        # @CPOpposition
        if system.PowerplayConflictProgress and len(system.PowerplayConflictProgress) > 1:
            second_power = system.PowerplayConflictProgress[1]
            progress = second_power.progress * 100
            result = result.replace('@CPOpposition', f"{second_power.power} {progress:.2f}%")
        else:
            result = result.replace('@CPOpposition', f"Opposition {system.PowerplayStateUndermining}")

        expected = "300 Fort Czerno - Felicia Winters 905 vs Opposition 0"
        assert result == expected

    def test_variable_replacement_order_matters(self):
        """Test that variable replacement order is critical"""
        # Create a simple test system
        event = {
            "event": "FSDJump",
            "StarSystem": "TestSystem",
            "PowerplayState": "Unoccupied",
            "Powers": ["Felicia Winters"],
            "PowerplayConflictProgress": [{"Power": "Felicia Winters", "ConflictProgress": 0.5}]
        }
        system = StarSystem(event, "TestCMDR")
        system.Merits = 1000

        template = "@MeritsValue @SystemStatus @System"

        # WRONG ORDER: @System before @SystemStatus
        wrong_result = template.replace('@MeritsValue', str(system.Merits))
        wrong_result = wrong_result.replace('@System', system.StarSystem)  # This breaks @SystemStatus!
        wrong_result = wrong_result.replace('@SystemStatus', system.getSystemStatusShort())

        # This would produce: "1000 TestSystem ACQ" (wrong!) or "1000 TestSystemStatus" (remnant!)

        # CORRECT ORDER: @SystemStatus before @System
        correct_result = template.replace('@MeritsValue', str(system.Merits))
        correct_result = correct_result.replace('@SystemStatus', system.getSystemStatusShort())
        correct_result = correct_result.replace('@System', system.StarSystem)

        assert correct_result == "1000 ACQ TestSystem"
        assert "Status" not in correct_result


class TestVariableEdgeCases:
    """Test edge cases in variable replacement"""

    def test_no_population(self):
        """Test system with no population data"""
        event = {
            "event": "FSDJump",
            "StarSystem": "Unpopulated System",
            "PowerplayState": "Exploited",
            "ControllingPower": "Felicia Winters",
            "Powers": ["Felicia Winters"]
        }
        system = StarSystem(event, "TestCMDR")
        assert system.Population is None

    def test_no_powerplay_state(self):
        """Test system with no powerplay connection"""
        event = {
            "event": "FSDJump",
            "StarSystem": "Neutral System"
        }
        system = StarSystem(event, "TestCMDR")
        assert system.PowerplayState == "no PP connection"
        assert system.ControllingPower == "no power"

    def test_empty_conflict_progress(self):
        """Test system with empty conflict progress array"""
        event = {
            "event": "FSDJump",
            "StarSystem": "Test",
            "PowerplayState": "Unoccupied",
            "PowerplayConflictProgress": []
        }
        system = StarSystem(event, "TestCMDR")
        assert len(system.PowerplayConflictProgress) == 0
        assert system.getSystemProgressNumber() == 0

    def test_zero_merits(self):
        """Test template with zero merits"""
        event = {
            "event": "FSDJump",
            "StarSystem": "Test"
        }
        system = StarSystem(event, "TestCMDR")
        system.Merits = 0

        template = "@MeritsValue merits"
        result = template.replace('@MeritsValue', str(system.Merits))
        assert result == "0 merits"

    def test_very_long_system_name(self):
        """Test system with very long name"""
        event = {
            "event": "FSDJump",
            "StarSystem": "Hyades Sector KC-U c3-9 Very Long Extended System Name For Testing Purposes",
            "PowerplayState": "Fortified",
            "ControllingPower": "Felicia Winters",
            "Powers": ["Felicia Winters"],
            "PowerplayStateReinforcement": 100
        }
        system = StarSystem(event, "TestCMDR")
        system.Merits = 50

        template = "@MeritsValue @System - @CPControlling"
        result = template.replace('@MeritsValue', str(system.Merits))
        result = result.replace('@System', system.StarSystem)
        result = result.replace('@CPControlling', f"{system.ControllingPower} {system.PowerplayStateReinforcement}")

        assert system.StarSystem in result
        assert str(system.Merits) in result
