#!/usr/bin/env python3
"""
Test script for Dynamic System functionality

Tests the new differential equation solving capabilities of TextToSolver.
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Add the package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_simple_ode():
    """Test a simple exponential decay ODE: dx/dt = -k*x"""
    try:
        from text_to_solver.dynamic_solver import DynamicEquationSolver
        
        print("Testing simple exponential decay: dx/dt = -k*x")
        
        solver = DynamicEquationSolver()
        solver.set_system(
            variables=['x'],
            equations=['dx/dt = -k*x'],
            parameters={'k': 0.5},
            initial_conditions={'x': 1.0}
        )
        
        result = solver.integrate(time_span=(0, 10), method='RK45')
        
        assert result.success, f"Simple ODE failed: {result.message}"
        print(f"✓ Simple ODE solved successfully!")
        print(f"  Initial value: x(0) = {result.initial_values['x']:.3f}")
        print(f"  Final value: x(10) = {result.final_values['x']:.3f}")
        print(f"  Analytical: x(10) = {np.exp(-0.5*10):.3f}")
        print(f"  Number of time points: {len(result.time_points)}")
            
    except Exception as e:
        print(f"✗ Simple ODE test failed with exception: {str(e)}")
        assert False, f"Simple ODE test failed: {e}"

def test_predator_prey():
    """Test the predator-prey system using the general-purpose solver"""
    try:
        from text_to_solver.dynamic_solver import DynamicEquationSolver
        
        print("\nTesting predator-prey dynamics")
        
        solver = DynamicEquationSolver()
        solver.set_system(
            variables=['x', 'y'],
            equations=[
                'dx/dt = alpha*x - beta*x*y',  # Prey growth - predation
                'dy/dt = delta*x*y - gamma*y'  # Predator growth from hunting - death
            ],
            parameters={'alpha': 1.0, 'beta': 0.1, 'delta': 0.075, 'gamma': 1.5},
            initial_conditions={'x': 10, 'y': 5}
        )
        result = solver.integrate(time_span=(0, 20), method='RK45')
        
        assert result.success, f"Predator-prey failed: {result.message}"
        print(f"✓ Predator-prey system solved successfully!")
        print(f"  Initial: prey={result.initial_values['x']:.1f}, predator={result.initial_values['y']:.1f}")
        print(f"  Final: prey={result.final_values['x']:.1f}, predator={result.final_values['y']:.1f}")
        print(f"  Integration method: {result.integration_info.get('method', 'unknown')}")
        
        # Check if solution looks oscillatory (as expected)
        prey_values = result['x']
        if len(prey_values) > 10:
            max_prey = np.max(prey_values)
            min_prey = np.min(prey_values)
            if max_prey > min_prey * 1.5:  # Some oscillation expected
                print(f"  ✓ Solution shows expected oscillatory behavior")
            else:
                print(f"  ⚠ Solution may not be oscillating as expected")
            
    except Exception as e:
        print(f"✗ Predator-prey test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        assert False, f"Predator-prey test failed: {e}"

def test_convenience_function():
    """Test the solve_ode_system convenience function"""
    try:
        from text_to_solver.dynamic_solver import solve_ode_system
        
        print("\nTesting convenience function solve_ode_system")
        
        result = solve_ode_system(
            variables=['x', 'y'],
            equations=['dx/dt = -0.5*x', 'dy/dt = 0.3*y'],
            initial_conditions={'x': 1.0, 'y': 2.0},
            time_span=(0, 5),
            method='RK45'
        )
        
        assert result.success, f"Convenience function failed: {result.message}"
        print(f"✓ Convenience function worked!")
        print(f"  x: {result.initial_values['x']:.3f} → {result.final_values['x']:.3f}")
        print(f"  y: {result.initial_values['y']:.3f} → {result.final_values['y']:.3f}")
            
    except Exception as e:
        print(f"✗ Convenience function test failed: {str(e)}")
        assert False, f"Convenience function test failed: {e}"

def test_integration_methods():
    """Test different integration methods on the same system"""
    try:
        from text_to_solver.dynamic_solver import DynamicEquationSolver
        
        print("\nTesting different integration methods")
        
        # Simple system for testing
        solver = DynamicEquationSolver()
        solver.set_system(
            variables=['x'],
            equations=['dx/dt = -x'],
            parameters={},
            initial_conditions={'x': 1.0}
        )
        
        methods = ['euler', 'rk4', 'RK45']
        results = {}
        
        for method in methods:
            try:
                if method in ['euler', 'rk4']:
                    result = solver.integrate((0, 2), method=method, dt=0.01)
                else:
                    result = solver.integrate((0, 2), method=method)
                
                if result.success:
                    results[method] = result.final_values['x']
                    print(f"  ✓ {method}: x(2) = {result.final_values['x']:.4f}")
                else:
                    print(f"  ✗ {method} failed: {result.message}")
                    
            except Exception as e:
                print(f"  ✗ {method} failed with exception: {str(e)}")
        
        # Compare with analytical solution
        analytical = np.exp(-2.0)  # x(2) for dx/dt = -x, x(0) = 1
        print(f"  Analytical: x(2) = {analytical:.4f}")
        
        success_count = len(results)
        print(f"  {success_count}/{len(methods)} methods succeeded")
        
        assert success_count > 0, f"No integration methods succeeded: {success_count}/{len(methods)}"
        
    except Exception as e:
        print(f"✗ Integration methods test failed: {str(e)}")
        assert False, f"Integration methods test failed: {e}"

def create_visualization():
    """Create a simple visualization of the predator-prey system"""
    try:
        from text_to_solver.dynamic_solver import DynamicEquationSolver
        
        print("\nCreating predator-prey visualization...")
        
        solver = DynamicEquationSolver()
        solver.set_system(
            variables=['x', 'y'],
            equations=[
                'dx/dt = alpha*x - beta*x*y',  # Prey growth - predation
                'dy/dt = delta*x*y - gamma*y'  # Predator growth from hunting - death
            ],
            parameters={'alpha': 1.0, 'beta': 0.1, 'delta': 0.075, 'gamma': 1.5},
            initial_conditions={'x': 10, 'y': 5}
        )
        result = solver.integrate(time_span=(0, 20), method='RK45')
        
        if result.success:
            plt.figure(figsize=(12, 4))
            
            # Time series plot
            plt.subplot(1, 2, 1)
            plt.plot(result.time_points, result['x'], label='Prey (x)', linewidth=2)
            plt.plot(result.time_points, result['y'], label='Predator (y)', linewidth=2)
            plt.xlabel('Time')
            plt.ylabel('Population')
            plt.title('Predator-Prey Dynamics')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Phase portrait
            plt.subplot(1, 2, 2)
            plt.plot(result['x'], result['y'], 'b-', linewidth=2, alpha=0.8)
            plt.plot(result['x'][0], result['y'][0], 'go', markersize=8, label='Start')
            plt.plot(result['x'][-1], result['y'][-1], 'ro', markersize=8, label='End')
            plt.xlabel('Prey Population (x)')
            plt.ylabel('Predator Population (y)')
            plt.title('Phase Portrait')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig('dynamic_system_test_result.png', dpi=150, bbox_inches='tight')
            print("  ✓ Visualization saved as 'dynamic_system_test_result.png'")
            
            return True
        else:
            print(f"  ✗ Could not create visualization: {result.message}")
            return False
            
    except Exception as e:
        print(f"✗ Visualization failed: {str(e)}")
        return False

def main():
    """Run all dynamic system tests"""
    print("=" * 60)
    print("TextToSolver: Dynamic Systems Test Suite")
    print("=" * 60)
    
    tests = [
        test_simple_ode,
        test_predator_prey,
        test_convenience_function,
        test_integration_methods
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    # Create visualization (optional)
    try:
        create_visualization()
    except ImportError:
        print("\nSkipping visualization (matplotlib not available)")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"  Passed: {passed}/{total}")
    
    if passed == total:
        print("  🎉 All dynamic system tests passed!")
        print("  Dynamic systems implementation is ready for use.")
    else:
        print("  ⚠ Some tests failed - check implementation")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
