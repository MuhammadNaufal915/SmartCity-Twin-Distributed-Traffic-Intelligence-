"""
Standard Library Test Runner for SmartCity Twin.
Executes all test functions without external dependencies.
"""

from __future__ import annotations

import sys
import traceback
from typing import Callable

# Add parent directory to path so we can import modules
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import test suites
import tests.test_traffic_logic as test_traffic_logic
import tests.test_messaging as test_messaging


def run_suite(module) -> tuple[int, int]:
    """Discover and run all test functions in a module."""
    passed = 0
    failed = 0
    print(f"\nRunning tests in {module.__name__}:")
    
    # Get all functions starting with 'test_'
    test_funcs = [
        (name, getattr(module, name))
        for name in dir(module)
        if name.startswith('test_') and isinstance(getattr(module, name), Callable)
    ]
    
    for name, func in test_funcs:
        try:
            print(f"  - {name}... ", end="", flush=True)
            func()
            print("PASSED")
            passed += 1
        except AssertionError as e:
            print("FAILED (AssertionError)")
            traceback.print_exc(limit=1, file=sys.stdout)
            failed += 1
        except Exception as e:
            print(f"FAILED (Unexpected Error: {e})")
            traceback.print_exc(file=sys.stdout)
            failed += 1
            
    return passed, failed


def main() -> None:
    print("==================================================")
    print("      SmartCity Twin Simulator Test Runner        ")
    print("==================================================")
    
    total_passed = 0
    total_failed = 0
    
    for suite in [test_traffic_logic, test_messaging]:
        p, f = run_suite(suite)
        total_passed += p
        total_failed += f
        
    print("\n==================================================")
    print(f"Result: {total_passed} passed, {total_failed} failed.")
    print("==================================================")
    
    if total_failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
