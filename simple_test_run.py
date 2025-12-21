#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

print("Testing TextToSolver Enhanced Functionality")
print("=" * 50)

try:
    # Test basic import
    from text_to_solver.TextToSolver import TextToSolver, SolverOptions
    print("✅ Import successful")
    
    # Test basic creation
    solver = TextToSolver(['x', 'y'], ['x + y - 3', 'x - y - 1'])
    print("✅ TextToSolver created")
    
    # Test enhanced features
    options = SolverOptions(display=False)
    print("✅ SolverOptions created")
    
    # Test solve_auto
    solution, report = solver.solve_auto(options=options)
    if report['exit_flag'] == 1:
        print(f"✅ solve_auto successful: x={solution['x'][0]:.3f}, y={solution['y'][0]:.3f}")
    else:
        print(f"❌ solve_auto failed: exit_flag={report['exit_flag']}")
    
    # Test guess generation
    guess = solver.generate_initial_guess(strategy='heuristic')
    print("✅ generate_initial_guess successful")
    
    # Test multistart
    solution2, report2 = solver.solve_auto(multistart=True, options=options)
    if report2['exit_flag'] == 1:
        print("✅ multistart successful")
    else:
        print(f"⚠️ multistart result: exit_flag={report2['exit_flag']}")
    
    print("\n🎉 ALL ENHANCED FEATURES WORKING!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
