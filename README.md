# EliteMeritTracker

EDMC Plugin to track Powerplay Merits in Elite Dangerous.

<img width="257" height="141" alt="grafik" src="https://github.com/user-attachments/assets/08e50d62-2a01-486b-b023-7c9257fed202" />
<img width="1724" height="621" alt="grafik" src="https://github.com/user-attachments/assets/44ced819-57b1-4dac-8195-f3b46f0214ed" />
<img width="1723" height="630" alt="grafik" src="https://github.com/user-attachments/assets/78e42e11-a9c8-4390-abc4-acfc055d1db9" />

## About

EliteMeritTracker is a comprehensive Powerplay 2.0 merit tracking plugin for Elite Dangerous Market Connector (EDMC). It automatically monitors your gameplay and tracks merit-earning activities across all star systems you visit.

The plugin reads Elite Dangerous journal events in real-time to capture:
- **Combat merits**: Ship kills, on-foot combat, and other hostile activities
- **Cargo deliveries**: PowerPlay cargo hand-ins with accurate merit calculations
- **Data collection**: Tracks PowerPlay micro-resources in your backpack (undermining, reinforcement, acquisition data)
- **System state**: Monitors reinforcement vs undermining percentages with NET status calculations

All tracking happens locally - your data never leaves your computer unless you choose to share via Discord webhooks.

## Features

- **Automatic Merit Tracking**: Merits tracked per system from journal events
- **Session & Total Counters**: See merits earned this session and all-time totals
- **Detailed System View**: Sortable table with filters for System, State, and Power
- **PowerPlay Backpack**: Tracks collected data items with per-system attribution
- **NET Status**: Color-coded reinforcement vs undermining balance per system
- **Discord Integration**: Send merit reports to your Discord server via webhooks
- **CSV Export**: Export all tracked data for external analysis
- **Auto-Update**: One-click updates from GitHub releases (stable and beta channels)

## Installation

### First-Time Install

1. Download the latest release from [Releases](https://github.com/Fumlop/EliteMeritTracker/releases)
2. Extract the ZIP contents to:
   ```
   %LOCALAPPDATA%\EDMarketConnector\plugins\EliteMeritTracker
   ```
3. Restart EDMC

### Updating

The plugin includes auto-update functionality. When a new version is available:
- A notification will appear in the plugin
- Click to update automatically

For manual updates:
1. Close EDMC completely
2. Delete all files in the plugin folder (keeps your data)
3. Extract new release to the same folder
4. Restart EDMC

## Usage

- **Merit Tracking**: Merits are tracked automatically when you're in a system
- **Detailed View**: Click the info button to see all tracked systems
- **Reset**: Trash icon clears cached systems (keeps current system)
- **Copy/Report**: Copy merit reports to clipboard or send to Discord

## Data Storage

All data is stored locally in the `data/` subfolder:
- `data/systems.json` - Tracked star systems and merit counts
- `data/power.json` - Power allegiance data
- `data/backpack.json` - PowerPlay micro-resources in your backpack
- `data/salvage.json` - Salvage tracking data

Legacy files from older versions are automatically migrated to `data/` on first run.

No external data transmission occurs (except optional Discord webhooks you configure).

## Credits

Developed by [Fumlop](https://github.com/Fumlop)

## License

See [LICENSE](LICENSE) for details.
