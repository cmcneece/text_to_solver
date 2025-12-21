#!/usr/bin/env python3
"""
Iteration Data Tracking Showcase for TextToSolver

This example demonstrates the powerful iteration tracking capabilities that allow
users to monitor solver behavior, debug convergence issues, and optimize
solver performance for complex nonlinear systems.

QUICK START:
    python examples/iteration_tracking_showcase.py

Features Demonstrated:
- Complete iteration history capture
- Convergence rate analysis and classification  
- Performance monitoring and timing analysis
- Debugging failed convergence scenarios
- Comparison of different solver configurations
- Real-time solver diagnostics

Examples Included:
1. Basic Iteration Tracking - Circle-hyperbola intersection with detailed analysis
2. Initial Guess Sensitivity - How different starting points affect convergence
3. Performance Monitoring - Comparing solver configurations for optimization
4. Debugging Failed Convergence - Using iteration data to diagnose problems

Key Iteration Data Available:
- Residual norms at each iteration
- Newton step sizes and directions
- Jacobian condition numbers
- Line search factors (λ)
- Solution vector progression
- Timing and performance metrics
- Automatic convergence classification

Author: TextToSolver Development Team
"""

import numpy as np
import sys
import os
from typing import Dict, List, Any
import time

# Add src directory to path for imports
# Note: In production, the package should be installed with 'pip install -e .'
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src'))

from text_to_solver.TextToSolver import TextToSolver, SolverOptions

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Note: matplotlib not available - plotting features disabled")


class IterationAnalyzer:
    """Helper class for analyzing and visualizing iteration data."""
    
    def __init__(self, solver: TextToSolver):
        self.solver = solver
        
    def plot_convergence_history(self, title: str = "Convergence History"):
        """Create a convergence plot showing residual reduction over iterations."""
        if not MATPLOTLIB_AVAILABLE:
            print("Matplotlib not available - plotting skipped.")
            return
            
        history = self.solver.get_iteration_history()
        if not history:
            print("No iteration history available for plotting.")
            return
            
        iterations = list(range(1, len(history) + 1))
        residuals = [iter_data.residual_norm for iter_data in history]
        step_norms = [iter_data.step_norm for iter_data in history]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Residual convergence
        ax1.semilogy(iterations, residuals, 'b-o', markersize=4, linewidth=2)
        ax1.set_xlabel('Iteration')
        ax1.set_ylabel('Residual Norm')
        ax1.set_title(f'{title} - Residual Convergence')
        ax1.grid(True, alpha=0.3)
        
        # Step size progression
        ax2.semilogy(iterations, step_norms, 'r-s', markersize=4, linewidth=2)
        ax2.set_xlabel('Iteration')
        ax2.set_ylabel('Step Norm')
        ax2.set_title('Newton Step Size Progression')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
    def print_detailed_analysis(self):
        """Print comprehensive analysis of solver performance."""
        analysis = self.solver.analyze_convergence()
        history = self.solver.get_iteration_history()
        
        print(f"\n{'='*60}")
        print("DETAILED CONVERGENCE ANALYSIS")
        print(f"{'='*60}")
        
        if 'error' in analysis:
            print(f"❌ {analysis['error']}")
            return
            
        # Basic statistics
        print(f"📊 SOLVER STATISTICS:")
        print(f"   Total iterations: {analysis['total_iterations']}")
        print(f"   Convergence type: {analysis['convergence_type']}")
        print(f"   Total solve time: {analysis['total_solve_time']:.4f} seconds")
        print(f"   Iterations per second: {analysis['iterations_per_second']:.1f}")
        
        # Convergence metrics
        print(f"\n🎯 CONVERGENCE METRICS:")
        print(f"   Initial residual: {analysis['initial_residual']:.6e}")
        print(f"   Final residual: {analysis['final_residual']:.6e}")
        print(f"   Residual reduction: {analysis['residual_reduction']:.2e}x")
        print(f"   Average convergence rate: {analysis['average_convergence_rate']:.4f}")
        
        # Per-iteration details
        print(f"\n🔍 ITERATION-BY-ITERATION BREAKDOWN:")
        residuals = self.solver.get_residual_history()
        steps = self.solver.get_step_history()
        
        for i, (iter_data, residual, step) in enumerate(zip(history, residuals, steps)):
            print(f"   Iteration {i+1:2d}: "
                  f"residual={residual:.2e}, "
                  f"step={step:.2e}, "
                  f"λ={iter_data.lambda_factor:.3f}, "
                  f"cond={iter_data.condition_number:.1e}")
        
        # Performance insights
        print(f"\n⚡ PERFORMANCE INSIGHTS:")
        if len(history) > 1:
            condition_numbers = [iter_data.condition_number for iter_data in history]
            lambda_factors = [iter_data.lambda_factor for iter_data in history]
            
            print(f"   Condition number range: {min(condition_numbers):.1e} - {max(condition_numbers):.1e}")
            print(f"   Line search factors: {min(lambda_factors):.3f} - {max(lambda_factors):.3f}")
            
            if max(condition_numbers) > 1e12:
                print("   ⚠️  WARNING: Poor conditioning detected - consider preconditioning")
            if min(lambda_factors) < 0.1:
                print("   ⚠️  WARNING: Frequent line search activation - might indicate poor initial guess")


