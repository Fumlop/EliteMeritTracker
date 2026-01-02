# EliteMeritTracker - Project Structure

## Overview
EliteMeritTracker is an EDMC (Elite Dangerous Market Connector) plugin for tracking Powerplay 2.0 merits. The codebase follows a modular architecture with clear separation of concerns.

## Directory Structure

```
EliteMeritTracker/
├── .github/              # GitHub workflows and CI configuration
├── assets/               # Images, icons, and other static resources
├── backup_legacy/        # Legacy code backup (pre-refactor)
├── data/                 # Runtime data storage (JSON files)
├── docs/                 # Documentation files
├── emt_core/             # Core utilities and business logic
├── emt_models/           # Data models and state management
├── emt_ppdata/           # Powerplay data validation modules
├── emt_tests/            # Comprehensive test suite (99% coverage target)
├── emt_ui/               # User interface components
├── system_data/          # System game data (too large for git)
├── load.py               # Main plugin entry point
├── pytest.ini            # Pytest configuration
├── CHANGELOG.md          # Version history
├── LICENSE               # License information
├── README.md             # User-facing documentation
└── structure.md          # This file
```

## Module Breakdown

### Entry Point
- **[load.py](load.py)** - Main plugin entry point
  - Implements EDMC plugin lifecycle hooks (`plugin_start`, `plugin_stop`, `journal_entry`)
  - Handles auto-update functionality (GitHub releases)
  - Coordinates between core, models, and UI modules
  - Processes Elite Dangerous journal events

### Core Package (`emt_core/`)
Core utilities and business logic shared across the application.

- **[__init__.py](emt_core/__init__.py)** - Package exports for convenient imports
- **[config.py](emt_core/config.py)** - Plugin configuration management
  - `ConfigPlugin` class for storing user preferences
  - Discord webhook settings
  - UI preferences (colors, filters)
- **[duplicate.py](emt_core/duplicate.py)** - Duplicate event detection
  - Tracks journal event IDs to prevent double-counting merits
  - `track_journal_event()` - Event deduplication
  - `process_powerplay_event()` - Process unique PP events
- **[logging.py](emt_core/logging.py)** - Centralized logging setup
  - Logger configuration
  - Plugin name constant
- **[report.py](emt_core/report.py)** - Merit report generation
  - `Report` class for formatting merit data
  - Clipboard and Discord webhook output
- **[state.py](emt_core/state.py)** - Global application state
  - Current system tracking
  - Session state management
- **[storage.py](emt_core/storage.py)** - File I/O utilities
  - `load_json()`, `save_json()` - JSON persistence
  - `get_plugin_dir()`, `get_data_dir()` - Path helpers
  - Legacy file migration support
- **[system_game_data.py](emt_core/system_game_data.py)** - Game data loading
  - Load system game data from compressed JSON
  - System lookup and caching

### Models Package (`emt_models/`)
Data models representing game entities and player state.

- **[__init__.py](emt_models/__init__.py)** - Package exports
- **[backpack.py](emt_models/backpack.py)** - Powerplay backpack tracking
  - `playerBackpack` - Tracks PP micro-resources (data items)
  - Persistence: `save_backpack()`, `load_backpack()`
- **[power.py](emt_models/power.py)** - Power allegiance tracking
  - `pledgedPower` - Stores player's pledged power
- **[ppcargo.py](emt_models/ppcargo.py)** - Powerplay cargo tracking
  - `ppcargo` - Tracks PP cargo in ship
- **[salvage.py](emt_models/salvage.py)** - Salvage item tracking
  - `Salvage` class - Individual salvage item
  - `salvageInventory` - Collection of salvage items
  - `VALID_POWERPLAY_SALVAGE_TYPES` - Whitelist of PP salvage
- **[system.py](emt_models/system.py)** - Star system tracking (**100% test coverage**)
  - `StarSystem` class - Individual system with merit counts
  - `PowerConflict` class - Multi-power acquisition tracking
  - `PowerConflictEntry` class - Individual power conflict entry
  - `SystemEncoder` - JSON encoder for system serialization
  - `systems` dict - All tracked systems
  - `loadSystems()`, `dumpSystems()` - Persistence
  - PowerPlay state tracking (Stronghold, Fortified, Exploited, Unoccupied)
  - Progress calculations and NET status
  - Copy text variable support (@MeritsValue, @System, @SystemStatus, etc.)

### UI Package (`emt_ui/`)
User interface components using tkinter.

