#!/usr/bin/env python3
"""
TextToSolver Performance Benchmark Script

Run this script to measure performance characteristics of your solver usage.
"""

import time
import numpy as np
from text_to_solver.TextToSolver import TextToSolver, SolverOptions

def benchmark_basic_operations():
    """Benchmark basic solver operations."""
    print("=" * 60)
    print("TEXTTO SOLVER PERFORMANCE BENCHMARK")
    print("=" * 60)
    
    # Test case 1: Simple linear system
    print("\n1. Linear System Performance")
    print("-" * 30)
    
    vars_linear = ['x', 'y']
    eqs_linear = ['2*x + 3*y - 7', 'x - y - 1']
    
    # Measure initialization time
    start = time.time()
    solver_linear = TextToSolver(vars_linear, eqs_linear)
    init_time = time.time() - start
    
    # Measure solve time
    start = time.time()
    solution, report = solver_linear.solve_auto(options=SolverOptions(display=False))
    solve_time = time.time() - start
    
    print(f"  Initialization: {init_time:.4f}s")
    print(f"  Solve time:     {solve_time:.4f}s")
    print(f"  Exit flag:      {report['exit_flag']}")
    print(f"  Iterations:     {report['iter_count']}")
    
    # Test case 2: Nonlinear system
    print("\n2. Nonlinear System Performance")
    print("-" * 30)
    
    vars_nonlin = ['x', 'y'] 
    eqs_nonlin = ['x**2 + y**2 - 4', 'x*y - 1']
    
    start = time.time()
    solver_nonlin = TextToSolver(vars_nonlin, eqs_nonlin)
    init_time = time.time() - start
    
    start = time.time()
    solution, report = solver_nonlin.solve_auto(options=SolverOptions(display=False))
    solve_time = time.time() - start
    
    print(f"  Initialization: {init_time:.4f}s")
    print(f"  Solve time:     {solve_time:.4f}s") 
    print(f"  Exit flag:      {report['exit_flag']}")
    print(f"  Iterations:     {report['iter_count']}")

def benchmark_guess_strategies():
    """Compare different initial guess strategies."""
    print("\n3. Initial Guess Strategy Comparison")
    print("-" * 40)
    
    # Circle-line intersection problem
    vars = ['x', 'y']
    eqs = ['x**2 + y**2 - 4', 'x + y - 2']
    solver = TextToSolver(vars, eqs)
    
    strategies = ['heuristic', 'scaled', 'random', 'auto']
    
    for strategy in strategies:
        times = []
        successes = 0
        
        # Run multiple trials
        for trial in range(5):
            start = time.time()
            try:
                solution, report = solver.solve_auto(
                    guess_strategy=strategy,
                    options=SolverOptions(display=False)
                )
                elapsed = time.time() - start
                times.append(elapsed)
                if report['exit_flag'] == 1:
                    successes += 1
            except Exception:
                times.append(float('inf'))
        
        avg_time = np.mean([t for t in times if t != float('inf')])
        success_rate = successes / 5 * 100
        
        print(f"  {strategy:10}: {avg_time:.4f}s avg, {success_rate:.0f}% success")

def benchmark_multistart():
    """Compare single-start vs multistart performance."""
    print("\n4. Multistart vs Single-start Comparison")  
    print("-" * 42)
    
    # Challenging nonlinear system
    vars = ['x', 'y', 'z']
    eqs = ['x**3 + y**2 - z', 'x*y + z**2 - 2', 'sin(x) + cos(y) - z/2']
    solver = TextToSolver(vars, eqs)
    
    # Single-start
    start = time.time()
    try:
        solution, report = solver.solve_auto(
            multistart=False,
            options=SolverOptions(display=False, max_iter=50)
        )
        single_time = time.time() - start
        single_success = report['exit_flag'] == 1
    except Exception:
        single_time = float('inf')
        single_success = False
    
    # Multistart  
    start = time.time()
    try:
        solution, report = solver.solve_auto(
            multistart=True,
            options=SolverOptions(display=False, max_iter=50)
        )
        multi_time = time.time() - start
        multi_success = report['exit_flag'] == 1
    except Exception:
        multi_time = float('inf')
        multi_success = False
    
    print(f"  Single-start: {single_time:.4f}s, Success: {single_success}")
    print(f"  Multistart:   {multi_time:.4f}s, Success: {multi_success}")
    
    if single_time != float('inf') and multi_time != float('inf'):
        speedup = single_time / multi_time
        print(f"  Speedup:      {speedup:.2f}x {'(multistart faster)' if speedup > 1 else '(single faster)'}")

