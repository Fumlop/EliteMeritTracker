# Changelog

All notable changes to EliteMeritTracker will be documented in this file.

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
