# Changelog

All notable changes to EliteMeritTracker will be documented in this file.

## [v0.4.400.4.000] - 2026-09-20

### Added
- The store is a SQLite database, `%LOCALAPPDATA%\EliteMeritTracker\db\merittracker.db`.
  Outside the plugin folder, so a manual reinstall no longer takes the merit
  history with it. One connection per piece of work, WAL, `PRAGMA user_version`
  for the schema, and each row keeping the whole record as JSON beside the
  columns a lookup needs.
- `data\*.json` is imported into it once, at the first start, by
  `emt_core/migrate.py`. A marker file `db\migrate.done` stops it running
  again; the same report is committed to the `meta` table, so a deleted marker
  rewrites the file instead of importing a second time. Nothing is deleted -
  `data\*.json` stays where it is, and removing the `db` folder is the way
  back.
- `database.backup()` keeps the newest two copies in `dbackups\`, and only
  writes one when the database passes `PRAGMA quick_check` and has rows in it.
- `emt_ui/palette.py`: the theme colours and the eight status tags in one
  module with no tkinter import, plus `tag_for()` holding the progress-band
  rule that was inlined in the table, and `contrast()` for checking the result.
- Screenshots in `docs/pic/`, rendered from the real widget code with example
  data by `lab/shoot_overview.py`.

- Every `PowerplayMerits` decision is logged to the `merit_events` table with
  what the server reported, what the ledger credited and why - credited,
  parked, restored, unwound or ignored. The resend threshold was tuned on 5
  journals / 84 events; this is what lets it be re-checked against a season.
- A large award rejected as a resend now survives a restart. It is parked
  until a later event's base proves the server held it, and closing EDMC in
  between used to lose those merits for good. The baseline is stored with it,
  because `_resolve_pending` allows no more than `base - baseline`: a ledger
  that took its baseline from the next snapshot had exactly zero room and
  could never give a parked award back.

- Merits are written when they move, not every five minutes. The 5-minute
  autosave timer is gone. A merit event now writes only the systems it
  changed, together with the ledger, in one transaction: about 7 ms whatever
  the system count, where rewriting every row is 100 ms at 5,000. A crash used
  to cost up to five minutes of merits.
  The write covers every system an event touched, not just the one you are in
  - a server correction takes merits off the systems that earned them, and a
  restored award gives them back to a fourth. The ledger's baseline and parked
  awards go with them, because merits kept without the ledger that explains
  them would hand a parked award back twice or never.
  Removing the timer also removes the thread that raced the journal callback
  over the `systems` dict.

### Changed
- The Overview window is three tabs - Session, Systems, Shiplocker - in one
  window, replacing the Show Detailed View toggle, the separate Shiplocker
  Toplevel and the two near-identical count dialogs. Every draw rebuilds the
  whole tab from a state dict kept outside the widgets, so scroll position,
  folds, sort and filters survive it.
- The window opens at 70 % of the screen, capped at 80 %, centred. The stored
  `power_info_width` / `power_info_height` are no longer read or written: a
  size saved on a large monitor opened off-screen on a laptop.
- `dumpSystems()` no longer drops reported or zero-merit systems. That filter
  is what made history impossible; the Session tab filters on `Merits > 0`
  instead.
- `loadSystems()` keys the `systems` dict by `StarSystem`, matching what
  `load.py` already did everywhere else.
- Rows are keyed by commander as well as system, so two commanders no longer
  share one row.
- `create_backup=` is gone from the four save functions. `load.py` takes one
  copy of the database before an update instead of four copies of four files.

### Fixed
- Two commanders on one install no longer mix. `plugin_start3` reads the
  models before EDMC replays a single journal line, so they were always read
  under whoever saved last; nothing reloaded when `LoadGame` finally named the
  pilot, and the next save wrote one commander's systems, merits and
  shiplocker under the other's name. The models are reloaded when the name
  turns out to be different, and rows saved while the pilot was unknown are
  adopted by the first commander to claim them rather than stranded - a
  commander who already owns rows never takes another's.
- Resetting a system no longer undoes itself. `save_systems()` wrote with
  `INSERT OR REPLACE` and never deleted, so a system dropped from memory kept
  its row and came back with its old merits at the next start. The JSON store
  rewrote the whole file, which is why Reset used to stick. It now deletes the
  rows for that commander that are no longer in memory - and an empty model is
  a no-op rather than a mass delete, so a failed load cannot become data loss.
- A database that cannot be read no longer destroys the backpack and the
  salvage hold. `load_inventory()` returned `[]` on failure, the loaders
  cleared the bags before reading, and the next save - which deletes and
  reinserts - wrote that emptiness over the stored rows. It returns `None` on
  failure now and the loaders keep what they have.
- The migration pins `meta['commander']` to the name it keyed the imported
  rows with. It only wrote `meta['power']`, so a `power.json` carrying a real
  commander name would have made the whole import invisible at the next start.
  Every shipped `power.json` has an empty name, so no live install could hit
  it; the invariant was accidental.
- The Overview's new Reset all button asks before zeroing every system, like
  the main panel's reset does.
- Every muted line in the Overview was drawn in `button_bg` - a button fill,
  not a text colour. On EDMC's dark theme that is `#323232` on `#000000`, a
  contrast ratio of 1.61:1. There is a real `muted` colour now, 8.53:1, and a
  test that measures every foreground the window draws against the surface it
  is drawn on.