def benchmark_parameter_sweep():
    """Benchmark parameter sweep efficiency."""
    print("\n5. Parameter Sweep Performance")
    print("-" * 32)
    
    vars = ['x', 'y']
    eqs = ['a*x + b*y - c', 'x**2 + y**2 - r**2']
    
    # Method 1: Recreate solver each time (inefficient)
    start = time.time()
    solutions_inefficient = []
    for i in range(10):
        params = {'a': i+1, 'b': i+2, 'c': i+3, 'r': i+4}
        solver = TextToSolver(vars, eqs, parameters=params)  # Recreate each time
        try:
            solution, _ = solver.solve_auto(options=SolverOptions(display=False))
            solutions_inefficient.append(solution)
        except Exception:
            pass
    inefficient_time = time.time() - start
    
    # Method 2: Reuse solver (efficient)
    start = time.time()
    solver = TextToSolver(vars, eqs)
    solutions_efficient = []
    for i in range(10):
        params = {'a': i+1, 'b': i+2, 'c': i+3, 'r': i+4}
        solver.parameters = params
        solver.generate_symbolic()
        solver.functionalize()
        try:
            solution, _ = solver.solve_auto(options=SolverOptions(display=False))
            solutions_efficient.append(solution)
        except Exception:
            pass
    efficient_time = time.time() - start
    
    speedup = inefficient_time / efficient_time if efficient_time > 0 else float('inf')
    
    print(f"  Recreate solver: {inefficient_time:.4f}s")
    print(f"  Reuse solver:    {efficient_time:.4f}s") 
    print(f"  Speedup:         {speedup:.1f}x")

def benchmark_system_size():
    """Test performance scaling with system size."""
    print("\n6. System Size Scaling")
    print("-" * 24)
    
    sizes = [2, 5, 10]
    
    for n in sizes:
        # Create n×n linear system 
        vars = [f'x{i}' for i in range(n)]
        eqs = []
        for i in range(n):
            # Each equation: sum of variables with coefficients = target
            eq_terms = [f'{i+j+1}*x{j}' for j in range(n)]
            eq = ' + '.join(eq_terms) + f' - {sum(range(i+1, i+n+1))}'
            eqs.append(eq)
        
        start = time.time()
        solver = TextToSolver(vars, eqs)
        solution, report = solver.solve_auto(options=SolverOptions(display=False))
        elapsed = time.time() - start
        
        print(f"  {n}×{n} system: {elapsed:.4f}s, Success: {report['exit_flag'] == 1}")

def benchmark_tolerance_effects():
    """Show how tolerances affect performance."""
    print("\n7. Tolerance vs Performance Trade-off") 
    print("-" * 38)
    
    vars = ['x', 'y']
    eqs = ['x**2 + y**2 - 4.0000001', 'x + y - 2.0000001']  # Slightly perturbed
    solver = TextToSolver(vars, eqs)
    
    tolerances = [
        ('Fast',      1e-4,  1e-6),
        ('Standard',  1e-6,  1e-8), 
        ('Precise',   1e-10, 1e-12),
        ('Very Precise', 1e-14, 1e-16)
    ]
    
    for name, tol_fun, tol_x in tolerances:
        start = time.time()
        try:
            solution, report = solver.solve_auto(
                options=SolverOptions(tol_fun=tol_fun, tol_x=tol_x, display=False)
            )
            elapsed = time.time() - start
            iterations = report['iter_count']
            success = report['exit_flag'] == 1
            
            print(f"  {name:12}: {elapsed:.4f}s, {iterations:2d} iter, Success: {success}")
        except Exception as e:
            print(f"  {name:12}: Failed ({str(e)[:20]}...)")

def main():
    """Run all benchmarks."""
    try:
        benchmark_basic_operations()
        benchmark_guess_strategies()
        benchmark_multistart()
        benchmark_parameter_sweep()
        benchmark_system_size()
        benchmark_tolerance_effects()
        
        print("\n" + "=" * 60)
        print("BENCHMARK COMPLETE")
        print("=" * 60)
        print("\n💡 Performance Tips:")
        print("   • Use appropriate tolerances for your accuracy needs")
        print("   • Reuse solver objects for parameter sweeps") 
        print("   • Try different guess strategies for convergence issues")
        print("   • Use multistart only when single-start fails")
        print("   • Profile your specific use case for targeted optimization")
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        print("Make sure TextToSolver is properly installed and working.")

if __name__ == "__main__":
    main()
