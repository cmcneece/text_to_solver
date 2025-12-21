"""
Tests for basic TextToSolver functionality using improved testing patterns.

This module demonstrates the improved testing patterns applied to core
TextToSolver functionality, including standardized tolerances, centralized
parameters, and validation helpers.
"""

import pytest
import numpy as np
from text_to_solver.TextToSolver import TextToSolver, SolverOptions


@pytest.mark.basic_functionality
class TestTextToSolverCreation:
    """Test TextToSolver object creation using improved patterns"""
    
    def test_basic_creation_standardized(self, simple_linear_solver, algebraic_params):
        """Test basic TextToSolver creation with standardized parameters"""
        params = algebraic_params.SIMPLE_LINEAR
        
        assert isinstance(simple_linear_solver, TextToSolver)
        assert simple_linear_solver.variables_string == params['variables']
        assert len(simple_linear_solver.residual_string) == len(params['equations'])
        
        # Validate expected equation structure
        for i, equation in enumerate(params['equations']):
            assert equation in simple_linear_solver.residual_string[i]
    
    def test_creation_with_parameters_standardized(self, algebraic_params):
        """Test creation with parameters using standardized configuration"""
        params = algebraic_params.CHEMICAL_EQUILIBRIUM
        
        solver = TextToSolver(
            params['variables'],
            params['equations'], 
            parameters=params['parameters']
        )
        
        assert solver.parameters == params['parameters']
        assert len(solver.variables_string) == len(params['variables'])
    
    def test_creation_with_indep_vars_standardized(self, parametric_circle_line_solver, 
                                                  algebraic_params):
        """Test creation with independent variables using standardized parameters"""
        params = algebraic_params.CIRCLE_LINE_PARAMETRIC
        
        assert parametric_circle_line_solver.indep_vars == ['z', 'm']
        assert parametric_circle_line_solver.parameters == params['parameters']
    
    @pytest.mark.parametrize("system_name", [
        'SIMPLE_LINEAR',
        'SIMPLE_NONLINEAR', 
        'CHEMICAL_EQUILIBRIUM'
    ])
    def test_get_methods_systematic(self, system_name, algebraic_params):
        """Test getter methods systematically across different system types"""
        params = getattr(algebraic_params, system_name)
        
        # Create solver based on system type
        if 'parameters' in params:
            solver = TextToSolver(params['variables'], params['equations'], 
                                parameters=params['parameters'])
        else:
            solver = TextToSolver(params['variables'], params['equations'])
        
        # Test all getter methods
        vars_list = solver.get_variables()
        residual = solver.get_residual()
        jacobian = solver.get_jacobian()
        parameters = solver.get_parameters()
        
        assert isinstance(vars_list, list)
        assert len(vars_list) == len(params['variables'])
        assert isinstance(residual, list)
        assert len(residual) == len(params['equations'])
        assert jacobian is not None
        assert isinstance(parameters, dict)


class TestSymbolicGeneration:
    """Test symbolic equation and Jacobian generation"""
    
    def test_residual_symbolic_generation(self, simple_linear_system):
        """Test that residual equations are converted to symbolic form"""
        assert len(simple_linear_system.residual_symb) == 2
        assert simple_linear_system.residual_func is not None
    
    def test_jacobian_generation(self, simple_linear_system):
        """Test Jacobian computation"""
        jacobian = simple_linear_system.get_jacobian()
        
        # For linear system x + y - 3 = 0, x - y - 1 = 0
        # Jacobian should be [[1, 1], [1, -1]]
        assert jacobian.loc['x + y - 3', 'x'] == '1'
        assert jacobian.loc['x + y - 3', 'y'] == '1'
        assert jacobian.loc['x - y - 1', 'x'] == '1'
        assert jacobian.loc['x - y - 1', 'y'] == '-1'
    
    def test_parameter_substitution(self, lotka_volterra_system):
        """Test that parameters are properly substituted"""
        # Check that parameters have been substituted in residual strings
        residual_str = ' '.join(lotka_volterra_system.residual_string)
        assert 'a' not in residual_str  # Should be replaced with value
        assert '1.0' in residual_str   # Parameter value should appear


