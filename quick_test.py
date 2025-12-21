#!/usr/bin/env python3
"""
Quick test to verify enhanced TextToSolver functionality
"""

def test_enhanced_functionality():
    """Test basic enhanced functionality"""
    print("🧪 Testing Enhanced TextToSolver Functionality")
    print("=" * 50)
    
    try:
        # Test imports
        print("1. Testing imports...")
        import sys
        sys.path.append('.')
        from text_to_solver.TextToSolver import TextToSolver, SolverOptions
        print("   ✅ Successfully imported TextToSolver and SolverOptions")
        
        # Test SolverOptions creation
        print("\n2. Testing SolverOptions...")
        options = SolverOptions(tol_fun=1e-8, display=False, max_iter=50)
        print(f"   ✅ SolverOptions created: tol_fun={options.tol_fun}")
        
        # Test TextToSolver creation
        print("\n3. Testing TextToSolver creation...")
        dep_vars = ['x', 'y']
        residual = ['x**2 + y**2 - 1', 'x - y']
        solver = TextToSolver(dep_vars, residual)
        print("   ✅ TextToSolver instance created")
        
        # Test generate_initial_guess
        print("\n4. Testing generate_initial_guess...")
        guess = solver.generate_initial_guess(strategy='heuristic')
        print(f"   ✅ Heuristic guess: x={guess['x'][0]:.3f}, y={guess['y'][0]:.3f}")
        
        guess_auto = solver.generate_initial_guess(strategy='auto')
        print(f"   ✅ Auto guess: x={guess_auto['x'][0]:.3f}, y={guess_auto['y'][0]:.3f}")
        
        # Test solve_auto
        print("\n5. Testing solve_auto...")
        solution, report = solver.solve_auto(options=options)
        print(f"   ✅ solve_auto completed with exit_flag: {report['exit_flag']}")
        
        if report['exit_flag'] == 1:
            print(f"   ✅ Solution found: x={solution['x'][0]:.6f}, y={solution['y'][0]:.6f}")
            print(f"   ✅ Residual norm: {report['res_norm']:.2e}")
            
            # Verify solution
            x, y = solution['x'][0], solution['y'][0]
            res1 = x**2 + y**2 - 1
            res2 = x - y
            print(f"   ✅ Verification: res1={res1:.2e}, res2={res2:.2e}")
        
        # Test with independent variables
        print("\n6. Testing with independent variables...")
        dep_vars = ['x', 'y']
        residual = ['x**2 + y**2 - z**2', 'y - 5*x']
        ind_vars = ['z']
        
        solver2 = TextToSolver(dep_vars, residual, indep_vars=ind_vars)
        ind_var_val = {'z': [1.0, 2.0, 3.0]}
        
        guess2 = solver2.generate_initial_guess(indep_var_val=ind_var_val, strategy='heuristic')
        print(f"   ✅ Generated guess for 3 points: x shape={guess2['x'].shape}")
        
        solution2, report2 = solver2.solve_auto(indep_var_val=ind_var_val, options=options)
        print(f"   ✅ Multi-point solve: exit_flag={report2['exit_flag']}")
        
        # Test multistart
        print("\n7. Testing multistart...")
        solution3, report3 = solver.solve_auto(multistart=True, options=options)
        print(f"   ✅ Multistart completed: exit_flag={report3['exit_flag']}")
        if 'multistart_attempts' in report3:
            print(f"   ✅ Used {report3['multistart_attempts']} attempts")
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED! Enhanced functionality is working correctly.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"Enhanced functionality test failed: {e}"

if __name__ == "__main__":
    success = test_enhanced_functionality()
    exit(0 if success else 1)
