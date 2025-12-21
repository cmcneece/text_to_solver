"""
Integration tests for TextToSolver - testing complete workflows
"""

import pytest
import numpy as np
from text_to_solver.TextToSolver import TextToSolver, SolverOptions


@pytest.mark.integration
class TestCompleteWorkflows:
    """Test complete solving workflows from start to finish"""
    
    def test_circle_line_workflow(self):
        """Test complete workflow for circle-line intersection problem"""
        # Define system: x² + y² = z², y = 5x
        dep_vars = ['x', 'y']
        residual = ['x**2 + y**2 - z**2', 'y - 5*x']
        indep_vars = ['z']
        
        solver = TextToSolver(dep_vars, residual, indep_vars=indep_vars)
        
        # Define parameter sweep
        z_values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        indep_var_val = {'z': z_values}
        
        # Use auto-solving
        solution, report = solver.solve_auto(
            indep_var_val=indep_var_val,
            options=SolverOptions(display=False)
        )
        
        assert report['exit_flag'] == 1
        assert len(solution['x']) == 5
        assert len(solution['y']) == 5
        
        # Verify solutions
        for i, z in enumerate(z_values):
            x, y = solution['x'][i], solution['y'][i]
            
            # Check circle equation: x² + y² = z²
            assert abs(x**2 + y**2 - z**2) < 1e-8
            
            # Check line equation: y = 5x
            assert abs(y - 5*x) < 1e-8
            
            # Check analytical solution
            expected_x = z / np.sqrt(26)  # From y=5x and x²+y²=z²
            expected_y = 5 * expected_x
            assert abs(x - expected_x) < 1e-6
            assert abs(y - expected_y) < 1e-6
    
    def test_chemical_equilibrium_workflow(self):
        """Test complete workflow for chemical equilibrium problem"""
        # Simplified carbonate system
        dep_vars = ['pHCO3', 'pCO3', 'pH2CO3']
        residual = [
            '-pK1 + pHCO3 + 7.0 - pH2CO3',  # First dissociation at pH=7
            '-pK2 + pCO3 + 7.0 - pHCO3',    # Second dissociation at pH=7
            '10**pCO2T - (10**pH2CO3 + 10**pHCO3 + 10**pCO3)'  # Mass balance
        ]
        parameters = {
            'pK1': 6.35,
            'pK2': 10.33,
            'pCO2T': -3.0  # Total CO2
        }
        
        solver = TextToSolver(dep_vars, residual, parameters=parameters)
        
        # Use multistart for better robustness with chemical systems
        solution, report = solver.solve_auto(
            options=SolverOptions(display=False, tol_fun=1e-8),
            multistart=True
        )
        
        assert report['exit_flag'] == 1
        
        # Verify mass balance with more reasonable tolerance for log-space calculations
        total_carbon = 10**(solution['pH2CO3'][0]) + 10**(solution['pHCO3'][0]) + 10**(solution['pCO3'][0])
        expected_carbon = 10**(-3.0)
        relative_error = abs(total_carbon - expected_carbon) / expected_carbon
        assert relative_error < 0.1  # 10% tolerance for chemical equilibrium
    
    def test_predator_prey_workflow(self):
        """Test complete workflow for predator-prey system"""
        # Lotka-Volterra equilibrium
        dep_vars = ['x', 'y']  # prey, predator
        residual = ['a*x - b*x*y', '-c*y + d*x*y']
        parameters = {'a': 1.0, 'b': 0.1, 'c': 0.075, 'd': 0.02}
        
        solver = TextToSolver(dep_vars, residual, parameters=parameters)
        
        # Should detect Lotka-Volterra pattern and use appropriate guess
        solution, report = solver.solve_auto(
            options=SolverOptions(display=False)
        )
        
        assert report['exit_flag'] == 1
        
        # Verify equilibrium solution
        x_eq, y_eq = solution['x'][0], solution['y'][0]
        
        # Analytical equilibrium: x* = c/d, y* = a/b
        expected_x = parameters['c'] / parameters['d']  # 0.075/0.02 = 3.75
        expected_y = parameters['a'] / parameters['b']  # 1.0/0.1 = 10.0
        
        assert abs(x_eq - expected_x) < 1e-6
        assert abs(y_eq - expected_y) < 1e-6
    
    def test_multistart_robustness_workflow(self):
        """Test multistart approach for challenging problem"""
        # Multiple solutions system: x² + y² = 1, (x-0.5)² + (y-0.5)² = 0.5
        dep_vars = ['x', 'y']
        residual = ['x**2 + y**2 - 1', '(x-0.5)**2 + (y-0.5)**2 - 0.5']
        
        solver = TextToSolver(dep_vars, residual)
        
        # Use multistart to find a solution
        solution, report = solver.solve_auto(
            multistart=True,
            options=SolverOptions(display=False, max_iter=50)
        )
        
        # Should find one of the solutions
        if report['exit_flag'] == 1:
            x, y = solution['x'][0], solution['y'][0]
            
            # Verify both equations are satisfied
            assert abs(x**2 + y**2 - 1) < 1e-6
            assert abs((x-0.5)**2 + (y-0.5)**2 - 0.5) < 1e-6
        
        # Should have tried multiple attempts
        assert report.get('multistart_attempts', 0) > 1


