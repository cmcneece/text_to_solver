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
    
    # Test files to run
    test_files = [
        "tests/test_web_api.py::TestParameterRange",
        "tests/test_web_api.py::TestSymbolDetection", 
        "tests/test_web_api.py::TestParameterSweep",
        "tests/test_symbol_parameter_integration.py"
    ]
    
    # Test markers to include
    markers = [
        "-m", "symbol_detection or parameter_sweep"
    ]
    
    # Configure pytest arguments
    pytest_args = [
        "-v",                    # Verbose output
        "--tb=short",           # Shorter traceback format
        "--strict-markers",     # Strict marker checking
        "-x",                   # Stop on first failure
        "--color=yes"           # Colored output
    ] + test_files
    
    print(f"📋 Running tests: {', '.join(test_files)}")
    print(f"🏷️  Test markers: symbol_detection, parameter_sweep")
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
