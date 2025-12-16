# plugin_state.py - Centralized state management for EliteMeritTracker


class PluginState:
    """Centralized state manager for the plugin.

    Replaces the sys.modules[__name__] pattern with explicit state management.
    """

    def __init__(self):
        # System state
        self.current_system = None  # Currently flying StarSystem object
        self.commander = ""

        # UI state
        self.parent = None
        self.assetpath = ""
        self.newest = 0  # Version check result: -1=Error, 0=Current, 1=Update available

        # SAR (Search and Rescue) tracking
        self.last_sar_counts = None  # Dict[system_name, count] for merit distribution
        self.last_sar_systems = []   # List of systems in current SAR batch

        # DeliverPowerMicroResources tracking (backpack hand-in)
        self.last_delivery_counts = None  # Dict[system_name, count] for merit distribution

        # Debug flag
        self.debug = False

    def reset_sar_tracking(self):
        """Reset SAR tracking state after merit distribution"""
        self.last_sar_counts = None
        self.last_sar_systems = []

    def reset_delivery_tracking(self):
        """Reset delivery tracking state after merit distribution"""
        self.last_delivery_counts = None

    def init_sar_tracking(self):
        """Initialize SAR tracking for a new batch"""
        if self.last_sar_counts is None:
            self.last_sar_counts = {}
            self.last_sar_systems = []

    def add_sar_count(self, system_name: str, count: int):
        """Add count to SAR tracking for a system"""
        self.init_sar_tracking()
        if system_name not in self.last_sar_counts:
            self.last_sar_counts[system_name] = 0
            self.last_sar_systems.append(system_name)
        self.last_sar_counts[system_name] += count

    def add_delivery_count(self, system_name: str, count: int):
        """Add count to delivery tracking for a system"""
        if self.last_delivery_counts is None:
            self.last_delivery_counts = {}
        self.last_delivery_counts[system_name] = self.last_delivery_counts.get(system_name, 0) + count


# Singleton instance
state = PluginState()