def example_1_basic_nonlinear_system():
    """Example 1: Basic iteration tracking for a simple nonlinear system."""
    
    print("\n" + "="*70)
    print("EXAMPLE 1: BASIC ITERATION TRACKING")
    print("="*70)
    print("System: Circle-Hyperbola intersection")
    print("  Equation 1: x² + y² = 13   (circle)")  
    print("  Equation 2: xy = 6         (hyperbola)")
    print("  Analytical solutions: (3,2), (2,3), (-3,-2), (-2,-3)")
    
    # Create solver
    solver = TextToSolver(['x', 'y'], [
        'x**2 + y**2 - 13',  # Circle: x² + y² = 13
        'x*y - 6'            # Hyperbola: xy = 6
    ])
    
    # Solve with iteration tracking - use better initial guess
    guess = {'x': np.array([2.8]), 'y': np.array([2.2])}  # Closer to analytical solution (3,2)
    options = SolverOptions(display=False, store_history=True, tol_fun=1e-10, max_iter=25)
    
    print(f"\nSolving with initial guess: x={guess['x'][0]}, y={guess['y'][0]}")
    
    solution, report = solver.solve(guess, options=options)
    
    # Display results
    print(f"\n📊 SOLUTION:")
    print(f"   x = {solution['x'][0]:.8f}")
    print(f"   y = {solution['y'][0]:.8f}")
    
    # Verify solution accuracy
    x_sol, y_sol = solution['x'][0], solution['y'][0]
    eq1_check = x_sol**2 + y_sol**2 - 13
    eq2_check = x_sol * y_sol - 6
    residual_norm = np.sqrt(eq1_check**2 + eq2_check**2)
    
    # More realistic convergence check
    converged = (report['exit_flag'] == 1) or (residual_norm < 1e-8)
    print(f"   Status: {'✅ Converged' if converged else '❌ Failed'}")
    print(f"   Verification: eq1 residual = {eq1_check:.2e}, eq2 residual = {eq2_check:.2e}")
    print(f"   Overall residual norm: {residual_norm:.2e}")
    
    # Analyze iterations
    analyzer = IterationAnalyzer(solver)
    
    # Check if we need alternative approach
    if not converged:
        print(f"   ⚠️  Convergence issue detected - trying alternative approach...")
        
        # Try with a different, better guess
        alt_guess = {'x': np.array([3.1]), 'y': np.array([1.9])}
        alt_solution, alt_report = solver.solve(alt_guess, options=options)
        
        if alt_report['exit_flag'] == 1:
            print(f"   ✅ Success with alternative guess!")
            solution, report = alt_solution, alt_report
            x_sol, y_sol = solution['x'][0], solution['y'][0] 
            eq1_check = x_sol**2 + y_sol**2 - 13
            eq2_check = x_sol * y_sol - 6
            print(f"   Updated solution: x={x_sol:.8f}, y={y_sol:.8f}")
            print(f"   Verification: eq1 residual = {eq1_check:.2e}, eq2 residual = {eq2_check:.2e}")
    
    analyzer.print_detailed_analysis()
    
    return solver, solution, report


