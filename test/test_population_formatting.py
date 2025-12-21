"""
Test population formatting for all ranges.
"""

def format_population(population):
    """Format population exactly as in main.py"""
    if population and population > 0:
        if population >= 1_000_000_000:  # Billions
            return f"Pop: {population / 1_000_000_000:.1f}B"
        elif population >= 1_000_000:  # Millions
            return f"Pop: {population / 1_000_000:.1f}M"
        elif population >= 100_000:  # 100K+
            return f"Pop: {population / 1_000:.1f}K"
        else:  # < 100K: show complete number
            return f"Pop: {population:,}"
    return None


def test_all_ranges():
    """Test all population ranges"""
    test_cases = [
        # (population, expected_output)
        (523, "Pop: 523"),
        (1_234, "Pop: 1,234"),
        (15_300, "Pop: 15,300"),
        (99_999, "Pop: 99,999"),
        (100_000, "Pop: 100.0K"),
        (150_000, "Pop: 150.0K"),
        (999_999, "Pop: 1000.0K"),  # Edge case
        (1_000_000, "Pop: 1.0M"),
        (4_091_441, "Pop: 4.1M"),
        (191_707_078, "Pop: 191.7M"),
        (999_999_999, "Pop: 1000.0M"),  # Edge case
        (1_000_000_000, "Pop: 1.0B"),
        (5_123_456_789, "Pop: 5.1B"),
    ]

    print("="*80)
    print("POPULATION FORMATTING TEST")
    print("="*80)
    print()

    all_passed = True

    for population, expected in test_cases:
        result = format_population(population)
        passed = result == expected
        status = "[PASS]" if passed else "[FAIL]"

        print(f"{status} Population: {population:>15,} -> {result:>15} (expected: {expected})")

        if not passed:
            all_passed = False

    print()
    print("="*80)
    print(f"RESULT: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print("="*80)

    return all_passed


if __name__ == "__main__":
    import sys
    success = test_all_ranges()
    sys.exit(0 if success else 1)