- The `warning` status colour, `#d07000`, was 3.50:1 under its white text -
  the only one of the eight tags under the 4.5:1 floor. Darkened the least
  that clears it, hue kept: `#b36000`, 4.58:1.
- The Systems table set its column widths in characters while the numbers were
  pixels, so the seven columns came out about twice the width of the window
  and the last one was cut off.
- The bottom button bar of the Session and Systems tabs was packed after the
  scrolling list, so the list took its space and the last row was drawn under
  the buttons.
- `emt_ui/main.py` had a second, different `get_theme_colors()` that returned
  three of the eight keys. Both files now use the one in `emt_ui/palette.py`.
- The test suite wrote to the commander's real database. `conftest.py` points
  `database.PATH` at a temporary file for every test.
- `emt_tests/mocks.py` had no `tkinter.ttk`, `tkinter.filedialog` or
  `myNotebook`, so any test importing `emt_ui` could only be collected when
  another module happened to be imported first. Added, and every test file now
  passes on its own.

## [v0.4.400.3.005] - 2026-09-13

### Fixed
- Log lines no longer fail with `KeyError: 'osthreadid'` when the plugin sits
  in a versioned folder such as `EliteMeritTracker-0.4.3.1.200`. The logger
  was named `EliteMeritTracker` whatever the folder was called; EDMC sets up
  the fields its formatter needs only on the logger named after the folder.
  It is now named after the folder holding `load.py`, as EDMC's plugin docs
  say.
- The first pickup of a salvage or PowerPlay goods type counted one too many:
  a new entry started at 1 and then had the collected amount added, so 1
  Black Box read 2. New entries start at 0. Later pickups were always right.

### Changed
- Expose `VERSION` and `__version__` from `load.py`. The number still lives on
  `configPlugin`, so there is one place to change it; the EDMC plugin registry
  reads it off the plugin, and the plugin is `load.py`.
- Stop shipping `backup_legacy/`. The folder is written at runtime by
  `_cleanup_legacy_files`, which moves pre-refactor folders out of the way on
  an upgrading install - that behaviour is unchanged. What was committed there
  was the pre-refactor code itself, 17 files the plugin registry would ask
  about under "bundle only what you need". Gitignored now, and untouched on
  anyone's disk.

## [v0.4.400.3.004] - 2026-09-11

### Fixed
- Follow the system EDMC names on every journal line, instead of waiting for
  FSDJump, Location, CarrierJump or Docked. Starting EDMC with the game
  already running restored whichever system was Active at the last shutdown,
  which is the wrong one if you jumped while it was closed, and it stayed
  wrong until one of those four events happened. The workaround noted in the
  code - "jump to another system or dock to trigger system update" - is no
  longer needed. A name carries no PowerPlay data, so a known system keeps
  what it has and an unknown one gets the same minimal entry a Docked event
  would create.

## [v0.4.400.3.003] - 2026-09-09