def example_2_challenging_system_comparison():
    """Example 2: Compare solver behavior for different initial guesses."""
    
    print("\n" + "="*70)
    print("EXAMPLE 2: CHALLENGING SYSTEM - INITIAL GUESS SENSITIVITY")
    print("="*70)
    print("System: Chemical equilibrium-like system")
    print("  Equation 1: x³ - 3xy + y² = 1")
    print("  Equation 2: x² + y² - 2xy = 2")
    
    # Create solver  
    solver = TextToSolver(['x', 'y'], [
        'x**3 - 3*x*y + y**2 - 1',
        'x**2 + y**2 - 2*x*y - 2'
    ])
    
    # Test different initial guesses
    initial_guesses = [
        {'name': 'Conservative', 'x': 0.5, 'y': 0.5},
        {'name': 'Aggressive', 'x': 2.0, 'y': 2.0}, 
        {'name': 'Asymmetric', 'x': 1.5, 'y': 0.8},
        {'name': 'Negative', 'x': -1.0, 'y': 1.0}
    ]
    
    results = []
    
    for i, guess_info in enumerate(initial_guesses):
        print(f"\n{i+1}. {guess_info['name'].upper()} GUESS: x={guess_info['x']}, y={guess_info['y']}")
        
        guess = {'x': np.array([guess_info['x']]), 'y': np.array([guess_info['y']])}
        options = SolverOptions(display=False, store_history=True, max_iter=25)
        
        solution, report = solver.solve(guess, options=options)
        
        # Analyze this attempt
        analysis = solver.analyze_convergence()
        history = solver.get_iteration_history()
        
        result_info = {
            'name': guess_info['name'],
            'initial': (guess_info['x'], guess_info['y']),
            'converged': report['exit_flag'] == 1,
            'solution': (solution['x'][0], solution['y'][0]) if report['exit_flag'] == 1 else None,
            'iterations': len(history),
            'convergence_type': analysis.get('convergence_type', 'unknown'),
            'residual_reduction': analysis.get('residual_reduction', 0),
            'solve_time': analysis.get('total_solve_time', 0)
        }
        results.append(result_info)
        
        # Display immediate results
        if result_info['converged']:
            x_sol, y_sol = result_info['solution']
            print(f"   ✅ Converged to: x={x_sol:.6f}, y={y_sol:.6f}")
            print(f"   🔄 Iterations: {result_info['iterations']}")
            print(f"   📈 Convergence: {result_info['convergence_type']}")
            print(f"   📉 Reduction: {result_info['residual_reduction']:.1e}x")
        else:
            print(f"   ❌ Failed to converge after {result_info['iterations']} iterations")
            
        # Show convergence pattern
        residuals = solver.get_residual_history()
        if len(residuals) >= 3:
            print(f"   📊 Residual pattern: {residuals[0]:.2e} → {residuals[1]:.2e} → {residuals[-1]:.2e}")
    
    # Summary comparison
    print(f"\n📋 SUMMARY COMPARISON:")
    print(f"{'Guess':<12} {'Success':<8} {'Iterations':<11} {'Convergence':<15} {'Time (ms)':<10}")
    print("-" * 65)
    
    for result in results:
        success = "✅ Yes" if result['converged'] else "❌ No"
        iterations = str(result['iterations'])
        convergence = result['convergence_type'][:14] if result['converged'] else "failed"
        solve_time = f"{result['solve_time']*1000:.2f}" if result['converged'] else "N/A"
        
        print(f"{result['name']:<12} {success:<8} {iterations:<11} {convergence:<15} {solve_time:<10}")
    
    return results


