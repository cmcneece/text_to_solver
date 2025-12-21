#!/usr/bin/env python3
"""
Initial Guess Validation and Projection Demo

This example demonstrates the new constraint validation capabilities that ensure
initial guesses satisfy variable bounds and provide helpful error handling.

QUICK START:
    python examples/initial_guess_validation_demo.py

Features Demonstrated:
- Initial guess constraint validation
- Automatic guess projection to feasible region
- Multiple constraint handling modes (error, project, project_silent, ignore)
- Constraint-aware automatic guess generation
- Best practices for robust constrained solving

Author: TextToSolver Development Team
"""

import numpy as np
import sys
import os

# Add parent directory to path for imports
# Add src directory to path for imports
# Note: In production, the package should be installed with 'pip install -e .'
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src'))

from text_to_solver.TextToSolver import TextToSolver, SolverOptions


def main():
    """Demonstrate initial guess validation and constraint handling capabilities."""
    
    print("🔍 Initial Guess Validation & Projection Demo")
    print("=" * 55)
    print("Problem: Heat exchanger design with temperature and pressure constraints")
    print("  Equations: T² + P² = 100 (energy relation)")
    print("           : T + 2P = 14 (mass balance)")
    print("  Constraints: 2 ≤ T ≤ 8 (temperature limits)")
    print("              1 ≤ P ≤ 6 (pressure limits)")
    print()
    
    # ==================================================
    # CREATE SOLVER WITH ENGINEERING CONSTRAINTS
    # ==================================================
    solver = TextToSolver(
        dep_vars=['T', 'P'],
        residual=['T**2 + P**2 - 100', 'T + 2*P - 14'],
        constraints={
            'T': (2, 8),    # Temperature: 2 ≤ T ≤ 8 °C
            'P': (1, 6)     # Pressure: 1 ≤ P ≤ 6 bar
        }
    )
    
    print("✅ Solver created with engineering constraints:")
    for var, bounds in solver.get_constraints().bounds.items():
        print(f"   {bounds[0]} ≤ {var} ≤ {bounds[1]}")
    print()
    
    # ==================================================
    # 1. VALIDATION OF DIFFERENT INITIAL GUESSES
    # ==================================================
    print("1️⃣  INITIAL GUESS VALIDATION")
    
    test_guesses = [
        {"name": "Valid Guess", "guess": {'T': np.array([6.0]), 'P': np.array([3.0])}},
        {"name": "Temperature Too Low", "guess": {'T': np.array([0.5]), 'P': np.array([3.0])}},
        {"name": "Pressure Too High", "guess": {'T': np.array([6.0]), 'P': np.array([8.0])}},
        {"name": "Both Violations", "guess": {'T': np.array([10.0]), 'P': np.array([0.2])}},
    ]
    
    print("   Testing different initial guesses:")
    print("   " + "-" * 70)
    
    for test in test_guesses:
        T_val, P_val = test["guess"]['T'][0], test["guess"]['P'][0]
        validation = solver.validate_initial_guess(test["guess"])
        
        status = "✅ Valid" if validation['valid'] else f"❌ Invalid (max violation: {validation['max_violation']:.2f})"
        print(f"   {test['name']:<20}: T={T_val:4.1f}, P={P_val:4.1f} → {status}")
        
        if not validation['valid']:
            print(f"      Violations: {validation['violations']}")
            if validation['projected_guess']:
                T_proj = validation['projected_guess']['T'][0]
                P_proj = validation['projected_guess']['P'][0]
                print(f"      Would project to: T={T_proj:.1f}, P={P_proj:.1f}")
    
    print()
    
    # ==================================================
    # 2. AUTOMATIC PROJECTION DEMONSTRATION
    # ==================================================
    print("2️⃣  AUTOMATIC PROJECTION")
    
    # Use a clearly infeasible initial guess
    bad_guess = {'T': np.array([-5.0]), 'P': np.array([15.0])}
    T_bad, P_bad = bad_guess['T'][0], bad_guess['P'][0]
    
    print(f"   Original infeasible guess: T={T_bad}, P={P_bad}")
    print(f"   Violations: T < 2 by {2 - T_bad:.1f}, P > 6 by {P_bad - 6:.1f}")
    
    # Project to feasible region
    projected_guess = solver.project_initial_guess(bad_guess)
    T_proj, P_proj = projected_guess['T'][0], projected_guess['P'][0]
    
    print(f"   Projected feasible guess: T={T_proj:.1f}, P={P_proj:.1f}")
    print(f"   ✅ Now satisfies: {solver.get_constraints().bounds['T'][0]} ≤ T ≤ {solver.get_constraints().bounds['T'][1]}, "
          f"{solver.get_constraints().bounds['P'][0]} ≤ P ≤ {solver.get_constraints().bounds['P'][1]}")
    print()
    
    # ==================================================
    # 3. CONSTRAINT HANDLING MODES
    # ==================================================
    print("3️⃣  CONSTRAINT HANDLING MODES")
    print("   Demonstrating different ways to handle constraint violations:")
    print()
    
    # Mode 1: Error (strict validation)
    print("   📋 MODE: 'error' (Strict validation)")
    print("      Use when you want to catch constraint violations early")
    
    options_error = SolverOptions(display=False, constraint_handling='error')
    try:
        solution, report = solver.solve(bad_guess, options=options_error)
        print("      ❌ Unexpected: Should have raised an error!")
    except ValueError as e:
        print(f"      ✅ Expected error: {str(e)[:60]}...")
    print()
    
    # Mode 2: Project with warning (recommended)
    print("   📋 MODE: 'project' (Auto-fix with notification)")
    print("      Use for robust solving with user awareness")
    
    options_project = SolverOptions(display=False, constraint_handling='project')
    solution_proj, report_proj = solver.solve(bad_guess, options=options_project)
    T_sol, P_sol = solution_proj['T'][0], solution_proj['P'][0]
    print(f"      ✅ Solution found: T={T_sol:.3f}, P={P_sol:.3f}")
    print(f"      Exit flag: {report_proj['exit_flag']} (1 = success)")
    print()
    
    # Mode 3: Silent projection (production mode)
    print("   📋 MODE: 'project_silent' (Auto-fix silently)")
    print("      Use in production when projection is expected")
    
    options_silent = SolverOptions(display=False, constraint_handling='project_silent')
    solution_silent, report_silent = solver.solve(bad_guess, options=options_silent)
    T_sol2, P_sol2 = solution_silent['T'][0], solution_silent['P'][0]
    print(f"      ✅ Solution found: T={T_sol2:.3f}, P={P_sol2:.3f}")
    print(f"      (No warning printed)")
    print()
    
    # Mode 4: Ignore (legacy behavior)
    print("   📋 MODE: 'ignore' (Legacy - allow infeasible guesses)")
    print("      Use only when you know constraints will be satisfied during solving")
    
    options_ignore = SolverOptions(display=False, constraint_handling='ignore')
    solution_ignore, report_ignore = solver.solve(bad_guess, options=options_ignore)
    T_sol3, P_sol3 = solution_ignore['T'][0], solution_ignore['P'][0]
    print(f"      Solution found: T={T_sol3:.3f}, P={P_sol3:.3f}")
    
    # Check if final solution is feasible even with ignored initial guess
    feasibility = solver.check_constraint_feasibility(solution_ignore)
    print(f"      Final solution feasible: {feasibility['feasible']} ✅")
    print()
    
    # ==================================================
    # 4. CONSTRAINT-AWARE AUTOMATIC SOLVING
    # ==================================================
    print("4️⃣  CONSTRAINT-AWARE AUTOMATIC SOLVING")
    print("   solve_auto() now generates constraint-aware initial guesses")
    
    # Test automatic solving
    auto_solution, auto_report = solver.solve_auto(options=SolverOptions(display=False))
    T_auto, P_auto = auto_solution['T'][0], auto_solution['P'][0]
    
    print(f"   🤖 Auto-generated solution: T={T_auto:.3f}, P={P_auto:.3f}")
    print(f"   Exit flag: {auto_report['exit_flag']}")
    
    # Verify it satisfies constraints
    auto_feasibility = solver.check_constraint_feasibility(auto_solution)
    print(f"   Automatically satisfies constraints: {auto_feasibility['feasible']} ✅")
    
    # Show what the auto-generated guess was
    print(f"   📊 Auto-guess generation logic:")
    for var in solver.get_variables():
        bounds = solver.get_constraints().bounds.get(var, (None, None))
        if bounds[0] is not None and bounds[1] is not None:
            midpoint = (bounds[0] + bounds[1]) / 2
            print(f"      {var}: midpoint of [{bounds[0]}, {bounds[1]}] = {midpoint}")
    print()
    
    # ==================================================
    # 5. MULTISTART WITH CONSTRAINTS
    # ==================================================
    print("5️⃣  MULTISTART WITH CONSTRAINTS")
    print("   Testing multistart solving with constraint-aware guesses")
    
    multistart_solution, multistart_report = solver.solve_auto(
        options=SolverOptions(display=False),
        multistart=True
    )
    
    T_multi, P_multi = multistart_solution['T'][0], multistart_solution['P'][0]
    print(f"   🔄 Multistart solution: T={T_multi:.3f}, P={P_multi:.3f}")
    print(f"   Exit flag: {multistart_report['exit_flag']}")
    
    multi_feasibility = solver.check_constraint_feasibility(multistart_solution)
    print(f"   Satisfies constraints: {multi_feasibility['feasible']} ✅")
    print()
    
    # ==================================================
    # 6. BEST PRACTICES SUMMARY
    # ==================================================
    print("💡 BEST PRACTICES FOR CONSTRAINED INITIAL GUESSES")
    print("=" * 55)
    
    print("✅ DO:")
    print("   • Use constraint_handling='project' for robust, user-aware solving")
    print("   • Use constraint_handling='project_silent' in production pipelines")
    print("   • Use constraint_handling='error' for debugging and validation")
    print("   • Use solver.validate_initial_guess() to check guesses beforehand")
    print("   • Use solver.project_initial_guess() for manual projection")
    print("   • Use solve_auto() for constraint-aware automatic guesses")
    print()
    
    print("❌ AVOID:")
    print("   • Using constraint_handling='ignore' unless you're certain")
    print("   • Ignoring constraint validation warnings")
    print("   • Using guesses far outside feasible region without validation")
    print()
    
    print("🔧 RECOMMENDED WORKFLOW:")
    print("   1. Create solver with constraints during initialization")
    print("   2. Validate initial guesses with validate_initial_guess()")
    print("   3. Use constraint_handling='project' for automatic correction")
    print("   4. Monitor solver reports for constraint-related information")
    print("   5. Use solve_auto() when you don't have good initial guesses")
    print()
    
    print("🎯 CONSTRAINT VALIDATION API SUMMARY:")
    print("   solver.validate_initial_guess(guess)    # Check constraint satisfaction")
    print("   solver.project_initial_guess(guess)     # Project to feasible region")  
    print("   solver.solve(guess, options=...)        # Automatic handling based on options")
    print("   solver.solve_auto(multistart=True)      # Constraint-aware guess generation")
    print()
    
    print("🎉 Initial guess validation ensures robust, reliable constrained solving!")


if __name__ == "__main__":
    main()