### Fixed
- **Large duplicate awards are rejected on arrival instead of waiting to be exposed**: a phantom award advances `TotalMerits` by exactly its own size, so nothing in the delta math can tell it from a real one - it was credited and only unwound when a later event reused the old base. A player who stops earning right after a big hand-in never gets that later event and reports the doubled number. Journal.2026-09-08T072628.01.log:1396,1398 shows 127,735 merits twice at 10:27:22, corrected only by a 90-merit award six seconds later.
- An identical `MeritsGained` of at least `DUPE_MIN_MERITS` (1,000) for the same power within `DUPE_WINDOW_SECONDS` (60) is now dropped without touching the baseline, so the next genuine event still reconciles against the total the server actually holds. Over 5 journals holding merit events / 84 events, all 4 awards >= 1,000 merits carrying that signature were phantom and all 11 without it were real; the largest legitimately repeated award was 112 merits (four in a row in test/Journal.2026-02-16T133244.01.log), and the 45/70/77/112 trickles are untouched. Replaying the four September journals end to end lands on 7,515,860, which is what the server reports at the next login.
- **The displayed total no longer comes from the raw event**: `pledgedPower.Merits` is taken from the ledger baseline, so a rejected event cannot put a total the server never held on screen. If a rejection is wrong the total is briefly *below* the server's instead, and heals on the next award or login.

- **A wrong rejection gives the merits back to the system that earned them**: a rejection is provisional. The dropped award is parked with the system it would have gone to, and the next event's base decides its fate - at or above the total the rejected event claimed, the server really did hold it, so it is restored to that system rather than landing in a lump on wherever the player happens to be. A `Powerplay` snapshot at the next game start counts as proof too, so the restore survives a relog with no further awards. This is the mirror of `unwind()`, which takes a phantom back off a system.
- Two rules bound a restore: an award whose own base is already below the tracked baseline is never parked, and no more is given back than the server base exceeds the baseline by. Without them a stale resend could be handed back on the next event that cleared its number, `credited` could go negative and be silently dropped, and an event with a frozen total could invent merits. Rejections also queue, so two of them go back to their own systems instead of the first being booked to wherever the player had moved.

### Known limits
- The threshold is the whole safety margin, over 15 awards >= 1,000 merits. A wrong rejection heals per-system when the next event carries an up-to-date server base. If that base is itself stale the parked award is released into the next credited lump instead, which keeps the total right but books it to whichever system is current.
- Nothing about the ledger survives an EDMC restart, so a parked award is lost across one while the per-system numbers persist. This is the same gap the credit history has always had.
- During a rejection window both the header total and the system's own merit count are short by the rejected award, so a Discord report sent in that window under-reports it. Reporting again after the restore makes up the difference.
- Small phantoms below the threshold are unaffected and still rely on a later event, so a session can end above the server total by a few tens of merits - 140, 45 and 45 across the three September journals that show it.
- A rejected award with no known system (merits before the first location) still falls back to the credited lump.
- A restored hand-in goes to the system the player was in, not to the source systems a cargo or salvage delivery was split across.

## [v0.4.400.3.002] - 2026-08-28

### Fixed
- **A correction and a genuine award in the same event no longer cancel out**: when a dropped award was exposed by the next award, the two were netted against each other, so the new award was silently booked onto the previous system. `TotalMerits` still decides whether anything happened at all - a frozen total means the award was dropped, whatever `MeritsGained` claims - but once the total has moved, `MeritsGained` splits the move between the correction and the new award. Yesterday's data: `Col 285 Sector HL-L b9-0` 39,271 -> 35,614 and `Aramo` 12,466 -> 16,123, with the total unchanged.

### Added
- `emt_tests/journal_builder.py` writes Elite journal files for tests, tracking what the server actually credited so each scenario carries its own ground truth
- `emt_tests/test_merit_journals.py` - one generated journal per case, replayed through the real `journal_entry`: round trips, phantoms exposed after jumping away or by a game restart, resend bursts, deep unwinds, power changes

## [v0.4.400.3.001] - 2026-08-28

### Fixed
- **Merit attribution no longer trusts `MeritsGained`**: deriving the server's pre-award base from `TotalMerits - MeritsGained` misattributed merits whenever `MeritsGained` was itself the lie. Journal.2026-01-15T110022.01.log:2052 reports 118,520 merits in Parapa while the server total stays frozen at 2,205,412 - the previous rule moved all 118,520 off Ross 444, which had genuinely earned them, and credited Parapa. Only the `TotalMerits` delta is used now. Measured over 388 journals the two rules disagree on 261,996 merits across 12 systems; the delta rule is the one that matches the journals.

