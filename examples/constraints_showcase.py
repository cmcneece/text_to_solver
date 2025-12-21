#!/usr/bin/env python3
"""
Constraint Handling Showcase for TextToSolver

This example demonstrates the powerful constraint handling capabilities that allow
users to solve nonlinear systems with box constraints (lower and upper bounds).

QUICK START:
    python examples/constraints_showcase.py

Features Demonstrated:
- Box constraint definition and management
- Automatic constraint projection during Newton iterations  
- Constraint violation detection and reporting
- Active constraint identification
- Constraint-specific analysis and diagnostics
- Real-world applications with physical bounds

Examples Included:
1. Basic Constraint Usage - Simple circle-line intersection with bounds
2. Engineering Problem - Heat exchanger design with physical limits
3. Economics Problem - Optimization with resource constraints
4. Constraint Behavior Analysis - Understanding projection and active sets
5. Multi-constraint Management - Adding, updating, and removing constraints

Key Constraint Features:
- Lower and upper bounds for each variable: x ∈ [lower, upper]
- Automatic Newton step projection to feasible region
- Real-time constraint violation tracking
- Active constraint identification at solution
- Comprehensive constraint behavior analysis
- Seamless integration with iteration tracking

Author: TextToSolver Development Team
"""

import numpy as np
import sys
import os
from typing import Dict, List, Any
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from text_to_solver.TextToSolver import TextToSolver, SolverOptions


class ConstraintAnalyzer:
    """Helper class for analyzing and reporting constraint behavior."""
    
    def __init__(self, solver: TextToSolver):
        self.solver = solver
        
    def print_constraint_summary(self, title: str = "Constraint Analysis"):
        """Print comprehensive constraint analysis."""
        if not self.solver.has_constraints():
            print(f"\n{title}: No constraints defined")
            return
            
        constraints = self.solver.get_constraints()
        analysis = self.solver.analyze_constraints()
        
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}")
        
        # Constraint definition
        print(f"📋 CONSTRAINT DEFINITION:")
        for var, (lower, upper) in constraints.bounds.items():
            bound_str = ""
            if lower is not None and upper is not None:
                bound_str = f"{lower} ≤ {var} ≤ {upper}"
            elif lower is not None:
                bound_str = f"{var} ≥ {lower}"
            elif upper is not None:
                bound_str = f"{var} ≤ {upper}"
            print(f"   {bound_str}")
        
        if 'error' in analysis:
            print(f"   Analysis error: {analysis['error']}")
            return
            
        # Constraint behavior during solve
        print(f"\n🔍 CONSTRAINT BEHAVIOR:")
        print(f"   Total iterations: {analysis['total_iterations']}")
        print(f"   Projections applied: {analysis['projections_applied']}")
        print(f"   Projection rate: {analysis['projection_rate']*100:.1f}%")
        print(f"   Max violation during solve: {analysis['max_violation_during_solve']:.6f}")
        print(f"   Behavior classification: {analysis['constraint_behavior']}")
        
        # Active constraints
        if analysis['final_active_constraints']:
            print(f"\n⚡ ACTIVE CONSTRAINTS AT SOLUTION:")
            for var, bound_type in analysis['final_active_constraints'].items():
                bound_val = constraints.lower_bounds.get(var) if bound_type == 'lower' else constraints.upper_bounds.get(var)
                print(f"   {var} {bound_type} bound active (value = {bound_val})")
        else:
            print(f"\n⚡ ACTIVE CONSTRAINTS: None (interior solution)")
        
        # Violations
        if analysis['final_violations']:
            print(f"\n❌ CONSTRAINT VIOLATIONS:")
            for var, violation in analysis['final_violations'].items():
                print(f"   {var}: violation = {violation:.6f}")
        else:
            print(f"\n✅ All constraints satisfied")


