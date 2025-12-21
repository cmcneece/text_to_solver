#!/usr/bin/env python3
"""
Chemical Equilibrium Performance Benchmark
Specialized for carbonate/chemical systems like your notebook
"""

import time
import numpy as np
from text_to_solver.TextToSolver import TextToSolver, SolverOptions

def benchmark_carbonate_system():
    """Benchmark performance on carbonate speciation system."""
    print("=" * 60)
    print("CARBONATE SYSTEM PERFORMANCE BENCHMARK")
    print("=" * 60)
    
    # Simplified carbonate system (similar to your notebook)
    dep_vars = ['pHCO3', 'pCO3', 'pH2CO3']
    residual = [
        '-pK1 + pHCO3 + pH - pH2CO3',      # First dissociation
        '-pK2 + pCO3 + pH - pHCO3',        # Second dissociation  
        'log10(10**pCO2T) - log10(10**pH2CO3 + 10**pHCO3 + 10**pCO3)'  # Mass balance
    ]
    
    parameters = {
        'pK1': 6.35,
        'pK2': 10.33,
        'pH': 7.0,
        'pCO2T': -3.0
    }
    
    print("\n1. Carbonate System Performance")
    print("-" * 32)
    
    # Test different solver approaches
    approaches = [
        ('Standard', {'multistart': False, 'guess_strategy': 'heuristic'}),
        ('Auto', {'multistart': False, 'guess_strategy': 'auto'}), 
        ('Scaled', {'multistart': False, 'guess_strategy': 'scaled'}),
        ('Multistart', {'multistart': True, 'guess_strategy': 'auto'}),
    ]
    
    for approach_name, kwargs in approaches:
        try:
            start = time.time()
            solver = TextToSolver(dep_vars, residual, parameters=parameters)
            init_time = time.time() - start
            
            start = time.time()
            solution, report = solver.solve_auto(
                options=SolverOptions(display=False, tol_fun=1e-8),
                **kwargs
            )
            solve_time = time.time() - start
            
            success = "✅" if report['exit_flag'] == 1 else "❌"
            total_time = init_time + solve_time
            
            print(f"  {approach_name:12}: {total_time:.4f}s, {report['iter_count']:2d} iter {success}")
            
            if report['exit_flag'] == 1:
                # Check mass balance
                total_carbon = 10**(solution['pH2CO3'][0]) + 10**(solution['pHCO3'][0]) + 10**(solution['pCO3'][0])
                expected = 10**(-3.0)
                error = abs(total_carbon - expected) / expected
                print(f"                 Mass balance error: {error:.2e}")
                
        except Exception as e:
            print(f"  {approach_name:12}: Failed - {str(e)[:30]}...")

def benchmark_ph_sweep():
    """Benchmark pH sweep performance."""
    print("\n2. pH Sweep Performance (Carbonate)")
    print("-" * 37)
    
    dep_vars = ['pHCO3', 'pCO3', 'pH2CO3']
    residual = [
        '-6.35 + pHCO3 + pH - pH2CO3',
        '-10.33 + pCO3 + pH - pHCO3', 
        'log10(0.001) - log10(10**pH2CO3 + 10**pHCO3 + 10**pCO3)'
    ]
    
    # Method 1: Recreate solver each time
    pH_values = np.linspace(6.0, 8.0, 20)
    
    start = time.time()
    results_slow = []
    for pH in pH_values:
        try:
            # Replace pH in equations (inefficient)
            pH_residual = [eq.replace('pH', str(pH)) for eq in residual]
            solver = TextToSolver(dep_vars, pH_residual)
            solution, report = solver.solve_auto(
                options=SolverOptions(display=False),
                guess_strategy='scaled'
            )
            if report['exit_flag'] == 1:
                results_slow.append(solution)
        except Exception:
            pass
    slow_time = time.time() - start
    
    # Method 2: Reuse solver with parameters
    start = time.time() 
    solver = TextToSolver(dep_vars, [
        '-6.35 + pHCO3 + pH_val - pH2CO3',
        '-10.33 + pCO3 + pH_val - pHCO3',
        'log10(0.001) - log10(10**pH2CO3 + 10**pHCO3 + 10**pCO3)'
    ])
    
    results_fast = []
    for pH in pH_values:
        try:
            solver.parameters = {'pH_val': pH}
            solver.generate_symbolic()
            solver.functionalize()
            solution, report = solver.solve_auto(
                options=SolverOptions(display=False),
                guess_strategy='scaled'
            )
            if report['exit_flag'] == 1:
                results_fast.append(solution)
        except Exception:
            pass
    fast_time = time.time() - start
    
    speedup = slow_time / fast_time if fast_time > 0 else float('inf')
    
    print(f"  Recreate each:   {slow_time:.4f}s ({len(results_slow)} successful)")
    print(f"  Reuse solver:    {fast_time:.4f}s ({len(results_fast)} successful)")  
    print(f"  Speedup:         {speedup:.1f}x")

