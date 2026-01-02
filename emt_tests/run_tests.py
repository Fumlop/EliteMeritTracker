"""
Test Runner for EliteMeritTracker

Runs all tests and generates coverage report.
Target: 99% code coverage
"""
import sys
import pytest
from pathlib import Path

def main():
    """Run all tests with coverage"""

    # Add parent directory to path
    plugin_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(plugin_dir))

    # Pytest arguments
    args = [
        str(Path(__file__).parent),  # Test directory
        '-v',  # Verbose
        '--tb=short',  # Short traceback format
        '--strict-markers',  # Error on unknown markers
        '-ra',  # Show summary of all test outcomes
        '--cov=emt_models',  # Coverage for models
        '--cov=emt_core',  # Coverage for core
        '--cov=emt_ui',  # Coverage for UI
        '--cov-report=html',  # Generate HTML coverage report
        '--cov-report=term-missing',  # Show missing lines in terminal
        '--cov-fail-under=99',  # Fail if coverage < 99%
    ]

    # Add any command line arguments
    args.extend(sys.argv[1:])

    print("=" * 80)
    print("EliteMeritTracker Test Suite")
    print("Target Coverage: 99%")
    print("=" * 80)
    print()

    # Run tests
    exit_code = pytest.main(args)

    if exit_code == 0:
        print()
        print("=" * 80)
        print("[OK] ALL TESTS PASSED - Coverage >= 99%")
        print("=" * 80)
    else:
        print()
        print("=" * 80)
        print("[FAIL] TESTS FAILED OR COVERAGE < 99%")
        print("=" * 80)

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
