#!/usr/bin/env python3
"""
Test the new function compilation caching feature
"""

import time
import numpy as np
from text_to_solver.TextToSolver import TextToSolver, SolverOptions

def test_caching_basic():
    """Test basic caching functionality."""
    print("=" * 50)
    print("FUNCTION COMPILATION CACHING TEST")
    print("=" * 50)
    
    # Test system
    vars = ['x', 'y']
    eqs = ['x**2 + y**2 - 4', 'x + y - 2']
    
    print("\n1. Basic Caching Functionality")
    print("-" * 32)
    
    solver = TextToSolver(vars, eqs)
    
    # Check initial cache stats
    stats = solver.get_cache_stats()
    print(f"  Initial cache size: {stats['cache_size']}")
    print(f"  Cache enabled: {stats['cache_enabled']}")
    
    # Test solve
    solution, report = solver.solve_auto(options=SolverOptions(display=False))
    print(f"  Solve successful: {report['exit_flag'] == 1}")
    
    # Check cache after solving
    stats_after = solver.get_cache_stats()
    print(f"  Cache size after solve: {stats_after['cache_size']}")

def test_caching_performance():
    """Test performance improvement from caching."""
    print("\n2. Performance Comparison")
    print("-" * 27)
    
    vars = ['x', 'y', 'z']
    eqs = ['x**3 + y*sin(z) - 2', 'exp(x) + log(y) - z**2', 'x*y*z - 1']
    
    # Test with caching enabled (default)
    print("  Testing with caching ENABLED:")
    
    times_cached = []
    for i in range(10):
        start = time.time()
        solver_cached = TextToSolver(vars, eqs)
        solver_cached.solve_auto(options=SolverOptions(display=False))
        elapsed = time.time() - start
        times_cached.append(elapsed)
    
    avg_cached = np.mean(times_cached)
    cache_stats = solver_cached.get_cache_stats()
    print(f"    Average time: {avg_cached:.4f}s")
    print(f"    Cache size: {cache_stats['cache_size']}")
    
    # Test with caching disabled
    print("  Testing with caching DISABLED:")
    
    times_uncached = []
    for i in range(10):
        start = time.time()
        solver_uncached = TextToSolver(vars, eqs)
        solver_uncached.set_cache_enabled(False)
        solver_uncached.functionalize()  # Re-functionalize without cache
        solver_uncached.solve_auto(options=SolverOptions(display=False))
        elapsed = time.time() - start
        times_uncached.append(elapsed)
    
    avg_uncached = np.mean(times_uncached)
    print(f"    Average time: {avg_uncached:.4f}s")
    
    # Calculate speedup
    speedup = avg_uncached / avg_cached if avg_cached > 0 else 1.0
    print(f"  Performance improvement: {speedup:.2f}x")

def test_parameter_sweep_caching():
    """Test caching benefits during parameter sweeps."""
    print("\n3. Parameter Sweep Caching Benefits")
    print("-" * 36)
    
    vars = ['pH', 'pOH']
    eqs = ['-Kw + pH + pOH', 'pH - pH_target']
    
    pH_values = np.linspace(6.0, 8.0, 20)
    
    # Method 1: With caching (reuse solver)
    start = time.time()
    solver = TextToSolver(vars, eqs)
    cache_stats_start = solver.get_cache_stats()
    
    results_cached = []
    for pH in pH_values:
        solver.parameters = {'Kw': 14.0, 'pH_target': pH}
        solver.generate_symbolic()
        solver.functionalize()  # Benefits from caching
        solution, report = solver.solve_auto(options=SolverOptions(display=False))
        if report['exit_flag'] == 1:
            results_cached.append(solution)
    
    cached_time = time.time() - start
    cache_stats_end = solver.get_cache_stats()
    
    # Method 2: Without caching (fresh solver each time)
    start = time.time()
    results_uncached = []
    for pH in pH_values:
        solver_fresh = TextToSolver(vars, eqs, parameters={'Kw': 14.0, 'pH_target': pH})
        solver_fresh.set_cache_enabled(False)
        solver_fresh.functionalize()  # No caching benefit
        solution, report = solver_fresh.solve_auto(options=SolverOptions(display=False))
        if report['exit_flag'] == 1:
            results_uncached.append(solution)
    
    uncached_time = time.time() - start
    
    print(f"  Cached method:   {cached_time:.4f}s ({len(results_cached)} successful)")
    print(f"  Uncached method: {uncached_time:.4f}s ({len(results_uncached)} successful)")
    
    speedup = uncached_time / cached_time if cached_time > 0 else 1.0
    print(f"  Caching speedup: {speedup:.2f}x")
    
    print(f"  Cache growth: {cache_stats_start['cache_size']} → {cache_stats_end['cache_size']} functions")