def example_1_basic_constraint_usage():
    """Example 1: Basic constraint usage with geometric interpretation."""
    
    print("\n" + "="*70)
    print("EXAMPLE 1: BASIC CONSTRAINT USAGE")
    print("="*70)
    print("Problem: Circle-line intersection with feasibility constraints")
    print("  Equations: x² + y² = 9 (circle), 2x + y = 6 (line)")
    print("  Constraints: x ≥ 0, y ≥ 0 (first quadrant only)")
    print("  Expected: Should find intersection in first quadrant")
    
    # Create constrained solver
    solver = TextToSolver(['x', 'y'], [
        'x**2 + y**2 - 9',      # Circle: x² + y² = 9
        '2*x + y - 6'           # Line: 2x + y = 6
    ], constraints={
        'x': (0, None),         # x ≥ 0
        'y': (0, None)          # y ≥ 0
    })
    
    print(f"\nSolving constrained system:")
    
    # Start from a reasonable guess
    guess = {'x': np.array([1.5]), 'y': np.array([2.0])}
    options = SolverOptions(display=False, store_history=True, tol_fun=1e-8)
    
    solution, report = solver.solve(guess, options=options)
    
    print(f"✅ Solution found:")
    x_sol, y_sol = solution['x'][0], solution['y'][0]
    print(f"   x = {x_sol:.6f}, y = {y_sol:.6f}")
    
    # Verify solution
    circle_check = x_sol**2 + y_sol**2 - 9
    line_check = 2*x_sol + y_sol - 6
    print(f"   Equation verification:")
    print(f"     Circle: x² + y² - 9 = {circle_check:.6f}")
    print(f"     Line: 2x + y - 6 = {line_check:.6f}")
    
    # Constraint analysis
    analyzer = ConstraintAnalyzer(solver)
    analyzer.print_constraint_summary("Constraint Analysis")
    
    # Compare with unconstrained solution
    print(f"\n🆚 COMPARISON WITH UNCONSTRAINED SOLUTION:")
    solver_uncon = TextToSolver(['x', 'y'], ['x**2 + y**2 - 9', '2*x + y - 6'])
    sol_uncon, _ = solver_uncon.solve(guess, options=options)
    x_uncon, y_uncon = sol_uncon['x'][0], sol_uncon['y'][0]
    
    print(f"   Unconstrained solution: x = {x_uncon:.6f}, y = {y_uncon:.6f}")
    print(f"   Constrained solution:   x = {x_sol:.6f}, y = {y_sol:.6f}")
    
    # Check if constraints affected the solution
    if x_uncon >= 0 and y_uncon >= 0:
        print(f"   → Constraints were not active (unconstrained solution is feasible)")
    else:
        print(f"   → Constraints forced different solution")
    
    return solver, solution, report


def example_2_engineering_problem():
    """Example 2: Heat exchanger design with physical constraints."""
    
    print("\n" + "="*70)
    print("EXAMPLE 2: ENGINEERING - HEAT EXCHANGER DESIGN")  
    print("="*70)
    print("Problem: Design heat exchanger with physical limitations")
    print("  Variables: T1 (hot fluid temp), T2 (cold fluid temp)")
    print("  Equations: Heat balance and effectiveness relations")
    print("  Constraints: Physical temperature limits")
    
    # Heat exchanger equations (simplified)
    # Energy balance: m1*cp1*(T1_in - T1) = m2*cp2*(T2 - T2_in)
    # Effectiveness: (T1_in - T1) = eff * (T1_in - T2_in)
    # Assuming m1*cp1 = m2*cp2 = 1, T1_in = 100, T2_in = 20, eff = 0.8
    
    solver = TextToSolver(['T1', 'T2'], [
        '100 - T1 - 0.8*(100 - 20)',    # Energy balance simplified
        'T2 - 20 - (100 - T1)'          # Cold fluid heating
    ], constraints={
        'T1': (25, 95),     # Hot outlet: 25°C ≤ T1 ≤ 95°C
        'T2': (25, 95)      # Cold outlet: 25°C ≤ T2 ≤ 95°C  
    })
    
    print(f"\nPhysical constraints:")
    print(f"   25°C ≤ T1 ≤ 95°C (hot fluid outlet temperature)")
    print(f"   25°C ≤ T2 ≤ 95°C (cold fluid outlet temperature)")
    
    # Initial engineering guess
    guess = {'T1': np.array([60.0]), 'T2': np.array([40.0])}
    options = SolverOptions(display=False, store_history=True, max_iter=15)
    
    print(f"\nSolving heat exchanger design:")
    solution, report = solver.solve(guess, options=options)
    
    T1_sol, T2_sol = solution['T1'][0], solution['T2'][0]
    print(f"✅ Optimal design found:")
    print(f"   Hot outlet temperature (T1): {T1_sol:.2f}°C")
    print(f"   Cold outlet temperature (T2): {T2_sol:.2f}°C")
    
    # Engineering interpretation
    heat_transfer = T2_sol - 20  # Heat gained by cold fluid
    efficiency = heat_transfer / (100 - 20) * 100
    
    print(f"   Heat transfer: {heat_transfer:.2f}°C temperature rise")
    print(f"   Heat exchanger efficiency: {efficiency:.1f}%")
    
    # Constraint analysis
    analyzer = ConstraintAnalyzer(solver)
    analyzer.print_constraint_summary("Engineering Constraint Analysis")
    
    # Check if design is on constraint boundary
    feasibility = solver.check_constraint_feasibility(solution)
    if feasibility['active_constraints']:
        print(f"\n⚠️  DESIGN LIMITATION:")
        print(f"   Design is limited by active constraints")
        for var, bound in feasibility['active_constraints'].items():
            print(f"   {var} is at its {bound} limit")
    
    return solver, solution, report


