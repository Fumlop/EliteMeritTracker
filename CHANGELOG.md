# Changelog

All notable changes to EliteMeritTracker will be documented in this file.

## [v0.4.300.1.011] - 2025-12-16

### Fixed
- **NET Calculation**: Fixed incorrect NET percentage in detailed view - now shows actual difference between reinforcement and undermining as percentage of total

## [v0.4.300.1.010] - 2025-12-15

### Changed
- **Reset Button Behavior**: Trash icon now clears all cached systems except current system (merits reset to 0)
- **System Column Width**: Increased default view System column width from 20 to 28 characters for long system names
- **Detailed View System Column**: Fixed column width to 300px with no shrinking to prevent truncation

## [v0.4.300.1.009] - 2025-12-12

### Changed
- **Code Quality Polish (Phase 5)**
  - Translate German comments to English in `load.py`
  - Remove remaining hardcoded "Ganimed" default values in `power.py` and `system.py`

## [v0.4.300.1.008] - 2025-12-12

### Fixed
- **Error Handling Standardization (Phase 4)**
  - Replace bare `except:` clauses with specific exception types across multiple files
  - `pluginUI.py`: Use `Exception`, `ValueError`, `IndexError` for theme/parsing errors
  - `pluginDetailsUI.py`: Use `tk.TclError` for destroyed windows, specific types for parsing
  - `pluginConfigUI.py`: Use `ValueError`, `TypeError`, `IOError`, `OSError` for date/file errors

## [v0.4.300.1.007] - 2025-12-12

### Added
- **Architecture Improvements (Phase 3)**
  - New `plugin_state.py` centralized state manager replacing `sys.modules[__name__]` antipattern
  - State manager provides explicit, type-safe access to plugin state variables
  - Helper methods for SAR and delivery tracking (`init_sar_tracking`, `add_sar_count`, `reset_sar_tracking`, etc.)

### Changed
- Refactored `load.py` to use centralized state manager instead of module-level `this` variables
- Refactored `pluginUI.py` to use state manager for current system reference
- Renamed `journal_entry` parameter from `state` to `game_state` to avoid conflict with state manager import

### Fixed
- Removed duplicate `isinstance(o, ConfigPlugin)` check in `pluginConfig.py` ConfigEncoder

## [v0.4.300.1.006] - 2025-12-12

### Added
- **Code Consolidation (Phase 2)**
  - New `storage.py` utility for centralized JSON file I/O with error handling and backup
  - Unified `update_system_merits()` function with optional parameters for all merit update scenarios
  - Named constants `MERIT_CARGO_DIVISOR` and `MERIT_CARGO_MULTIPLIER` for cargo delivery formula

### Changed
- Refactored `backpack.py`, `salvage.py`, `system.py`, `power.py` to use centralized storage utility
- Merged 4 nearly identical merit update functions into single unified function
- Removed 60+ lines of duplicated file I/O code

## [v0.4.300.1.005] - 2025-12-12

### Fixed
- **Critical Bug Fixes & Cleanup (Phase 1)**
  - Fixed silent data loss in `system.py`: corrupted JSON files now create backup before clearing
  - Added 10-second timeout to GitHub API requests to prevent indefinite hangs
  - Added 30-second timeout to ZIP download requests for updates
  - Removed hardcoded "Ganimed" Commander fallback (now uses empty string)

### Removed
- Deleted unused `history.py` file (dead code with broken imports)
- Removed unused `crow` and `mainframerow` variables from `load.py`

## [v0.4.300.1.004] - 2025-12-12

### Added
- **Main UI Visual Improvements**
  - Split state word and details into separate widgets for cleaner layout
  - Dim labels vs bright values for visual separation (Pledged:, Rank:, Session:, Total:)
  - Color-coded NET value with arrows: green ▲ for positive, red ▼ for negative
  - Green highlight for positive merits gained in current system
  - Split `stateWord` and `stateDetails` widgets for independent styling

### Fixed
- Value labels (power, rank, session, total) now use explicit theme foreground color for dark/transparent themes

## [v0.4.300.1.003] - 2025-12-12

