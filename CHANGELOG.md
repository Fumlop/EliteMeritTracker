# Changelog

All notable changes to EliteMeritTracker will be documented in this file.

## [v0.4.300.1.030] - 2025-01-01

### Fixed
- **@CPOpposition Variable for Acquisition Systems**: Fixed to show 2nd place power and progress percentage
  - Acquisition systems now show both leading power and opposition power with percentages
  - Example: "@CPControlling" = "Felicia Winters 30.69%", "@CPOpposition" = "Arissa Lavigny-Duval 25.43%"
  - Previously showed "Opposition 0" for acquisition systems (undermining value is always 0)
  - Reinforcement/Undermining systems continue to show numeric values as before
  - Applied to Overview copy, detailed view copy, and Discord FSD jump reporting

## [v0.4.300.1.029] - 2025-01-01

### Fixed
- **Acquisition Systems Overview Bug**: Fixed `AttributeError: 'StarSystem' object has no attribute 'getProgressPercentage'`
  - Changed method calls from `getProgressPercentage()` to `getSystemProgressNumber()`
  - Acquisition systems now display correctly in Overview window without errors
  - Progress percentage calculation for copy text variables now works properly

## [v0.4.300.1.028] - 2025-01-01

### Fixed
- **Discord Webhook Not Working**: Fixed webhook URL retrieval from Tkinter StringVar
  - Changed from `getattr(configPlugin, "discordHook", None)` to `configPlugin.discordHook.get()`
  - Was returning the StringVar object instead of the actual URL string
  - Discord webhook now works correctly for sending reports

## [v0.4.300.1.027] - 2025-01-01

### Fixed
- **Logging Formatter Error**: Fixed `KeyError: 'osthreadid'` logging errors
  - Removed custom logging formatter that was incompatible with EDMC's logging system
  - Plugin now uses EDMC's native logging handlers for proper integration
  - Fixes spam of "Formatting field not found in record" errors in EDMC logs

### Changed
- **Backup File Creation**: Changed from every-save to update-only
  - Backup files (.backup) now only created during plugin auto-updates
  - Normal plugin shutdown no longer creates backup files
  - Reduces unnecessary file I/O and clutter in data/ directory
  - Atomic writes still protect against corruption during normal saves

## [v0.4.300.1.026] - 2025-12-29

### Fixed
- **Plugin Loading with Versioned Directory**: Fixed plugin loading failure when directory has version suffix
  - Plugin now strips version suffix from directory name (e.g., "EliteMeritTracker-0.4.300.1.025" → "EliteMeritTracker")
  - Fixes `ModuleNotFoundError: No module named 'EliteMeritTracker-0'` error
  - Works with any semantic version suffix pattern
  - No user action required - plugin auto-detects and works correctly

## [v0.4.300.1.025] - 2025-12-21

### Fixed
- **Copy Text Variable for Acquisition Systems**: Fixed `@CPControlling` to show progress percentage instead of 0 for acquisition systems
  - Acquisition systems (Unoccupied with progress) now show: "Felicia Winters 45.23%" instead of "Felicia Winters 0"
  - Reinforcement/Undermining systems continue to show: "Felicia Winters 8500" (reinforcement value)
  - Progress correctly calculated from decimal (0.0-1.0) to percentage
  - Applied to both Overview copy button and detailed view copy buttons

## [v0.4.300.1.024] - 2025-12-21

### Added
- **System Information Display**: Added Row 7 showing system allegiance, government, and population
  - Format: "Federation (Democracy) - Pop: 4.1M"
  - Population formatting: Shows complete numbers <100K, then uses K/M/B suffixes
  - All data extracted from FSDJump events (no external file dependencies)
  - Added SystemAllegiance, SystemGovernment, and Population fields to StarSystem model
  - Data persists through to_dict/from_dict serialization

### Added
- **Data Analysis Documentation**: Created DATA_CHECK.md analyzing all available journal data
  - Documents currently used vs. available data in FSDJump events
  - Identifies PowerPlay-relevant data vs. irrelevant data (mining, market prices)
  - Provides recommendations for future enhancements
  - Confirms economy/security data comes from journal events (no external lookup needed)

## [v0.4.300.1.023] - 2025-12-19

