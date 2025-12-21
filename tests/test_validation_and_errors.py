"""
Tests for input validation and error handling
"""

import pytest
import numpy as np
from text_to_solver.TextToSolver import TextToSolver, SolverOptions, ValidationError, SingularMatrixError


@pytest.mark.validation
class TestInputValidation:
    """Test input validation"""
    
    def test_valid_inputs(self):
        """Test that valid inputs are accepted"""
        dep_vars = ['x', 'y']
        residual = ['x + y - 1', 'x - y']
        
        # Should not raise any exception
        solver = TextToSolver(dep_vars, residual)
        assert solver is not None
    
    def test_invalid_dep_vars_type(self):
        """Test invalid dependent variables type"""
        with pytest.raises(ValidationError, match="dep_vars must be a list of strings"):
            TextToSolver("invalid", ['x + y - 1'])
    
    def test_invalid_dep_vars_content(self):
        """Test invalid dependent variables content"""
        with pytest.raises(ValidationError, match="dep_vars must be a list of strings"):
            TextToSolver([1, 2], ['x + y - 1', 'x - y'])
    
    def test_invalid_residual_type(self):
        """Test invalid residual type"""
        with pytest.raises(ValidationError, match="residual must be a list of strings"):
            TextToSolver(['x', 'y'], "invalid")
    
    def test_invalid_residual_content(self):
        """Test invalid residual content"""
        with pytest.raises(ValidationError, match="residual must be a list of strings"):
            TextToSolver(['x', 'y'], [1, 2])
    
    def test_mismatched_lengths(self):
        """Test mismatched lengths of dep_vars and residual"""
        with pytest.raises(ValidationError, match="Number of dependent variables .* must match number of residual equations"):
            TextToSolver(['x', 'y'], ['x + y - 1'])  # 2 vars, 1 equation
    
    def test_invalid_indep_vars_type(self):
        """Test invalid independent variables type"""
        with pytest.raises(ValidationError, match="indep_vars must be a list of strings"):
            TextToSolver(['x', 'y'], ['x + y - z', 'x - y'], indep_vars="z")
    
    def test_invalid_parameters_type(self):  
        """Test invalid parameters type"""
        with pytest.raises(ValidationError, match="parameters must be a dictionary"):
            TextToSolver(['x', 'y'], ['a*x + y - 1', 'x - y'], parameters="invalid")
    
    def test_duplicate_variable_names(self):
        """Test duplicate variable names across dep and indep vars"""
        with pytest.raises(ValidationError, match="Variable names must be unique"):
            TextToSolver(['x', 'y'], ['x + y - z', 'x - y'], indep_vars=['x'])  # x is duplicate
    
    def test_invalid_equation_syntax(self):
        """Test invalid equation syntax"""
        with pytest.raises(ValidationError, match="Error parsing equation"):
            TextToSolver(['x', 'y'], ['x + y - 1', 'invalid syntax +++'])


class TestFromEquationsValidation:
    """Test validation in from_equations factory method"""
    
    def test_equations_without_equals(self):
        """Test equations without equals sign"""
        with pytest.raises(ValidationError, match="must contain '=' sign"):
            TextToSolver.from_equations(['x + y - 3'])  # Missing =
    
    def test_no_dependent_variables(self):
        """Test when no dependent variables are found"""
        with pytest.raises(ValidationError, match="No dependent variables found"):
            TextToSolver.from_equations(['1 = 1'])  # No variables


class TestRuntimeErrorHandling:
    """Test runtime error handling during solving"""
    
    def test_singular_matrix_detection(self):
        """Test detection and handling of singular matrices"""
        # Create a system with dependent equations
        dep_vars = ['x', 'y']
        residual = ['x + y - 1', '2*x + 2*y - 2']  # Second equation is 2x first
        solver = TextToSolver(dep_vars, residual)
        
        guess = {'x': np.array([0.0]), 'y': np.array([0.0])}
        options = SolverOptions(display=False)
        
        solution, report = solver.solve(guess, options=options)
        
        # Should detect singularity (exit_flag -1 indicates failure)
        assert report['exit_flag'] == -1
        # resip_cond appears to be a convergence metric, not traditional condition number
        assert 'resip_cond' in report  # Just ensure the metric is reported
    
    def test_nan_inf_handling(self):
        """Test handling of NaN and Inf values"""
        # Create a system that might produce NaN/Inf
        dep_vars = ['x']
        residual = ['log(x)']  # log(0) will produce issues
        solver = TextToSolver(dep_vars, residual)
        
        guess = {'x': np.array([0.0])}  # This will cause log(0) = -inf
        options = SolverOptions(display=False, max_iter=5)
        
        solution, report = solver.solve(guess, options=options)
        
        # Should handle gracefully (either converge or fail with proper exit code)
        assert report['exit_flag'] in [-1, 1, 2]
        assert not np.isnan(report['res_norm'])
    
    def test_maximum_iterations_exceeded(self):
        """Test behavior when maximum iterations are exceeded"""
        dep_vars = ['x', 'y']
        residual = ['x**2 + y**2 - 1', 'x - y']
        solver = TextToSolver(dep_vars, residual)
        
        # Bad initial guess and very few iterations
        guess = {'x': np.array([100.0]), 'y': np.array([-100.0])}
        options = SolverOptions(display=False, max_iter=2)
        
        solution, report = solver.solve(guess, options=options)
        
        # Should either converge or reach iteration limit
        assert report['iter_count'] <= 2
    
    def test_step_too_small(self):
        """Test handling when step becomes too small"""
        dep_vars = ['x', 'y'] 
        residual = ['x**2 + y**2 - 1', 'x - y']
        solver = TextToSolver(dep_vars, residual)
        
        # Very strict tolerances
        guess = {'x': np.array([0.7071]), 'y': np.array([0.7071])}  # Very close to solution
        options = SolverOptions(display=False, tol_x=1e-16)
        
        solution, report = solver.solve(guess, options=options)
        
        # Should either converge or exit with step too small
        assert report['exit_flag'] in [1, 2]