### Added
- **Power Info UI Overhaul**
  - Rounded buttons with hover effects
  - Detailed view with sortable Treeview table
  - Filter dropdowns for System, State, and Power
  - Zebra-striped rows with status-based coloring (danger/safe/warning/neutral)
  - Proper EDMC theme integration (background, foreground, highlights)
  - Centered column alignment for all columns except System name
  - CSV export functionality in detailed view

### Fixed
- Layout issues when switching between default and detailed views
- Window lifecycle errors when clicking after window closed
- Treeview theme matching on Windows (using clam theme base)

## [v0.4.300.1.002] - 2025-12-12

### Fixed
- **Import Conflict Resolution**
  - Renamed `log.py` to `merit_log.py` to avoid import conflicts with other EDMC plugins
  - Updated all 11 files to use `from merit_log import logger`
  - Fixes `ImportError: cannot import name 'logger' from 'log'` when another plugin (e.g., EDMC-SettlementDataTracker) has its own `log.py`

### Files Modified
- `merit_log.py` (renamed from `log.py`)
- `load.py`, `report.py`, `duplicate.py`, `backpack.py`, `salvage.py`, `ppcargo.py`, `system.py`, `power.py`, `pluginUI.py`, `pluginDetailsUI.py`, `pluginConfigUI.py` - Updated imports

## [v0.4.300.1.001] - 2025-12-02

### Added
- **PowerPlay Backpack Tracking System**
  - New backpack system to track PowerPlay data collection with 3 separate bags:
    - `umbag`: Undermining data (collected in enemy power territory)
    - `reinfbag`: Reinforcement data (collected in own power territory)
    - `acqbag`: Acquisition data (collected in neutral territory)
  - Automatic categorization based on controlling power vs pledged power
  - **Per-system tracking**: Items tracked per collection system for accurate merit distribution
  - JSON persistence for backpack state

- **Merit Distribution System**
  - Tracks which system each item was collected from
  - On hand-in (`DeliverPowerMicroResources`), items removed alphabetically by system
  - `PowerplayMerits` event distributes merits proportionally to collection systems
  - New `update_system_merits_for_collection()` function for backpack hand-ins

- **Journal Event Handling**
  - `BackpackChange` event: Tracks PowerPlay data collection (Added) and removal (Removed)
  - `DeliverPowerMicroResources` event: Captures system distribution for merit assignment
  - `PowerplayMerits` event: Distributes merits to collection systems
  - `ShipLocker` event: Cross-checks tracked state against game state (handles death, etc.)

- **PowerPlay Data Type Definitions**
  - `umdata.py`: Undermining data types (5 types)
  - `reinfdata.py`: Reinforcement data types (3 types)
  - `acqdata.py`: Acquisition data types (5 types)

- **Beta Update Feature** (Options Panel)
  - "Update to Pre-Release" button: Install latest GitHub pre-release
  - "Revert to Latest Release" button: Downgrade from beta to stable
  - Persistent beta flag in config
  - Status indicator showing current version type (Beta/Stable)

- **Test Suite**
  - Standalone test driver (`test_backpack.py`) with 8 tests
  - Tests cover all territory types, hand-in events, ShipLocker sync, and merit distribution

### Technical Details
- Bag structure: `{item_name: {system_name: count}}` for per-system tracking
- Items removed alphabetically by system name on hand-in
- Merits distributed proportionally based on item counts per system
- Territory detection logic: Neutral -> Own -> Enemy (order matters)
- ShipLocker sync aggregates multiple entries for same item (handles OwnerID variations)
- Legacy format compatibility for existing backpack.json files

### Files Added
- `backpack.py` - Main backpack tracking system with per-system tracking
- `umdata.py` - Undermining data type definitions
- `reinfdata.py` - Reinforcement data type definitions
- `acqdata.py` - Acquisition data type definitions
- `test_backpack.py` - Standalone test driver
- `CHANGELOG.md` - This file

### Files Modified
- `load.py` - Added event handlers, merit distribution, and beta update functions
- `pluginConfig.py` - Added beta flag with persistence
- `pluginConfigUI.py` - Added Beta Updates section in options panel
