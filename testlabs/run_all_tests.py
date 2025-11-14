#!/usr/bin/env python3
"""
Master Test Runner: All 6 Menu Options
Executes all test labs sequentially and reports results.
"""

import sys
import subprocess
from pathlib import Path

def run_test_lab(lab_number):
    """Run a single test lab and return success status."""
    test_file = Path(__file__).parent / f"test_lab_{lab_number}_*.py"
    
    # Find the test file
    test_files = list(Path(__file__).parent.glob(f"test_lab_{lab_number}_*.py"))
    
    if not test_files:
        print(f"✗ Test lab {lab_number} not found")
        return False
    
    test_file = test_files[0]
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"✗ Test lab {lab_number} timed out")
        return False
    except Exception as e:
        print(f"✗ Test lab {lab_number} error: {e}")
        return False

def main():
    """Run all test labs."""
    print("\n" + "="*70)
    print("MASTER TEST RUNNER: All 6 Menu Options")
    print("="*70)
    
    results = {}
    test_descriptions = {
        1: "Show Previous Runs",
        2: "Show Traces",
        3: "Show Last Requests",
        4: "Execute Single Request",
        5: "Run Entire Trace (Trace #17, Limit 10)",
        6: "Show Caches"
    }
    
    for lab_num in range(1, 7):
        print(f"\n{'─'*70}")
        print(f"Running Test Lab {lab_num}: {test_descriptions[lab_num]}")
        print(f"{'─'*70}")
        
        results[lab_num] = run_test_lab(lab_num)
    
    # Summary
    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)
    
    for lab_num in range(1, 7):
        status = "✓ PASSED" if results[lab_num] else "✗ FAILED"
        print(f"Test Lab {lab_num}: {test_descriptions[lab_num]:<40} {status}")
    
    all_passed = all(results.values())
    print("="*70)
    
    if all_passed:
        print("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED!")
        return 1

if __name__ == '__main__':
    sys.exit(main())