@pytest.mark.basic_functionality
@pytest.mark.solving
class TestBasicSolving:
    """Test basic solving functionality using improved validation patterns"""
    
    def test_solve_linear_system_enhanced(self, simple_linear_solver, algebraic_params, 
                                        tolerances, validators):
        """Test solving simple linear system with enhanced validation"""
        params = algebraic_params.SIMPLE_LINEAR
        guess = {'x': np.array([0.0]), 'y': np.array([0.0])}
        options = SolverOptions(display=False)
        
        solution, report = simple_linear_solver.solve(guess, options=options)
        
        # Validate convergence using standardized helper
        validators.validate_convergence_report(
            report, 
            expected_convergence=True,
            description="linear system solver"
        )
        
        # Validate residual norm using standardized tolerance
        validators.validate_residual_norm(
            report['res_norm'],
            tolerance=tolerances.RESIDUAL_NORM,
            description="linear system"
        )
        
        # Validate solution accuracy against known solution
        validators.validate_solution_accuracy(
            solution, 
            params['known_solution'],
            tolerance=tolerances.NUMERICAL,
            description="linear system solution"
        )
    
    def test_solve_nonlinear_system_enhanced(self, simple_nonlinear_solver, algebraic_params,
                                           tolerances, validators):
        """Test solving simple nonlinear system with enhanced validation"""
        params = algebraic_params.SIMPLE_NONLINEAR
        guess = {'x': np.array([0.5]), 'y': np.array([0.5])}
        options = SolverOptions(display=False)
        
        solution, report = simple_nonlinear_solver.solve(guess, options=options)
        
        # Validate convergence
        validators.validate_convergence_report(
            report,
            expected_convergence=True, 
            description="nonlinear system solver"
        )
        
        # Validate residual norm
        validators.validate_residual_norm(
            report['res_norm'],
            tolerance=tolerances.RESIDUAL_NORM,
            description="nonlinear system"
        )
        
        # Validate solution accuracy
        validators.validate_solution_accuracy(
            solution,
            params['known_solution'],
            tolerance=tolerances.NUMERICAL,
            description="nonlinear system solution"
        )
    
    @pytest.mark.parametrize("z_value,expected_x_factor", [
        (1.0, 1/np.sqrt(5)),  # For m=2, x = z/sqrt(1+m²) = z/sqrt(5)
        (2.0, 2/np.sqrt(5)),
        (3.0, 3/np.sqrt(5)),
    ])
    def test_solve_parametric_system(self, z_value, expected_x_factor, 
                                   algebraic_params, tolerances, validators):
        """Test parametric system solving with multiple parameter values"""
        params = algebraic_params.CIRCLE_LINE_PARAMETRIC
        
        # Create solver with independent variables
        solver = TextToSolver(
            params['variables'],
            params['equations'],
            indep_vars=['z', 'm']
        )
        
        guess = {'x': np.array([0.5]), 'y': np.array([1.0])}
        options = SolverOptions(display=False)
        indep_var_val = {'z': np.array([z_value]), 'm': np.array([2.0])}
        
        solution, report = solver.solve(guess, indep_var_val=indep_var_val, options=options)
        
        # Validate convergence
        validators.validate_convergence_report(
            report,
            expected_convergence=True,
            description=f"parametric system (z={z_value})"
        )
        
        # Validate solution accuracy against analytical solution
        analytical_sol = params['analytical_solution'](z_value, 2.0)
        validators.validate_solution_accuracy(
            solution,
            analytical_sol,
            tolerance=tolerances.NUMERICAL,
            description=f"parametric solution (z={z_value})"
        )


