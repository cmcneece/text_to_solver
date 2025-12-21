#!/usr/bin/env python3
"""
Demonstration and documentation tests for iteration tracking functionality.

This file provides practical examples of how to use the new iteration tracking
features for debugging and analysis purposes.
"""

import pytest
import numpy as np

from text_to_solver.TextToSolver import TextToSolver, SolverOptions
from text_to_solver import EquationSolver


@pytest.mark.iteration_tracking
def test_iteration_tracking_demo():
    """Demonstrate practical use of iteration tracking for debugging."""
    
    print("\n" + "="*60)
    print("ITERATION TRACKING DEMONSTRATION")
    print("="*60)
    
    # Create a nonlinear system
    solver = TextToSolver(['x', 'y'], [
        'x**2 + y**2 - 10',  # Circle: x² + y² = 10
        'x*y - 3'            # Hyperbola: xy = 3
    ])
    
    guess = {'x': np.array([2.0]), 'y': np.array([1.5])}
    
    # Solve with iteration tracking enabled
    print("\n1. SOLVING WITH ITERATION TRACKING:")
    options = SolverOptions(display=False, store_history=True, tol_fun=1e-8)
    solution, report = solver.solve(guess, options=options)
    
    print(f"   ✅ Converged: exit_flag = {report['exit_flag']}")
    print(f"   📊 Solution: x = {solution['x'][0]:.6f}, y = {solution['y'][0]:.6f}")
    print(f"   ⏱️  Total time: {report['total_solve_time']:.4f} seconds")
    
    # Access iteration history
    print("\n2. ITERATION-BY-ITERATION ANALYSIS:")
    history = solver.get_iteration_history()
    residuals = solver.get_residual_history()
    
    for i, (iter_data, residual) in enumerate(zip(history, residuals)):
        print(f"   Iteration {i+1}:")
        print(f"     Residual norm: {residual:.6f}")
        print(f"     Step norm: {iter_data.step_norm:.6f}")
        print(f"     Lambda factor: {iter_data.lambda_factor}")
        print(f"     Condition #: {iter_data.condition_number:.2f}")
        
        # Show solution progress
        x_val = iter_data.solution_vector[0]
        y_val = iter_data.solution_vector[1]
        print(f"     Solution: x={x_val:.6f}, y={y_val:.6f}")
        
        # Verify equations at this point
        eq1_residual = x_val**2 + y_val**2 - 10
        eq2_residual = x_val * y_val - 3
        print(f"     Equation residuals: [{eq1_residual:.6f}, {eq2_residual:.6f}]")
        print()
    
    # Convergence analysis
    print("3. CONVERGENCE ANALYSIS:")
    analysis = solver.analyze_convergence()
    
    print(f"   📈 Convergence type: {analysis['convergence_type']}")
    print(f"   📉 Residual reduction: {analysis['residual_reduction']:.2e}x improvement")
    print(f"   ⚡ Speed: {analysis['iterations_per_second']:.1f} iterations/second")
    print(f"   🔄 Total iterations: {analysis['total_iterations']}")
    
    # Performance comparison
    print("\n4. PERFORMANCE COMPARISON:")
    
    # Time with tracking
    import time
    start = time.time()
    for _ in range(10):
        solver.solve(guess, options=SolverOptions(store_history=True, display=False))
    time_with_tracking = time.time() - start
    
    # Time without tracking  
    start = time.time()
    for _ in range(10):
        solver.solve(guess, options=SolverOptions(store_history=False, display=False))
    time_without_tracking = time.time() - start
    
    overhead = (time_with_tracking / time_without_tracking - 1) * 100
    print(f"   📊 Performance overhead: {overhead:.1f}%")
    
    # Validation
    assert report['exit_flag'] == 1, "Should converge successfully"
    assert len(history) > 0, "Should capture iteration history"
    assert analysis['residual_reduction'] > 10, "Should show significant improvement"
    assert overhead < 50, "Overhead should be reasonable"
    
    print(f"\n✅ All validations passed!")
    print("="*60)