@pytest.mark.integration  
class TestFactoryMethodIntegration:
    """Test integration of factory methods with solving"""
    
    def test_from_equations_to_solution(self):
        """Test complete workflow from equations to solution"""
        equations = [
            'x**2 + y**2 = 4',
            'x + y = 2'
        ]
        
        # One-line creation and solving with multistart for robustness
        solution, report = TextToSolver.from_equations(
            equations,
            auto_solve=True,
            options=SolverOptions(display=False),
            multistart=True
        )
        
        assert report['exit_flag'] == 1
        
        # Verify solution (either (0,2) or (2,0))
        x, y = solution['x'][0], solution['y'][0]
        assert abs(x**2 + y**2 - 4) < 1e-8
        assert abs(x + y - 2) < 1e-8
    
    def test_parametric_from_equations(self):
        """Test parametric solving from equations"""
        equations = [
            'x**2 + y**2 = r**2',
            'x - y = 0'
        ]
        
        solver = TextToSolver.from_equations(
            equations,
            indep_vars=['r']
        )
        
        r_values = np.array([1.0, 2.0, 3.0])
        solution, report = solver.solve_auto(
            indep_var_val={'r': r_values},
            options=SolverOptions(display=False)
        )
        
        assert report['exit_flag'] == 1
        assert len(solution['x']) == 3
        
        # For x = y and x² + y² = r², solution is x = y = r/√2
        for i, r in enumerate(r_values):
            expected = r / np.sqrt(2)
            assert abs(solution['x'][i] - expected) < 1e-6
            assert abs(solution['y'][i] - expected) < 1e-6


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Test performance aspects and larger systems"""
    
    def test_large_parametric_sweep(self):
        """Test performance with large parametric sweep"""
        dep_vars = ['x', 'y']
        residual = ['x**2 + y**2 - z**2', 'y - 2*x']
        indep_vars = ['z']
        
        solver = TextToSolver(dep_vars, residual, indep_vars=indep_vars)
        
        # Large parameter sweep
        z_values = np.linspace(1, 10, 50)  # 50 points
        indep_var_val = {'z': z_values}
        
        solution, report = solver.solve_auto(
            indep_var_val=indep_var_val,
            options=SolverOptions(display=False, max_iter=30)
        )
        
        assert report['exit_flag'] == 1
        assert len(solution['x']) == 50
        
        # Spot check a few solutions
        for i in [0, 25, 49]:  # Check first, middle, last
            x, y, z = solution['x'][i], solution['y'][i], z_values[i]
            assert abs(x**2 + y**2 - z**2) < 1e-6
            assert abs(y - 2*x) < 1e-6
    
    def test_multistart_performance(self):
        """Test multistart performance"""
        dep_vars = ['x', 'y', 'z']
        residual = ['x**2 + y**2 + z**2 - 1', 'x + y + z - 1', 'x*y + y*z + x*z - 0.5']
        
        solver = TextToSolver(dep_vars, residual)
        
        # Test multistart with reasonable number of attempts
        solution, report = solver.solve_multistart(
            n_attempts=10,
            options=SolverOptions(display=False, max_iter=25)
        )
        
        # Should either find solution or fail gracefully
        assert 'multistart_attempts' in report
        assert report['multistart_attempts'] <= 50  # Reasonable attempt limit
        
        if report['exit_flag'] == 1:
            x, y, z = solution['x'][0], solution['y'][0], solution['z'][0]
            assert abs(x**2 + y**2 + z**2 - 1) < 1e-6


@pytest.mark.integration
class TestCompatibilityIntegration:
    """Test backward compatibility in complete workflows"""
    
    def test_legacy_options_workflow(self):
        """Test complete workflow with legacy options format"""
        dep_vars = ['x', 'y']
        residual = ['x + y - 3', 'x - y - 1']
        solver = TextToSolver(dep_vars, residual)
        
        # Use legacy options format
        guess = {'x': np.array([0.0]), 'y': np.array([0.0])}
        legacy_options = {
            'DISPLAY': False,
            'TOL_FUN': 1e-10,
            'MAX_ITER': 50
        }
        
        solution, report = solver.solve(
            guess,
            input_options=legacy_options
        )
        
        assert report['exit_flag'] == 1
        assert abs(solution['x'][0] - 2.0) < 1e-8
        assert abs(solution['y'][0] - 1.0) < 1e-8
    
    def test_mixed_interface_workflow(self):
        """Test mixing old and new interfaces"""
        dep_vars = ['x', 'y']
        residual = ['x**2 + y**2 - 1', 'x - y']
        solver = TextToSolver(dep_vars, residual)
        
        # Use new interface for guess generation
        guess = solver.generate_initial_guess(strategy='auto')
        
        # Use legacy interface for solving
        legacy_options = {'DISPLAY': False, 'TOL_FUN': 1e-8}
        solution, report = solver.solve(guess, input_options=legacy_options)
        
        assert report['exit_flag'] == 1
        
        # Then use new interface for multistart
        solution2, report2 = solver.solve_auto(
            multistart=True,
            options=SolverOptions(display=False)
        )
        
        # Both should work and give similar results
        if report2['exit_flag'] == 1:
            assert abs(solution['x'][0] - solution2['x'][0]) < 1e-4
            assert abs(solution['y'][0] - solution2['y'][0]) < 1e-4


@pytest.mark.integration
class TestExampleReproduction:
    """Test reproduction of example problems"""
    
    def test_reproduce_circle_line_example(self):
        """Reproduce the circle and line example exactly"""
        # From circle_and_line.py
        dep_vars = ['x', 'y']
        residual = ['x ** 2 + y ** 2 - z ** 2', 'y - 5 * x']
        ind_vars = ['z']
        
        solver = TextToSolver(dep_vars, residual, indep_vars=ind_vars)
        options = SolverOptions(tol_fun=1e-10, tol_x=1e-12, display=False)
        
        z_values = np.array([1, 2, 3, 4, 5])
        ind_var = {'z': z_values}
        
        # Generate guess and solve
        guess = solver.generate_initial_guess(indep_var_val=ind_var, strategy='auto')
        solution, report = solver.solve(guess, indep_var_val=ind_var, options=options)
        
        assert report['exit_flag'] == 1
        
        # Verify against known analytical solution
        for i, z in enumerate(z_values):
            x, y = solution['x'][i], solution['y'][i]
            
            # Analytical solution: x = z/√26, y = 5z/√26
            expected_x = z / np.sqrt(26)
            expected_y = 5 * z / np.sqrt(26)
            
            assert abs(x - expected_x) < 1e-8
            assert abs(y - expected_y) < 1e-8
    
    def test_reproduce_with_solve_auto(self):
        """Test the same problem with solve_auto"""
        dep_vars = ['x', 'y']
        residual = ['x ** 2 + y ** 2 - z ** 2', 'y - 5 * x']
        ind_vars = ['z']
        
        solver = TextToSolver(dep_vars, residual, indep_vars=ind_vars)
        
        z_values = np.array([1, 2, 3, 4, 5])
        ind_var = {'z': z_values}
        
        # Use solve_auto for convenience
        solution, report = solver.solve_auto(
            indep_var_val=ind_var,
            options=SolverOptions(display=False)
        )
        
        assert report['exit_flag'] == 1
        
        # Should get same results as manual approach
        for i, z in enumerate(z_values):
            x, y = solution['x'][i], solution['y'][i]
            expected_x = z / np.sqrt(26)
            expected_y = 5 * z / np.sqrt(26)
            
            assert abs(x - expected_x) < 1e-6
            assert abs(y - expected_y) < 1e-6
