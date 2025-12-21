#!/usr/bin/env python3
"""
Demonstration of the new automatic function compilation caching
"""

import time
import numpy as np
from text_to_solver.TextToSolver import TextToSolver, SolverOptions

def demo_caching_benefits():
    """Demonstrate the performance benefits of function compilation caching."""
    print("🚀 TextToSolver Function Compilation Caching Demo")
    print("=" * 55)
    
    print("\nFunction compilation caching is now AUTOMATICALLY ENABLED!")
    print("This provides significant performance improvements for:")
    print("  • Parameter sweeps")
    print("  • Repeated solving with different parameters")
    print("  • Complex symbolic expressions")
    
    # Demonstration system - chemical equilibrium
    vars = ['pH', 'pOH', 'pA']
    eqs = [
        '-Kw + pH + pOH',           # Water autoionization
        '-pKa + pA + pH - 3.0',     # Acid dissociation (total = 1e-3 M)
        'pH - target_pH'            # Target pH constraint
    ]
    
    print(f"\n📚 Example System:")
    print(f"  Variables: {vars}")
    print(f"  Equations: {len(eqs)} chemical equilibrium equations")
    
    # Parameter sweep: different pH targets
    pH_targets = np.linspace(5.0, 9.0, 25)
    print(f"\n🔬 Parameter Sweep: {len(pH_targets)} different pH values")
    
    # Method 1: With automatic caching (current behavior)
    print("\n⚡ WITH AUTOMATIC CACHING:")
    
    start = time.time()
    solver = TextToSolver(vars, eqs)
    
    # Show initial cache stats
    cache_stats = solver.get_cache_stats()
    print(f"  Initial functions cached: {cache_stats['cache_size']}")
    
    results_cached = []
    for pH_target in pH_targets:
        solver.parameters = {'Kw': 14.0, 'pKa': 6.0, 'target_pH': pH_target}
        solver.generate_symbolic()
        solver.functionalize()  # Benefits from caching!
        
        solution, report = solver.solve_auto(
            options=SolverOptions(display=False, tol_fun=1e-10)
        )
        if report['exit_flag'] == 1:
            results_cached.append((pH_target, solution))
    
    cached_time = time.time() - start
    final_cache_stats = solver.get_cache_stats()
    
    print(f"  Time: {cached_time:.4f} seconds")
    print(f"  Successful solves: {len(results_cached)}/{len(pH_targets)}")
    print(f"  Functions cached: {final_cache_stats['cache_size']}")
    print(f"  Avg per solve: {cached_time/len(pH_targets):.5f}s")
    
    # Method 2: Without caching (for comparison)
    print("\n🐌 WITHOUT CACHING (for comparison):")
    
    start = time.time()
    results_uncached = []
    for pH_target in pH_targets:
        # Create fresh solver each time (no caching benefit)
        solver_fresh = TextToSolver(vars, eqs, parameters={
            'Kw': 14.0, 'pKa': 6.0, 'target_pH': pH_target
        })
        solver_fresh.set_cache_enabled(False)  # Disable caching
        solver_fresh.functionalize()  # Force recompilation
        
        solution, report = solver_fresh.solve_auto(
            options=SolverOptions(display=False, tol_fun=1e-10)
        )
        if report['exit_flag'] == 1:
            results_uncached.append((pH_target, solution))
    
    uncached_time = time.time() - start
    
    print(f"  Time: {uncached_time:.4f} seconds")
    print(f"  Successful solves: {len(results_uncached)}/{len(pH_targets)}")
    print(f"  Avg per solve: {uncached_time/len(pH_targets):.5f}s")
    
    # Show the improvement
    if cached_time > 0:
        speedup = uncached_time / cached_time
        time_saved = uncached_time - cached_time
        
        print(f"\n🎯 PERFORMANCE IMPROVEMENT:")
        print(f"  Speedup: {speedup:.2f}x faster with caching")
        print(f"  Time saved: {time_saved:.4f} seconds ({time_saved/uncached_time*100:.1f}%)")
        
        if speedup > 1.1:
            print("  ✅ Significant performance improvement!")
        else:
            print("  ℹ️  Modest improvement (benefits increase with complexity)")
    
    # Show sample results
    if results_cached:
        print(f"\n📊 Sample Results:")
        for i in [0, len(results_cached)//2, -1]:
            pH, sol = results_cached[i]
            pOH_val = sol['pOH'][0]
            print(f"  pH {pH:.1f} → pOH = {pOH_val:.3f} (Kw check: {10**(-pH) * 10**(-pOH_val):.2e})")

def demo_cache_management():
    """Show cache management features."""
    print(f"\n🔧 CACHE MANAGEMENT FEATURES:")
    print("-" * 30)
    
    solver = TextToSolver(['x', 'y'], ['x**2 + y**2 - r', 'x - y - s'])
    
    # Show cache utilities
    stats = solver.get_cache_stats()
    print(f"Cache size: {stats['cache_size']} functions")
    print(f"Cache enabled: {stats['cache_enabled']}")
    
    print("\nCache management methods:")
    print("  solver.get_cache_stats()      - Check cache status")
    print("  solver.clear_function_cache() - Clear all cached functions")
    print("  solver.set_cache_enabled(False) - Disable caching (for debugging)")
    
    # Demonstrate clearing
    solver.clear_function_cache()
    stats_after = solver.get_cache_stats()
    print(f"\nAfter clearing: {stats_after['cache_size']} functions cached")

def main():
    """Run the caching demonstration."""
    try:
        demo_caching_benefits()
        demo_cache_management()
        
        print("\n" + "=" * 55)
        print("🎉 AUTOMATIC CACHING IS NOW BUILT-IN!")
        print("=" * 55)
        print("\n✨ Key Benefits:")
        print("  • No code changes required - works automatically")
        print("  • Significant speedup for parameter sweeps")
        print("  • Especially beneficial for complex expressions")
        print("  • Transparent operation with optional control")
        
        print("\n💡 Best Practices:")
        print("  • Reuse solver objects for parameter sweeps")
        print("  • Use solver.get_cache_stats() to monitor performance")  
        print("  • Clear cache if memory usage becomes a concern")
        print("  • Disable caching only for debugging purposes")
        
        print("\n🔗 This optimization addresses Performance Strategy #1")
        print("   from the performance guide automatically!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