def example_3_economics_problem():
    """Example 3: Resource allocation with budget constraints."""
    
    print("\n" + "="*70)
    print("EXAMPLE 3: ECONOMICS - RESOURCE ALLOCATION")
    print("="*70)
    print("Problem: Optimize production with resource constraints")
    print("  Variables: x1 (product 1 quantity), x2 (product 2 quantity)")
    print("  Equations: Profit optimization conditions")
    print("  Constraints: Resource limitations and non-negativity")
    
    # Simplified optimization problem:
    # Maximize profit: P = 3*x1 + 2*x2
    # Subject to: Labor constraint: 2*x1 + x2 ≤ 100
    #            Material constraint: x1 + 2*x2 ≤ 80
    # KKT conditions for constrained optimization
    
    solver = TextToSolver(['x1', 'x2'], [
        '2*x1 + x2 - 90',      # Near labor constraint
        'x1 + 2*x2 - 70'       # Near material constraint  
    ], constraints={
        'x1': (0, 50),         # Production limits: 0 ≤ x1 ≤ 50
        'x2': (0, 45)          # Production limits: 0 ≤ x2 ≤ 45
    })
    
    print(f"\nResource constraints:")
    print(f"   0 ≤ x1 ≤ 50 (product 1 production capacity)")
    print(f"   0 ≤ x2 ≤ 45 (product 2 production capacity)")
    
    # Business initial estimate
    guess = {'x1': np.array([25.0]), 'x2': np.array([20.0])}
    options = SolverOptions(display=False, store_history=True, max_iter=20)
    
    print(f"\nSolving resource allocation:")
    solution, report = solver.solve(guess, options=options)
    
    x1_sol, x2_sol = solution['x1'][0], solution['x2'][0]
    print(f"✅ Optimal allocation found:")
    print(f"   Product 1 quantity (x1): {x1_sol:.2f} units")
    print(f"   Product 2 quantity (x2): {x2_sol:.2f} units")
    
    # Economic interpretation
    profit = 3*x1_sol + 2*x2_sol
    labor_used = 2*x1_sol + x2_sol
    material_used = x1_sol + 2*x2_sol
    
    print(f"   Total profit: ${profit:.2f}")
    print(f"   Labor utilization: {labor_used:.1f}/100 hours")
    print(f"   Material utilization: {material_used:.1f}/80 units")
    
    # Constraint analysis
    analyzer = ConstraintAnalyzer(solver)
    analyzer.print_constraint_summary("Economic Constraint Analysis")
    
    # Business insights
    feasibility = solver.check_constraint_feasibility(solution)
    if feasibility['active_constraints']:
        print(f"\n💼 BUSINESS INSIGHTS:")
        print(f"   Production is limited by capacity constraints")
        for var, bound in feasibility['active_constraints'].items():
            product_name = "Product 1" if var == "x1" else "Product 2"
            print(f"   {product_name} is at {bound} capacity limit")
    
    return solver, solution, report


