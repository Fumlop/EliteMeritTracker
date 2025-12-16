# EliteMeritTracker

EDMC Plugin to track Powerplay Merits in Elite Dangerous.

![Main UI](https://github.com/user-attachments/assets/5a09ef25-42d3-427c-acb6-5f4a6d0c5cea)
![Detailed View](https://github.com/user-attachments/assets/82bbfbdd-5d0f-4082-a0ee-fe83f8fbd145)
![Settings](https://github.com/user-attachments/assets/b068658f-af1e-464e-bf60-95dcf886e8d0)

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