def example_3_performance_monitoring():
    """Example 3: Performance monitoring and optimization insights."""
    
    print("\n" + "="*70)
    print("EXAMPLE 3: PERFORMANCE MONITORING & OPTIMIZATION")
    print("="*70)
    print("System: Large nonlinear system (5 variables)")
    
    # Create a larger system
    n = 5
    variables = [f'x{i}' for i in range(n)]
    equations = []
    
    # Create a challenging but well-conditioned system
    for i in range(n):
        if i == 0:
            eq = f"x0**2 + x1**2 - {2*(i+1)}"
        elif i == n-1:
            eq = f"x{i-1} * x{i} - {i+1}"
        else:
            eq = f"x{i-1}**2 + x{i}**2 + x{i+1} - {3*(i+1)}"
        equations.append(eq)
    
    print(f"Variables: {variables}")
    print(f"Equations: {len(equations)} nonlinear equations")
    
    solver = TextToSolver(variables, equations)
    
    # Test different solver configurations
    configurations = [
        {'name': 'Standard', 'tol_fun': 1e-6, 'max_iter': 20},
        {'name': 'High Precision', 'tol_fun': 1e-10, 'max_iter': 30},
        {'name': 'Fast', 'tol_fun': 1e-4, 'max_iter': 15}
    ]
    
    print(f"\n🔧 TESTING SOLVER CONFIGURATIONS:")
    
    # Initial guess
    guess = {f'x{i}': np.array([1.0]) for i in range(n)}
    
    performance_results = []
    
    for config in configurations:
        print(f"\n   {config['name'].upper()} Configuration:")
        print(f"     Tolerance: {config['tol_fun']:.0e}, Max iterations: {config['max_iter']}")
        
        options = SolverOptions(
            display=False,
            store_history=True,
            tol_fun=config['tol_fun'],
            max_iter=config['max_iter']
        )
        
        # Multiple runs for timing accuracy
        times = []
        converged_runs = 0
        total_iterations = 0
        
        for _ in range(5):
            start_time = time.time()
            solution, report = solver.solve(guess, options=options)
            run_time = time.time() - start_time
            
            times.append(run_time)
            if report['exit_flag'] == 1:
                converged_runs += 1
            
            analysis = solver.analyze_convergence()
            total_iterations += analysis.get('total_iterations', 0)
        
        avg_time = np.mean(times)
        avg_iterations = total_iterations / 5
        
        perf_result = {
            'name': config['name'],
            'avg_time': avg_time,
            'avg_iterations': avg_iterations,
            'success_rate': converged_runs / 5,
            'tolerance': config['tol_fun']
        }
        performance_results.append(perf_result)
        
        print(f"     Average time: {avg_time*1000:.2f} ms")
        print(f"     Average iterations: {avg_iterations:.1f}")
        print(f"     Success rate: {converged_runs}/5 ({100*converged_runs/5:.0f}%)")
        
        # Detailed analysis for successful run
        if converged_runs > 0:
            analysis = solver.analyze_convergence()
            print(f"     Convergence type: {analysis.get('convergence_type', 'unknown')}")
    
    # Performance comparison
    print(f"\n⚡ PERFORMANCE COMPARISON:")
    print(f"{'Config':<15} {'Avg Time (ms)':<13} {'Avg Iterations':<14} {'Success Rate':<12} {'Efficiency':<10}")
    print("-" * 75)
    
    for result in performance_results:
        efficiency = result['avg_iterations'] / (result['avg_time'] * 1000)  # iter per ms
        success_pct = f"{result['success_rate']*100:.0f}%"
        
        print(f"{result['name']:<15} "
              f"{result['avg_time']*1000:<13.2f} "
              f"{result['avg_iterations']:<14.1f} "
              f"{success_pct:<12} "
              f"{efficiency:<10.1f}")
    
    # Recommendations
    print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
    best_time = min(perf_result['avg_time'] for perf_result in performance_results)
    best_accuracy = min(perf_result['tolerance'] for perf_result in performance_results if perf_result['success_rate'] == 1.0)
    
    for result in performance_results:
        if result['avg_time'] == best_time:
            print(f"   🚀 Fastest configuration: {result['name']}")
        if result['tolerance'] == best_accuracy and result['success_rate'] == 1.0:
            print(f"   🎯 Most accurate configuration: {result['name']}")
    
    return performance_results