## [v0.4.400.3.000] - 2026-08-28

### Fixed
- **Merit tracking rebuilt on TotalMerits deltas**: `MeritsGained` is regularly reported for awards the server never credits - concurrent awards clobber each other under server lag, and the following event exposes it by reusing the same base. The old duplicate detection caught 39% of these; measured against 388 journals / 2732 PowerplayMerits events it overcounted by 5.59% (4,852,696 vs 4,595,953 actual). Delta tracking matches the server exactly at all 363 snapshot checkpoints.
- **Corrections now hit the right system**: when a dropped event is exposed after the player changed system, the merits are taken back off the system that received them via a LIFO credit history instead of the current one. Previously 29,298 merits were subtracted from the wrong systems and two systems went negative.
- **Reported and cleared systems are no longer clawed back**: banking a system (Discord report, entry delete, reset) marks its credits so a later correction cannot subtract merits that were already submitted.
- Worked example, 2026-08-27: `Col 285 Sector HL-L b9-0` was credited 83,734 (actual 71,790) and `Aramo` 23,572 (actual 30,822).

### Changed
- `emt_core/duplicate.py` now exposes `MeritLedger` / `merit_ledger` / `reset_merit_tracking`; `DuplicateDetector`, `process_powerplay_event` and `track_journal_event` are gone

## [v0.4.400.2.001] - 2026-07-21

### Reverted
- Rolled back the TotalMerits-diff merit tracking (v0.4.400.2.000) to the v0.4.300.1.052 behavior; restored `emt_core/duplicate.py` and the prior `load.py` handling

## [v0.4.300.1.046] - 2026-03-27

### Changed
- **Real Undermining Display**: The Cycle NET% display is replaced with `UM: X (decay) | Reinf: Y` showing actual hostile undermining CP separated from natural decay
  - Uses piecewise linear decay formula (ported from EDIntel) with per-type lookup tables for Exploited, Fortified, and Stronghold systems
  - Natural CP decay is subtracted from the raw journal undermining value; decay amount shown in parentheses when non-zero
  - Color coding: green arrow when Reinf > real UM, red arrow when real UM > Reinf

## [v0.4.300.1.045] - 2026-03-04

### Fixed
- **Overview window duplicate opening**: Clicking Overview multiple times no longer opens multiple windows; existing window is raised to front instead

## [v0.4.300.1.044] - 2026-02-16

### Fixed
- **Cross-Session Merit Attribution Bug**: Fixed merits being attributed to wrong systems from previous sessions
  - SearchAndRescue now only processes salvage from current system instead of all systems alphabetically
  - Prevents old salvage from previous sessions being attributed when handed in during new session
  - Example: Salvage collected in "Hyades Sector" in previous session was incorrectly getting merits when user handed in salvage in "LHS 2476" in new session
  - Adds warning logs when salvage inventory is short or missing (helps detect desync issues)

## [v0.4.300.1.043] - 2026-02-11

### Fixed
- **Duplicate Detection Bug**: Fixed duplicate checker incorrectly blocking legitimate merit gains
  - When handing in multiple same-value donations quickly (e.g., multiple 56-merit salvage), events 2+ were incorrectly marked as duplicates
  - Now validates TotalMerits progression - if TotalMerits increments correctly, it's not a duplicate
  - Fixes issue where rapid merit donations at Search & Rescue were being ignored
- **EDMC Logging Compatibility**: Fixed logging failures causing plugin output to be suppressed
  - Added EDMCLogRecordFilter to inject 'osthreadid' field required by EDMC's log formatter
  - Prevents KeyError: 'osthreadid' that was causing all plugin log messages to fail
  - Plugin activity now properly logged and visible for debugging

## [v0.4.300.1.042] - 2026-02-11

### Added
- **Hide PowerPlay Stats Option**: Added option to hide PowerPlay stats and Economy/Security info from main UI
  - New checkbox in preferences: "Hide PowerPlay stats (Power, Rank, Total Merits) from main UI"
  - Default: unchecked (stats visible)
  - When enabled, hides: Pledged Power, Rank, Total Merits, and Economy/Security info
  - When enabled, Cycle NET stat and Session Merits remain visible
  - Settings apply immediately when saved in preferences