- **[__init__.py](emt_ui/__init__.py)** - Package exports
- **[main.py](emt_ui/main.py)** - Main plugin frame
  - `TrackerFrame` class - EDMC main window widget
  - Session/total merit counters
  - Reset, details, copy/report buttons
  - Update notification UI
- **[details.py](emt_ui/details.py)** - Detailed system view window
  - `DetailedView` class - Sortable system table
  - Filters (system name, state, power)
  - CSV export functionality
  - Column sorting
  - Theme-aware styling
  - Copy text template support with variable replacement
- **[config.py](emt_ui/config.py)** - Plugin configuration UI
  - `create_config_frame()` - EDMC settings page
  - Discord webhook configuration
  - Update channel selection (stable/beta)
  - Copy text template configuration

### Powerplay Data Package (`emt_ppdata/`)
Validation modules for Powerplay micro-resources.

- **[__init__.py](emt_ppdata/__init__.py)** - Package exports
- **[undermining.py](emt_ppdata/undermining.py)** - Undermining data validation
  - `is_valid_um_data()` - Validates undermining data items
- **[reinforcement.py](emt_ppdata/reinforcement.py)** - Reinforcement data validation
  - `is_valid_reinf_data()` - Validates reinforcement data items
- **[acquisition.py](emt_ppdata/acquisition.py)** - Acquisition data validation
  - `is_valid_acq_data()` - Validates acquisition data items

### Tests Package (`emt_tests/`)
Comprehensive test suite with 99% coverage target.

- **[__init__.py](emt_tests/__init__.py)** - Test package initialization
- **[conftest.py](emt_tests/conftest.py)** - Pytest configuration and fixtures
  - Real journal event fixtures from actual gameplay
  - Mock infrastructure for EDMC dependencies
- **[mocks.py](emt_tests/mocks.py)** - EDMC module mocks
  - Mock config, tkinter, EDMCLogging, theme modules
  - Enables standalone testing outside EDMC
- **[run_tests.py](emt_tests/run_tests.py)** - Test runner
  - Runs all tests with coverage reporting
  - Enforces 99% coverage requirement
  - Generates HTML coverage reports
- **[test_system_model.py](emt_tests/test_system_model.py)** - StarSystem model tests
  - 64 tests covering all StarSystem functionality
  - **100% coverage** of emt_models/system.py
  - Tests: creation, acquisition, progress, state, serialization, edge cases
- **[test_copy_text_variables.py](emt_tests/test_copy_text_variables.py)** - Copy text tests
  - 17 tests for variable replacement (@MeritsValue, @System, @SystemStatus, etc.)
  - Variable replacement order validation
  - Template scenarios for all system types
- **[README.md](emt_tests/README.md)** - Test suite documentation
  - Test structure and organization
  - Running instructions
  - Coverage goals and status

Run tests: `python emt_tests/run_tests.py`

## Data Flow

### Journal Event Processing
1. Elite Dangerous writes event to journal file
2. EDMC calls `journal_entry()` in [load.py](load.py)
3. Event passed to `track_journal_event()` in [emt_core/duplicate.py](emt_core/duplicate.py)
4. If unique, `process_powerplay_event()` processes the event
5. Event data updates models ([emt_models/system.py](emt_models/system.py), [emt_models/backpack.py](emt_models/backpack.py), etc.)
6. UI ([emt_ui/main.py](emt_ui/main.py)) refreshes to display updated data
7. Changes persisted to JSON files via [emt_core/storage.py](emt_core/storage.py)

### Merit Tracking Flow
```
Journal Event → Duplicate Check → Merit Calculation → System Update → UI Refresh → JSON Save
```

### UI Data Flow
```
User Action → TrackerFrame → Models → emt_core/report.py → Output (Clipboard/Discord)
```

### Copy Text Variable Replacement
```
Template → Variable Expansion (@MeritsValue, @System, @SystemStatus, @CPControlling, @CPOpposition) → Output
```

**CRITICAL**: Variable replacement order matters!
- `@SystemStatus` must be replaced **BEFORE** `@System`
- Otherwise "Status" remnant appears in output
- Tested in [emt_tests/test_copy_text_variables.py](emt_tests/test_copy_text_variables.py)

## Data Storage

All runtime data stored in `data/` directory:
- `data/systems.json` - Star systems and merit counts (via [emt_models/system.py](emt_models/system.py))
- `data/power.json` - Power allegiance (via [emt_models/power.py](emt_models/power.py))
- `data/backpack.json` - PP micro-resources (via [emt_models/backpack.py](emt_models/backpack.py))
- `data/salvage.json` - Salvage inventory (via [emt_models/salvage.py](emt_models/salvage.py))

