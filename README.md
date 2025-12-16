# EliteMeritTracker

EDMC Plugin to track Powerplay Merits in Elite Dangerous.

<img width="257" height="141" alt="grafik" src="https://github.com/user-attachments/assets/08e50d62-2a01-486b-b023-7c9257fed202" />
<img width="1724" height="621" alt="grafik" src="https://github.com/user-attachments/assets/44ced819-57b1-4dac-8195-f3b46f0214ed" />
<img width="1723" height="630" alt="grafik" src="https://github.com/user-attachments/assets/78e42e11-a9c8-4390-abc4-acfc055d1db9" />


## Features

- Automatic merit tracking per system
- Session and total merit counters
- Detailed Powerplay system view with filters
- Discord webhook integration for reporting
- CSV export functionality
- Auto-update from GitHub releases

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

All data is stored locally:
- `%LOCALAPPDATA%\EDMarketConnector\plugins\EliteMeritTracker\systems.json`
- No external data transmission (except optional Discord webhooks)

## Credits

Developed by [Fumlop](https://github.com/Fumlop)

## License

See [LICENSE](LICENSE) for details.
