"""
PowerPlay Duplicate Detection Module

This module handles duplicate detection for PowerplayMerits events in Elite Dangerous.
It tracks event history, manages state variables, and provides methods to detect and 
handle duplicate events including retroactive correction.
"""

from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from merit_log import logger


class DuplicateDetector:
    """
    PowerPlay duplicate detection system.
    
    Handles detection of duplicate PowerplayMerits events by tracking:
    - Event timestamps and content
    - Journal event sequences between PowerplayMerits events  
    - Retroactive duplicate detection based on TotalMerits consistency
    """
    
    def __init__(self, time_window: float = 3.0):
        """
        Initialize duplicate detector.
        
        Args:
            time_window: Time window in seconds for duplicate detection (default: 3.0)
        """
        self.time_window = time_window
        self.reset()
    
    def reset(self):
        """Reset all tracking variables to initial state."""
        self.last_powerplay_event: Optional[Dict[str, Any]] = None
        self.last_journal_timestamp: Optional[str] = None
        self.retroactive_duplicate_detected: bool = False
    
    def track_journal_event(self, timestamp: str) -> None:
        """
        Track non-PowerplayMerits journal event timestamp.
        
        Args:
            timestamp: Event timestamp in Elite Dangerous format
        """
        self.last_journal_timestamp = timestamp
    
    def parse_timestamp_diff(self, timestamp1: str, timestamp2: str) -> float:
        """
        Calculate difference in seconds between two Elite Dangerous timestamps.
        
        Args:
            timestamp1: First timestamp
            timestamp2: Second timestamp
            
        Returns:
            Time difference in seconds, or float('inf') if parsing fails
        """
        if not timestamp1 or not timestamp2:
            return float('inf')
        
        try:
            # Parse Elite Dangerous timestamp format: "2025-10-05T17:12:04Z"
            dt1 = datetime.fromisoformat(timestamp1.replace('Z', '+00:00'))
            dt2 = datetime.fromisoformat(timestamp2.replace('Z', '+00:00'))
            return (dt1 - dt2).total_seconds()
        except Exception as e:
            logger.warning(f"Error parsing timestamps: {e}")
            return float('inf')
    
    def check_retroactive_duplicate(self, current_event: Dict[str, Any]) -> Tuple[bool, int]:
        """
        Check if previous event was a retroactive duplicate.
        
        A retroactive duplicate is detected when the current TotalMerits is lower 
        than expected based on the previous event.
        
        Args:
            current_event: Current PowerplayMerits event data
            
        Returns:
            Tuple of (is_retroactive_duplicate, duplicate_merits_to_correct)
        """
        if not self.last_powerplay_event or self.retroactive_duplicate_detected:
            return False, 0
        
        # Expected total should be previous total + previous merits gained (since previous was counted)
        expected_minimum_total = self.last_powerplay_event['total_merits']
        current_total = current_event['total_merits']
        
        # If current total is less than the previous total, the previous event must have been a duplicate
        if current_total < expected_minimum_total:
            duplicate_merits = self.last_powerplay_event['merits_gained']
            logger.error(f"RETROACTIVE DUPLICATE DETECTED: Previous PowerplayMerits event was a duplicate! "
                        f"Expected minimum total: {expected_minimum_total}, got: {current_total} "
                        f"Previous duplicate merits: {duplicate_merits}")
            
            self.retroactive_duplicate_detected = True
            return True, duplicate_merits
        
        self.retroactive_duplicate_detected = False
        return False, 0
    
    def check_sequence_events(self, current_event: Dict[str, Any]) -> bool:
        """
        Check if there were events between the last and current PowerplayMerits events.
        
        Args:
            current_event: Current PowerplayMerits event data
            
        Returns:
            True if no events between, False if events detected between
        """
        if not self.last_powerplay_event or not self.last_journal_timestamp:
            return True
        
        try:
            last_pp_dt = datetime.fromisoformat(self.last_powerplay_event['timestamp'].replace('Z', '+00:00'))
            current_pp_dt = datetime.fromisoformat(current_event['timestamp'].replace('Z', '+00:00'))
            last_journal_dt = datetime.fromisoformat(self.last_journal_timestamp.replace('Z', '+00:00'))
            
            # If there was an event between the two PowerplayMerits events, it's not a duplicate
            if last_pp_dt < last_journal_dt < current_pp_dt:
                logger.debug(f"Event between PP events detected: {self.last_journal_timestamp} "
                           f"between {self.last_powerplay_event['timestamp']} and {current_event['timestamp']}")
                return False
        except Exception as e:
            logger.warning(f"Error parsing timestamps for event sequence check: {e}")
            # Conservative: assume no events between if parsing fails
        
        return True
    
    def is_duplicate_event(self, current_event: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if current PowerplayMerits event is a duplicate.
        
        Args:
            current_event: Current PowerplayMerits event data with keys:
                          'timestamp', 'merits_gained', 'total_merits', 'power'
                          
        Returns:
            Tuple of (is_duplicate, reason_description)
        """
        if not self.last_powerplay_event:
            return False, "No previous event to compare"
        
        # Calculate time difference
        time_diff = abs(self.parse_timestamp_diff(
            current_event['timestamp'], 
            self.last_powerplay_event['timestamp']
        ))
        
        # Check basic duplicate conditions
        same_merits = current_event['merits_gained'] == self.last_powerplay_event['merits_gained']
        same_power = current_event['power'] == self.last_powerplay_event['power']
        within_time_window = time_diff < self.time_window
        
        # For very short time differences (< 1 second), check event sequence
        # For longer time differences, focus on merit/power matching regardless of intermediate events
        apply_sequence_check = time_diff < 1.0
        no_events_between = True
        
        if apply_sequence_check:
            no_events_between = self.check_sequence_events(current_event)
        
        # Duplicate condition logic from original code
        duplicate_condition = (within_time_window and same_merits and same_power)
        if apply_sequence_check:
            duplicate_condition = duplicate_condition and no_events_between
        
        if not duplicate_condition:
            if not within_time_window:
                return False, f"Not duplicate: time_diff={time_diff:.1f}s (outside {self.time_window}s window)"
            elif not same_merits:
                return False, f"Not duplicate: different merits ({current_event['merits_gained']} vs {self.last_powerplay_event['merits_gained']})"
            elif not same_power:
                return False, f"Not duplicate: different powers ({current_event['power']} vs {self.last_powerplay_event['power']})"
            elif apply_sequence_check and not no_events_between:
                return False, f"Events between detected within {time_diff:.1f}s"
            else:
                return False, f"Not duplicate: unknown reason"
        
        # Check TotalMerits consistency
        expected_total = self.last_powerplay_event['total_merits'] + current_event['merits_gained']
        total_merits_inconsistent = current_event['total_merits'] != expected_total
        
        # Build reason description
        if total_merits_inconsistent:
            reason = f"Duplicate with inconsistent totals: expected {expected_total}, got {current_event['total_merits']}"
        else:
            sequence_info = (f", no events between" if apply_sequence_check and no_events_between 
                           else f", events between ignored (>{time_diff:.1f}s)" if not apply_sequence_check 
                           else f", events between detected")
            reason = f"Duplicate within {time_diff:.1f}s{sequence_info}"
        
        return True, reason
    
    def process_powerplay_event(self, entry: Dict[str, Any]) -> Tuple[bool, Optional[int], str]:
        """
        Process PowerplayMerits event and check for duplicates.
        
        Args:
            entry: Raw PowerplayMerits journal event
            
        Returns:
            Tuple of (is_duplicate, retroactive_correction_merits, log_message)
        """
        current_event = {
            'timestamp': entry.get('timestamp'),
            'merits_gained': entry.get('MeritsGained', 0),
            'total_merits': entry.get('TotalMerits', 0),
            'power': entry.get('Power', '')
        }
        
        # Check for retroactive duplicate first
        is_retroactive, retroactive_merits = self.check_retroactive_duplicate(current_event)
        
        # Check for current duplicate
        is_duplicate, duplicate_reason = self.is_duplicate_event(current_event)
        
        if is_duplicate:
            # Reset tracking on duplicate to prevent cascade
            self.last_powerplay_event = None
            self.last_journal_timestamp = None
            self.retroactive_duplicate_detected = False
            return True, retroactive_merits if is_retroactive else None, duplicate_reason
        
        # Store this event for future comparison
        self.last_powerplay_event = current_event
        
        # Reset retroactive flag after processing
        self.retroactive_duplicate_detected = False
        
        log_message = f"Valid PowerplayMerits: {current_event['merits_gained']} merits"
        if is_retroactive:
            log_message += f" (corrected {retroactive_merits} retroactive duplicate merits)"
        
        return False, retroactive_merits if is_retroactive else None, log_message


# Global instance for backward compatibility
duplicate_detector = DuplicateDetector()


# Backward compatibility functions
def track_journal_event(timestamp: str) -> None:
    """Track non-PowerplayMerits journal event timestamp."""
    duplicate_detector.track_journal_event(timestamp)


def process_powerplay_event(entry: Dict[str, Any]) -> Tuple[bool, Optional[int], str]:
    """
    Process PowerplayMerits event and check for duplicates.
    
    Returns:
        Tuple of (is_duplicate, retroactive_correction_merits, log_message)
    """
    return duplicate_detector.process_powerplay_event(entry)


def reset_duplicate_tracking() -> None:
    """Reset all duplicate tracking state."""
    duplicate_detector.reset()