"""
Test plugin name parsing with version suffix stripping.
"""

import re


def parse_plugin_name(raw_name):
    """Strip version suffix from plugin directory name"""
    return re.sub(r'-\d+\.\d+\.\d+(\.\d+)*$', '', raw_name)


def test_plugin_name_parsing():
    """Test that plugin names are parsed correctly"""

    print("="*80)
    print("PLUGIN NAME PARSING TEST")
    print("="*80)
    print()

    test_cases = [
        # (input_name, expected_output)
        ("EliteMeritTracker", "EliteMeritTracker"),
        ("EliteMeritTracker-0.4.300.1.025", "EliteMeritTracker"),
        ("EliteMeritTracker-0.4.300", "EliteMeritTracker"),
        ("EliteMeritTracker-1.0.0", "EliteMeritTracker"),
        ("EliteMeritTracker-2.5.10.123", "EliteMeritTracker"),
        ("SomeOtherPlugin-1.2.3", "SomeOtherPlugin"),
        ("PluginWithDash-InName-1.2.3", "PluginWithDash-InName"),
        ("NoVersion", "NoVersion"),
        ("Plugin-WithText-1.2.3", "Plugin-WithText"),
    ]

    all_passed = True

    for raw_name, expected in test_cases:
        result = parse_plugin_name(raw_name)
        passed = result == expected
        status = "[PASS]" if passed else "[FAIL]"

        print(f"{status} '{raw_name}' -> '{result}' (expected: '{expected}')")

        if not passed:
            all_passed = False

    print()
    print("="*80)
    print(f"RESULT: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print("="*80)
    print()

    if all_passed:
        print("The plugin will now work correctly even if the user's directory is named:")
        print("  - EliteMeritTracker")
        print("  - EliteMeritTracker-0.4.300.1.025")
        print("  - EliteMeritTracker-1.0.0")
        print("  - Any other version suffix")

    return all_passed


if __name__ == "__main__":
    import sys
    success = test_plugin_name_parsing()
    sys.exit(0 if success else 1)