def example_4_debugging_failed_convergence():
    """Example 4: Using iteration data to debug convergence failures."""
    
    print("\n" + "="*70)
    print("EXAMPLE 4: DEBUGGING CONVERGENCE FAILURES")
    print("="*70)
    print("System: Problematic nonlinear system with poor conditioning")
    
    # Create a system that might have convergence issues
    solver = TextToSolver(['x', 'y'], [
        'x**4 - 2*x**2*y + y**2 - 1',    # Creates nearly singular Jacobian near solution
        '(x-1)**3 + (y-1)**3 - 0.001'   # Very flat near solution
    ])
    
    # Try with a poor initial guess
    guess = {'x': np.array([0.1]), 'y': np.array([0.1])}
    options = SolverOptions(display=False, store_history=True, max_iter=15, tol_fun=1e-8)
    
    print(f"Attempting to solve with challenging initial guess: x=0.1, y=0.1")
    
    solution, report = solver.solve(guess, options=options)
    
    print(f"\n🔍 DEBUGGING ANALYSIS:")
    
    if report['exit_flag'] != 1:
        print(f"   ❌ Solver failed with exit_flag = {report['exit_flag']}")
        
        # Analyze what went wrong
        history = solver.get_iteration_history()
        if len(history) > 0:
            print(f"   📊 Completed {len(history)} iterations before failure")
            
            # Check for common issues
            condition_numbers = [iter_data.condition_number for iter_data in history]
            residual_norms = [iter_data.residual_norm for iter_data in history]
            step_norms = [iter_data.step_norm for iter_data in history]
            lambda_factors = [iter_data.lambda_factor for iter_data in history]
            
            print(f"\n   🔧 DIAGNOSTIC CHECKS:")
            
            # Check conditioning
            max_cond = max(condition_numbers)
            if max_cond > 1e12:
                print(f"   ⚠️  POOR CONDITIONING: Max condition number = {max_cond:.2e}")
                print(f"       → Consider: Better initial guess, scaling, or preconditioning")
            
            # Check residual progress
            if len(residual_norms) > 3:
                initial_residual = residual_norms[0]
                final_residual = residual_norms[-1] 
                if final_residual > initial_residual * 0.1:
                    print(f"   ⚠️  SLOW CONVERGENCE: Residual only reduced {initial_residual/final_residual:.1f}x")
                    print(f"       → Consider: Different solver method or better initial guess")
            
            # Check step sizes
            max_step = max(step_norms)
            min_step = min(step_norms)
            if max_step > 100:
                print(f"   ⚠️  LARGE STEPS: Max step norm = {max_step:.2e}")
                print(f"       → Consider: More conservative step size control")
            
            # Check line search behavior
            min_lambda = min(lambda_factors)
            if min_lambda < 0.01:
                print(f"   ⚠️  FREQUENT LINE SEARCH: Min λ = {min_lambda:.3f}")
                print(f"       → Consider: Better initial guess or different algorithm")
            
            # Show iteration progression
            print(f"\n   📈 ITERATION PROGRESSION:")
            for i, iter_data in enumerate(history[-5:], start=max(1, len(history)-4)):
                print(f"     Iter {i:2d}: residual={iter_data.residual_norm:.2e}, "
                      f"step={iter_data.step_norm:.2e}, "
                      f"cond={iter_data.condition_number:.1e}, "
                      f"λ={iter_data.lambda_factor:.3f}")
        
        # Suggest improved approach
        print(f"\n   💡 SUGGESTED FIXES:")
        print(f"     1. Try better initial guess closer to solution")
        print(f"     2. Increase max_iter or relax tolerance")
        print(f"     3. Use different solver algorithm")
        print(f"     4. Add regularization or scaling")
        
        # Try with improved settings
        print(f"\n   🔄 TRYING IMPROVED SETTINGS:")
        
        # Better guess and more iterations
        better_guess = {'x': np.array([0.8]), 'y': np.array([0.8])}
        better_options = SolverOptions(
            display=False, 
            store_history=True, 
            max_iter=30, 
            tol_fun=1e-6,
            tol_x=1e-6
        )
        
        solution2, report2 = solver.solve(better_guess, options=better_options)
        
        if report2['exit_flag'] == 1:
            print(f"   ✅ SUCCESS with improved settings!")
            print(f"     Solution: x={solution2['x'][0]:.6f}, y={solution2['y'][0]:.6f}")
            
            analysis2 = solver.analyze_convergence()
            print(f"     Iterations: {analysis2['total_iterations']}")
            print(f"     Convergence: {analysis2['convergence_type']}")
        else:
            print(f"   ❌ Still failed - may need more advanced techniques")
    else:
        print(f"   ✅ Solver succeeded!")
        analyzer = IterationAnalyzer(solver)
        analyzer.print_detailed_analysis()