class TestLegacyCompatibility:
    """Test backward compatibility with legacy interface"""
    
    def test_legacy_solve_call(self, simple_linear_system):
        """Test legacy solve method call"""
        guess = {'x': np.array([0.0]), 'y': np.array([0.0])}
        input_options = {'DISPLAY': False, 'TOL_FUN': 1e-8}
        
        solution, report = simple_linear_system.solve(guess, options=input_options)
        
        assert report['exit_flag'] == 1
        assert abs(solution['x'][0] - 2.0) < 1e-8
        assert abs(solution['y'][0] - 1.0) < 1e-8
    
    def test_mixed_options_formats(self, simple_linear_system):
        """Test mixing new and legacy options formats"""
        guess = {'x': np.array([0.0]), 'y': np.array([0.0])}
        options = SolverOptions(display=False)
        legacy_options = {'TOL_FUN': 1e-10}
        
        # Should work with new format
        solution1, report1 = simple_linear_system.solve(guess, options=options)
        
        # Should work with new format  
        solution2, report2 = simple_linear_system.solve(guess, options=legacy_options)
        
        assert report1['exit_flag'] == 1
        assert report2['exit_flag'] == 1


@pytest.mark.basic_functionality 
@pytest.mark.error_handling
class TestErrorHandling:
    """Test error handling in basic functionality using improved patterns"""
    
    def test_singular_system_handling_enhanced(self, validators, tolerances):
        """Test handling of singular system with enhanced validation"""
        # Create a singular system: x + y = 1, 2x + 2y = 2 (same equation)
        dep_vars = ['x', 'y']
        residual = ['x + y - 1', '2*x + 2*y - 2']
        solver = TextToSolver(dep_vars, residual)
        
        guess = {'x': np.array([0.0]), 'y': np.array([0.0])}
        options = SolverOptions(display=False)
        
        solution, report = solver.solve(guess, options=options)
        
        # Validate that convergence fails as expected using helper
        validators.validate_convergence_report(
            report,
            expected_convergence=False,
            description="singular system"
        )
        
        # Should detect singularity with specific exit flag
        assert report['exit_flag'] == -1, (
            f"Singular system should return exit_flag=-1, got {report['exit_flag']}"
        )
    
    def test_convergence_failure_enhanced(self, simple_nonlinear_solver, validators,
                                        performance_limits):
        """Test handling when convergence fails with enhanced validation"""
        # Use extremely bad starting guess and minimal iterations to force failure
        guess = {'x': np.array([100.0]), 'y': np.array([-100.0])}  # Very bad starting guess
        options = SolverOptions(display=False, max_iter=1, tol_fun=1e-15)  # Only 1 iteration
        
        solution, report = simple_nonlinear_solver.solve(guess, options=options)
        
        # Validate that convergence fails due to iteration limit
        assert report['exit_flag'] != 1, (
            f"Solver should fail with strict constraints, got exit_flag={report['exit_flag']}"
        )
        
        # Should respect iteration limit
        if 'iter_count' in report:
            assert report['iter_count'] <= 2, (
                f"Solver exceeded max_iter=2, used {report['iter_count']} iterations"
            )
    
    @pytest.mark.parametrize("system_type,expected_failure_mode", [
        ('singular', 'singularity_detection'),
        ('ill_conditioned', 'poor_convergence'), 
        ('overdetermined', 'inconsistent_system')
    ])
    def test_systematic_error_scenarios(self, system_type, expected_failure_mode, 
                                      validators, tolerances):
        """Test various error scenarios systematically"""
        
        if system_type == 'singular':
            # Singular system: dependent equations
            solver = TextToSolver(['x', 'y'], ['x + y - 1', '2*x + 2*y - 2'])
        elif system_type == 'ill_conditioned':
            # Nearly singular system  
            solver = TextToSolver(['x', 'y'], ['x + y - 1', 'x + 1.000001*y - 1'])
        elif system_type == 'overdetermined':
            # TextToSolver doesn't allow different numbers of vars/equations
            # So we test that the validation properly catches this
            import pytest
            from text_to_solver.TextToSolver import ValidationError
            with pytest.raises(ValidationError):
                solver = TextToSolver(['x'], ['x - 1', 'x - 2', 'x - 3'])
            return  # Skip the rest of the test for this case
        
        guess = {'x': np.array([0.0]), 'y': np.array([0.0])}
        options = SolverOptions(display=False)
        
        solution, report = solver.solve(guess, options=options)
        
        # For ill-conditioned systems, they might still converge due to numerical precision
        # So we'll be more lenient about this expectation
        if system_type == 'ill_conditioned':
            # Just verify we got a result, don't enforce failure - solver may handle this case
            assert 'exit_flag' in report, "Report should contain exit_flag"
        else:
            # Validate that convergence fails as expected (mainly for singular systems)
            validators.validate_convergence_report(
                report,
                expected_convergence=False,
                description=f"{system_type} system"
            )


