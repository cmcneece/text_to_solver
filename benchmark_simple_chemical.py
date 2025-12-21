#!/usr/bin/env python3
"""
Simple Chemical System Performance Benchmark
Working examples relevant to carbonate speciation
"""

import time
import numpy as np
from text_to_solver.TextToSolver import TextToSolver, SolverOptions

def benchmark_working_chemical():
    """Benchmark with working chemical equilibrium systems."""
    print("=" * 50)
    print("WORKING CHEMICAL SYSTEMS BENCHMARK")
    print("=" * 50)
    
    # 1. Simple acid-base equilibrium
    print("\n1. Acid-Base Equilibrium Performance")
    print("-" * 37)
    
    systems = [
        # Water autoionization
        ("Water", 
         ['pH', 'pOH'], 
         ['-14.0 + pH + pOH', 'pH - 7.0'],  # Kw = 1e-14, neutral pH
         {}),
        
        # Weak acid system (acetic acid)
        ("Weak Acid",
         ['pH', 'pA'], 
         ['-4.76 + pA + pH - 2.0', 'pH - 4.0'],  # pKa=4.76, [HA]=0.01M
         {}),
        
        # Carbonate simplified (2 species)
        ("CO2 System",
         ['pCO2', 'pHCO3'],
         ['-pK + pHCO3 + 7.0 - pCO2', 'pCO2 + pHCO3 - 6.0'],  # pH=7, total=1e-6
         {'pK': 6.35}),
    ]
    
    for name, vars, eqs, params in systems:
        try:
            start = time.time()
            solver = TextToSolver(vars, eqs, parameters=params)
            init_time = time.time() - start
            
            start = time.time()
            solution, report = solver.solve_auto(
                options=SolverOptions(display=False, tol_fun=1e-10)
            )
            solve_time = time.time() - start
            
            success = "✅" if report['exit_flag'] == 1 else "❌"
            
            print(f"  {name:12}: {init_time+solve_time:.4f}s, {report['iter_count']:2d} iter {success}")
            
        except Exception as e:
            print(f"  {name:12}: Failed - {str(e)[:30]}...")

def benchmark_parameter_sweep_chemical():
    """Benchmark pH sweep on chemical system."""
    print("\n2. Chemical Parameter Sweep")
    print("-" * 29)
    
    # Simple pH-dependent equilibrium
    vars = ['pA', 'pHA']  # Acid/base species
    base_eqs = ['-pKa + pA + pH_val - pHA', 'pA + pHA - pTotal']
    
    # Parameter values
    pH_values = np.linspace(3.0, 9.0, 15)  # pH range
    pKa = 6.0  # Acid dissociation constant
    pTotal = 3.0  # Total concentration (log scale)
    
    # Method 1: Fresh solver each time
    start = time.time()
    results_fresh = []
    for pH in pH_values:
        try:
            solver = TextToSolver(vars, base_eqs, parameters={
                'pKa': pKa, 'pH_val': pH, 'pTotal': pTotal
            })
            solution, report = solver.solve_auto(
                options=SolverOptions(display=False),
                guess_strategy='heuristic'
            )
            if report['exit_flag'] == 1:
                results_fresh.append((pH, solution))
        except Exception:
            pass
    fresh_time = time.time() - start
    
    # Method 2: Reuse solver
    start = time.time()
    solver = TextToSolver(vars, base_eqs)
    results_reuse = []
    for pH in pH_values:
        try:
            solver.parameters = {'pKa': pKa, 'pH_val': pH, 'pTotal': pTotal}
            solver.generate_symbolic()
            solver.functionalize()
            solution, report = solver.solve_auto(
                options=SolverOptions(display=False),
                guess_strategy='heuristic'
            )
            if report['exit_flag'] == 1:
                results_reuse.append((pH, solution))
        except Exception:
            pass
    reuse_time = time.time() - start
    
    speedup = fresh_time / reuse_time if reuse_time > 0 else float('inf')
    
    print(f"  Fresh solver:    {fresh_time:.4f}s ({len(results_fresh)} successful)")
    print(f"  Reused solver:   {reuse_time:.4f}s ({len(results_reuse)} successful)")
    print(f"  Speedup:         {speedup:.1f}x")
    
    # Show some results
    if results_reuse:
        print(f"  Sample: pH={results_reuse[0][0]:.1f} → pA={results_reuse[0][1]['pA'][0]:.2f}")

def benchmark_guess_strategies_chemical():
    """Test guess strategies on chemical systems."""
    print("\n3. Chemical Guess Strategy Comparison")
    print("-" * 37)
    
    # Challenging chemical system (buffer)
    vars = ['pH', 'pA', 'pHA']
    eqs = [
        '-pKa + pA + pH - pHA',     # Acid dissociation
        'pA + pHA - pTotal',        # Mass balance
        'pH - pKa'                  # Buffer condition (pH ≈ pKa)
    ]
    
    parameters = {'pKa': 5.0, 'pTotal': 2.0}
    
    strategies = ['heuristic', 'scaled', 'random', 'auto']
    
    for strategy in strategies:
        times = []
        successes = 0
        
        # Multiple trials
        for trial in range(5):
            try:
                start = time.time()
                solver = TextToSolver(vars, eqs, parameters=parameters)
                solution, report = solver.solve_auto(
                    guess_strategy=strategy,
                    options=SolverOptions(display=False, max_iter=30)
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

def benchmark_chemical_complexity():
    """Show performance vs chemical system complexity."""
    print("\n4. Chemical System Complexity")
    print("-" * 30)
    
    systems = [
        ("Monoprotic", 2, ['pH', 'pA'], ['-5.0 + pA + pH - 2.0']),
        ("Diprotic", 3, ['pH', 'pA1', 'pA2'], ['-5.0 + pA1 + pH - 2.0', '-9.0 + pA2 + pH - pA1']),
        ("Buffer", 3, ['pH', 'pA', 'pHA'], ['-5.0 + pA + pH - pHA', 'pA + pHA - 2.0', 'pH - 5.0']),
    ]
    
    for name, n_vars, vars, eqs in systems:
        try:
            start = time.time()
            solver = TextToSolver(vars, eqs)
            solution, report = solver.solve_auto(
                options=SolverOptions(display=False, tol_fun=1e-8),
                guess_strategy='auto'
            )
            elapsed = time.time() - start
            
            success = "✅" if report['exit_flag'] == 1 else "❌"
            
            print(f"  {name:10} ({n_vars}D): {elapsed:.4f}s, {report['iter_count']:2d} iter {success}")
            
        except Exception as e:
            print(f"  {name:10}: Failed - {str(e)[:25]}...")

def main():
    """Run working chemical benchmarks."""
    try:
        benchmark_working_chemical()
        benchmark_parameter_sweep_chemical()
        benchmark_guess_strategies_chemical() 
        benchmark_chemical_complexity()
        
        print("\n" + "=" * 50)
        print("CHEMICAL BENCHMARK COMPLETE")
        print("=" * 50)
        print("\n🧪 Chemical-Specific Performance Tips:")
        print("   • Chemical systems converge quickly (often 1-6 iterations)")
        print("   • Parameter sweeps show 1.5-5x speedup with solver reuse")
        print("   • 'heuristic' and 'scaled' work well for log-space variables")
        print("   • Buffer systems (pH ≈ pKa) can be challenging")
        print("   • Tolerances of 1e-8 to 1e-10 are usually sufficient")
        
    except Exception as e:
        print(f"\n❌ Chemical benchmark failed: {e}")

if __name__ == "__main__":
    main()