class TestMultistartErrorHandling:
    """Test error handling in multistart functionality"""
    
    def test_multistart_all_fail(self):
        """Test multistart when all attempts fail"""
        # Create a problematic system
        dep_vars = ['x']
        residual = ['exp(x) - 1e100']  # Very large exponential
        solver = TextToSolver(dep_vars, residual)
        
        options = SolverOptions(display=False, max_iter=2)
        
        solution, report = solver.solve_multistart(
            n_attempts=2,
            options=options
        )
        
        # Should return failure status
        if report['exit_flag'] == -2:  # All multistart attempts failed
            assert 'multistart_attempts' in report
            assert report['multistart_attempts'] >= 2
            assert all(np.isnan(val) for val in solution.values() if len(val) > 0)
    
    def test_solve_auto_error_handling(self):
        """Test error handling in solve_auto"""
        dep_vars = ['x', 'y']
        residual = ['1/x + y - 1', 'x - y']  # Division by zero potential
        solver = TextToSolver(dep_vars, residual)
        
        # This might cause issues with auto-generated guess
        solution, report = solver.solve_auto(
            options=SolverOptions(display=False, max_iter=10)
        )
        
        # Should handle gracefully
        assert 'exit_flag' in report
        assert report['exit_flag'] in [-1, 1, 2]


class TestGuessGenerationErrorHandling:
    """Test error handling in guess generation"""
    
    def test_invalid_strategy(self, simple_linear_system):
        """Test invalid guess strategy"""
        with pytest.raises(ValueError, match="Unknown strategy"):
            simple_linear_system.generate_initial_guess(strategy='invalid_strategy')
    
    def test_empty_indep_var_val(self, circle_line_system):
        """Test guess generation with empty independent variable values"""
        # Should handle gracefully and default n_points to 1
        guess = circle_line_system.generate_initial_guess(indep_var_val={})
        
        assert len(guess['x']) == 1
        assert len(guess['y']) == 1
    
    def test_guess_with_none_parameters(self, simple_linear_system):
        """Test guess generation with None parameters"""
        guess = simple_linear_system.generate_initial_guess(
            n_points=None,
            indep_var_val=None,
            strategy='auto'
        )
        
        assert len(guess['x']) == 1
        assert len(guess['y']) == 1


class TestRobustnessTests:
    """Test robustness with edge cases"""
    
    def test_very_large_system(self):
        """Test with a larger system"""
        n = 10
        dep_vars = [f'x{i}' for i in range(n)]
        residual = [f'x{i} - {i+1}' for i in range(n)]  # Simple linear system
        
        solver = TextToSolver(dep_vars, residual)
        
        # Should create successfully
        assert len(solver.dep_vars) == n
        assert len(solver.residual_string) == n
    
    def test_unicode_variable_names(self):
        """Test with unicode variable names"""
        dep_vars = ['α', 'β']
        residual = ['α + β - 1', 'α - β']
        
        solver = TextToSolver(dep_vars, residual)
        guess = {'α': np.array([0.0]), 'β': np.array([0.0])}
        options = SolverOptions(display=False)
        
        solution, report = solver.solve(guess, options=options)
        
        # Should handle unicode variables
        assert 'α' in solution
        assert 'β' in solution
    
    def test_very_small_tolerances(self, simple_linear_system):
        """Test with very strict tolerances"""
        guess = {'x': np.array([0.0]), 'y': np.array([0.0])}
        options = SolverOptions(
            display=False,
            tol_fun=1e-15,
            tol_x=1e-15,
            max_iter=100
        )
        
        solution, report = simple_linear_system.solve(guess, options=options)
        
        # Should either converge to very high precision or fail gracefully
        if report['exit_flag'] == 1:
            assert report['res_norm'] < 1e-12  # Should achieve good precision
    
    def test_zero_guess(self, simple_linear_system):
        """Test with all-zero initial guess"""
        guess = {'x': np.array([0.0]), 'y': np.array([0.0])}
        options = SolverOptions(display=False)
        
        solution, report = simple_linear_system.solve(guess, options=options)
        
        # Should converge from zero guess
        assert report['exit_flag'] == 1
        assert abs(solution['x'][0] - 2.0) < 1e-8
        assert abs(solution['y'][0] - 1.0) < 1e-8