@pytest.mark.iteration_tracking
def test_debugging_convergence_issues():
    """Demonstrate using iteration tracking to debug convergence problems."""
    
    print("\n" + "="*60)
    print("DEBUGGING CONVERGENCE ISSUES")
    print("="*60)
    
    # Create a challenging system (multiple solutions)
    solver = TextToSolver(['x'], ['x**3 - 3*x**2 + 2*x'])  # Has roots at 0, 1, 2
    
    # Try different initial guesses
    guesses_to_try = [0.1, 0.9, 1.5, 2.1]
    
    for i, initial_x in enumerate(guesses_to_try):
        print(f"\n{i+1}. STARTING FROM x = {initial_x}")
        
        guess = {'x': np.array([initial_x])}
        solution, report = solver.solve(
            guess, 
            options=SolverOptions(display=False, store_history=True, tol_fun=1e-10)
        )
        
        # Analyze this attempt
        history = solver.get_iteration_history()
        analysis = solver.analyze_convergence()
        
        print(f"   Result: x = {solution['x'][0]:.6f}")
        print(f"   Status: {'✅ Converged' if report['exit_flag'] == 1 else '❌ Failed'}")
        print(f"   Iterations: {len(history)}")
        print(f"   Convergence: {analysis['convergence_type']}")
        
        # Show residual progression
        residuals = solver.get_residual_history()
        if len(residuals) > 1:
            initial_residual = residuals[0]
            final_residual = residuals[-1]
            reduction = initial_residual / final_residual if final_residual > 0 else float('inf')
            print(f"   Residual: {initial_residual:.2e} → {final_residual:.2e} ({reduction:.1e}x)")
        
        # Check for potential issues
        steps = solver.get_step_history()
        if len(steps) > 2:
            avg_step = np.mean(steps)
            if avg_step > 10:
                print("   ⚠️  Large step sizes detected - might indicate poor conditioning")
            elif max(steps) / min(steps) > 100:
                print("   ⚠️  Highly variable step sizes - might indicate oscillation")
        
        # Check condition numbers
        if len(history) > 0:
            condition_numbers = [iter_data.condition_number for iter_data in history]
            max_condition = max(condition_numbers)
            if max_condition > 1e12:
                print(f"   ⚠️  Poor conditioning detected: max condition # = {max_condition:.2e}")


@pytest.mark.iteration_tracking
def test_user_api_integration_demo():
    """Demonstrate iteration tracking integration with user API."""
    
    print("\n" + "="*50)
    print("USER API INTEGRATION")
    print("="*50)
    
    # Use the high-level API
    solver = EquationSolver()
    solver.set_system(['x', 'y', 'z'], [
        'x + y + z - 6',
        'x**2 + y**2 + z**2 - 14', 
        'x*y - z - 2'
    ])
    
    print("\n1. SOLVING WITH USER API:")
    result = solver.solve()
    
    print(f"   ✅ Success: {result.success}")
    print(f"   📊 Variables: x={result['x']:.3f}, y={result['y']:.3f}, z={result['z']:.3f}")
    print(f"   🔄 Iterations: {result.iterations}")
    
    # Check if detailed history is available
    print("\n2. ACCESSING DETAILED HISTORY:")
    if 'iteration_history' in result.solver_info:
        detailed_history = result.solver_info['iteration_history']
        print(f"   📋 Detailed history available: {len(detailed_history)} iterations")
        
        # Show convergence progression
        residual_norms = [iter_data.residual_norm for iter_data in detailed_history]
        print(f"   📉 Residual progression: {residual_norms[0]:.2e} → {residual_norms[-1]:.2e}")
        
    else:
        print("   ℹ️  Detailed history not available in user API result")
        print("      (Use TextToSolver directly for detailed iteration data)")
    
    print("="*50)


if __name__ == "__main__":
    # Run demonstrations when executed directly
    test_iteration_tracking_demo()
    test_debugging_convergence_issues()  
    test_user_api_integration_demo()