def example_4_constraint_behavior_analysis():
    """Example 4: Detailed analysis of constraint behavior during solving."""
    
    print("\n" + "="*70)
    print("EXAMPLE 4: CONSTRAINT BEHAVIOR ANALYSIS")
    print("="*70)
    print("Problem: Study how constraints affect Newton method convergence")
    
    # Create a problem where we can observe constraint effects
    solver = TextToSolver(['x', 'y'], [
        'x**2 + y**2 - 10',     # Circle
        'x + y - 3'             # Line
    ], constraints={
        'x': (0.5, 2.5),        # Tight constraints
        'y': (0.5, 2.5)
    })
    
    print(f"System: x² + y² = 10, x + y = 3")
    print(f"Constraints: 0.5 ≤ x ≤ 2.5, 0.5 ≤ y ≤ 2.5")
    
    # Test multiple starting points
    test_cases = [
        {'name': 'Interior Start', 'guess': {'x': np.array([1.5]), 'y': np.array([1.5])}},
        {'name': 'Near Boundary', 'guess': {'x': np.array([2.3]), 'y': np.array([0.7])}},
        {'name': 'Outside Region', 'guess': {'x': np.array([3.0]), 'y': np.array([3.0])}}
    ]
    
    results = []
    
    for i, case in enumerate(test_cases):
        print(f"\n{i+1}. {case['name'].upper()}: x={case['guess']['x'][0]}, y={case['guess']['y'][0]}")
        
        # Project initial guess if necessary
        x_init = solver.constraints.project_vector(['x', 'y'], 
                                                  np.array([case['guess']['x'][0], case['guess']['y'][0]]))
        
        if not np.allclose([case['guess']['x'][0], case['guess']['y'][0]], x_init):
            print(f"   Initial guess projected to: x={x_init[0]:.3f}, y={x_init[1]:.3f}")
            guess = {'x': np.array([x_init[0]]), 'y': np.array([x_init[1]])}
        else:
            guess = case['guess']
            print(f"   Initial guess is feasible")
        
        options = SolverOptions(display=False, store_history=True, max_iter=20)
        solution, report = solver.solve(guess, options=options)
        
        x_sol, y_sol = solution['x'][0], solution['y'][0]
        print(f"   Solution: x={x_sol:.4f}, y={y_sol:.4f}, exit_flag={report['exit_flag']}")
        
        # Analyze constraint behavior
        constraint_analysis = solver.analyze_constraints()
        convergence_analysis = solver.analyze_convergence()
        
        case_result = {
            'name': case['name'],
            'solution': (x_sol, y_sol),
            'projections': constraint_analysis.get('projections_applied', 0),
            'iterations': constraint_analysis.get('total_iterations', 0),
            'behavior': constraint_analysis.get('constraint_behavior', 'unknown'),
            'convergence_type': convergence_analysis.get('convergence_type', 'unknown')
        }
        results.append(case_result)
        
        print(f"   Projections: {case_result['projections']}/{case_result['iterations']}")
        print(f"   Behavior: {case_result['behavior']}")
        print(f"   Convergence: {case_result['convergence_type']}")
        
        # Show iteration-by-iteration constraint activity
        history = solver.get_iteration_history()
        if len(history) > 1:
            print(f"   Iteration details:")
            for j, iter_data in enumerate(history[:3]):  # Show first 3 iterations
                x_val, y_val = iter_data.solution_vector[0], iter_data.solution_vector[1]
                proj_symbol = "📍" if iter_data.projection_applied else "  "
                active_symbol = "⚡" if iter_data.active_constraints else "  "
                print(f"     {j+1}: x={x_val:.3f}, y={y_val:.3f} {proj_symbol} {active_symbol}")
    
    # Summary comparison
    print(f"\n📊 BEHAVIOR COMPARISON:")
    print(f"{'Case':<15} {'Solution':<15} {'Projections':<12} {'Behavior':<25} {'Convergence':<20}")
    print("-" * 85)
    
    for result in results:
        x, y = result['solution']
        solution_str = f"({x:.2f},{y:.2f})"
        proj_str = f"{result['projections']}/{result['iterations']}"
        
        print(f"{result['name']:<15} {solution_str:<15} {proj_str:<12} {result['behavior']:<25} {result['convergence_type']:<20}")
    
    return solver, results


