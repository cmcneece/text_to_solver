#!/usr/bin/env python3
"""
Test Runner for Symbol Detection and Parameter Sweep Features

Runs all tests related to the new symbol detection and parameter 
sweep functionality, providing comprehensive validation.

Usage:
    python run_symbol_parameter_tests.py

Author: TextToSolver Test Team
"""

import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Run symbol detection and parameter sweep tests."""
    print("=" * 80)
    print("🧪 Symbol Detection & Parameter Sweep Test Suite")
    print("=" * 80)
    
    # Note: Symbol detection and parameter sweep tests were removed
    # along with web API components. This test runner is now deprecated.
    
    print("⚠️  Symbol detection and parameter sweep tests have been removed.")
    print("    These features were part of the web API components.")
    print("    This test runner is deprecated.")
    
    test_files = []
    
    # Configure pytest arguments
    pytest_args = [
        "-v",                    # Verbose output
        "--tb=short",           # Shorter traceback format
        "--strict-markers",     # Strict marker checking
        "--color=yes"           # Colored output
    ] + test_files
    print()
    
    # Run the tests
    exit_code = pytest.main(pytest_args)
    
    print()
    print("=" * 80)
    if exit_code == 0:
        print("✅ All symbol detection and parameter sweep tests passed!")
    else:
        print("❌ Some tests failed. Check output above for details.")
    print("=" * 80)
    
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
