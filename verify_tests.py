#!/usr/bin/env python3
"""
Simple test verification script to check if the test suite can be imported and run
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def verify_test_imports():
    """Verify that all test modules can be imported"""
    print("🧪 Verifying Test Suite")
    print("=" * 50)
    
    test_modules = [
        'tests.conftest',
        'tests.test_basic_functionality', 
        'tests.test_enhanced_functionality',
        'tests.test_validation_and_errors',
        'tests.test_integration'
    ]
    
    success = True
    for module in test_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except Exception as e:
            print(f"❌ {module}: {e}")
            success = False
    
    return success

def verify_fixtures():
    """Verify that test fixtures work"""
    print("\n🔧 Verifying Test Fixtures")
    print("=" * 50)
    
    try:
        from tests.conftest import (
            simple_linear_system, simple_nonlinear_system, 
            circle_line_system, default_solver_options
        )
        print("✅ Test fixtures imported successfully")
        return True
    except Exception as e:
        print(f"❌ Fixture import failed: {e}")
        return False

def verify_enhanced_functionality():
    """Verify that enhanced functionality is available"""
    print("\n⚡ Verifying Enhanced Functionality")
    print("=" * 50)
    
    try:
        from text_to_solver.TextToSolver import TextToSolver, SolverOptions
        
        # Test basic creation
        solver = TextToSolver(['x', 'y'], ['x + y - 1', 'x - y'])
        print("✅ TextToSolver creation")
        
        # Test SolverOptions
        options = SolverOptions(display=False)
        print("✅ SolverOptions creation")
        
        # Test enhanced methods
        guess = solver.generate_initial_guess(strategy='heuristic')
        print("✅ generate_initial_guess method")
        
        solution, report = solver.solve_auto(options=options)
        print("✅ solve_auto method")
        
        # Test multistart capability
        solution2, report2 = solver.solve_auto(multistart=True, options=options)  
        print("✅ multistart capability")
        
        # Test pattern detection
        pattern = solver._detect_equation_patterns()
        print(f"✅ pattern detection: {pattern}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced functionality error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_basic_test():
    """Run a basic functionality test"""
    print("\n🔬 Running Basic Test")
    print("=" * 50)
    
    try:
        from text_to_solver.TextToSolver import TextToSolver, SolverOptions
        
        # Create simple linear system: x + y = 3, x - y = 1
        solver = TextToSolver(['x', 'y'], ['x + y - 3', 'x - y - 1'])
        
        # Solve with auto guess
        solution, report = solver.solve_auto(options=SolverOptions(display=False))
        
        # Check results
        if report['exit_flag'] == 1:
            x, y = solution['x'][0], solution['y'][0]
            if abs(x - 2.0) < 1e-6 and abs(y - 1.0) < 1e-6:
                print(f"✅ Correct solution: x={x:.6f}, y={y:.6f}")
                return True
            else:
                print(f"❌ Incorrect solution: x={x:.6f}, y={y:.6f}")
                return False
        else:
            print(f"❌ Solver failed with exit_flag: {report['exit_flag']}")
            return False
            
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main verification function"""
    print("🚀 TextToSolver Test Suite Verification")
    print("=" * 60)
    
    results = []
    
    # Run all verifications
    results.append(("Test Imports", verify_test_imports()))
    results.append(("Test Fixtures", verify_fixtures()))
    results.append(("Enhanced Functionality", verify_enhanced_functionality()))
    results.append(("Basic Test", run_basic_test()))
    
    # Summary
    print("\n📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL" 
        print(f"{name:<25} {status}")
        all_passed &= success
    
    print("=" * 60)
    if all_passed:
        print("🎉 ALL VERIFICATIONS PASSED!")
        print("   The test suite is ready and functional")
    else:
        print("❌ SOME VERIFICATIONS FAILED!")
        print("   Please check the errors above")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
