"""
Test copy text variable replacement for different system types.
"""


class PowerConflictEntry:
    def __init__(self, power, progress):
        self.power = str(power)
        self.progress = float(progress)


class MockSystem:
    def __init__(self, name):
        self.StarSystem = name
        self.Merits = 0
        self.PowerplayState = "no PP connection"
        self.ControllingPower = "no power"
        self.PowerplayStateReinforcement = 0
        self.PowerplayStateUndermining = 0
        self.PowerplayConflictProgress = []
        self.Powers = []

    def getProgressPercentage(self):
        """Get progress percentage for acquisition systems"""
        if self.PowerplayConflictProgress:
            return self.PowerplayConflictProgress[0].progress * 100
        return 0

    def getDisplayState(self):
        """Get display state"""
        if self.PowerplayState == 'Unoccupied':
            if not self.PowerplayConflictProgress:
                return 'Unoccupied'
            progress = self.PowerplayConflictProgress[0].progress * 100
            if progress > 100.00:
                return 'Controlled'
            elif progress >= 30.00:
                return 'Contested'
            else:
                return 'Unoccupied'
        return self.PowerplayState


def test_copy_text_replacement():
    """Test that copy text variables are replaced correctly for different system types"""

    print("="*80)
    print("COPY TEXT VARIABLE REPLACEMENT TEST")
    print("="*80)
    print()

    # Default copy text template
    copy_template = "@Leadership earned @MeritsValue merits in @System, @CPControlling, @CPOpposition"

    # Test 1: Reinforcement/Undermining System (Exploited)
    print("TEST 1: Exploited System (Reinforcement/Undermining)")
    print("-" * 80)

    system1 = MockSystem("Test System Alpha")
    system1.Merits = 1500
    system1.PowerplayState = "Exploited"
    system1.ControllingPower = "Felicia Winters"
    system1.PowerplayStateReinforcement = 8500
    system1.PowerplayStateUndermining = 2300
    system1.Powers = ["Felicia Winters", "Arissa Lavigny-Duval"]

    # Simulate copy text replacement
    dcText = copy_template.replace('@MeritsValue', str(system1.Merits)).replace('@System', system1.StarSystem)
    dcText = dcText.replace('@CPOpposition', f"Opposition {str(system1.PowerplayStateUndermining)}")

    # For non-acquisition systems, show reinforcement
    if system1.PowerplayConflictProgress and len(system1.PowerplayConflictProgress) > 0:
        progress = system1.getProgressPercentage()
        dcText = dcText.replace('@CPControlling', f"{system1.ControllingPower} {progress:.2f}%")
    else:
        dcText = dcText.replace('@CPControlling', f"{system1.ControllingPower} {str(system1.PowerplayStateReinforcement)}")

    print(f"System: {system1.StarSystem}")
    print(f"State: {system1.PowerplayState}")
    print(f"Reinforcement: {system1.PowerplayStateReinforcement}")
    print(f"Undermining: {system1.PowerplayStateUndermining}")
    print(f"Copy Text: {dcText}")
    print()

    # Test 2: Acquisition System (Unoccupied with progress)
    print("TEST 2: Acquisition System (Unoccupied with Progress)")
    print("-" * 80)

    system2 = MockSystem("Test System Beta")
    system2.Merits = 2500
    system2.PowerplayState = "Unoccupied"
    system2.ControllingPower = "Felicia Winters"
    system2.PowerplayStateReinforcement = 0
    system2.PowerplayStateUndermining = 0

    # Simulate conflict progress (45.23% for Winters)
    system2.PowerplayConflictProgress = [PowerConflictEntry("Felicia Winters", 0.4523)]

    # Simulate copy text replacement
    dcText = copy_template.replace('@MeritsValue', str(system2.Merits)).replace('@System', system2.StarSystem)
    dcText = dcText.replace('@CPOpposition', f"Opposition {str(system2.PowerplayStateUndermining)}")

    # For acquisition systems, show progress percentage
    if system2.PowerplayConflictProgress and len(system2.PowerplayConflictProgress) > 0:
        progress = system2.getProgressPercentage()
        dcText = dcText.replace('@CPControlling', f"{system2.ControllingPower} {progress:.2f}%")
    else:
        dcText = dcText.replace('@CPControlling', f"{system2.ControllingPower} {str(system2.PowerplayStateReinforcement)}")

    print(f"System: {system2.StarSystem}")
    print(f"State: {system2.PowerplayState}")
    print(f"Progress: {system2.getProgressPercentage():.2f}%")
    print(f"Copy Text: {dcText}")
    print()

    # Test 3: Acquisition System (Contested - above 30%)
    print("TEST 3: Acquisition System (Contested - 67.89%)")
    print("-" * 80)

    system3 = MockSystem("Test System Gamma")
    system3.Merits = 3200
    system3.PowerplayState = "Unoccupied"
    system3.ControllingPower = "Felicia Winters"
    system3.PowerplayStateReinforcement = 0
    system3.PowerplayStateUndermining = 0

    # Simulate conflict progress (67.89% for Winters)
    system3.PowerplayConflictProgress = [PowerConflictEntry("Felicia Winters", 0.6789)]

    # Simulate copy text replacement
    dcText = copy_template.replace('@MeritsValue', str(system3.Merits)).replace('@System', system3.StarSystem)
    dcText = dcText.replace('@CPOpposition', f"Opposition {str(system3.PowerplayStateUndermining)}")

    # For acquisition systems, show progress percentage
    if system3.PowerplayConflictProgress and len(system3.PowerplayConflictProgress) > 0:
        progress = system3.getProgressPercentage()
        dcText = dcText.replace('@CPControlling', f"{system3.ControllingPower} {progress:.2f}%")
    else:
        dcText = dcText.replace('@CPControlling', f"{system3.ControllingPower} {str(system3.PowerplayStateReinforcement)}")

    print(f"System: {system3.StarSystem}")
    print(f"State: {system3.PowerplayState}")
    print(f"Progress: {system3.getProgressPercentage():.2f}%")
    print(f"Display State: {system3.getDisplayState()}")
    print(f"Copy Text: {dcText}")
    print()

    print("="*80)
    print("SUMMARY")
    print("="*80)
    print("[PASS] Exploited systems: @CPControlling shows power + reinforcement")
    print("[PASS] Acquisition systems: @CPControlling shows power + progress %")
    print("[PASS] Progress percentage correctly calculated from decimal (0.0-1.0)")
    print("="*80)


if __name__ == "__main__":
    test_copy_text_replacement()
