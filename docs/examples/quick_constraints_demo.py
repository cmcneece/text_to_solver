#!/usr/bin/env python3
"""
Quick Constraints Demo - 30 Second Introduction

A minimal example showing the essential constraint features.

QUICK START:
    python examples/quick_constraints_demo.py

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
    print("🚀 Quick Constraints Demo (30 seconds)")
    print("=" * 40)
    
    # Problem: Find intersection of x² + y² = 9 and x + y = 5
    # With constraints: 1 ≤ x ≤ 4, 1 ≤ y ≤ 4
    
    print("Problem: x² + y² = 9, x + y = 5")
    print("Constraints: 1 ≤ x ≤ 4, 1 ≤ y ≤ 4")
    
    # Create constrained solver
    solver = TextToSolver(
        ['x', 'y'], 
        ['x**2 + y**2 - 9', 'x + y - 5'],
        constraints={'x': (1, 4), 'y': (1, 4)}
    )
    
    # Solve
    guess = {'x': np.array([0.5]), 'y': np.array([0.5])}  # Start outside bounds
    print(f"Starting guess: x={guess['x'][0]}, y={guess['y'][0]} (violates constraints)")
    
    options = SolverOptions(display=False, store_history=True)
    solution, report = solver.solve(guess, options=options)
    
    x, y = solution['x'][0], solution['y'][0]
    print(f"✅ Solution: x={x:.4f}, y={y:.4f}")
    
    # Check constraints
    feasibility = solver.check_constraint_feasibility(solution)
    print(f"Constraints satisfied: {feasibility['feasible']}")
    if feasibility['active_constraints']:
        print(f"Active constraints: {feasibility['active_constraints']}")
    
    # Show constraint impact
    solver_uncon = TextToSolver(['x', 'y'], ['x**2 + y**2 - 9', 'x + y - 5'])
    sol_uncon, _ = solver_uncon.solve({'x': np.array([2.5]), 'y': np.array([2.5])}, options)
    x_uncon, y_uncon = sol_uncon['x'][0], sol_uncon['y'][0]
    
    distance = np.sqrt((x - x_uncon)**2 + (y - y_uncon)**2)
    print(f"\nUnconstrained solution: x={x_uncon:.4f}, y={y_uncon:.4f}")
    print(f"Constrained solution:   x={x:.4f}, y={y:.4f}")
    print(f"Distance moved by constraints: {distance:.4f}")
    
    if distance > 0.001:
        print("✅ Constraints actively changed the solution!")
    else:
        print("Constraints didn't affect this solution.")
    
    print("\n🎯 Key API:")
    print("• TextToSolver(..., constraints={'var': (lower, upper)})")
    print("• solver.add_constraint(var, lower=None, upper=None)")  
    print("• solver.check_constraint_feasibility(solution)")
    print("\n🎉 Constraints work automatically during solving!")


if __name__ == "__main__":
    main()