def main():
    """Run all iteration tracking examples."""
    
    print("🚀 TEXTTOSOLVER ITERATION TRACKING SHOWCASE")
    print("This demonstration shows how to use iteration data for:")
    print("  • Monitoring solver convergence behavior")
    print("  • Debugging convergence failures") 
    print("  • Optimizing solver performance")
    print("  • Understanding numerical characteristics")
    
    print(f"\n💡 BASIC USAGE:")
    print("""
    from text_to_solver.TextToSolver import TextToSolver, SolverOptions
    
    # Create solver with iteration tracking enabled
    solver = TextToSolver(['x', 'y'], ['x**2 + y**2 - 4', 'x - y - 1'])
    options = SolverOptions(store_history=True)  # Enable tracking
    
    # Solve and get iteration history
    solution, report = solver.solve(guess, options=options)
    
    # Access detailed iteration data
    history = solver.get_iteration_history()      # Complete iteration data
    residuals = solver.get_residual_history()     # Just residual norms
    analysis = solver.analyze_convergence()       # Automatic analysis
    
    # Each iteration contains: residual_norm, step_norm, condition_number,
    # lambda_factor, solution_vector, residual_vector, timing, etc.
    """)
    
    try:
        # Run examples
        solver1, solution1, report1 = example_1_basic_nonlinear_system()
        
        results2 = example_2_challenging_system_comparison()
        
        performance_results = example_3_performance_monitoring()
        
        example_4_debugging_failed_convergence()
        
        print("\n" + "="*70)
        print("🎯 SUMMARY AND BEST PRACTICES")
        print("="*70)
        
        print("✅ KEY FEATURES DEMONSTRATED:")
        print("   • Complete iteration history capture")
        print("   • Automatic convergence rate classification") 
        print("   • Performance timing and efficiency analysis")
        print("   • Condition number and numerical health monitoring")
        print("   • Line search behavior tracking")
        print("   • Systematic debugging of convergence failures")
        
        print("\n💡 BEST PRACTICES FOR ITERATION TRACKING:")
        print("   1. Always enable store_history for debugging new problems")
        print("   2. Use analyze_convergence() for automatic performance insights")
        print("   3. Monitor condition numbers for numerical stability")
        print("   4. Compare different initial guesses systematically")
        print("   5. Use iteration data to optimize solver parameters")
        print("   6. Check residual progression patterns for convergence issues")
        
        print("\n🎉 Iteration tracking showcase completed successfully!")
        
    except ImportError:
        print("❌ Error: TextToSolver not available. Please install the package.")
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        raise


if __name__ == "__main__":
    main()
