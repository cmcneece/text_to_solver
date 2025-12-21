"""
Tests for enhanced TextToSolver functionality
"""

import pytest
import numpy as np
from text_to_solver.TextToSolver import TextToSolver, SolverOptions


class TestSolverOptions:
    """Test SolverOptions dataclass"""
    
    def test_default_options(self):
        """Test default SolverOptions creation"""
        options = SolverOptions()
        
        assert options.tol_fun == 1e-6
        assert options.tol_x == 1e-8
        assert options.max_iter == 20
        assert options.display == True
        assert options.alpha == 1e-4
    
    def test_custom_options(self):
        """Test custom SolverOptions creation"""
        options = SolverOptions(
            tol_fun=1e-10,
            tol_x=1e-12,
            max_iter=100,
            display=False
        )
        
        assert options.tol_fun == 1e-10
        assert options.tol_x == 1e-12
        assert options.max_iter == 100
        assert options.display == False






@pytest.mark.enhanced
class TestSolveAuto:
    """Test solve_auto convenience method"""
    
    def test_solve_auto_basic(self, simple_linear_system, default_solver_options):
        """Test basic solve_auto functionality"""
        solution, report = simple_linear_system.solve_auto(options=default_solver_options)
        
        assert report['exit_flag'] == 1
        assert 'x' in solution
        assert 'y' in solution
        # Should find correct solution
        assert abs(solution['x'][0] - 2.0) < 1e-6
        assert abs(solution['y'][0] - 1.0) < 1e-6
    
    def test_solve_auto_with_strategy(self, simple_nonlinear_system, default_solver_options):
        """Test solve_auto with specific guess strategy"""
        solution, report = simple_nonlinear_system.solve_auto(
            options=default_solver_options,
            guess_strategy='heuristic'
        )
        
        assert report['exit_flag'] == 1
        # Verify solution
        x, y = solution['x'][0], solution['y'][0]
        assert abs(x**2 + y**2 - 1) < 1e-8
        assert abs(x - y) < 1e-8
    
    def test_solve_auto_with_indep_vars(self, circle_line_system, sample_indep_var_values, default_solver_options):
        """Test solve_auto with independent variables"""
        solution, report = circle_line_system.solve_auto(
            indep_var_val=sample_indep_var_values,
            options=default_solver_options
        )
        
        assert report['exit_flag'] == 1
        assert len(solution['x']) == 5
        
        # Verify constraint y = 5x
        for i in range(5):
            assert abs(solution['y'][i] - 5 * solution['x'][i]) < 1e-8


@pytest.mark.multistart
class TestMultistart:
    """Test multistart functionality"""
    
    def test_solve_multistart_basic(self, simple_nonlinear_system, default_solver_options):
        """Test basic multistart solving"""
        solution, report = simple_nonlinear_system.solve_multistart(
            n_attempts=3,
            options=default_solver_options
        )
        
        assert 'multistart_attempts' in report
        assert 'best_strategy' in report
        assert report['multistart_attempts'] >= 1
        
        if report['exit_flag'] == 1:
            # Verify solution if converged
            x, y = solution['x'][0], solution['y'][0]
            assert abs(x**2 + y**2 - 1) < 1e-6
            assert abs(x - y) < 1e-6
    
    def test_solve_auto_multistart(self, simple_nonlinear_system, default_solver_options):
        """Test solve_auto with multistart=True"""
        solution, report = simple_nonlinear_system.solve_auto(
            multistart=True,
            options=default_solver_options
        )
        
        assert 'multistart_attempts' in report
        if report['exit_flag'] == 1:
            x, y = solution['x'][0], solution['y'][0]
            assert abs(x**2 + y**2 - 1) < 1e-6
    
    def test_multistart_strategies(self, simple_nonlinear_system, default_solver_options):
        """Test multistart with specific strategies"""
        strategies = ['heuristic', 'scaled', 'random']
        solution, report = simple_nonlinear_system.solve_multistart(
            guess_strategies=strategies,
            n_attempts=2,
            options=default_solver_options
        )
        
        assert report['best_strategy'] in strategies + ['none']


class TestFromEquations:
    """Test from_equations factory method"""
    
    def test_from_equations_basic(self):
        """Test creating solver from equations"""
        equations = ['x + y = 3', 'x - y = 1']
        solver = TextToSolver.from_equations(equations)
        
        assert isinstance(solver, TextToSolver)
        assert set(solver.dep_vars) == {'x', 'y'}
        assert len(solver.residual_string) == 2
    
    def test_from_equations_with_parameters(self):
        """Test from_equations with parameters"""
        equations = ['a*x + y = 5', 'x - b*y = 1']
        parameters = {'a': 2.0, 'b': 0.5}
        solver = TextToSolver.from_equations(equations, parameters=parameters)
        
        assert 'x' in solver.dep_vars
        assert 'y' in solver.dep_vars
        assert solver.parameters == parameters
    
    def test_from_equations_with_indep_vars(self):
        """Test from_equations with independent variables"""
        equations = ['x**2 + y**2 = z**2', 'y = 5*x']
        indep_vars = ['z']
        solver = TextToSolver.from_equations(equations, indep_vars=indep_vars)
        
        assert solver.indep_vars == ['z']
        assert set(solver.dep_vars) == {'x', 'y'}
    
    def test_from_equations_auto_solve(self):
        """Test from_equations with auto_solve=True"""
        equations = ['x + y = 3', 'x - y = 1']
        solution, report = TextToSolver.from_equations(equations, auto_solve=True)
        
        assert isinstance(solution, dict)
        assert isinstance(report, dict)
        assert report['exit_flag'] == 1
        assert abs(solution['x'][0] - 2.0) < 1e-6
        assert abs(solution['y'][0] - 1.0) < 1e-6


class TestEnhancedSolveMethod:
    """Test enhanced solve method with new parameters"""
    
    def test_solve_with_auto_guess(self, simple_linear_system, default_solver_options):
        """Test solve method with auto_guess=True"""
        solution, report = simple_linear_system.solve(
            auto_guess=True,
            options=default_solver_options
        )
        
        assert report['exit_flag'] == 1
        assert abs(solution['x'][0] - 2.0) < 1e-6
        assert abs(solution['y'][0] - 1.0) < 1e-6
    
    def test_solve_with_multistart(self, simple_nonlinear_system, default_solver_options):
        """Test solve method with multistart=True"""
        solution, report = simple_nonlinear_system.solve(
            multistart=True,
            options=default_solver_options
        )
        
        assert 'multistart_attempts' in report
        if report['exit_flag'] == 1:
            x, y = solution['x'][0], solution['y'][0]
            assert abs(x**2 + y**2 - 1) < 1e-6