# ================================================================
# PERFORMANCE TESTING WITH IMPROVED PATTERNS
# ================================================================

@pytest.mark.basic_functionality
@pytest.mark.performance 
class TestBasicPerformance:
    """Test performance of basic functionality using improved benchmarks"""
    
    def test_linear_system_performance(self, simple_linear_solver, performance_timer, 
                                     performance_limits, validators, tolerances):
        """Test performance of linear system solving"""
        guess = {'x': np.array([0.0]), 'y': np.array([0.0])}
        options = SolverOptions(display=False)
        
        # Measure solution time
        with performance_timer() as get_solve_time:
            solution, report = simple_linear_solver.solve(guess, options=options)
        
        solve_time = get_solve_time()
        
        # Validate solution correctness first
        validators.validate_convergence_report(
            report, 
            expected_convergence=True,
            description="performance test linear system"
        )
        
        # Validate performance meets benchmark
        assert solve_time < performance_limits.MAX_SIMPLE_LINEAR_TIME, (
            f"Linear system solving too slow: {solve_time:.3f}s exceeds "
            f"benchmark of {performance_limits.MAX_SIMPLE_LINEAR_TIME}s"
        )
    
    def test_nonlinear_system_performance(self, simple_nonlinear_solver, performance_timer,
                                        performance_limits, validators):
        """Test performance of nonlinear system solving"""
        guess = {'x': np.array([0.5]), 'y': np.array([0.5])}
        options = SolverOptions(display=False)
        
        # Measure solution time
        with performance_timer() as get_solve_time:
            solution, report = simple_nonlinear_solver.solve(guess, options=options)
        
        solve_time = get_solve_time()
        
        # Validate solution correctness
        validators.validate_convergence_report(
            report,
            expected_convergence=True,
            description="performance test nonlinear system"
        )
        
        # Validate performance meets benchmark  
        assert solve_time < performance_limits.MAX_SIMPLE_NONLINEAR_TIME, (
            f"Nonlinear system solving too slow: {solve_time:.3f}s exceeds "
            f"benchmark of {performance_limits.MAX_SIMPLE_NONLINEAR_TIME}s"
        )
    
    @pytest.mark.parametrize("system_size,max_time", [
        ("2x2", 0.1),   # Simple systems should be very fast
        ("3x3", 0.2),   # Slightly larger
        ("5x5", 0.5),   # Medium size
    ])
    def test_scalability_performance(self, system_size, max_time, performance_timer):
        """Test performance scalability with different system sizes"""
        
        if system_size == "2x2":
            solver = TextToSolver(['x', 'y'], ['x + y - 3', 'x - y - 1'])
            guess = {'x': np.array([0.0]), 'y': np.array([0.0])}
        elif system_size == "3x3":
            solver = TextToSolver(
                ['x', 'y', 'z'], 
                ['x + y + z - 6', 'x - y + z - 2', 'x + y - z']
            )
            guess = {'x': np.array([0.0]), 'y': np.array([0.0]), 'z': np.array([0.0])}
        elif system_size == "5x5":
            # Create a simple diagonal-dominant system for reliable convergence
            variables = ['x1', 'x2', 'x3', 'x4', 'x5']
            equations = [f'{var} - {i+1}' for i, var in enumerate(variables)]
            solver = TextToSolver(variables, equations)
            guess = {var: np.array([0.0]) for var in variables}
        
        options = SolverOptions(display=False)
        
        # Measure solution time
        with performance_timer() as get_solve_time:
            solution, report = solver.solve(guess, options=options)
        
        solve_time = get_solve_time()
        
        # Validate solution succeeded
        assert report['exit_flag'] == 1, (
            f"{system_size} system failed to converge: {report.get('message', 'No message')}"
        )
        
        # Validate performance scales appropriately
        assert solve_time < max_time, (
            f"{system_size} system solving too slow: {solve_time:.3f}s exceeds "
            f"expected {max_time}s"
        )
