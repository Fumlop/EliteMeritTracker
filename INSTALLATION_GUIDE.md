# 📦 Manual Installation Guide

## Prerequisites
- Close **Elite Dangerous Market Connector** completely before installation
- Ensure no EDMC processes are running

## Installation Steps

### 1. Download
Click **"Source code (zip)"** below to download the release

### 2. Backup (Recommended)
Create a backup of your current plugin:
```powershell
Copy-Item "C:\Users\<user>\AppData\Local\EDMarketConnector\plugins\EliteMeritTracker" "C:\Users\<user>\AppData\Local\EDMarketConnector\plugins\EliteMeritTracker_backup" -Recurse
```

### 3. Clear Plugin Directory
Navigate to your EDMC plugins folder:
```
C:\Users\<user>\AppData\Local\EDMarketConnector\plugins\EliteMeritTracker
```
⚠️ **Delete all files and folders** inside this directory (keep the `EliteMeritTracker` folder itself)

### 4. Extract Files
1. Open the downloaded ZIP file
2. Navigate to the subfolder inside (usually `Fumlop-EliteMeritTracker-xxxxxxx`)
3. Select **all contents** of this subfolder
4. Extract directly to: `C:\Users\<user>\AppData\Local\EDMarketConnector\plugins\EliteMeritTracker`

### 5. Verify Installation
Your folder structure should look like:
```
EliteMeritTracker/
├── load.py
├── pluginUI.py
├── system.py
├── power.py
├── assets/
└── ... (other files)
```

### 6. Restart EDMC
Start Elite Dangerous Market Connector and verify the plugin loads correctly.

## 🎯 Important Notes
- **Settings preserved:** Your configuration will remain intact
- **Data preserved:** Systems, merits, and salvage inventory are maintained
- **Compatibility:** Fully backward compatible

## 🔧 Troubleshooting
If the plugin doesn't load:
1. Verify all files were extracted to the correct location
2. Check that no ZIP subfolders were accidentally included
3. Review EDMC logs for error messages
4. Restore from backup if needed

## ✨ What's New
This release includes advanced PowerPlay duplicate detection with:
- Dual-layer detection system (proactive + retroactive)
- Automatic merit correction
- Enhanced cargo delivery formula
- Improved data integrity

---
*For technical details about the duplicate detection system, see the full changelog above.*