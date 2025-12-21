#!/usr/bin/env python3
"""
TextToSolver Constraint Capabilities Demo

A clean, working example showing how constraints improve solution finding
by enforcing physical bounds on variables.

QUICK START:
    python examples/constraint_demo_final.py

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
    print("🎯 TextToSolver Constraint Capabilities")
    print("=" * 45)
    print("Demonstration: Solving equations with variable bounds")
    print()
    
    # ==================================================
    # EXAMPLE: Engineering Design Problem
    # ==================================================
    print("🔧 ENGINEERING DESIGN PROBLEM")
    print("Design a system where:")
    print("  • Temperature T and Pressure P are related: T² + P² = 100")
    print("  • Energy balance: T + 2P = 12") 
    print("  • Physical constraints: T ≥ 2 (min temp), P ≥ 1 (min pressure)")
    print("  • Safety limits: T ≤ 8 (max temp), P ≤ 6 (max pressure)")
    print()
    
    # Create solver with engineering constraints
    solver = TextToSolver(
        dep_vars=['T', 'P'],
        residual=['T**2 + P**2 - 100', 'T + 2*P - 12'],
        constraints={
            'T': (2, 8),    # 2 ≤ T ≤ 8 (temperature bounds)
            'P': (1, 6)     # 1 ≤ P ≤ 6 (pressure bounds)
        }
    )
    
    print(f"✅ Created solver with constraints:")
    for var, bounds in solver.get_constraints().bounds.items():
        print(f"   {bounds[0]} ≤ {var} ≤ {bounds[1]}")
    print()
    
    # Solve the constrained problem
    print("🚀 Solving constrained system:")
    guess = {'T': np.array([6.0]), 'P': np.array([3.0])}
    print(f"   Initial guess: T = {guess['T'][0]}, P = {guess['P'][0]}")
    
    options = SolverOptions(display=False, store_history=True, tol_fun=1e-8)
    solution, report = solver.solve(guess, options=options)
    
    T_sol, P_sol = solution['T'][0], solution['P'][0]
    print(f"   ✅ Solution: T = {T_sol:.4f}, P = {P_sol:.4f}")
    print(f"   Exit status: {report['exit_flag']} (1 = success)")
    
    # Verify solution
    eq1_check = T_sol**2 + P_sol**2 - 100
    eq2_check = T_sol + 2*P_sol - 12
    print(f"   Verification: eq1 error = {abs(eq1_check):.2e}, eq2 error = {abs(eq2_check):.2e}")
    print()
    
    # ==================================================
    # CONSTRAINT ANALYSIS
    # ==================================================
    print("📊 CONSTRAINT ANALYSIS")
    
    # Check if solution satisfies all constraints
    feasibility = solver.check_constraint_feasibility(solution)
    print(f"   All constraints satisfied: {feasibility['feasible']}")
    
    if feasibility['active_constraints']:
        print(f"   Active constraints (at boundary): {feasibility['active_constraints']}")
        print(f"   → Solution is limited by these constraints")
    else:
        print(f"   No active constraints (interior solution)")
        print(f"   → Solution found within all bounds")
    
    if feasibility['violations']:
        print(f"   Constraint violations: {feasibility['violations']}")
    else:
        print(f"   ✅ No constraint violations")
    print()
    
    # ==================================================
    # COMPARISON WITH UNCONSTRAINED SOLUTION
    # ==================================================
    print("🆚 IMPACT OF CONSTRAINTS")
    
    # Solve same problem without constraints
    unconstrained_solver = TextToSolver(
        dep_vars=['T', 'P'],
        residual=['T**2 + P**2 - 100', 'T + 2*P - 12']
    )
    
    solution_uncon, _ = unconstrained_solver.solve(guess, options=options)
    T_uncon, P_uncon = solution_uncon['T'][0], solution_uncon['P'][0]
    
    print(f"   Unconstrained solution: T = {T_uncon:.4f}, P = {P_uncon:.4f}")
    print(f"   Constrained solution:   T = {T_sol:.4f}, P = {P_sol:.4f}")
    
    # Calculate impact
    distance = np.sqrt((T_sol - T_uncon)**2 + (P_sol - P_uncon)**2)
    print(f"   Distance between solutions: {distance:.4f}")
    
    # Check if unconstrained solution violates bounds
    T_violation = max(0, 2 - T_uncon) + max(0, T_uncon - 8)
    P_violation = max(0, 1 - P_uncon) + max(0, P_uncon - 6)
    
    if T_violation > 0 or P_violation > 0:
        print(f"   ❌ Unconstrained solution violates bounds:")
        if T_violation > 0:
            print(f"      Temperature violation: {T_violation:.4f}")
        if P_violation > 0:
            print(f"      Pressure violation: {P_violation:.4f}")
        print(f"   ✅ Constraints provided feasible alternative!")
    else:
        print(f"   ✅ Unconstrained solution also satisfies bounds")
        print(f"   → Constraints didn't need to intervene")
    print()
    
    # ==================================================
    # DYNAMIC CONSTRAINT MANAGEMENT
    # ==================================================
    print("🔧 DYNAMIC CONSTRAINT MANAGEMENT")
    
    print(f"   Original bounds: T ∈ [2, 8], P ∈ [1, 6]")
    
    # Tighten temperature constraint
    solver.add_constraint('T', lower=3, upper=7)
    print(f"   Tightening temperature: T ∈ [3, 7]")
    
    solution2, _ = solver.solve(guess, options=options)
    T_sol2, P_sol2 = solution2['T'][0], solution2['P'][0]
    print(f"   New solution: T = {T_sol2:.4f}, P = {P_sol2:.4f}")
    
    distance2 = np.sqrt((T_sol2 - T_sol)**2 + (P_sol2 - P_sol)**2)
    if distance2 > 1e-3:
        print(f"   ✅ Tighter constraints changed solution (moved {distance2:.4f})")
    else:
        print(f"   Tighter constraints didn't affect solution")
    
    # Remove pressure constraints
    solver.remove_constraint('P')
    print(f"   Removing pressure constraints")
    
    solution3, _ = solver.solve(guess, options=options)
    T_sol3, P_sol3 = solution3['T'][0], solution3['P'][0]
    print(f"   Final solution: T = {T_sol3:.4f}, P = {P_sol3:.4f}")
    print()
    
    # ==================================================
    # CONSTRAINT API SUMMARY
    # ==================================================
    print("🚀 CONSTRAINT API SUMMARY")
    print("=" * 45)
    print("✅ Creating constraints:")
    print("   solver = TextToSolver(vars, eqs, constraints={'x': (lower, upper)})")
    print()
    print("✅ Managing constraints:")
    print("   solver.add_constraint('x', lower=0, upper=10)")
    print("   solver.add_constraints({'x': (0, 10), 'y': (-1, 5)})")
    print("   solver.remove_constraint('x')")
    print("   solver.clear_constraints()")
    print()
    print("✅ Analyzing constraints:")
    print("   solver.check_constraint_feasibility(solution)")
    print("   solver.analyze_constraints()")
    print("   solver.has_constraints()")
    print()
    print("✅ Key benefits:")
    print("   • Automatic enforcement during Newton iterations")
    print("   • Real-time constraint violation detection")
    print("   • Active constraint identification")
    print("   • Seamless integration with existing solve workflow")
    print()
    print("🎉 Constraint capabilities enable robust solving of")
    print("    engineering, economic, and scientific problems")
    print("    with physical bounds and design limitations!")


if __name__ == "__main__":
    main()
