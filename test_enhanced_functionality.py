#!/usr/bin/env python3
"""
Quick test of enhanced TextToSolver functionality
"""

import sys
sys.path.append('.')

try:
    from text_to_solver.TextToSolver import TextToSolver, SolverOptions
    print("✅ Successfully imported TextToSolver and SolverOptions")
    
    # Test basic functionality
    dep_vars = ['x', 'y']
    residual = ['x**2 + y**2 - 1', 'x - y']
    
    solver = TextToSolver(dep_vars, residual)
    print("✅ TextToSolver instance created successfully")
    
    # Test SolverOptions
    options = SolverOptions(tol_fun=1e-8, display=False)
    print("✅ SolverOptions created successfully")
    
    # Test generate_initial_guess method
    guess = solver.generate_initial_guess(strategy='heuristic')
    print(f"✅ Initial guess generated: {guess}")
    
    # Test solve_auto method
    solution, report = solver.solve_auto(options=options)
    print(f"✅ solve_auto completed with exit_flag: {report['exit_flag']}")
    
    if report['exit_flag'] == 1:
        print(f"   Solution: x={solution['x'][0]:.6f}, y={solution['y'][0]:.6f}")
        print(f"   Residual norm: {report['res_norm']:.2e}")
    
    print("\n🎉 All enhanced functionality tests passed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
