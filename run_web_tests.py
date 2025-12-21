#!/usr/bin/env python3
"""
Web API Test Runner

Comprehensive test runner for all web API functionality including:
- Web API service layer tests
- Session management tests
- Visualization utilities tests
- Integration tests
- Performance and concurrent user tests

Usage:
    python run_web_tests.py                    # Run all web tests
    python run_web_tests.py --fast             # Run only fast tests
    python run_web_tests.py --category web_api # Run specific category
    python run_web_tests.py --verbose          # Verbose output

Author: TextToSolver Test Team
"""

import subprocess
import sys
import argparse
from typing import List, Optional


def run_pytest_command(args: List[str], description: str) -> bool:
    """
    Run a pytest command and return success status.
    
    Args:
        args: pytest command line arguments
        description: Description of what's being tested
        
    Returns:
        True if tests passed, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    cmd = ["python", "-m", "pytest"] + args
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            return False
            
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def main():
    """Main test runner function."""
    
    parser = argparse.ArgumentParser(description="Web API Test Runner")
    parser.add_argument("--fast", action="store_true", 
                       help="Run only fast tests (exclude slow/performance tests)")
    parser.add_argument("--category", type=str,
                       choices=["web_api", "session_management", "visualization", 
                               "web_integration", "concurrent", "real_time"],
                       help="Run tests for specific category only")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--coverage", action="store_true",
                       help="Run with coverage reporting")
    
    args = parser.parse_args()
    
    print("🌐 TextToSolver Web API Test Suite")
    print("=" * 60)
    
    base_args = []
    if args.verbose:
        base_args.extend(["-v", "--tb=short"])
    else:
        base_args.extend(["--tb=short"])
    
    if args.coverage:
        base_args.extend(["--cov=text_to_solver", "--cov-report=html", "--cov-report=term"])
    
    test_results = []
    
    if args.category:
        # Run specific category
        test_args = base_args + ["-m", args.category]
        if args.fast:
            test_args.extend(["-m", f"{args.category} and not performance"])
        
        success = run_pytest_command(
            test_args,
            f"{args.category.replace('_', ' ').title()} Tests"
        )
        test_results.append((f"{args.category} tests", success))
        
    else:
        # Run all web API test categories
        test_categories = [
            ("web_api", "Web API Service Layer Tests"),
            ("session_management", "Session Management Tests"),
            ("visualization", "Visualization Utilities Tests"),
            ("web_integration", "Web Integration Tests")
        ]
        
        if not args.fast:
            test_categories.extend([
                ("concurrent", "Concurrent User Tests"),
                ("real_time", "Real-Time Features Tests"),
                ("performance", "Performance Tests")
            ])
        
        for marker, description in test_categories:
            test_args = base_args + ["-m", marker]
            success = run_pytest_command(test_args, description)
            test_results.append((description, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed_count = sum(1 for _, success in test_results if success)
    total_count = len(test_results)
    
    for test_name, success in test_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Overall Result: {passed_count}/{total_count} test suites passed")
    
    if passed_count == total_count:
        print("🎉 All web API tests completed successfully!")
        print("\n🚀 Web API components are ready for production use!")
        return 0
    else:
        print("❌ Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
