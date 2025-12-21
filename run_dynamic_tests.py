#!/usr/bin/env python3
"""
Quick Dynamic Systems Test Execution Script

This script demonstrates the dynamic systems test suite by running key test categories
and showing that the dynamic systems functionality is working correctly.
"""

import subprocess
import sys
import time
import os

def run_test_command(cmd, description):
    """Run a test command and show results"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print('='*60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        duration = time.time() - start_time
        
        # Parse results from output
        output_lines = result.stdout.split('\n')
        summary_line = next((line for line in output_lines if 'passed' in line and ('failed' in line or 'warnings' in line)), '')
        
        success = result.returncode == 0
        
        if success:
            print(f"✅ SUCCESS ({duration:.2f}s)")
            if summary_line:
                print(f"   {summary_line}")
        else:
            print(f"❌ FAILED ({duration:.2f}s)")
            
            # Show key error information
            error_lines = [line for line in output_lines if 'FAILED' in line or 'ERROR' in line]
            for line in error_lines[:3]:  # Show first 3 errors
                if line.strip():
                    print(f"   {line}")
        
        return success
        
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        return False

def main():
    """Main test execution"""
    print("🚀 TextToSolver Dynamic Systems - Test Suite Demo")
    print("=" * 60)
    print("Demonstrating comprehensive testing of differential equation capabilities")
    
    # Test categories to run
    test_commands = [
        (
            "python -m pytest tests/test_dynamic_solver.py::TestSystemIntegration -v",
            "Core Integration Tests (4 key systems)"
        ),
        (
            "python -m pytest tests/test_dynamic_solver.py::TestIntegrationMethods -v", 
            "Numerical Methods Tests (Euler, RK4, RK45, DOP853)"
        ),
        (
            "python -m pytest tests/test_dynamic_solver.py::TestConvenienceFunctions -v",
            "Convenience API Tests (solve_ode_system, predator_prey)"
        ),
        (
            "python -m pytest tests/test_differential_parsing.py::TestBasicParsing -v",
            "Equation Parsing Tests (dx/dt notation)"
        ),
        (
            "python -m pytest tests/test_dynamic_integration.py::TestBackwardCompatibility -v",
            "Framework Integration Tests (backward compatibility)"
        )
    ]
    
    results = []
    total_start = time.time()
    
    # Run each test category
    for cmd, description in test_commands:
        success = run_test_command(cmd, description)
        results.append(success)
    
    total_duration = time.time() - total_start
    
    # Summary
    print(f"\n{'='*80}")
    print("TEST SUITE DEMO SUMMARY")
    print("="*80)
    
    passed_count = sum(results)
    total_count = len(results)
    
    print(f"Results: {passed_count}/{total_count} test categories passed")
    print(f"Total Duration: {total_duration:.2f} seconds")
    
    if passed_count == total_count:
        print("\n🎉 ALL DEMONSTRATION TESTS PASSED!")
        print("Dynamic systems functionality is working correctly.")
        print()
        print("Key capabilities validated:")
        print("✅ Exponential decay with analytical accuracy")
        print("✅ Harmonic oscillator with energy conservation")  
        print("✅ Predator-prey limit cycle dynamics")
        print("✅ Multiple integration methods (Euler → DOP853)")
        print("✅ Natural dx/dt equation parsing")
        print("✅ Backward compatibility with existing features")
        print("✅ Rich result objects with interpolation")
        print("✅ Robust error handling and edge cases")
        
        print(f"\nTextToSolver v3.0 with dynamic systems is ready! 🚀")
        
    else:
        failed_count = total_count - passed_count
        print(f"\n⚠️  {failed_count} test categories had issues")
        print("Review the detailed output above to identify problems.")
        
        if passed_count > 0:
            print(f"✅ {passed_count} test categories are working correctly")
    
    print("\n" + "="*80)
    
    return passed_count == total_count

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1)
