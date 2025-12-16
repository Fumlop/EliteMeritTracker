import tkinter as tk
import myNotebook as nb
from core.config import configPlugin
from core.logging import logger, plugin_name

# Simple duplicate scanner that shows results in config window
def scan_for_duplicates(days, result_text_widget):
    """Simple duplicate scanner that updates a text widget"""
    try:
        import threading
        import os
        import glob
        import json
        from datetime import datetime, timedelta
        
        def update_result(text):
            result_text_widget.delete(1.0, tk.END)
            result_text_widget.insert(1.0, text)
        
        def perform_scan():
            try:
                update_result("🔍 Scanning...")
                
                # Open debug file in plugin root
                plugin_dir = os.path.dirname(os.path.dirname(__file__))
                debug_file_path = os.path.join(plugin_dir, "debug_scan.txt")
                with open(debug_file_path, 'w', encoding='utf-8') as debug_file:
                    debug_file.write("=== Duplicate Scanner Debug Log ===\n")
                    debug_file.write(f"Scan started: {datetime.now()}\n")
                    debug_file.write(f"Scanning last {days} days\n\n")
                
                # Find journal directory
                journal_dir = None
                possible_paths = [
                    r"E:\DATA\EliteDangerous",
                    os.path.expanduser(r"~\Saved Games\Frontier Developments\Elite Dangerous"),
                    os.path.expanduser(r"~\Documents\Frontier Developments\Elite Dangerous"),
                ]
                
                for path in possible_paths:
                    if os.path.exists(path) and any(f.startswith('Journal.') for f in os.listdir(path) if f.endswith('.log')):
                        journal_dir = path
                        break
                
                if not journal_dir:
                    update_result("❌ No journal directory found")
                    return
                
                # Log to debug file
                with open(debug_file_path, 'a', encoding='utf-8') as debug_file:
                    debug_file.write(f"Journal directory: {journal_dir}\n")
                
                # Get recent files
                cutoff_date = datetime.now() - timedelta(days=int(days))
                pattern = os.path.join(journal_dir, "Journal.*.log")
                all_files = glob.glob(pattern)
                
                recent_files = []
                for file_path in all_files:
                    try:
                        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if mod_time >= cutoff_date:
                            recent_files.append(file_path)
                    except OSError:
                        continue
                
                if not recent_files:
                    update_result(f"❌ No files found (last {days} days)")
                    return
                
                # Log files to debug
                with open(debug_file_path, 'a', encoding='utf-8') as debug_file:
                    debug_file.write(f"Found {len(recent_files)} recent files:\n")
                    for f in recent_files[:5]:  # Log first 5 files
                        debug_file.write(f"  - {os.path.basename(f)}\n")
                    debug_file.write(f"\n")
                
                # Simple duplicate detection
                total_events = 0
                total_duplicates = 0
                total_valid_merits = 0
                total_duplicate_merits = 0
                last_event = None
                
                event_debug_count = 0
                
                for file_path in recent_files:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if not line:
                                    continue
                                
                                try:
                                    event = json.loads(line)
                                    if event.get('event') == 'PowerplayMerits':
                                        total_events += 1
                                        merits = event.get('MeritsGained', 0)  # FIXED: Use correct field!
                                        timestamp = event.get('timestamp', '')
                                        
                                        # Debug: Log first 10 events to file
                                        if event_debug_count < 10:
                                            event_debug_count += 1
                                            with open(debug_file_path, 'a', encoding='utf-8') as debug_file:
                                                debug_file.write(f"Event {event_debug_count}:\n")
                                                debug_file.write(f"  Raw event: {json.dumps(event, indent=2)}\n")
                                                debug_file.write(f"  Extracted merits: {merits}\n")
                                                debug_file.write(f"  Timestamp: {timestamp}\n\n")
                                        
                                        # Simple duplicate check
                                        is_duplicate = False
                                        if last_event:
                                            last_timestamp = last_event.get('timestamp', '')
                                            last_merits = last_event.get('MeritsGained', 0)  # FIXED: Use correct field!
                                            
                                            # Same timestamp and merits = duplicate
                                            if timestamp == last_timestamp and merits == last_merits:
                                                is_duplicate = True
                                            # Or very close in time with same merits
                                            elif merits == last_merits:
                                                try:
                                                    dt1 = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                                    dt2 = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
                                                    time_diff = abs((dt1 - dt2).total_seconds())
                                                    if time_diff <= 3.0:
                                                        is_duplicate = True
                                                except (ValueError, TypeError):
                                                    pass
                                        
                                        if is_duplicate:
                                            total_duplicates += 1
                                            total_duplicate_merits += merits
                                            # Log duplicate to debug file
                                            if event_debug_count <= 10:
                                                with open(debug_file_path, 'a', encoding='utf-8') as debug_file:
                                                    debug_file.write(f"  --> DUPLICATE DETECTED! Merits: {merits}\n\n")
                                        else:
                                            total_valid_merits += merits
                                        
                                        last_event = event
                                        
                                except json.JSONDecodeError:
                                    continue
                                except Exception:
                                    continue
                    except Exception:
                        continue
                
                # Log summary to debug file
                with open(debug_file_path, 'a', encoding='utf-8') as debug_file:
                    debug_file.write(f"=== SCAN RESULTS ===\n")
                    debug_file.write(f"Total events: {total_events}\n")
                    debug_file.write(f"Total duplicates: {total_duplicates}\n")
                    debug_file.write(f"Total valid merits: {total_valid_merits}\n")
                    debug_file.write(f"Total duplicate merits: {total_duplicate_merits}\n")
                    debug_file.write(f"Debug file saved to: {debug_file_path}\n")
                
                # Create summary
                if total_events == 0:
                    summary = f"ℹ️ No PowerPlay events found (last {days} days)"
                else:
                    duplicate_rate = (total_duplicates / total_events) * 100
                    summary = f"""📊 Last {days} days: {len(recent_files)} files, {total_events} events
🚫 Duplicates: {total_duplicates} ({duplicate_rate:.1f}%)
💰 Valid merits: {total_valid_merits:,}
❌ Duplicate merits: {total_duplicate_merits:,}
✅ System working: {total_duplicate_merits:,} fraudulent merits prevented!

🔍 Debug log saved to: debug_scan.txt"""
                
                update_result(summary)
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                update_result(error_msg)
                # Also log error to debug file
                try:
                    with open(debug_file_path, 'a', encoding='utf-8') as debug_file:
                        debug_file.write(f"ERROR: {str(e)}\n")
                except (IOError, OSError):
                    pass
        
        # Start scan in thread
        threading.Thread(target=perform_scan, daemon=True).start()
        
    except Exception as e:
        result_text_widget.delete(1.0, tk.END)
        result_text_widget.insert(1.0, f"❌ Import error: {str(e)}")

