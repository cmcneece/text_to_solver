#!/usr/bin/env python3
"""
Direct test of updated examples without using terminal/subprocess
"""
import sys
import os
import traceback

# Add project to path
project_path = '/Users/colin.mcneece@cognitedata.com/personal/text_to_solver'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

def test_circle_line_new_api():
    """Test circle line example with new API"""
    print("\nTesting circle-line with new EquationSolver...")
    try:
        from text_to_solver import EquationSolver
        
        # Test one-liner approach
        result = EquationSolver.solve_equations(
            variables=['x', 'y'],
            equations=['x**2 + y**2 = z**2', 'y = 5*x'],
            parameters={'z': 3.0},
            tolerance=1e-10
        )
        
        if result.success:
            x, y = result['x'], result['y']
            error = abs(x**2 + y**2 - 9.0)  # z²=9
            constraint_error = abs(y - 5*x)
            print(f"  Solution: x={x:.4f}, y={y:.4f}")
            print(f"  Circle error: {error:.2e}")
            print(f"  Line error: {constraint_error:.2e}")
            
            assert error < 1e-8, f"Circle equation error too large: {error:.2e}"
            assert constraint_error < 1e-8, f"Line constraint error too large: {constraint_error:.2e}"
            print("✅ Circle-line test passed")
        else:
            assert False, "Failed to converge"
            
    except Exception as e:
        print(f"❌ Circle-line test failed: {e}")
        traceback.print_exc()
        assert False, f"Circle-line test failed: {e}"

def test_parameter_sweep():
    """Test parameter sweep functionality"""
    print("\nTesting parameter sweep...")
    try:
        from text_to_solver import EquationSolver
        
        solver = (EquationSolver()
                  .set_system(['x', 'y'], ['x**2 + y**2 = z**2', 'y = 5*x'])
                  .tolerance(1e-8)
                  .guess_strategy('auto'))
        
        results = solver.parameter_sweep('z', [1.0, 2.0, 3.0])
        successful = sum(1 for r in results if r.success)
        
        print(f"  Parameter sweep: {successful}/3 successful")
        
        assert successful >= 2, f"Insufficient successful solutions: {successful}/3"
        print("✅ Parameter sweep test passed")
            
    except Exception as e:
        print(f"❌ Parameter sweep test failed: {e}")
        traceback.print_exc()
        assert False, f"Parameter sweep test failed: {e}"

def test_original_api_compatibility():
    """Test that original API still works"""
    print("\nTesting original API compatibility...")
    try:
        from text_to_solver import TextToSolver, SolverOptions
        import numpy as np
        
        # Simple circle-line test with original API
        residual = ['x ** 2 + y ** 2 - z ** 2', 'y - 5 * x']
        dep_vars = ['x', 'y']
        ind_vars = ['z']
        
        solver = TextToSolver(dep_vars, residual, indep_vars=ind_vars)
        options = SolverOptions(display=False, tol_fun=1e-10)
        
        z_values = np.array([3.0])
        ind_var = {'z': z_values}
        guess = {'x': np.array([0.5]), 'y': np.array([2.5])}
        
        solution, report = solver.solve(guess, indep_var_val=ind_var, options=options)
        
        # Accept both exit_flag=1 (function convergence) and exit_flag=2 (step size convergence)
        # as successful if residual norm is small
        converged = report['exit_flag'] == 1 or (report['exit_flag'] == 2 and report.get('res_norm', 1) < 1e-6)
        
        if converged:
            x, y = solution['x'][0], solution['y'][0]
            print(f"  Original API solution: x={x:.4f}, y={y:.4f}")
            print(f"  Residual norm: {report.get('res_norm', 'N/A'):.2e}")
            print("✅ Original API compatibility maintained")
        else:
            print("❌ Original API failed to converge")
            print(f"  Exit flag: {report['exit_flag']}, Residual norm: {report.get('res_norm', 'N/A')}")
            assert False, f"Original API failed to converge: exit_flag={report['exit_flag']}, res_norm={report.get('res_norm', 'N/A')}"
            
    except Exception as e:
        print(f"❌ Original API test failed: {e}")
        traceback.print_exc()
        assert False, f"Original API test failed: {e}"

def run_all_tests():
    """Run all tests"""
    print("🧪 Running comprehensive test suite for updated examples")
    print("=" * 60)
    
    tests = [
        ("Circle-Line New API", test_circle_line_new_api),
        ("Parameter Sweep", test_parameter_sweep),
        ("Original API Compatibility", test_original_api_compatibility)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{name}:")
        print("-" * len(name))
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:<25} {status}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed ({100*passed/total:.0f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Examples are working correctly with new API.")
    else:
        print(f"\n⚠️  {total-passed} tests failed. Some functionality may need attention.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