def example_5_constraint_management():
    """Example 5: Dynamic constraint management during problem solving."""
    
    print("\n" + "="*70)
    print("EXAMPLE 5: DYNAMIC CONSTRAINT MANAGEMENT")
    print("="*70)
    print("Problem: Demonstrate constraint addition, modification, and removal")
    
    # Start with unconstrained problem
    solver = TextToSolver(['x', 'y'], [
        'x**3 - 3*x*y + y**2 - 1',
        'x**2 + y**2 - x - y - 2'
    ])
    
    print(f"Base system: Nonlinear equations with multiple solutions")
    
    guess = {'x': np.array([1.5]), 'y': np.array([1.5])}
    options = SolverOptions(display=False, store_history=True, max_iter=15)
    
    # Solve unconstrained
    print(f"\n1. UNCONSTRAINED SOLUTION:")
    solution_uncon, report_uncon = solver.solve(guess, options=options)
    x_uncon, y_uncon = solution_uncon['x'][0], solution_uncon['y'][0]
    print(f"   Solution: x = {x_uncon:.4f}, y = {y_uncon:.4f}")
    
    # Add lower bound constraints
    print(f"\n2. ADDING LOWER BOUNDS:")
    solver.add_constraint('x', lower=0.0)
    solver.add_constraint('y', lower=0.0)
    print(f"   Constraints: {solver.get_constraints().bounds}")
    
    solution_lower, report_lower = solver.solve(guess, options=options)
    x_lower, y_lower = solution_lower['x'][0], solution_lower['y'][0]
    print(f"   Solution: x = {x_lower:.4f}, y = {y_lower:.4f}")
    
    analyzer = ConstraintAnalyzer(solver)
    constraint_analysis_lower = solver.analyze_constraints()
    print(f"   Behavior: {constraint_analysis_lower['constraint_behavior']}")
    
    # Add upper bound constraints
    print(f"\n3. ADDING UPPER BOUNDS:")
    solver.add_constraint('x', upper=2.0)
    solver.add_constraint('y', upper=2.0)
    print(f"   Constraints: {solver.get_constraints().bounds}")
    
    solution_both, report_both = solver.solve(guess, options=options)
    x_both, y_both = solution_both['x'][0], solution_both['y'][0]
    print(f"   Solution: x = {x_both:.4f}, y = {y_both:.4f}")
    
    constraint_analysis_both = solver.analyze_constraints()
    print(f"   Behavior: {constraint_analysis_both['constraint_behavior']}")
    
    # Tighten constraints
    print(f"\n4. TIGHTENING CONSTRAINTS:")
    solver.add_constraint('x', lower=0.5, upper=1.5)
    solver.add_constraint('y', lower=0.5, upper=1.5)
    print(f"   Constraints: {solver.get_constraints().bounds}")
    
    solution_tight, report_tight = solver.solve(guess, options=options)
    x_tight, y_tight = solution_tight['x'][0], solution_tight['y'][0]
    print(f"   Solution: x = {x_tight:.4f}, y = {y_tight:.4f}")
    
    constraint_analysis_tight = solver.analyze_constraints()
    print(f"   Behavior: {constraint_analysis_tight['constraint_behavior']}")
    
    # Remove some constraints
    print(f"\n5. REMOVING Y CONSTRAINTS:")
    solver.remove_constraint('y')
    print(f"   Constraints: {solver.get_constraints().bounds}")
    
    solution_partial, report_partial = solver.solve(guess, options=options)
    x_partial, y_partial = solution_partial['x'][0], solution_partial['y'][0]
    print(f"   Solution: x = {x_partial:.4f}, y = {y_partial:.4f}")
    
    # Clear all constraints
    print(f"\n6. CLEARING ALL CONSTRAINTS:")
    solver.clear_constraints()
    print(f"   Constraints: {solver.get_constraints().bounds}")
    
    solution_clear, report_clear = solver.solve(guess, options=options)
    x_clear, y_clear = solution_clear['x'][0], solution_clear['y'][0]
    print(f"   Solution: x = {x_clear:.4f}, y = {y_clear:.4f}")
    
    # Summary
    print(f"\n📊 CONSTRAINT MANAGEMENT SUMMARY:")
    cases = [
        ("Unconstrained", x_uncon, y_uncon),
        ("Lower bounds", x_lower, y_lower),  
        ("Both bounds", x_both, y_both),
        ("Tight bounds", x_tight, y_tight),
        ("Partial constraints", x_partial, y_partial),
        ("No constraints", x_clear, y_clear)
    ]
    
    print(f"{'Case':<20} {'x':<10} {'y':<10} {'Distance from original':<20}")
    print("-" * 60)
    
    for case_name, x_val, y_val in cases:
        distance = np.sqrt((x_val - x_uncon)**2 + (y_val - y_uncon)**2)
        print(f"{case_name:<20} {x_val:<10.4f} {y_val:<10.4f} {distance:<20.4f}")
    
    return solver


