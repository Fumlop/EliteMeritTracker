# EliteMeritTracker - Project Structure

## Overview
EliteMeritTracker is an EDMC (Elite Dangerous Market Connector) plugin for tracking Powerplay 2.0 merits. The codebase follows a modular architecture with clear separation of concerns.

## Directory Structure

```
EliteMeritTracker/
├── .github/              # GitHub workflows and CI configuration
├── assets/               # Images, icons, and other static resources
├── core/                 # Core utilities and business logic
├── data/                 # Runtime data storage (JSON files)
├── docs/                 # Documentation files
├── models/               # Data models and state management
├── ppdata/               # Powerplay data validation modules
├── tests/                # Unit tests
├── ui/                   # User interface components
├── load.py               # Main plugin entry point
├── CHANGELOG.md          # Version history
├── LICENSE               # License information
└── README.md             # User-facing documentation
```

## Module Breakdown

### Entry Point
- **[load.py](load.py)** - Main plugin entry point
  - Implements EDMC plugin lifecycle hooks (`plugin_start`, `plugin_stop`, `journal_entry`)
  - Handles auto-update functionality (GitHub releases)
  - Coordinates between core, models, and UI modules
  - Processes Elite Dangerous journal events

### Core Package (`core/`)
Core utilities and business logic shared across the application.

- **[__init__.py](core/__init__.py)** - Package exports for convenient imports
- **[config.py](core/config.py)** - Plugin configuration management
  - `ConfigPlugin` class for storing user preferences
  - Discord webhook settings
  - UI preferences (colors, filters)
- **[duplicate.py](core/duplicate.py)** - Duplicate event detection
  - Tracks journal event IDs to prevent double-counting merits
  - `track_journal_event()` - Event deduplication
  - `process_powerplay_event()` - Process unique PP events
- **[logging.py](core/logging.py)** - Centralized logging setup
  - Logger configuration
  - Plugin name constant
- **[report.py](core/report.py)** - Merit report generation
  - `Report` class for formatting merit data
  - Clipboard and Discord webhook output
- **[state.py](core/state.py)** - Global application state
  - Current system tracking
  - Session state management
- **[storage.py](core/storage.py)** - File I/O utilities
  - `load_json()`, `save_json()` - JSON persistence
  - `get_plugin_dir()`, `get_data_dir()` - Path helpers
  - Legacy file migration support

### Models Package (`models/`)
Data models representing game entities and player state.

- **[__init__.py](models/__init__.py)** - Package exports
- **[backpack.py](models/backpack.py)** - Powerplay backpack tracking
  - `playerBackpack` - Tracks PP micro-resources (data items)
  - Persistence: `save_backpack()`, `load_backpack()`
- **[power.py](models/power.py)** - Power allegiance tracking
  - `pledgedPower` - Stores player's pledged power
- **[ppcargo.py](models/ppcargo.py)** - Powerplay cargo tracking
  - `ppcargo` - Tracks PP cargo in ship
- **[salvage.py](models/salvage.py)** - Salvage item tracking
  - `Salvage` class - Individual salvage item
  - `salvageInventory` - Collection of salvage items
  - `VALID_POWERPLAY_SALVAGE_TYPES` - Whitelist of PP salvage
- **[system.py](models/system.py)** - Star system tracking
  - `StarSystem` class - Individual system with merit counts
  - `systems` dict - All tracked systems
  - `loadSystems()`, `dumpSystems()` - Persistence
  - Merit calculations (combat, cargo, data)

### UI Package (`ui/`)
User interface components using tkinter.

- **[__init__.py](ui/__init__.py)** - Package exports
- **[main.py](ui/main.py)** - Main plugin frame
  - `TrackerFrame` class - EDMC main window widget
  - Session/total merit counters
  - Reset, details, copy/report buttons
  - Update notification UI
- **[details.py](ui/details.py)** - Detailed system view window
  - `DetailedView` class - Sortable system table
  - Filters (system name, state, power)
  - CSV export functionality
  - Column sorting
  - Theme-aware styling
- **[config.py](ui/config.py)** - Plugin configuration UI
  - `create_config_frame()` - EDMC settings page
  - Discord webhook configuration
  - Update channel selection (stable/beta)

### Powerplay Data Package (`ppdata/`)
Validation modules for Powerplay micro-resources.

- **[__init__.py](ppdata/__init__.py)** - Package exports
- **[undermining.py](ppdata/undermining.py)** - Undermining data validation
  - `is_valid_um_data()` - Validates undermining data items
- **[reinforcement.py](ppdata/reinforcement.py)** - Reinforcement data validation
  - `is_valid_reinf_data()` - Validates reinforcement data items
- **[acquisition.py](ppdata/acquisition.py)** - Acquisition data validation
  - `is_valid_acq_data()` - Validates acquisition data items

### Tests Package (`tests/`)
Unit tests for the plugin.

- **[__init__.py](tests/__init__.py)** - Test package initialization
- **[test_backpack.py](tests/test_backpack.py)** - Backpack model tests

## Data Flow

### Journal Event Processing
1. Elite Dangerous writes event to journal file
2. EDMC calls `journal_entry()` in [load.py](load.py)
3. Event passed to `track_journal_event()` in [core/duplicate.py](core/duplicate.py)
4. If unique, `process_powerplay_event()` processes the event
5. Event data updates models ([models/system.py](models/system.py), [models/backpack.py](models/backpack.py), etc.)
6. UI ([ui/main.py](ui/main.py)) refreshes to display updated data
7. Changes persisted to JSON files via [core/storage.py](core/storage.py)

### Merit Tracking Flow
```
Journal Event → Duplicate Check → Merit Calculation → System Update → UI Refresh → JSON Save
```

### UI Data Flow
```
User Action → TrackerFrame → Models → core/report.py → Output (Clipboard/Discord)
```

## Data Storage

All runtime data stored in `data/` directory:
- `data/systems.json` - Star systems and merit counts (via [models/system.py](models/system.py))
- `data/power.json` - Power allegiance (via [models/power.py](models/power.py))
- `data/backpack.json` - PP micro-resources (via [models/backpack.py](models/backpack.py))
- `data/salvage.json` - Salvage inventory (via [models/salvage.py](models/salvage.py))

Storage handled by [core/storage.py](core/storage.py) with automatic migration from legacy locations.

## Plugin Lifecycle

### Startup (`plugin_start`)
1. Initialize logger
2. Load configuration from EDMC config
3. Load persisted data (systems, backpack, salvage, power)
4. Create UI frame
5. Check for updates (async)

### Runtime (`journal_entry`)
1. Receive journal event from EDMC
2. Deduplicate event
3. Update models based on event type
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

## Configuration

Plugin configuration managed by [core/config.py](core/config.py):
- Discord webhook URL
- Update channel (stable/beta)
- UI preferences (window size, column widths, filters)

Settings UI in [ui/config.py](ui/config.py) integrates with EDMC preferences.

## Theming

The plugin respects EDMC's theme settings:
- Light/dark theme support
- Color schemes defined in [ui/main.py](ui/main.py) and [ui/details.py](ui/details.py)
- Theme detection via `config.get_int('theme')`

## Auto-Update System

Implemented in [load.py](load.py):
- Fetches latest release from GitHub API
- Supports stable and beta/pre-release channels
- Downloads and extracts updates automatically
- Preserves user data during updates
- Requires EDMC restart after update
