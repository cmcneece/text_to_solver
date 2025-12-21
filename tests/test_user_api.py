#!/usr/bin/env python3
"""
Comprehensive tests for the user-friendly TextToSolver API
Tests all user-friendly API enhancements: EquationSolver, SolutionResult, etc.
"""

import pytest
import numpy as np
from numpy.testing import assert_allclose

from text_to_solver.user_api import (
    EquationSolver, SolutionResult, EquationSystem,
    EquationSystemError, SolverError
)

# Note: Chemical functionality removed - using general-purpose solver for all tests
CHEMICAL_EXTENSION_AVAILABLE = False


class TestEquationSystem:
    """Test the EquationSystem domain object."""

    def test_valid_system_creation(self):
        """Test creating a valid equation system."""
        system = EquationSystem(
            dependent_variables=['x', 'y'],
            equations=['x + y - 3', 'x - y - 1']
        )
        
        assert system.n_variables == 2
        assert system.n_equations == 2
        assert system.dependent_variables == ['x', 'y']
        assert system.equations == ['x + y - 3', 'x - y - 1']

    def test_system_with_parameters(self):
        """Test system creation with parameters."""
        system = EquationSystem(
            dependent_variables=['x', 'y'],
            equations=['x + y - total', 'x - y - diff'],
            parameters={'total': 5.0, 'diff': 1.0}
        )
        
        assert system.parameters == {'total': 5.0, 'diff': 1.0}

    def test_system_with_independent_variables(self):
        """Test system with independent variables."""
        system = EquationSystem(
            dependent_variables=['y'],
            equations=['y - a*x - b'],
            independent_variables=['x'],
            parameters={'a': 2.0, 'b': 1.0}
        )
        
        assert system.independent_variables == ['x']
        assert 'x' not in system.dependent_variables

    def test_immutable_parameter_update(self):
        """Test immutable parameter updates."""
        original = EquationSystem(
            dependent_variables=['x', 'y'],
            equations=['x + y - 3', 'x - y - 1'],
            parameters={'a': 1.0}
        )
        
        updated = original.with_parameters({'b': 2.0})
        
        # Original unchanged
        assert original.parameters == {'a': 1.0}
        # Updated has both parameters
        assert updated.parameters == {'a': 1.0, 'b': 2.0}

    def test_validation_mismatched_dimensions(self):
        """Test validation of mismatched system dimensions."""
        with pytest.raises(EquationSystemError) as exc_info:
            EquationSystem(['x'], ['eq1', 'eq2'])
        
        error_msg = str(exc_info.value)
        assert "mismatch" in error_msg.lower()
        assert "1" in error_msg  # 1 variable
        assert "2" in error_msg  # 2 equations

    def test_validation_duplicate_variables(self):
        """Test validation of duplicate variable names."""
        with pytest.raises(EquationSystemError) as exc_info:
            EquationSystem(['x', 'x'], ['eq1', 'eq2'])
        
        error_msg = str(exc_info.value)
        assert "duplicate" in error_msg.lower()

    def test_validation_invalid_variable_types(self):
        """Test validation of invalid variable types."""
        with pytest.raises(EquationSystemError) as exc_info:
            EquationSystem([1, 2], ['eq1', 'eq2'])
        
        error_msg = str(exc_info.value)
        assert "variables" in error_msg.lower()
        assert "strings" in error_msg.lower()

    def test_validation_invalid_equation_types(self):
        """Test validation of invalid equation types."""
        with pytest.raises(EquationSystemError) as exc_info:
            EquationSystem(['x', 'y'], [1, 2])
        
        error_msg = str(exc_info.value)
        assert "equations" in error_msg.lower()
        assert "strings" in error_msg.lower()


