# EliteMeritTracker Test Suite

Comprehensive test suite for EliteMeritTracker EDMC plugin.

**Coverage Target: 99%**

## Test Structure

```
emt_tests/
├── conftest.py                      # Pytest configuration and fixtures
├── test_system_model.py            # StarSystem model tests
├── test_copy_text_variables.py     # Copy text variable tests
├── run_tests.py                    # Test runner with coverage
└── README.md                       # This file
```

## Test Data Sources

Tests use real journal event data from:
- `E:\DATA\EliteDangerous\Journal.2026-01-02T212654.01.log`

Sample events include:
- **FSDJump** to acquisition systems (Hyades Sector KC-U c3-9)
- **FSDJump** to fortified systems (Czerno)
- **PowerplayMerits** events
- Multi-power acquisition scenarios
- Stronghold and Exploited systems

## Running Tests

### Prerequisites

```bash
pip install pytest pytest-cov
```

### Run All Tests

```bash
cd c:\Users\waldp\AppData\Local\EDMarketConnector\plugins\EliteMeritTracker
python emt_tests/run_tests.py
```

### Run Specific Test File

```bash
pytest emt_tests/test_system_model.py -v
```

### Run Specific Test Class

```bash
pytest emt_tests/test_system_model.py::TestAcquisitionSystems -v
```

### Run Specific Test

```bash
pytest emt_tests/test_system_model.py::TestAcquisitionSystems::test_acquisition_single_power -v
```

### Run with Coverage

```bash
pytest emt_tests/ --cov=emt_models --cov=emt_core --cov=emt_ui --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`

### Run Tests by Marker

```bash
# Run only unit tests
pytest emt_tests/ -m unit

# Run only integration tests
pytest emt_tests/ -m integration

# Run only system tests
pytest emt_tests/ -m system

# Run only performance tests
pytest emt_tests/ -m performance
```

## Test Coverage

### Current Test Modules

#### test_system_model.py
Covers `emt_models/system.py` - **100% COVERAGE ACHIEVED** (64 tests):
- ✓ StarSystem creation and initialization
- ✓ Acquisition system handling (single and multi-power)
- ✓ ControllingPower derivation from conflict progress
- ✓ Progress calculations (all system types)
- ✓ System state text generation
- ✓ @SystemStatus abbreviations
- ✓ Population storage
- ✓ PowerPlay cycle status (NET calculations)
- ✓ Serialization (to_dict/from_dict)
- ✓ PowerConflictEntry model
- ✓ PowerConflict model
- ✓ Edge cases: updateSystem, addMerits, setReported
- ✓ Edge cases: _parse_security_level, _safe_list
- ✓ Edge cases: getPowerplayCycleNetValue (single/multi power)
- ✓ Edge cases: getSystemStatePowerPlay (all branches)
- ✓ File I/O: dumpSystems, loadSystems
- ✓ SystemEncoder JSON serialization

#### test_copy_text_variables.py
Covers copy text variable replacement:
- ✓ @MeritsValue replacement
- ✓ @System replacement
- ✓ @SystemStatus replacement
- ✓ @CPControlling replacement (acquisition and fortified)
- ✓ @CPOpposition replacement (single and multi-power)
- ✓ Variable replacement order (critical!)
- ✓ Complete template scenarios
- ✓ Edge cases (no population, no powerplay, etc.)

### Coverage Goals

| Module | Target | Current | Tests |
|--------|--------|---------|-------|
| emt_models/system.py | 99% | **100%** ✓ | test_system_model.py (64 tests) |
| emt_core/storage.py | 99% | 55% | TBD |
| emt_core/config.py | 99% | 61% | TBD |
| emt_core/logging.py | 99% | 83% | TBD |
| emt_ui/details.py | 99% | 0% | test_copy_text_variables.py (17 tests) |
| load.py | 95% | N/A | TBD (UI interactions excluded) |

## Test Scenarios

### Acquisition Systems

1. **Single Power Acquisition**
   - System: Hyades Sector KC-U c3-9
   - Progress: 30.69%
   - Expected: ControllingPower = "Felicia Winters"
   - Expected: @SystemStatus = "ACQ"

2. **Multi-Power Acquisition**
   - System: Test Acquisition System
   - Powers: Felicia Winters (45.23%), Arissa Lavigny-Duval (25.43%)
   - Expected: Leading power shown in @CPControlling
   - Expected: Second power shown in @CPOpposition

3. **Acquisition Stages**
   - Unoccupied (<30%): @SystemStatus = "ACQ"
   - Contested (30-100%): @SystemStatus = "ACQ"
   - Controlled (>100%): @SystemStatus = "ACQ"

### Reinforcement/Undermining Systems

1. **Fortified System**
   - System: Czerno
   - Reinforcement: 905
   - Expected: @SystemStatus = "Fort"
   - Expected: @CPControlling = "Felicia Winters 905"

2. **Stronghold System**
   - Progress: 85%
   - Expected: @SystemStatus = "Stronghold"

3. **Exploited System**
   - Reinforcement: 8500, Undermining: 2300
   - Expected: @SystemStatus = "Exploited"
   - Expected: NET +57.41%

### Copy Text Variables

1. **Variable Replacement Order**
   - CRITICAL: @SystemStatus MUST be replaced BEFORE @System
   - Wrong order leaves "Status" remnant

2. **Complete Templates**
   ```
   Template: "@MeritsValue @SystemStatus @System - @CPControlling vs @CPOpposition"

   Acquisition (single): "3000 ACQ Hyades Sector KC-U c3-9 - Felicia Winters 30.69% vs Opposition 0"
   Acquisition (multi):  "5000 ACQ Test System - Felicia Winters 45.23% vs Arissa 25.43%"
   Fortified:            "300 Fort Czerno - Felicia Winters 905 vs Opposition 0"
   ```

## Test Fixtures

All fixtures are defined in `conftest.py`:

- `sample_fsdjump_event` - Real FSDJump to Hyades Sector KC-U c3-9
- `sample_fortified_system` - Fortified system (Czerno)
- `sample_powerplay_merits` - PowerplayMerits event
- `sample_multi_power_acquisition` - Acquisition with 2 powers
- `sample_stronghold_system` - Stronghold system
- `sample_exploited_system` - Exploited with undermining

## Pass Criteria

**99% Code Coverage Required**

Tests will FAIL if:
- Any test case fails
- Code coverage drops below 99%
- Any critical function is untested

## Future Test Additions

- [ ] Storage tests (JSON save/load)
- [ ] Config tests (version, settings)
- [ ] Discord webhook tests
- [ ] UI interaction tests (if possible in headless mode)
- [ ] Performance tests (large datasets)
- [ ] Stress tests (thousands of systems)

## CI/CD Integration

To run in CI/CD pipeline:

```bash
python emt_tests/run_tests.py --junitxml=test-results.xml
```

## Contributing

When adding new features:
1. Write tests FIRST (TDD)
2. Ensure 99% coverage maintained
3. Add fixtures for new event types
4. Update this README

## Troubleshooting

### Import Errors

If you get import errors, ensure the plugin directory is in your Python path:

```python
import sys
sys.path.insert(0, 'c:/Users/waldp/AppData/Local/EDMarketConnector/plugins/EliteMeritTracker')
```

### Coverage Not Meeting 99%

Run with missing lines report:

```bash
pytest emt_tests/ --cov=emt_models --cov-report=term-missing
```

This shows which lines are not covered.

## License

Same as EliteMeritTracker main project.