def main():
    """Run all constraint showcases."""
    
    print("🚀 TEXTTOSOLVER CONSTRAINT HANDLING SHOWCASE")
    print("This demonstration shows how to use constraints for:")
    print("  • Enforcing physical bounds on variables")
    print("  • Handling engineering design limitations")  
    print("  • Managing economic resource constraints")
    print("  • Understanding constraint solver behavior")
    print("  • Dynamic constraint management")
    
    print(f"\n💡 BASIC CONSTRAINT USAGE:")
    print("""
    from text_to_solver.TextToSolver import TextToSolver
    
    # Create solver with constraints during construction
    solver = TextToSolver(['x', 'y'], ['x**2 + y**2 - 4', 'x - y'], 
                         constraints={'x': (0, 5), 'y': (-1, 3)})
    
    # Or add constraints after creation
    solver.add_constraint('x', lower=0, upper=5)     # 0 ≤ x ≤ 5
    solver.add_constraint('y', upper=3)              # y ≤ 3 (keep existing lower)
    
    # Solve with automatic constraint projection
    solution, report = solver.solve(guess)
    
    # Analyze constraint behavior
    constraint_analysis = solver.analyze_constraints()
    feasibility = solver.check_constraint_feasibility(solution)
    """)
    
    try:
        # Run examples
        solver1, solution1, report1 = example_1_basic_constraint_usage()
        
        solver2, solution2, report2 = example_2_engineering_problem()
        
        solver3, solution3, report3 = example_3_economics_problem()
        
        solver4, results4 = example_4_constraint_behavior_analysis()
        
        solver5 = example_5_constraint_management()
        
        print("\n" + "="*70)
        print("🎯 SUMMARY AND BEST PRACTICES")
        print("="*70)
        
        print("✅ KEY FEATURES DEMONSTRATED:")
        print("   • Box constraint definition: lower ≤ variable ≤ upper")
        print("   • Automatic Newton step projection to feasible region")
        print("   • Real-time constraint violation detection and tracking")
        print("   • Active constraint identification at solution")
        print("   • Comprehensive constraint behavior analysis")
        print("   • Dynamic constraint management (add/update/remove)")
        
        print("\n💡 BEST PRACTICES FOR CONSTRAINED SOLVING:")
        print("   1. Define constraints during solver creation when possible")
        print("   2. Use reasonable initial guesses within or near feasible region")
        print("   3. Monitor constraint analysis for solver behavior insights")
        print("   4. Check for active constraints to understand solution nature")
        print("   5. Use constraint management methods for iterative design")
        print("   6. Combine with iteration tracking for debugging")
        
        print("\n🔧 CONSTRAINT API SUMMARY:")
        print("   • solver.add_constraint(var, lower=None, upper=None)")
        print("   • solver.add_constraints({var: (lower, upper), ...})")
        print("   • solver.remove_constraint(var)")
        print("   • solver.clear_constraints()")
        print("   • solver.has_constraints()")
        print("   • solver.check_constraint_feasibility(solution)")
        print("   • solver.analyze_constraints()")
        
        print("\n🎉 Constraint handling showcase completed successfully!")
        
    except ImportError:
        print("❌ Error: TextToSolver not available. Please install the package.")
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        raise


if __name__ == "__main__":
    main()