def create_config_frame(parent, nb):
    config_frame = nb.Frame(parent)
    config_frame.columnconfigure(1, weight=1)
    config_frame.grid(sticky=tk.EW)

    row = 0
    def next_config_row():
        nonlocal row
        row += 1
        return row

    nb.Label(
        config_frame,
        text="Copy paste text value - Text must contain @MeritsValue and @System for replacement"
    ).grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=5)

    nb.Label(
        config_frame,
        text="@MeritsValue, @System, @CPOpposition, @CPControlling"
    ).grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=5)
    #logger.warning(f"config {configPlugin.copyText}")
    nb.Entry(
        config_frame,
        textvariable=configPlugin.copyText,
        width=50
    ).grid(row=next_config_row(), column=0, padx=5, pady=5, sticky="we")

    nb.Label(config_frame, text="").grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=5)

    nb.Label(config_frame, text="Discord webhook URL").grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=5)

    nb.Entry(
        config_frame,
        textvariable=configPlugin.discordHook,
        width=50
    ).grid(row=next_config_row(), column=0, padx=5, pady=5, sticky="we")

    nb.Checkbutton(
        config_frame,
        text="Report merits from source system to Discord on FSDJump",
        variable=configPlugin.reportOnFSDJump
    ).grid(row=next_config_row(), columnspan=2, sticky=tk.W)

    nb.Label(config_frame, text="").grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=5)

    # Duplicate Scanner Section
    #nb.Label(config_frame, text="Duplicate Merit Scanner", font=("TkDefaultFont", 9, "bold")).grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=(10, 5))
    
    # Scanner controls frame
    #scanner_frame = nb.Frame(config_frame)
    #scanner_frame.grid(row=next_config_row(), column=0, columnspan=2, sticky="we", padx=5, pady=5)
    #scanner_frame.columnconfigure(4, weight=1)
    
    #nb.Label(scanner_frame, text="Scan last").grid(row=0, column=0, sticky="w")
    
    #nb.Entry(
    #    scanner_frame,
    #    textvariable=configPlugin.duplicateScanDays,
    #    width=5
    #).grid(row=0, column=1, padx=(5, 5), sticky="w")
    
    #nb.Label(scanner_frame, text="days for duplicate merits").grid(row=0, column=2, sticky="w", padx=(0, 10))
    
    #def start_duplicate_scan():
    #    try:
    #        days = configPlugin.duplicateScanDays.get()
    #        scan_for_duplicates(days, scan_results_text)
    #    except Exception as e:
    #        logger.error(f"Error starting duplicate scan: {e}")
    
    #nb.Button(
    #    scanner_frame,
    #    text="🔍 Scan",
    #    command=start_duplicate_scan
    #).grid(row=0, column=3, padx=(10, 0))
    
    # Results text area
    #scan_results_text = tk.Text(
    #    config_frame,
    #    height=6,
    #    width=70,
    #    font=("Consolas", 8),
    #    wrap=tk.WORD
    #)
    #scan_results_text.grid(row=next_config_row(), column=0, columnspan=2, sticky="we", padx=5, pady=5)
    #scan_results_text.insert(1.0, "Click 'Scan' to check for duplicate merits...")

    nb.Label(config_frame, text="").grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=5)

    # Beta Update Section
    nb.Label(config_frame, text="Beta Updates", font=("TkDefaultFont", 9, "bold")).grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=(10, 5))

    beta_frame = nb.Frame(config_frame)
    beta_frame.grid(row=next_config_row(), column=0, columnspan=2, sticky="we", padx=5, pady=5)

    # Status label
    beta_status_label = nb.Label(beta_frame, text="")
    beta_status_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))

    def update_beta_status():
        if configPlugin.beta:
            beta_status_label.config(text="Currently running: Beta version")
        else:
            beta_status_label.config(text="Currently running: Stable release")

    update_beta_status()

    def on_update_to_beta():
        from load import update_to_prerelease, check_prerelease_available
        prerelease = check_prerelease_available()
        if prerelease:
            if update_to_prerelease():
                beta_status_label.config(text=f"Beta {prerelease} installed! Restart EDMC.")
                update_beta_status()
        else:
            beta_status_label.config(text="No pre-release available")

    def on_revert_to_release():
        from load import revert_to_release
        if revert_to_release():
            beta_status_label.config(text="Reverted to stable! Restart EDMC.")
            update_beta_status()

    # Show different buttons based on current state
    if not configPlugin.beta:
        nb.Button(
            beta_frame,
            text="Update to Pre-Release",
            command=on_update_to_beta
        ).grid(row=1, column=0, padx=(0, 10), sticky="w")
    else:
        nb.Button(
            beta_frame,
            text="Revert to Latest Release",
            command=on_revert_to_release
        ).grid(row=1, column=0, padx=(0, 10), sticky="w")

    nb.Label(config_frame, text="").grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=5)

    # Version label with beta indicator
    version_text = f"Version {configPlugin.version}"
    if configPlugin.beta:
        version_text += " (Beta)"
    nb.Label(
        config_frame,
        text=version_text
    ).grid(row=next_config_row(), column=0, sticky="w", padx=5, pady=5)

    return config_frame