class TestSolutionResult:
    """Test the SolutionResult rich result object."""

    def create_sample_result(self):
        """Create a sample result for testing."""
        return SolutionResult(
            variables={'x': np.array([2.0]), 'y': np.array([1.0])},
            converged=True,
            iterations=5,
            residual_norm=1e-10
        )

    def test_direct_variable_access(self):
        """Test direct variable access with result['x']."""
        result = self.create_sample_result()
        
        assert result['x'] == 2.0
        assert result['y'] == 1.0

    def test_array_variable_access(self):
        """Test access to array results."""
        result = SolutionResult(
            variables={'x': np.array([1.0, 2.0, 3.0])},
            converged=True,
            iterations=3,
            residual_norm=1e-8
        )
        
        # Should return the array when multiple values
        x_values = result['x']
        assert isinstance(x_values, np.ndarray)
        assert_allclose(x_values, [1.0, 2.0, 3.0])

    def test_contains_operator(self):
        """Test 'in' operator for variable checking."""
        result = self.create_sample_result()
        
        assert 'x' in result
        assert 'y' in result
        assert 'z' not in result

    def test_success_property(self):
        """Test the success property."""
        converged_result = self.create_sample_result()
        failed_result = SolutionResult(
            variables={'x': np.array([np.nan])},
            converged=False,
            iterations=0,
            residual_norm=np.inf
        )
        
        assert converged_result.success is True
        assert failed_result.success is False

    def test_to_dict_conversion(self):
        """Test conversion to simple dictionary."""
        result = self.create_sample_result()
        result_dict = result.to_dict()
        
        expected = {'x': 2.0, 'y': 1.0}
        assert result_dict == expected

    def test_string_representation(self):
        """Test human-readable string representation."""
        result = self.create_sample_result()
        repr_str = repr(result)
        
        assert "SolutionResult" in repr_str
        assert "✅ Converged" in repr_str
        assert "5 iterations" in repr_str
        assert "x=2" in repr_str
        assert "y=1" in repr_str

    def test_failed_result_representation(self):
        """Test string representation for failed results."""
        failed_result = SolutionResult(
            variables={'x': np.array([np.nan])},
            converged=False,
            iterations=50,
            residual_norm=1e-2
        )
        
        repr_str = repr(failed_result)
        assert "❌ Failed" in repr_str

    def test_variable_not_found_error(self):
        """Test error when accessing non-existent variable."""
        result = self.create_sample_result()
        
        with pytest.raises(KeyError) as exc_info:
            _ = result['z']
        
        error_msg = str(exc_info.value)
        assert "'z'" in error_msg
        assert "Available" in error_msg


