#!/usr/bin/env python3
"""
Dynamic Systems Test Suite Runner

This script runs comprehensive tests for the dynamic systems functionality,
providing detailed reporting on test results and coverage.
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Add the package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))


def check_dynamic_solver_availability():
    """Check if dynamic solver is available"""
    try:
        from text_to_solver.dynamic_solver import DynamicEquationSolver
        return True
    except ImportError:
        return False


def run_pytest_command(command, description):
    """Run a pytest command and return results"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print('='*60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        duration = time.time() - start_time
        
        print(f"Exit code: {result.returncode}")
        print(f"Duration: {duration:.2f} seconds")
        
        if result.stdout:
            print("\nSTDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        return result.returncode == 0, result.stdout, result.stderr, duration
        
    except Exception as e:
        print(f"Error running command: {e}")
        return False, "", str(e), 0


def run_dynamic_tests():
    """Run all dynamic systems related tests"""
    
    if not check_dynamic_solver_availability():
        print("❌ Dynamic solver not available - cannot run Dynamic Systems tests")
        return False
    
    print("🚀 Dynamic Systems Dynamic Systems Test Suite")
    print("=" * 60)
    print("Testing differential equation solving capabilities...")
    
    test_results = {}
    total_duration = 0
    
    # Define test categories and commands
    test_categories = [
        {
            'name': 'Core Dynamic Solver Tests',
            'command': ['python', '-m', 'pytest', 'tests/test_dynamic_solver.py', '-v'],
            'description': 'Core functionality, system creation, and basic integration'
        },
        {
            'name': 'Differential Equation Parsing Tests', 
            'command': ['python', '-m', 'pytest', 'tests/test_differential_parsing.py', '-v'],
            'description': 'Parsing of dx/dt notation and mathematical expressions'
        },
        {
            'name': 'Integration Methods Tests',
            'command': ['python', '-m', 'pytest', 'tests/test_integration_methods.py', '-v'],
            'description': 'Euler, RK4, RK45, DOP853 methods and accuracy comparison'
        },
        {
            'name': 'Dynamic Results Tests',
            'command': ['python', '-m', 'pytest', 'tests/test_dynamic_results.py', '-v'],
            'description': 'Result objects, interpolation, and analysis capabilities'
        },
        {
            'name': 'All Dynamic Systems Tests (by marker)',
            'command': ['python', '-m', 'pytest', '-m', 'dynamic', '-v'],
            'description': 'All tests marked with dynamic systems markers'
        },
        {
            'name': 'Dynamic Systems Error Handling Tests',
            'command': ['python', '-m', 'pytest', '-m', 'error_handling and dynamic', '-v'],
            'description': 'Error handling and edge cases for dynamic systems'
        },
        {
            'name': 'Dynamic Systems Performance Tests',
            'command': ['python', '-m', 'pytest', '-m', 'performance and dynamic', '-v'],
            'description': 'Performance and scalability tests (marked as slow)'
        }
    ]
    
    # Run each test category
    for category in test_categories:
        success, stdout, stderr, duration = run_pytest_command(
            category['command'],
            f"{category['name']}: {category['description']}"
        )
        
        test_results[category['name']] = {
            'success': success,
            'stdout': stdout,
            'stderr': stderr,
            'duration': duration
        }
        
        total_duration += duration
        
        if success:
            print(f"✅ {category['name']} - PASSED")
        else:
            print(f"❌ {category['name']} - FAILED")
    
    # Summary report
    print("\n" + "="*80)
    print("PHASE 3 TEST SUITE SUMMARY")
    print("="*80)
    
    passed_tests = sum(1 for result in test_results.values() if result['success'])
    total_tests = len(test_results)
    
    print(f"Overall Results: {passed_tests}/{total_tests} test categories passed")
    print(f"Total Duration: {total_duration:.2f} seconds")
    print()
    
    for name, result in test_results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status:10} {result['duration']:6.2f}s  {name}")
    
    # Detailed failure analysis
    failed_tests = [name for name, result in test_results.items() if not result['success']]
    
    if failed_tests:
        print(f"\n{'='*80}")
        print("FAILURE ANALYSIS")
        print("="*80)
        
        for name in failed_tests:
            result = test_results[name]
            print(f"\n❌ {name}")
            print("-" * 40)
            if result['stderr']:
                # Extract key error information
                lines = result['stderr'].split('\n')
                error_lines = [line for line in lines if 'ERROR' in line or 'FAILED' in line]
                for line in error_lines[:5]:  # Show first 5 error lines
                    print(f"  {line}")
            
            if result['stdout']:
                # Extract failure summary from stdout
                lines = result['stdout'].split('\n')
                failure_lines = [line for line in lines if 'FAILED' in line or '==' in line]
                for line in failure_lines[-10:]:  # Show last 10 relevant lines
                    if line.strip():
                        print(f"  {line}")
    
    # Success analysis
    if passed_tests > 0:
        print(f"\n{'='*80}")
        print("SUCCESS SUMMARY")
        print("="*80)
        
        successful_tests = [name for name, result in test_results.items() if result['success']]
        for name in successful_tests:
            result = test_results[name]
            
            # Extract passed test count from stdout
            stdout_lines = result['stdout'].split('\n')
            passed_line = next((line for line in stdout_lines if 'passed' in line and ('failed' in line or 'error' in line or 'skipped' in line)), None)
            
            if passed_line:
                print(f"✅ {name}: {passed_line.strip()}")
            else:
                print(f"✅ {name}: Duration {result['duration']:.2f}s")
    
    # Overall assessment
    print(f"\n{'='*80}")
    print("PHASE 3 READINESS ASSESSMENT")
    print("="*80)
    
    if passed_tests == total_tests:
        print("🎉 EXCELLENT! All Dynamic Systems tests passed!")
        print("   The dynamic systems functionality is fully validated and ready for production use.")
        print("   TextToSolver v3.0 is complete with differential equation solving capabilities.")
        
    elif passed_tests >= total_tests * 0.8:
        print("✅ GOOD! Most Dynamic Systems tests passed.")
        print(f"   {passed_tests}/{total_tests} test categories successful.")
        print("   Core functionality is working. Review failures for minor issues.")
        
    elif passed_tests >= total_tests * 0.5:
        print("⚠️  PARTIAL! Some Dynamic Systems tests passed.")
        print(f"   {passed_tests}/{total_tests} test categories successful.")
        print("   Basic functionality works but significant issues remain.")
        
    else:
        print("❌ NEEDS WORK! Few Dynamic Systems tests passed.")
        print(f"   Only {passed_tests}/{total_tests} test categories successful.")
        print("   Major issues need to be resolved before Dynamic Systems is ready.")
    
    return passed_tests == total_tests