def test_cache_management():
    """Test cache management features."""
    print("\n4. Cache Management")
    print("-" * 21)
    
    vars = ['x', 'y']
    eqs = ['x**2 + y**2 - r', 'x + y - s']
    
    solver = TextToSolver(vars, eqs, parameters={'r': 4, 's': 2})
    
    # Initial state
    stats = solver.get_cache_stats()
    print(f"  Initial cache size: {stats['cache_size']}")
    
    # Add more functions to cache
    for i in range(5):
        solver.parameters = {'r': i+1, 's': i+2}
        solver.generate_symbolic()
        solver.functionalize()
    
    stats_after = solver.get_cache_stats()
    print(f"  Cache size after multiple functionalizations: {stats_after['cache_size']}")
    
    # Clear cache
    solver.clear_function_cache()
    stats_cleared = solver.get_cache_stats()
    print(f"  Cache size after clearing: {stats_cleared['cache_size']}")
    
    # Test disabling cache
    solver.set_cache_enabled(False)
    stats_disabled = solver.get_cache_stats()
    print(f"  Cache enabled after disabling: {stats_disabled['cache_enabled']}")

def test_chemical_system_caching():
    """Test caching on chemical equilibrium systems."""
    print("\n5. Chemical System Caching")
    print("-" * 28)
    
    # Chemical equilibrium system
    vars = ['pA', 'pHA']
    eqs = ['-pKa + pA + pH - pHA', 'pA + pHA - pTotal']
    
    # Parameter sweep
    pKa_values = np.linspace(4.0, 8.0, 15)
    
    start = time.time()
    solver = TextToSolver(vars, eqs)
    
    successful_solves = 0
    for pKa in pKa_values:
        solver.parameters = {'pKa': pKa, 'pH': 7.0, 'pTotal': 3.0}
        solver.generate_symbolic()
        solver.functionalize()
        solution, report = solver.solve_auto(options=SolverOptions(display=False))
        if report['exit_flag'] == 1:
            successful_solves += 1
    
    elapsed = time.time() - start
    cache_stats = solver.get_cache_stats()
    
    print(f"  Chemical sweep: {elapsed:.4f}s ({successful_solves}/{len(pKa_values)} successful)")
    print(f"  Functions cached: {cache_stats['cache_size']}")
    print(f"  Avg time per solve: {elapsed/len(pKa_values):.5f}s")

def main():
    """Run all caching tests."""
    try:
        test_caching_basic()
        test_caching_performance()
        test_parameter_sweep_caching()
        test_cache_management()
        test_chemical_system_caching()
        
        print("\n" + "=" * 50)
        print("CACHING TEST COMPLETE")
        print("=" * 50)
        print("\n✅ Benefits of Function Compilation Caching:")
        print("   • Automatic caching of expensive sp.lambdify() operations")
        print("   • Significant speedup for parameter sweeps and repeated solving")
        print("   • Transparent operation - no user code changes required")
        print("   • Cache management utilities for memory control")
        print("   • Especially beneficial for complex symbolic expressions")
        
    except Exception as e:
        print(f"\n❌ Caching test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