class TestEquationSolver:
    """Test the EquationSolver main interface."""

    def test_one_liner_solve(self):
        """Test one-liner equation solving."""
        result = EquationSolver.solve_equations(
            variables=['x', 'y'],
            equations=['x + y - 3', 'x - y - 1']
        )
        
        assert result.success
        assert_allclose(result['x'], 2.0, atol=1e-8)
        assert_allclose(result['y'], 1.0, atol=1e-8)

    def test_one_liner_with_parameters(self):
        """Test one-liner with parameters."""
        result = EquationSolver.solve_equations(
            variables=['x', 'y'],
            equations=['x + y - total', 'x - y - diff'],
            parameters={'total': 5.0, 'diff': 1.0}
        )
        
        assert result.success
        assert_allclose(result['x'], 3.0, atol=1e-8)
        assert_allclose(result['y'], 2.0, atol=1e-8)

    def test_one_liner_with_tolerance(self):
        """Test one-liner with custom tolerance."""
        result = EquationSolver.solve_equations(
            variables=['x'],
            equations=['x - 2'],
            tolerance=1e-12
        )
        
        assert result.success
        assert result.residual_norm < 1e-12

    def test_fluent_interface_basic(self):
        """Test basic fluent interface usage."""
        result = (EquationSolver()
                  .set_system(['x', 'y'], ['x + y - 3', 'x - y - 1'])
                  .tolerance(1e-10)
                  .solve())
        
        assert result.success
        assert_allclose(result['x'], 2.0, atol=1e-8)
        assert_allclose(result['y'], 1.0, atol=1e-8)

    def test_fluent_interface_comprehensive(self):
        """Test comprehensive fluent interface configuration."""
        result = (EquationSolver()
                  .set_system(['x', 'y'], ['x + y - 3', 'x - y - 1'])
                  .tolerance(1e-10)
                  .max_iterations(100)
                  .guess_strategy('scaled')
                  .show_progress(False)
                  .solve())
        
        assert result.success
        assert_allclose(result['x'], 2.0, atol=1e-8)
        assert_allclose(result['y'], 1.0, atol=1e-8)

    def test_parameter_management(self):
        """Test parameter updates using fluent interface."""
        solver = (EquationSolver()
                  .set_system(['x', 'y'], ['x + y - total', 'x - y - diff']))
        
        # Test first parameter set
        result1 = solver.with_parameters({'total': 3.0, 'diff': 1.0}).solve()
        assert result1.success
        assert_allclose(result1['x'], 2.0, atol=1e-8)
        assert_allclose(result1['y'], 1.0, atol=1e-8)
        
        # Test second parameter set
        result2 = solver.with_parameters({'total': 7.0, 'diff': 3.0}).solve()
        assert result2.success
        assert_allclose(result2['x'], 5.0, atol=1e-8)
        assert_allclose(result2['y'], 2.0, atol=1e-8)

    def test_parameter_sweep(self):
        """Test efficient parameter sweep functionality."""
        solver = (EquationSolver()
                  .set_system(['x', 'y'], ['x + y - total', 'x - y - 1']))
        
        # Sweep total parameter
        results = solver.parameter_sweep('total', [3.0, 5.0, 7.0])
        
        assert len(results) == 3
        assert all(r.success for r in results)
        
        # Check specific values
        assert_allclose(results[0]['x'], 2.0, atol=1e-8)  # total=3: x=2, y=1
        assert_allclose(results[1]['x'], 3.0, atol=1e-8)  # total=5: x=3, y=2
        assert_allclose(results[2]['x'], 4.0, atol=1e-8)  # total=7: x=4, y=3

    def test_custom_initial_guess(self):
        """Test solving with custom initial guess."""
        custom_guess = {'x': np.array([1.5]), 'y': np.array([1.5])}
        
        result = (EquationSolver()
                  .set_system(['x', 'y'], ['x + y - 3', 'x - y - 1'])
                  .solve(custom_guess=custom_guess))
        
        assert result.success
        assert_allclose(result['x'], 2.0, atol=1e-8)
        assert_allclose(result['y'], 1.0, atol=1e-8)

    def test_multistart_option(self):
        """Test multistart option for robustness."""
        result = EquationSolver.solve_equations(
            variables=['x', 'y'],
            equations=['x**2 + y**2 - 4', 'x + y - 2'],
            multistart=True
        )
        
        # Should find one of the intersection points
        if result.success:
            x, y = result['x'], result['y']
            # Check that it satisfies both equations
            circle_error = abs(x**2 + y**2 - 4)
            line_error = abs(x + y - 2)
            assert circle_error < 1e-6
            assert line_error < 1e-6

    def test_system_not_set_error(self):
        """Test error when trying to solve without setting system."""
        solver = EquationSolver()
        
        with pytest.raises(ValueError) as exc_info:
            solver.solve()
        
        assert "No equation system set" in str(exc_info.value)

    def test_nonlinear_system(self):
        """Test with a nonlinear system."""
        # Simple nonlinear: x^2 = 4
        result = EquationSolver.solve_equations(
            variables=['x'],
            equations=['x**2 - 4']
        )
        
        if result.success:
            # Should find x = 2 or x = -2
            assert_allclose(abs(result['x']), 2.0, atol=1e-6)


# NOTE: ChemicalEquilibrium tests removed - functionality intentionally moved to extensions