Storage handled by [emt_core/storage.py](emt_core/storage.py) with automatic migration from legacy locations.

## Plugin Lifecycle

### Startup (`plugin_start`)
1. Initialize logger
2. Load configuration from EDMC config
3. Load persisted data (systems, backpack, salvage, power)
4. Load system game data (if available)
5. Create UI frame
6. Check for updates (async)

### Runtime (`journal_entry`)
1. Receive journal event from EDMC
2. Deduplicate event
3. Update models based on event type:
   - `FSDJump` / `Location` → Update current system
   - `PowerplayMerits` → Track merits gained
   - `Backpack` → Update micro-resource inventory
   - `SellMicroResources` → Calculate merits from sale
4. Refresh UI
5. Auto-save data

### Shutdown (`plugin_stop`)
1. Save all data to JSON
2. Clean up resources

## Key Dependencies

- **EDMC API** - Plugin hooks and configuration
- **tkinter** - UI framework
- **requests** - GitHub API for auto-updates
- **myNotebook** - EDMC's notebook widget wrapper
- **pytest** - Test framework (dev dependency)
- **pytest-cov** - Coverage reporting (dev dependency)

## Configuration

Plugin configuration managed by [emt_core/config.py](emt_core/config.py):
- Discord webhook URL
- Update channel (stable/beta)
- Copy text template
- UI preferences (window size, column widths, filters)

Settings UI in [emt_ui/config.py](emt_ui/config.py) integrates with EDMC preferences.

## Theming

The plugin respects EDMC's theme settings:
- Light/dark theme support
- Color schemes defined in [emt_ui/main.py](emt_ui/main.py) and [emt_ui/details.py](emt_ui/details.py)
- Theme detection via `config.get_int('theme')`

## Auto-Update System

Implemented in [load.py](load.py):
- Fetches latest release from GitHub API
- Supports stable and beta/pre-release channels
- Downloads and extracts updates automatically
- Preserves user data during updates
- Requires EDMC restart after update

## Testing

Comprehensive test suite in `emt_tests/`:
- **Target**: 99% code coverage
- **Current**: 100% for emt_models/system.py
- **Tests**: 90 total (64 system model, 17 copy text, 9 edge cases)
- **Data Source**: Real journal events from actual gameplay
- **Standalone**: Mocks EDMC dependencies for standalone execution

### Test Coverage Status

| Module | Target | Current | Tests |
|--------|--------|---------|-------|
| emt_models/system.py | 99% | **100%** ✓ | test_system_model.py (64 tests) |
| emt_core/storage.py | 99% | 55% | TBD |
| emt_core/config.py | 99% | 61% | TBD |
| emt_core/logging.py | 99% | 83% | TBD |

See [emt_tests/README.md](emt_tests/README.md) for detailed test documentation.

## PowerPlay 2.0 Mechanics

The plugin tracks PowerPlay 2.0 mechanics:

### System States
- **Stronghold** - Power HQ systems (high CP threshold: 120,000)
- **Fortified** - Reinforced control systems (CP threshold: 120,000)
- **Exploited** - Standard control systems (CP threshold: 60,000)
- **Unoccupied** - Acquisition targets with conflict progress

### Acquisition Stages
- **Unoccupied** (<30% progress) - Early acquisition
- **Contested** (30-100% progress) - Active acquisition
- **Controlled** (>100% progress) - Acquisition complete

### Progress Tracking
- Control Progress (CP) for established systems
- Conflict Progress (decimal 0.0-1.0) for acquisitions
- NET calculations for reinforcement vs undermining

### Copy Text Variables
- `@MeritsValue` - Merit count
- `@System` - System name
- `@SystemStatus` - State abbreviation (ACQ, Fort, Stronghold, Exploited)
- `@CPControlling` - Controlling power and progress
- `@CPOpposition` - Opposition power and progress

## Legacy Code

`backup_legacy/` contains pre-refactor code:
- Old package structure (models/, core/, ui/ → emt_models/, emt_core/, emt_ui/)
- Kept for reference during migration
- Not used in production

## System Game Data

`system_data/` contains game reference data:
- `systems-game-data.json.gz` - Compressed system database
- Too large for git repository
- Distributed via releases
- Loaded by [emt_core/system_game_data.py](emt_core/system_game_data.py)