## [v0.4.300.1.041] - 2026-01-15

### Fixed
- **PowerPlay Data Loss on Docking**: Fixed system PowerPlay data disappearing when docking at stations
  - Docked events don't contain PowerPlay data (Status, Progress, Power, Cycle, Reinf)
  - Docked event handler now only updates current system tracking without overwriting PowerPlay data
  - Only FSDJump and Location events update PowerPlay data (they contain full system info)
  - Prevents "no PP connection" status appearing after docking in PowerPlay systems

## [v0.4.300.1.040] - 2026-01-15

### Fixed
- **Merit Attribution Bugs**: Fixed critical bugs causing merits to be attributed to wrong systems
  - Mining commodities (Osmium, Platinum, etc.) were incorrectly tracked as PowerPlay salvage cargo
  - CollectCargo handler now only tracks PowerPlay salvage types (black boxes, wreckage, etc.)
  - Added Docked event to system tracking so current system updates when docking
  - Merits from mining/trading now correctly attributed to the system where goods are sold
  - Example: Mining in System A and selling in System B now gives merits to System B (not A)

### Changed
- **System Validation**: Temporarily disabled system validation feature to prevent data loss
  - Feature caused TypeError and risk of losing merit data
  - Will be re-implemented safely in future update
  - Workaround: Jump to another system or dock to trigger system update if needed

## [v0.4.300.1.039] - 2026-01-13

### Fixed
- **UI Refresh After Salvage Hand-In**: Fixed main UI not updating after salvage hand-in at Search and Rescue
  - Added UI refresh calls after SAR merit distribution across systems
  - Added UI refresh calls after DeliverPowerMicroResources merit distribution
  - Merit counts now display immediately after hand-in instead of waiting for system jump

### Improved
- **System Validation Optimization**: Improved efficiency of system location validation
  - Validation now only runs on StartUp, Location, and FSDJump events (not every event)
  - Added logging to show which event triggered validation and system status
  - Handles EDMC StartUp event properly when started with Elite already running
  - More targeted event filtering for better performance

## [v0.4.300.1.038] - 2026-01-09

### Fixed
- **Fleet Carrier System Tracking**: Fixed system tracking when EDMC is started after traveling via Fleet Carrier
  - Added validation using EDMC's system parameter on first journal entry
  - Automatically detects and corrects system mismatch after plugin restart
  - Creates new StarSystem object if correct system not in database to ensure merit tracking works immediately
  - Prevents merit tracking issues when user travels while EDMC is closed
  - Improves reliability of current system detection across all scenarios

## [v0.4.300.1.037] - 2026-01-07

### Added
- **PowerPlay Item-Type Materials Tracking**: Added support for 15 PowerPlay salvage items (PowerPlay Goods)
  - New items: Agricultural Sample, Computer Parts, Data Storage Device, Electronics Package, Energy Regulator, Experiment Prototype, Extraction Sample, Industrial Component, Industrial Machinery, Inventory Record, Medical Sample, Military Schematic, Personal Protective Equipment, Research Notes, Security Logs
  - Items now tracked in salvage system alongside legacy Black Box and Wreckage Components
  - Full merit calculation support when delivered to Search & Rescue or Power contacts
  - Complete coverage of all PowerPlay Item-type materials from game

- **Shiplocker UI Enhancement**: Added fourth table to display PowerPlay Item-type materials
  - New "PowerPlay Items (Salvage)" table shows system, item type, and count
  - Sortable columns (click headers to sort by system, item type, or count)
  - Double-click count column to edit inventory amounts
  - Add new entries via "+ Add New Entry" button
  - Real-time total count display
  - Changes auto-save to salvage.json

