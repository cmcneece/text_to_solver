#!/usr/bin/env python3
"""
Simple test to verify our examples work with the new API
"""
import sys
import os
sys.path.append('/Users/colin.mcneece@cognitedata.com/personal/text_to_solver')

def test_new_api_circle_line():
    """Test the circle and line example with new API"""
    print("Testing circle and line with new EquationSolver API...")
    
    try:
        from text_to_solver import EquationSolver
        
        # Test the new API approach from our updated example
        equations = ['x**2 + y**2 = z**2', 'y = 5*x']
        variables = ['x', 'y']
        
        # Test parameter sweep
        solver = (EquationSolver()
                  .set_system(variables, equations)
                  .tolerance(1e-10)
                  .guess_strategy('auto'))
        
        results = solver.parameter_sweep('z', [1, 2, 3])
        
        successful = sum(1 for r in results if r.success)
        print(f"Parameter sweep: {successful}/3 successful")
        
        # Test one-liner
        result = EquationSolver.solve_equations(
            variables=['x', 'y'],
            equations=['x**2 + y**2 = z**2', 'y = 5*x'],
            parameters={'z': 3.0},
            tolerance=1e-10
        )
        
        if result.success:
            x, y = result['x'], result['y']
            # Verify solution: x² + y² should equal z²
            error = abs(x**2 + y**2 - 9.0)  # z=3, so z²=9
            print(f"One-liner test: x={x:.3f}, y={y:.3f}, error={error:.2e}")
            
            # Verify y = 5x constraint
            constraint_error = abs(y - 5*x)
            print(f"Constraint error (y=5x): {constraint_error:.2e}")
            
            assert error < 1e-8, f"Circle equation error too large: {error:.2e}"
            assert constraint_error < 1e-8, f"Constraint error too large: {constraint_error:.2e}"
        else:
            assert False, "One-liner test failed to converge"
            
    except Exception as e:
        assert False, f"Error in circle/line test: {e}"

if __name__ == "__main__":
    print("Running focused tests for updated examples...")
    print("=" * 50)
    
    tests = [
        test_new_api_circle_line
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Test {test.__name__} crashed: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTest Results: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All focused tests passed!")
    else:
        print("❌ Some tests failed")
