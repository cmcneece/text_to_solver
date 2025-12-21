#!/usr/bin/env python3
"""
Simple Constraints Demo for TextToSolver

A clear, focused example showing how to use box constraints to solve
nonlinear systems with variable bounds.

QUICK START:
    python examples/simple_constraints_demo.py

This example demonstrates:
- Defining constraints during solver creation
- Automatic constraint enforcement during solving
- Adding and modifying constraints dynamically
- Checking constraint satisfaction
- Analyzing constraint behavior

Author: TextToSolver Development Team
"""

import numpy as np
import sys
import os

# Add src directory to path for imports
# Note: In production, the package should be installed with 'pip install -e .'
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src'))

from text_to_solver.TextToSolver import TextToSolver, SolverOptions


def main():
    """Demonstrate constraint capabilities with a simple, clear example."""
    
    print("🎯 TextToSolver Constraints Demo")
    print("=" * 40)
    print("Problem: Find where circle x² + y² = 25 intersects line x + y = 7")
    print("Constraint: Both x and y must be positive (x ≥ 0, y ≥ 0)")
    print()

    # ==================================================
    # 1. CREATE SOLVER WITH CONSTRAINTS
    # ==================================================
    print("1️⃣  CREATING CONSTRAINED SOLVER")
    print("   System: x² + y² = 25, x + y = 7")
    print("   Constraints: x ≥ 0, y ≥ 0")
    
    solver = TextToSolver(
        dep_vars=['x', 'y'],
        residual=['x**2 + y**2 - 25', 'x + y - 7'],
        constraints={
            'x': (0, None),    # x ≥ 0
            'y': (0, None)     # y ≥ 0
        }
    )
    
    print(f"   ✅ Solver created with constraints: {solver.get_constraints().bounds}")
    print()

    # ==================================================
    # 2. SOLVE WITH CONSTRAINTS
    # ==================================================
    print("2️⃣  SOLVING CONSTRAINED SYSTEM")
    
    # Initial guess
    guess = {'x': np.array([3.0]), 'y': np.array([4.0])}
    print(f"   Initial guess: x = {guess['x'][0]}, y = {guess['y'][0]}")
    
    # Solve with constraint tracking
    options = SolverOptions(display=False, store_history=True, tol_fun=1e-8)
    solution, report = solver.solve(guess, options=options)
    
    # Display results
    x_sol, y_sol = solution['x'][0], solution['y'][0]
    print(f"   ✅ Solution: x = {x_sol:.6f}, y = {y_sol:.6f}")
    print(f"   Exit flag: {report['exit_flag']} (1 = success)")
    
    # Verify solution satisfies equations
    circle_check = x_sol**2 + y_sol**2 - 25
    line_check = x_sol + y_sol - 7
    print(f"   Verification: circle error = {abs(circle_check):.2e}, line error = {abs(line_check):.2e}")
    print()

    # ==================================================
    # 3. CHECK CONSTRAINT SATISFACTION
    # ==================================================
    print("3️⃣  CONSTRAINT ANALYSIS")
    
    feasibility = solver.check_constraint_feasibility(solution)
    print(f"   Constraints satisfied: {feasibility['feasible']}")
    
    if feasibility['active_constraints']:
        print(f"   Active constraints: {feasibility['active_constraints']}")
    else:
        print(f"   No active constraints (interior solution)")
    
    if feasibility['violations']:
        print(f"   Violations: {feasibility['violations']}")
    else:
        print(f"   No constraint violations ✅")
    print()

    # ==================================================
    # 4. CONSTRAINT BEHAVIOR DURING SOLVING
    # ==================================================
    print("4️⃣  SOLVER BEHAVIOR WITH CONSTRAINTS")
    
    constraint_analysis = solver.analyze_constraints()
    if 'error' in constraint_analysis:
        print(f"   Constraint analysis: {constraint_analysis['error']}")
    else:
        print(f"   Total iterations: {constraint_analysis['total_iterations']}")
        print(f"   Constraint projections applied: {constraint_analysis['projections_applied']}")
        print(f"   Constraint behavior: {constraint_analysis['constraint_behavior']}")
    
    # Show iteration details
    history = solver.get_iteration_history()
    if history:
        print(f"   Iteration details:")
        for i, iter_data in enumerate(history[:3]):  # Show first 3 iterations
            x_val, y_val = iter_data.solution_vector[0], iter_data.solution_vector[1]
            proj_indicator = "📍" if iter_data.projection_applied else "  "
            print(f"     Iter {i+1}: x={x_val:.4f}, y={y_val:.4f} {proj_indicator}")
    else:
        print(f"   No iteration history available")
    print()

    # ==================================================
    # 5. DYNAMIC CONSTRAINT MANAGEMENT
    # ==================================================
    print("5️⃣  DYNAMIC CONSTRAINT MANAGEMENT")
    
    print(f"   Original constraints: {solver.get_constraints().bounds}")
    
    # Add upper bounds
    solver.add_constraint('x', upper=6.0)
    solver.add_constraint('y', upper=6.0)
    print(f"   After adding upper bounds: {solver.get_constraints().bounds}")
    
    # Solve again with tighter constraints
    solution2, report2 = solver.solve(guess, options=options)
    x_sol2, y_sol2 = solution2['x'][0], solution2['y'][0]
    print(f"   New solution with bounds: x = {x_sol2:.6f}, y = {y_sol2:.6f}")
    
    # Check if constraints affected the solution
    distance_moved = np.sqrt((x_sol2 - x_sol)**2 + (y_sol2 - y_sol)**2)
    if distance_moved > 1e-6:
        print(f"   Tighter constraints changed solution (moved {distance_moved:.6f})")
    else:
        print(f"   Tighter constraints didn't affect solution")
    print()

    # ==================================================
    # 6. COMPARISON: UNCONSTRAINED VS CONSTRAINED
    # ==================================================
    print("6️⃣  COMPARISON WITH UNCONSTRAINED SOLUTION")
    
    # Solve without constraints
    unconstrained_solver = TextToSolver(
        dep_vars=['x', 'y'],
        residual=['x**2 + y**2 - 25', 'x + y - 7']
    )
    
    solution_uncon, _ = unconstrained_solver.solve(guess, options=options)
    x_uncon, y_uncon = solution_uncon['x'][0], solution_uncon['y'][0]
    
    print(f"   Unconstrained solution: x = {x_uncon:.6f}, y = {y_uncon:.6f}")
    print(f"   Constrained solution:   x = {x_sol:.6f}, y = {y_sol:.6f}")
    
    # Check if constraints were active
    if x_uncon >= 0 and y_uncon >= 0:
        print(f"   ➡️  Unconstrained solution satisfies constraints")
        print(f"       (Constraints were not limiting)")
    else:
        print(f"   ➡️  Constraints forced a different solution")
        print(f"       (Unconstrained solution: x={x_uncon:.3f}, y={y_uncon:.3f})")
    print()

    # ==================================================
    # SUMMARY
    # ==================================================
    print("📊 SUMMARY")
    print("=" * 40)
    print("✅ Key Features Demonstrated:")
    print("   • Box constraints: lower ≤ variable ≤ upper")
    print("   • Automatic constraint enforcement during Newton solving")
    print("   • Real-time constraint projection and tracking")
    print("   • Dynamic constraint addition and modification")
    print("   • Constraint satisfaction checking and analysis")
    print("   • Comparison with unconstrained solutions")
    print()
    
    print("🔧 Constraint API Used:")
    print("   • TextToSolver(..., constraints={'x': (lower, upper)})")
    print("   • solver.add_constraint(var, lower=None, upper=None)")
    print("   • solver.check_constraint_feasibility(solution)")
    print("   • solver.analyze_constraints()")
    print("   • solver.get_constraints()")
    print()
    
    print("🎯 Results:")
    final_feasibility = solver.check_constraint_feasibility(solution2)
    if final_feasibility['feasible']:
        print("   ✅ All constraints satisfied successfully")
    else:
        print("   ⚠️  Some constraints violated")
    
    print(f"   Final solution: x = {x_sol2:.4f}, y = {y_sol2:.4f}")
    print(f"   Constraints active: {bool(final_feasibility['active_constraints'])}")
    print()
    print("🎉 Constraints demo completed successfully!")


if __name__ == "__main__":
    main()
