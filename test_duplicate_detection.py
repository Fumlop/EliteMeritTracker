#!/usr/bin/env python3
"""
Test driver for PowerplayMerits duplicate detection
Scans all Journal files from E:\DATA\EliteDangerous from 2025-09-30 onwards
"""
import os
import json
import glob
from datetime import datetime
from pathlib import Path

class DuplicateDetector:
    def __init__(self):
        # PowerPlay deduplication tracking (same as in load.py)
        self.lastPowerplayMeritsEvent = None
        self.powerplayEventTimeWindow = 3.0  # 3 seconds tolerance
        self.retroactiveDuplicateDetected = False
        self.lastJournalEventTimestamp = None
        
        # Statistics
        self.total_powerplay_events = 0
        self.proactive_duplicates_found = 0
        self.retroactive_duplicates_found = 0
        self.events_processed = 0
        self.files_processed = 0
        
        # Results storage
        self.duplicate_events = []
        self.retroactive_corrections = []

    def parse_timestamp_diff(self, timestamp1, timestamp2):
        """Calculate difference in seconds between two Elite Dangerous timestamps"""
        if not timestamp1 or not timestamp2:
            return float('inf')
        
        try:
            dt1 = datetime.fromisoformat(timestamp1.replace('Z', '+00:00'))
            dt2 = datetime.fromisoformat(timestamp2.replace('Z', '+00:00'))
            return (dt1 - dt2).total_seconds()
        except Exception as e:
            print(f"Error parsing timestamps: {e}")
            return float('inf')

    def process_powerplay_merits_event(self, entry, filename):
        """Process PowerplayMerits event with duplicate detection logic from load.py"""
        self.total_powerplay_events += 1
        
        # Create event key (same as in load.py)
        current_event_key = {
            'timestamp': entry.get('timestamp'),
            'merits_gained': entry.get('MeritsGained', 0),
            'total_merits': entry.get('TotalMerits', 0),
            'power': entry.get('Power', ''),
            'filename': filename,
            'entry': entry
        }
        
        if self.lastPowerplayMeritsEvent is not None:
            # RETROACTIVE CHECK (same logic as load.py)
            expected_minimum_total = self.lastPowerplayMeritsEvent['total_merits']
            if current_event_key['total_merits'] < expected_minimum_total and not self.retroactiveDuplicateDetected:
                self.retroactive_duplicates_found += 1
                correction = {
                    'type': 'retroactive',
                    'previous_event': self.lastPowerplayMeritsEvent.copy(),
                    'current_event': current_event_key.copy(),
                    'expected_total': expected_minimum_total,
                    'actual_total': current_event_key['total_merits'],
                    'duplicate_merits': self.lastPowerplayMeritsEvent['merits_gained']
                }
                self.retroactive_corrections.append(correction)
                
                print(f"🔄 RETROACTIVE DUPLICATE in {filename}:")
                print(f"   Previous: {self.lastPowerplayMeritsEvent['merits_gained']} merits, Total: {self.lastPowerplayMeritsEvent['total_merits']}")
                print(f"   Current:  {current_event_key['merits_gained']} merits, Total: {current_event_key['total_merits']}")
                print(f"   Expected minimum: {expected_minimum_total}, got: {current_event_key['total_merits']}")
                
                self.retroactiveDuplicateDetected = True
            else:
                self.retroactiveDuplicateDetected = False
            
            # PROACTIVE CHECK (same logic as load.py)
            time_diff = abs(self.parse_timestamp_diff(current_event_key['timestamp'], self.lastPowerplayMeritsEvent['timestamp']))
            same_merits = current_event_key['merits_gained'] == self.lastPowerplayMeritsEvent['merits_gained']
            same_power = current_event_key['power'] == self.lastPowerplayMeritsEvent['power']
            
            # Event sequence check logic
            no_events_between = True
            apply_sequence_check = time_diff < 1.0
            
            if apply_sequence_check and self.lastJournalEventTimestamp:
                try:
                    last_pp_dt = datetime.fromisoformat(self.lastPowerplayMeritsEvent['timestamp'].replace('Z', '+00:00'))
                    current_pp_dt = datetime.fromisoformat(current_event_key['timestamp'].replace('Z', '+00:00'))
                    last_journal_dt = datetime.fromisoformat(self.lastJournalEventTimestamp.replace('Z', '+00:00'))
                    
                    if last_pp_dt < last_journal_dt < current_pp_dt:
                        no_events_between = False
                except Exception:
                    no_events_between = True
            
            # Duplicate condition
            duplicate_condition = (time_diff < self.powerplayEventTimeWindow and same_merits and same_power)
            if apply_sequence_check:
                duplicate_condition = duplicate_condition and no_events_between
            
            if duplicate_condition:
                self.proactive_duplicates_found += 1
                duplicate = {
                    'type': 'proactive',
                    'previous_event': self.lastPowerplayMeritsEvent.copy(),
                    'current_event': current_event_key.copy(),
                    'time_diff': time_diff,
                    'sequence_check_applied': apply_sequence_check,
                    'events_between': not no_events_between if apply_sequence_check else 'ignored'
                }
                self.duplicate_events.append(duplicate)
                
                print(f"⚠️  PROACTIVE DUPLICATE in {filename}:")
                print(f"   Time diff: {time_diff:.1f}s, Same merits: {same_merits} ({current_event_key['merits_gained']})")
                print(f"   Same power: {same_power} ({current_event_key['power']})")
                print(f"   Sequence check: {'applied' if apply_sequence_check else 'skipped'}")
                
                # Reset tracking (same as load.py)
                self.lastPowerplayMeritsEvent = None
                self.lastJournalEventTimestamp = None
                self.retroactiveDuplicateDetected = False
                return  # Skip this duplicate
        
        # Store event for future comparison
        self.lastPowerplayMeritsEvent = current_event_key
        self.retroactiveDuplicateDetected = False

    def process_journal_entry(self, entry, filename):
        """Process a single journal entry"""
        self.events_processed += 1
        
        # Track non-PowerplayMerits events for sequence detection
        current_timestamp = entry.get('timestamp')
        if current_timestamp and entry['event'] != 'PowerplayMerits':
            self.lastJournalEventTimestamp = current_timestamp
        
        # Process PowerplayMerits events
        if entry['event'] == 'PowerplayMerits':
            self.process_powerplay_merits_event(entry, filename)

    def process_journal_file(self, filepath):
        """Process a single journal file"""
        filename = os.path.basename(filepath)
        print(f"📄 Processing {filename}...")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        entry = json.loads(line)
                        if 'event' in entry and 'timestamp' in entry:
                            self.process_journal_entry(entry, filename)
                    except json.JSONDecodeError as e:
                        print(f"   JSON error in {filename} line {line_num}: {e}")
                        continue
                        
            self.files_processed += 1
            
        except Exception as e:
            print(f"   Error processing {filename}: {e}")

    def get_journal_files(self, directory, start_date):
        """Get all journal files from start_date onwards"""
        pattern = os.path.join(directory, "Journal.*.log")
        all_files = glob.glob(pattern)
        
        valid_files = []
        for filepath in all_files:
            filename = os.path.basename(filepath)
            # Extract date from filename: Journal.2025-10-05T183330.01.log
            try:
                # Extract the date part
                date_part = filename.split('.')[1].split('T')[0]  # "2025-10-05"
                file_date = datetime.strptime(date_part, '%Y-%m-%d').date()
                
                if file_date >= start_date:
                    valid_files.append(filepath)
            except (ValueError, IndexError):
                print(f"⚠️  Could not parse date from filename: {filename}")
                continue
        
        # Sort by date
        valid_files.sort()
        return valid_files

    def print_statistics(self):
        """Print comprehensive statistics"""
        print("\n" + "="*80)
        print("📊 DUPLICATE DETECTION STATISTICS")
        print("="*80)
        
        print(f"Files processed: {self.files_processed}")
        print(f"Total events processed: {self.events_processed:,}")
        print(f"PowerplayMerits events: {self.total_powerplay_events}")
        print(f"Proactive duplicates found: {self.proactive_duplicates_found}")
        print(f"Retroactive duplicates found: {self.retroactive_duplicates_found}")
        print(f"Total duplicates: {self.proactive_duplicates_found + self.retroactive_duplicates_found}")
        
        if self.total_powerplay_events > 0:
            duplicate_rate = ((self.proactive_duplicates_found + self.retroactive_duplicates_found) / self.total_powerplay_events) * 100
            print(f"Duplicate rate: {duplicate_rate:.2f}%")

    def calculate_merit_correction(self):
        """Calculate merit correction since first reported duplicate case"""
        # First reported case: 2025-10-05T17:12:04Z with 31948 merits
        first_reported_timestamp = "2025-10-05T17:12:04Z"
        first_reported_dt = datetime.fromisoformat(first_reported_timestamp.replace('Z', '+00:00'))
        
        total_duplicate_merits = 0
        duplicates_since_report = []
        
        # Check all proactive duplicates
        for dup in self.duplicate_events:
            dup_timestamp = dup['current_event']['timestamp']
            dup_dt = datetime.fromisoformat(dup_timestamp.replace('Z', '+00:00'))
            
            if dup_dt >= first_reported_dt:
                merit_loss = dup['current_event']['merits_gained']
                total_duplicate_merits += merit_loss
                duplicates_since_report.append({
                    'timestamp': dup_timestamp,
                    'merits': merit_loss,
                    'filename': dup['current_event']['filename'],
                    'type': 'proactive'
                })
        
        # Check all retroactive corrections
        for corr in self.retroactive_corrections:
            corr_timestamp = corr['current_event']['timestamp']
            corr_dt = datetime.fromisoformat(corr_timestamp.replace('Z', '+00:00'))
            
            if corr_dt >= first_reported_dt:
                merit_loss = corr['duplicate_merits']
                total_duplicate_merits += merit_loss
                duplicates_since_report.append({
                    'timestamp': corr_timestamp,
                    'merits': merit_loss,
                    'filename': corr['current_event']['filename'],
                    'type': 'retroactive'
                })
        
        # Sort by timestamp
        duplicates_since_report.sort(key=lambda x: x['timestamp'])
        
        print("\n" + "="*80)
        print(f"💰 MERIT CORRECTION CALCULATION (seit {first_reported_timestamp})")
        print("="*80)
        
        print(f"Erste gemeldete Duplikat: {first_reported_timestamp} (31,948 Merits)")
        print(f"Duplikate seit Meldung: {len(duplicates_since_report)}")
        print(f"Total zu korrigierende Merits: {total_duplicate_merits:,}")
        
        if duplicates_since_report:
            print(f"\nDetails der zu korrigierenden Duplikate:")
            print("-" * 60)
            running_total = 0
            for i, dup in enumerate(duplicates_since_report, 1):
                running_total += dup['merits']
                dup_type = "🔄" if dup['type'] == 'retroactive' else "⚠️"
                print(f"{i:2}. {dup_type} {dup['timestamp']} | {dup['merits']:,} Merits | Running total: {running_total:,}")
                print(f"    File: {dup['filename']}")
            
            print(f"\n🎯 FINAL RESULT:")
            print(f"Sie müssen {total_duplicate_merits:,} Merits von Ihren aktuellen Merits abziehen!")
        
        return total_duplicate_merits, duplicates_since_report

    def print_detailed_results(self):
        """Print detailed results of found duplicates"""
        if self.duplicate_events:
            print(f"\n🔍 PROACTIVE DUPLICATES DETAIL ({len(self.duplicate_events)} found):")
            print("-" * 60)
            for i, dup in enumerate(self.duplicate_events, 1):
                prev = dup['previous_event']
                curr = dup['current_event']
                print(f"{i}. {curr['filename']}")
                print(f"   Time: {prev['timestamp']} → {curr['timestamp']} ({dup['time_diff']:.1f}s)")
                print(f"   Merits: {prev['merits_gained']} → {curr['merits_gained']}")
                print(f"   Total: {prev['total_merits']} → {curr['total_merits']}")
                print(f"   Power: {prev['power']}")
                print(f"   Sequence check: {dup['sequence_check_applied']}")
                print()

        if self.retroactive_corrections:
            print(f"\n🔄 RETROACTIVE DUPLICATES DETAIL ({len(self.retroactive_corrections)} found):")
            print("-" * 60)
            for i, corr in enumerate(self.retroactive_corrections, 1):
                prev = corr['previous_event']
                curr = corr['current_event']
                print(f"{i}. {curr['filename']}")
                print(f"   Previous: {prev['merits_gained']} merits, Total: {prev['total_merits']}")
                print(f"   Current: {curr['merits_gained']} merits, Total: {curr['total_merits']}")
                print(f"   Expected: {corr['expected_total']}, Difference: {corr['expected_total'] - corr['actual_total']}")
                print()