class TestErrorHandling:
    """Test enhanced error handling."""

    def test_equation_system_dimension_mismatch(self):
        """Test helpful error for dimension mismatch."""
        with pytest.raises(EquationSystemError) as exc_info:
            EquationSolver.solve_equations(['x'], ['eq1', 'eq2'])
        
        error_msg = str(exc_info.value)
        assert "mismatch" in error_msg.lower()
        assert "suggestion" in error_msg.lower()
        assert "1" in error_msg  # Variables count
        assert "2" in error_msg  # Equations count

    def test_helpful_error_messages_include_examples(self):
        """Test that error messages include helpful examples."""
        with pytest.raises(EquationSystemError) as exc_info:
            # This should trigger validation in EquationSystem - pass non-list
            EquationSystem("not_a_list", ['eq1'])
        
        error_msg = str(exc_info.value)
        assert "example" in error_msg.lower()
        assert "received" in error_msg.lower()
        assert "expected" in error_msg.lower()



class TestRobustnessAndEdgeCases:
    """Test robustness and edge cases."""

    def test_single_variable_system(self):
        """Test single variable system."""
        result = EquationSolver.solve_equations(['x'], ['x - 5'])
        
        assert result.success
        assert_allclose(result['x'], 5.0, atol=1e-8)

    def test_parameter_sweep_with_failures(self):
        """Test parameter sweep when some solutions fail."""
        # Create a system that might fail for some parameter values
        solver = (EquationSolver()
                  .set_system(['x'], ['x - param']))
        
        # Include some reasonable and some potentially problematic values
        results = solver.parameter_sweep('param', [1.0, 2.0, 3.0])
        
        # Should handle all cases gracefully
        assert len(results) == 3
        # Most should succeed for this simple case
        successful = sum(1 for r in results if r.success)
        assert successful >= 2

    def test_empty_parameter_dict(self):
        """Test system with empty parameters."""
        result = EquationSolver.solve_equations(
            variables=['x', 'y'],
            equations=['x + y - 3', 'x - y - 1'],
            parameters={}  # Empty dict
        )
        
        assert result.success
        assert_allclose(result['x'], 2.0, atol=1e-8)

    def test_large_system_dimensions(self):
        """Test with larger system dimensions."""
        # 3x3 system
        result = EquationSolver.solve_equations(
            variables=['x', 'y', 'z'],
            equations=['x + y + z - 6', 'x - y + z - 2', 'x + y - z - 2']
        )
        
        assert result.success
        assert_allclose(result['x'], 2.0, atol=1e-8)
        assert_allclose(result['y'], 2.0, atol=1e-8)
        assert_allclose(result['z'], 2.0, atol=1e-8)


# Performance and integration tests
class TestPerformanceAndIntegration:
    """Test performance and integration scenarios."""

    def test_repeated_solves_performance(self):
        """Test that repeated solves with same system are efficient."""
        solver = (EquationSolver()
                  .set_system(['x', 'y'], ['x + y - total', 'x - y - 1']))
        
        # Should be fast due to caching
        import time
        start_time = time.time()
        
        for total in range(3, 13):  # 10 solves
            result = solver.with_parameters({'total': float(total)}).solve()
            assert result.success
        
        elapsed = time.time() - start_time
        # Should be reasonably fast (< 1 second for 10 simple solves)
        assert elapsed < 1.0

    # NOTE: test_complex_chemical_workflow removed - ChemicalEquilibrium functionality moved to extensions

    @pytest.mark.slow
    def test_multistart_robustness(self):
        """Test multistart robustness on difficult systems."""
        # Challenging nonlinear system
        result = EquationSolver.solve_equations(
            variables=['x', 'y'],
            equations=['sin(x) + cos(y) - 0.5', 'x*y - 1.0'],
            multistart=True,
            tolerance=1e-6
        )
        
        # Should either converge or fail gracefully
        if result.success:
            x, y = result['x'], result['y']
            # Verify solution
            eq1_residual = abs(np.sin(x) + np.cos(y) - 0.5)
            eq2_residual = abs(x * y - 1.0)
            assert eq1_residual < 1e-5
            assert eq2_residual < 1e-5