def run_integration_validation():
    """Run integration validation with existing framework"""
    print(f"\n{'='*80}")
    print("INTEGRATION VALIDATION")
    print("="*80)
    print("Testing integration with existing Phase 1 & 2 functionality...")
    
    # Test that all phases still work together
    success, stdout, stderr, duration = run_pytest_command(
        ['python', '-m', 'pytest', 'tests/', '-v', '--tb=short'],
        "Full test suite (all phases)"
    )
    
    if success:
        print("✅ Integration validation passed!")
        print("   All phases (1, 2, 3) work together seamlessly.")
    else:
        print("❌ Integration issues detected!")
        print("   Dynamic Systems may have broken existing functionality.")
        
        # Try to identify the specific issue
        if stderr and 'ImportError' in stderr:
            print("   → Likely import/dependency issue")
        elif stderr and 'AttributeError' in stderr:
            print("   → Likely API compatibility issue")
        else:
            print("   → Review detailed output above")
    
    return success


def run_example_validation():
    """Validate that examples work with the new functionality"""
    print(f"\n{'='*80}")
    print("EXAMPLE VALIDATION")
    print("="*80)
    print("Testing that Dynamic Systems examples execute successfully...")
    
    examples_to_test = [
        ('examples/dynamic_systems_showcase.py', 'Comprehensive dynamic systems demonstration'),
        ('examples/predator_prey_dynamics.py', 'Predator-prey ecological modeling'),
        ('test_dynamic_system.py', 'Dynamic Systems validation test suite')
    ]
    
    example_results = {}
    
    for example_file, description in examples_to_test:
        if os.path.exists(example_file):
            print(f"\nTesting: {example_file}")
            print(f"Description: {description}")
            
            start_time = time.time()
            
            try:
                result = subprocess.run(
                    ['python', example_file],
                    capture_output=True,
                    text=True,
                    timeout=60,  # 60 second timeout
                    cwd=os.path.dirname(__file__)
                )
                
                duration = time.time() - start_time
                success = result.returncode == 0
                
                example_results[example_file] = {
                    'success': success,
                    'duration': duration,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
                if success:
                    print(f"  ✅ SUCCESS ({duration:.2f}s)")
                else:
                    print(f"  ❌ FAILED ({duration:.2f}s)")
                    if result.stderr:
                        # Show first few lines of error
                        error_lines = result.stderr.split('\n')[:3]
                        for line in error_lines:
                            if line.strip():
                                print(f"     {line}")
                
            except subprocess.TimeoutExpired:
                print(f"  ⏰ TIMEOUT (>60s)")
                example_results[example_file] = {
                    'success': False,
                    'duration': 60,
                    'stdout': '',
                    'stderr': 'Timeout after 60 seconds'
                }
            
            except Exception as e:
                print(f"  💥 EXCEPTION: {e}")
                example_results[example_file] = {
                    'success': False,
                    'duration': 0,
                    'stdout': '',
                    'stderr': str(e)
                }
        else:
            print(f"⚠️  Example not found: {example_file}")
    
    # Example validation summary
    successful_examples = sum(1 for result in example_results.values() if result['success'])
    total_examples = len(example_results)
    
    print(f"\nExample Results: {successful_examples}/{total_examples} examples successful")
    
    return successful_examples == total_examples


def main():
    """Main test runner"""
    print("TextToSolver Dynamic Systems Dynamic Systems Test Suite")
    print("=" * 60)
    
    overall_success = True
    
    # Step 1: Core Dynamic Systems tests
    print("\n🧪 STEP 1: Core Dynamic Systems Functionality Tests")
    dynamic_success = run_dynamic_tests()
    overall_success = overall_success and dynamic_success
    
    # Step 2: Integration validation
    print("\n🔗 STEP 2: Integration with Existing Framework")
    integration_success = run_integration_validation()
    overall_success = overall_success and integration_success
    
    # Step 3: Example validation
    print("\n📝 STEP 3: Example and Demo Validation")
    examples_success = run_example_validation()
    overall_success = overall_success and examples_success
    
    # Final assessment
    print(f"\n{'='*80}")
    print("FINAL ASSESSMENT")
    print("="*80)
    
    if overall_success:
        print("🎉 PHASE 3 IMPLEMENTATION COMPLETE AND VALIDATED!")
        print()
        print("✅ All core tests passed")
        print("✅ Integration with existing framework successful") 
        print("✅ Examples and demonstrations working")
        print()
        print("TextToSolver v3.0 is ready with dynamic systems capabilities!")
        print("Users can now solve differential equations alongside algebraic systems.")
        
    else:
        print("⚠️  PHASE 3 IMPLEMENTATION NEEDS ATTENTION")
        print()
        
        if not dynamic_success:
            print("❌ Core Dynamic Systems functionality has issues")
        else:
            print("✅ Core Dynamic Systems functionality working")
            
        if not integration_success:
            print("❌ Integration issues detected")
        else:
            print("✅ Integration successful")
            
        if not examples_success:
            print("❌ Example execution issues")
        else:
            print("✅ Examples working")
        
        print("\nReview the detailed output above to identify and fix issues.")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
