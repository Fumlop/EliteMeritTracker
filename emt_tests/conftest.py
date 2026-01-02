"""
Pytest configuration and fixtures for EliteMeritTracker tests
"""
import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
plugin_dir = Path(__file__).parent.parent
sys.path.insert(0, str(plugin_dir))

# Import mocks BEFORE any plugin imports
import emt_tests.mocks  # This installs the mocks into sys.modules


@pytest.fixture
def sample_fsdjump_event():
    """Sample FSDJump event from real journal"""
    return {
        "timestamp": "2026-01-02T21:26:54Z",
        "event": "FSDJump",
        "StarSystem": "Hyades Sector KC-U c3-9",
        "SystemAddress": 84180519395914,
        "StarPos": [-47.65625, -141.90625, -99.03125],
        "SystemAllegiance": "Independent",
        "SystemEconomy": "$economy_Military;",
        "SystemEconomy_Localised": "Military",
        "SystemSecondEconomy": "$economy_Extraction;",
        "SystemSecondEconomy_Localised": "Extraction",
        "SystemGovernment": "$government_Corporate;",
        "SystemGovernment_Localised": "Corporate",
        "SystemSecurity": "$SYSTEM_SECURITY_low;",
        "Population": 2070564,
        "Body": "Hyades Sector KC-U c3-9",
        "BodyID": 0,
        "BodyType": "Star",
        "PowerplayState": "Unoccupied",
        "Powers": ["Felicia Winters"],
        "PowerplayConflictProgress": [
            {
                "Power": "Felicia Winters",
                "ConflictProgress": 0.306875
            }
        ]
    }


@pytest.fixture
def sample_fortified_system():
    """Sample Fortified system event"""
    return {
        "timestamp": "2026-01-02T20:00:00Z",
        "event": "FSDJump",
        "StarSystem": "Czerno",
        "SystemAddress": 3107509783499,
        "StarPos": [-46.5, -140.75, -97.28125],
        "SystemAllegiance": "Independent",
        "SystemEconomy": "$economy_Refinery;",
        "SystemEconomy_Localised": "Refinery",
        "SystemSecondEconomy": "$economy_Extraction;",
        "SystemSecondEconomy_Localised": "Extraction",
        "SystemGovernment": "$government_Corporate;",
        "SystemGovernment_Localised": "Corporate",
        "SystemSecurity": "$SYSTEM_SECURITY_low;",
        "Population": 132302,
        "Body": "Czerno",
        "BodyID": 0,
        "BodyType": "Star",
        "PowerplayState": "Fortified",
        "ControllingPower": "Felicia Winters",
        "Powers": ["Felicia Winters"],
        "PowerplayStateControlProgress": 0.134008,
        "PowerplayStateReinforcement": 905,
        "PowerplayStateUndermining": 0
    }


@pytest.fixture
def sample_powerplay_merits():
    """Sample PowerplayMerits event"""
    return {
        "timestamp": "2026-01-02T21:30:00Z",
        "event": "PowerplayMerits",
        "Power": "Felicia Winters",
        "Merits": 10
    }


@pytest.fixture
def sample_multi_power_acquisition():
    """Sample acquisition system with multiple competing powers"""
    return {
        "timestamp": "2026-01-02T22:00:00Z",
        "event": "FSDJump",
        "StarSystem": "Test Acquisition System",
        "SystemAddress": 12345678901234,
        "StarPos": [0.0, 0.0, 0.0],
        "SystemAllegiance": "Federation",
        "SystemEconomy": "$economy_HighTech;",
        "SystemEconomy_Localised": "High Tech",
        "SystemGovernment": "$government_Democracy;",
        "SystemGovernment_Localised": "Democracy",
        "SystemSecurity": "$SYSTEM_SECURITY_high;",
        "Population": 5000000000,
        "Body": "Test Acquisition System",
        "BodyID": 0,
        "BodyType": "Star",
        "PowerplayState": "Unoccupied",
        "Powers": ["Felicia Winters", "Arissa Lavigny-Duval"],
        "PowerplayConflictProgress": [
            {
                "Power": "Felicia Winters",
                "ConflictProgress": 0.4523
            },
            {
                "Power": "Arissa Lavigny-Duval",
                "ConflictProgress": 0.2543
            }
        ]
    }


@pytest.fixture
def sample_stronghold_system():
    """Sample Stronghold system"""
    return {
        "timestamp": "2026-01-02T22:30:00Z",
        "event": "FSDJump",
        "StarSystem": "Test Stronghold",
        "SystemAddress": 98765432109876,
        "StarPos": [10.0, 20.0, 30.0],
        "SystemAllegiance": "Federation",
        "SystemEconomy": "$economy_Colony;",
        "SystemEconomy_Localised": "Colony",
        "SystemGovernment": "$government_Democracy;",
        "SystemGovernment_Localised": "Democracy",
        "SystemSecurity": "$SYSTEM_SECURITY_medium;",
        "Population": 125000,
        "Body": "Test Stronghold",
        "BodyID": 0,
        "BodyType": "Star",
        "PowerplayState": "Stronghold",
        "ControllingPower": "Felicia Winters",
        "Powers": ["Felicia Winters"],
        "PowerplayStateControlProgress": 0.85,
        "PowerplayStateReinforcement": 45000,
        "PowerplayStateUndermining": 5000
    }


@pytest.fixture
def sample_exploited_system():
    """Sample Exploited system with undermining"""
    return {
        "timestamp": "2026-01-02T23:00:00Z",
        "event": "FSDJump",
        "StarSystem": "Test Exploited",
        "SystemAddress": 11111111111111,
        "StarPos": [5.0, 10.0, 15.0],
        "SystemAllegiance": "Independent",
        "SystemEconomy": "$economy_Industrial;",
        "SystemEconomy_Localised": "Industrial",
        "SystemGovernment": "$government_Dictatorship;",
        "SystemGovernment_Localised": "Dictatorship",
        "SystemSecurity": "$SYSTEM_SECURITY_low;",
        "Population": 890000,
        "Body": "Test Exploited",
        "BodyID": 0,
        "BodyType": "Star",
        "PowerplayState": "Exploited",
        "ControllingPower": "Felicia Winters",
        "Powers": ["Felicia Winters", "Zemina Torval"],
        "PowerplayStateControlProgress": 0.42,
        "PowerplayStateReinforcement": 8500,
        "PowerplayStateUndermining": 2300
    }


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual functions"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for module interactions"
    )
    config.addinivalue_line(
        "markers", "system: System-level end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and stress tests"
    )