### Fixed
- **Unoccupied System Progress Display**: Fixed bug where PowerplayConflictProgress was treated as percentage instead of decimal
  - Journal provides ConflictProgress as decimal (0.0-1.0), now correctly converted to percentage
  - Systems now show correct progress: "Unoccupied 19.82%" instead of "Unoccupied 0.02%"
  - Fixed threshold comparisons for Contested (30%) and Controlled (100%) states
  - Affects all three usages: display percentage, state classification, and cycle net value

## [v0.4.300.1.022] - 2025-12-18

### Fixed
- **Data Corruption Prevention**: Implemented atomic JSON writes to prevent data loss if EDMC crashes during save
  - Uses temp file + rename pattern for atomic operations
  - Creates backup files before overwriting
  - Ensures original data remains intact if write fails
- **Location Validation**: Added validation after EDMC restart to prevent merit misattribution
  - Detects when player moved systems while EDMC was down
  - Logs warning and corrects system mismatch automatically
  - Prevents merits being attributed to wrong system
- **Autoupdate Data Protection**: Protected data/ directory from being overwritten during plugin autoupdate
  - Explicitly skips data/ directory when copying update files
  - Prevents accidental user data loss during updates

## [v0.4.300.1.021] - 2025-12-17

### Fixed
- **Stronghold Progress Display**: Fixed bug where Stronghold/Fortified/Exploited systems showed 0.0% when PowerplayStateControlProgress was provided as a decimal percentage (0.0-1.0) instead of raw CP values
  - Added logic to detect decimal percentage format (0 < x <= 1) and convert properly
  - Systems now correctly display percentages regardless of data format from game journal

## [v0.4.300.1.020] - 2025-12-17

### Fixed
- **Unoccupied System Display**: Systems with progress below 30% now correctly show as "Unoccupied X% by Power" instead of "Exploited X% by Power"

## [v0.4.300.1.019] - 2025-12-17

### Changed
- **Plugin Structure**: Renamed folders to avoid EDMC plugin loading conflicts
  - `ui/` → `emt_ui/`
  - `core/` → `emt_core/`
  - `models/` → `emt_models/`
  - `ppdata/` → `emt_ppdata/`
  - Auto-cleanup of old folders on startup (backed up to `backup_legacy/`)
  - Fixes import conflicts when other plugins use generic folder names

## [v0.4.300.1.018] - 2025-12-16

### Fixed
- **Progress Percentage Calculation**: Properly calculate progress percentages using CP thresholds
  - Stronghold: Progress CP / 120000 * 100
  - Fortified: Progress CP / 120000 * 100
  - Exploited: Progress CP / 60000 * 100
  - Now correctly shows 5.51% instead of 660761% for 6607 CP in Fortified system

## [v0.4.300.1.017] - 2025-12-16

### Fixed
- **Progress Display**: Fixed progress percentage calculation (partial fix)

## [v0.4.300.1.016] - 2025-12-16

### Added
- **Backpack View Window**: New "Show Backpack" button on overview
  - Three separate tables for Undermining, Acquisition, and Reinforcement data
  - Displays System, Count, and Data Type columns
  - Editable Count column (double-click to edit)
  - Sortable columns (click headers to sort)
  - Add New Entry button for manual data entry
  - Auto-saves all changes to backpack.json

### Changed
- **Backpack Data Structure**: Simplified JSON format (removed CP values tracking)

## [v0.4.300.1.014] - 2025-12-16

### Fixed
- **Detailed View Scrollbar**: Hide redundant outer scrollbar when in detailed view (treeview has its own)

### Changed
- **README**: Enhanced with detailed plugin description and updated data storage paths

## [v0.4.300.1.013] - 2025-12-16

### Fixed
- **Path Resolution**: Fixed plugin directory path resolution for files in subfolders (storage, logging, assets, debug)
- **Auto-Update**: Added legacy file cleanup with backup to `backup_legacy/` folder during updates

### Changed
- **Project Restructure**: Reorganized codebase into logical packages
  - `ui/` - UI components (main, details, config)
  - `models/` - Data models (system, power, backpack, salvage, ppcargo)
  - `ppdata/` - Powerplay data validators (undermining, reinforcement, acquisition)
  - `core/` - Core utilities (config, state, storage, logging, duplicate, report)
  - `tests/` - Test files
  - `data/` - JSON data storage with auto-migration from legacy location
  - `docs/` - Documentation files

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