- **Auto-Save Feature**: Implemented 5-minute periodic auto-save to prevent data loss
  - Automatic background save every 300 seconds
  - Protects against data loss from game crashes or EDMC termination
  - Daemon thread implementation (doesn't block shutdown)
  - Graceful cancellation on plugin stop
  - Reduces max data loss from full session to 5 minutes

- **Comprehensive Test Suite**: Added test_powerplay_items.py with 95%+ coverage
  - Tests for all Data-type items (Undermining, Reinforcement, Acquisition)
  - Tests for all Item-type materials (15 PowerPlay Goods)
  - Real-world scenario tests based on actual journal events
  - Merit calculation and distribution tests
  - Edge case and error handling tests

### Technical
- Updated `emt_models/salvage.py`: Added 15 PowerPlay Goods to VALID_POWERPLAY_SALVAGE_TYPES
  - poweragriculture, powercomputer, powermisccomputer, powerelectronics, powerpower
  - powerexperiment, powerextraction, powerindustrial, powermiscindust, powerinventory
  - powermedical, powerplaymilitary, powerequipment, powerresearch, powersecurity
- Updated `emt_ui/details.py`: Added create_salvage_table() function for UI display
- Updated `load.py`: Added threading support for auto-save timer
- All changes maintain backward compatibility with existing salvage tracking

## [v0.4.300.1.036] - 2026-01-03

### Improved
- **Reset Confirmation Dialog Positioning**: Dialog now appears near EDMC window instead of default screen position
  - Creates temporary toplevel window to control dialog placement
  - Positions dialog 50 pixels offset from EDMC window location
  - Falls back to default position if window positioning fails

## [v0.4.300.1.035] - 2026-01-03

### Fixed
- **CRITICAL: Reset Button Data Loss**: Fixed complete data loss when reset clicked while game not running
  - Bug: reset() relied on state.current_system which is None/invalid after game shutdown
  - Could cause ALL merit tracking data to be permanently lost (systems.json wiped to {})
  - Fix: Now finds most recently active system from systems dict instead of state
  - Fix: Added confirmation dialog before clearing data ("Are you sure?")
  - Fix: Added comprehensive logging to track reset operations
  - Prevents data loss scenario: game closes → EDMC still running → reset clicked → all data lost

## [v0.4.300.1.034] - 2026-01-03

### Added
- **Comprehensive Test Suite**: Added standalone test suite with 99% coverage target
  - 90 tests total (64 for system model, 17 for copy text variables, 9 edge cases)
  - **100% code coverage** achieved for emt_models/system.py (188/188 lines)
  - Tests use real journal data from actual gameplay
  - Standalone execution with EDMC dependency mocking
  - pytest configuration with HTML coverage reports
  - Run tests: `python emt_tests/run_tests.py`

### Fixed
- **Reset Button Loses Current System**: Fixed current system disappearing after clicking trash bin
  - Current system now properly preserved with 0 merits after reset
  - Bug: Was using StarSystem object as dict key instead of system name string
  - Fixed: Changed `state.current_system` → `state.current_system.StarSystem`
  - System remains visible in UI after reset instead of disappearing completely

### Documentation
- Updated structure.md to reflect current project state
  - Added emt_tests/ documentation with coverage status
  - Added PowerPlay 2.0 mechanics section
  - Documented all copy text variables with critical replacement order notes
  - Updated all module paths to use emt_* prefix

## [v0.4.300.1.033] - 2025-01-01

### Fixed
- **@SystemStatus Variable Replacement Order**: Fixed variable being partially replaced
  - @SystemStatus must be processed before @System to avoid "Status" remnant
  - Changed replacement order: @MeritsValue → @SystemStatus → @System → other variables
  - Fixes output like "3000 Hyades Sector KC-U c3-9Status" → "3000 ACQ Hyades Sector KC-U c3-9"

## [v0.4.300.1.032] - 2025-01-01

### Added
- **@SystemStatus Copy Text Variable**: Added new variable showing system type abbreviation
  - Returns: "Stronghold", "Fort", "Exploited", or "ACQ" for acquisition systems
  - Works for all acquisition stages: Unoccupied (<30%), Contested (30-100%), Controlled (>100%)
  - Example usage: "@Leadership earned @MeritsValue merits in @System [@SystemStatus]"
  - Applied to Overview copy, detailed view copy, and Discord FSD jump reporting
  - Variable list updated in config UI

## [v0.4.300.1.031] - 2025-01-01

### Fixed
- **ControllingPower Shows "no power" for Acquisition Systems**: Fixed to show leading power name
  - Unoccupied systems with conflict progress now correctly show the leading power
  - Example: Changed from "no power 30.69%" to "Felicia Winters 30.69%"
  - ControllingPower derived from first entry in PowerplayConflictProgress array
  - Fixes display in main UI, Overview window, and all copy text variables

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