def benchmark_tolerance_chemical():
    """Test tolerance effects on chemical systems."""
    print("\n3. Chemical System Tolerance Effects")
    print("-" * 36)
    
    # Chemical system with tight constraints
    dep_vars = ['pH', 'pOH']
    residual = ['-14.0 + pH + pOH', 'pH - 7.0']  # Pure water at 25°C
    
    solver = TextToSolver(dep_vars, residual)
    
    tolerances = [
        ('Chemical Standard', 1e-8,  1e-10),
        ('High Precision',    1e-12, 1e-14),
        ('Ultra Precision',   1e-16, 1e-18)
    ]
    
    for name, tol_fun, tol_x in tolerances:
        start = time.time()
        try:
            solution, report = solver.solve_auto(
                options=SolverOptions(tol_fun=tol_fun, tol_x=tol_x, display=False),
                guess_strategy='heuristic'
            )
            elapsed = time.time() - start
            
            success = "✅" if report['exit_flag'] == 1 else "❌"
            iters = report['iter_count']
            
            print(f"  {name:16}: {elapsed:.4f}s, {iters:2d} iter {success}")
            
            if report['exit_flag'] == 1:
                # Check water equilibrium
                pH_val = solution['pH'][0]
                pOH_val = solution['pOH'][0] 
                Kw_check = 10**(-pH_val) * 10**(-pOH_val)
                print(f"                     Kw = {Kw_check:.2e} (should be 1e-14)")
                
        except Exception as e:
            print(f"  {name:16}: Failed - {str(e)[:25]}...")

def benchmark_system_complexity():
    """Compare simple vs complex chemical systems."""
    print("\n4. Chemical System Complexity Scaling")
    print("-" * 38)
    
    systems = [
        ("Simple (H2O)", 
         ['pH', 'pOH'], 
         ['-14 + pH + pOH']),
        
        ("CO2 (2-species)",
         ['pH2CO3', 'pHCO3'],
         ['-6.35 + pHCO3 + 7.0 - pH2CO3']),
        
        ("CO2 (3-species)", 
         ['pH2CO3', 'pHCO3', 'pCO3'],
         ['-6.35 + pHCO3 + 7.0 - pH2CO3',
          '-10.33 + pCO3 + 7.0 - pHCO3']),
        
        ("Full Carbonate",
         ['pH2CO3', 'pHCO3', 'pCO3', 'pH', 'pOH'], 
         ['-6.35 + pHCO3 + pH - pH2CO3',
          '-10.33 + pCO3 + pH - pHCO3', 
          '-14 + pH + pOH',
          'log10(0.001) - log10(10**pH2CO3 + 10**pHCO3 + 10**pCO3)'])
    ]
    
    for name, vars, eqs in systems:
        try:
            start = time.time()
            solver = TextToSolver(vars, eqs)
            solution, report = solver.solve_auto(
                options=SolverOptions(display=False, tol_fun=1e-8),
                guess_strategy='auto'
            )
            elapsed = time.time() - start
            
            success = "✅" if report['exit_flag'] == 1 else "❌"
            n_vars = len(vars)
            
            print(f"  {name:16} ({n_vars}×{len(eqs)}): {elapsed:.4f}s {success}")
            
        except Exception as e:
            print(f"  {name:16}: Failed - {str(e)[:25]}...")

def main():
    """Run chemical system benchmarks."""
    try:
        benchmark_carbonate_system()
        benchmark_ph_sweep()
        benchmark_tolerance_chemical() 
        benchmark_system_complexity()
        
        print("\n" + "=" * 60)
        print("CHEMICAL BENCHMARK COMPLETE")
        print("=" * 60)
        print("\n💡 Chemical System Optimization Tips:")
        print("   • Use 'scaled' or 'auto' guess strategies for log-space variables")
        print("   • Reuse solver objects for pH/parameter sweeps (big speedup!)")
        print("   • Chemical tolerances: tol_fun=1e-8 is usually sufficient")
        print("   • For mass balance checks, expect some numerical error in log-space")
        print("   • Multistart helps with multiple equilibria but adds overhead")
        
    except Exception as e:
        print(f"\n❌ Chemical benchmark failed: {e}")

if __name__ == "__main__":
    main()