def main():
    """Main test function"""
    print("🧪 PowerPlay Duplicate Detection Test Driver")
    print("=" * 50)
    
    # Configuration
    journal_directory = r"E:\DATA\EliteDangerous"
    start_date = datetime(2025, 9, 30).date()
    
    print(f"📁 Journal directory: {journal_directory}")
    print(f"📅 Start date: {start_date}")
    
    # Check if directory exists
    if not os.path.exists(journal_directory):
        print(f"❌ Directory not found: {journal_directory}")
        return
    
    # Initialize detector
    detector = DuplicateDetector()
    
    # Get journal files
    journal_files = detector.get_journal_files(journal_directory, start_date)
    print(f"📄 Found {len(journal_files)} journal files to process")
    
    if not journal_files:
        print("❌ No journal files found for the specified date range")
        return
    
    print(f"Files to process:")
    for f in journal_files:
        print(f"   {os.path.basename(f)}")
    
    print("\n🔄 Starting duplicate detection...")
    print("-" * 50)
    
    # Process all files
    for filepath in journal_files:
        detector.process_journal_file(filepath)
    
    # Print results
    detector.print_statistics()
    
    # Calculate merit correction
    total_correction, correction_details = detector.calculate_merit_correction()
    
    detector.print_detailed_results()
    
    print("\n✅ Duplicate detection test completed!")

if __name__ == "__main__":
    main()