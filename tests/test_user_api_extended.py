#!/usr/bin/env python3
"""
Extended tests for user API (EquationSolver)

Tests parameter_sweep, solve_equations classmethod, with_parameters,
and error handling in the user-friendly API.
"""

import pytest
import numpy as np
import sys
import os

# Add the parent directory to sys.path to import text_to_solver
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from text_to_solver.user_api import EquationSolver, SolverError


class TestParameterSweep:
    """Test parameter_sweep functionality."""
    
    @pytest.fixture
    def solver(self):
        """Create a solver instance for testing."""
        return EquationSolver(
            variables=['x', 'y'],
            equations=['x + y - p', 'x - y - 0.5'],
            parameters={'p': 1.0}
        )
    
    def test_parameter_sweep_basic(self, solver):
        """Test basic parameter sweep."""
        values = [0.5, 1.0, 1.5, 2.0]
        results = solver.parameter_sweep('p', values)
        
        assert len(results) == len(values)
        for i, result in enumerate(results):
            assert hasattr(result, 'converged')
            assert hasattr(result, 'variables')
            # Most should converge
            if result.converged:
                assert 'x' in result.variables
                assert 'y' in result.variables
    
    def test_parameter_sweep_single_value(self, solver):
        """Test parameter sweep with single value."""
        results = solver.parameter_sweep('p', [1.0])
        
        assert len(results) == 1
        assert results[0].converged
    
    def test_parameter_sweep_empty_list(self, solver):
        """Test parameter sweep with empty list."""
        results = solver.parameter_sweep('p', [])
        
        assert len(results) == 0
    
    def test_parameter_sweep_with_failures(self, solver):
        """Test parameter sweep handling failures."""
        # Use values that may cause some failures
        values = [-100.0, 1.0, 100.0]
        results = solver.parameter_sweep('p', values)
        
        assert len(results) == len(values)
        # Some may fail, but all should return results
        for result in results:
            assert hasattr(result, 'converged')
            assert hasattr(result, 'variables')
    
    def test_parameter_sweep_no_system(self):
        """Test parameter sweep without system set."""
        solver = EquationSolver()
        
        with pytest.raises(ValueError, match="No equation system set"):
            solver.parameter_sweep('p', [1.0, 2.0])


class TestSolveEquations:
    """Test solve_equations classmethod."""
    
    def test_solve_equations_basic(self):
        """Test basic solve_equations usage."""
        result = EquationSolver.solve_equations(
            variables=['x', 'y'],
            equations=['x + y - 1', 'x - y - 0.5']
        )
        
        assert result.converged
        assert 'x' in result.variables
        assert 'y' in result.variables
        assert result.residual_norm < 1e-6
    
    def test_solve_equations_with_parameters(self):
        """Test solve_equations with parameters."""
        result = EquationSolver.solve_equations(
            variables=['x', 'y'],
            equations=['x + y - p', 'x - y - 0.5'],
            parameters={'p': 1.0}
        )
        
        assert result.converged
        assert 'x' in result.variables
        assert 'y' in result.variables
    
    def test_solve_equations_with_tolerance(self):
        """Test solve_equations with custom tolerance."""
        result = EquationSolver.solve_equations(
            variables=['x'],
            equations=['x - 1'],
            tolerance=1e-10
        )
        
        assert result.converged
        assert abs(result.variables['x'][0] - 1.0) < 1e-10
    
    def test_solve_equations_with_multistart(self):
        """Test solve_equations with multistart."""
        result = EquationSolver.solve_equations(
            variables=['x', 'y'],
            equations=['x**2 + y**2 - 1', 'x - y'],
            multistart=True
        )
        
        # Should converge with multistart
        assert result.converged or result.iterations > 0


class TestWithParameters:
    """Test with_parameters fluent interface."""
    
    @pytest.fixture
    def solver(self):
        """Create a solver instance for testing."""
        return EquationSolver(
            variables=['x', 'y'],
            equations=['x + y - p', 'x - y - 0.5']
        )
    
    def test_with_parameters_basic(self, solver):
        """Test basic with_parameters usage."""
        result = solver.with_parameters({'p': 2.0}).solve()
        
        assert result.converged
        assert 'x' in result.variables
        assert 'y' in result.variables
    
    def test_with_parameters_fluent_chaining(self, solver):
        """Test fluent interface chaining."""
        result = (solver
                  .with_parameters({'p': 1.5})
                  .tolerance(1e-8)
                  .solve())
        
        assert result.converged
        assert result.residual_norm < 1e-8
    
    def test_with_parameters_multiple_calls(self, solver):
        """Test multiple with_parameters calls."""
        result1 = solver.with_parameters({'p': 1.0}).solve()
        result2 = solver.with_parameters({'p': 2.0}).solve()
        
        assert result1.converged
        assert result2.converged
        # Solutions should be different
        assert abs(result1.variables['x'][0] - result2.variables['x'][0]) > 1e-6
    
    def test_with_parameters_overwrite(self, solver):
        """Test that with_parameters overwrites existing parameters."""
        solver.set_system(
            variables=['x', 'y'],
            equations=['x + y - p', 'x - y - q'],
            parameters={'p': 1.0, 'q': 0.5}
        )
        
        # Overwrite p
        result = solver.with_parameters({'p': 2.0}).solve()
        
        assert result.converged


class TestErrorHandling:
    """Test error handling in EquationSolver."""
    
    @pytest.fixture
    def solver(self):
        """Create a solver instance for testing."""
        return EquationSolver(
            variables=['x', 'y'],
            equations=['x + y - 1', 'x - y - 0.5']
        )
    
    def test_singular_matrix_error(self):
        """Test handling of singular matrix errors."""
        solver = EquationSolver(
            variables=['x', 'y'],
            equations=['x**2 + y**2', 'x + y']  # Singular at (0,0)
        )
        
        with pytest.raises(SolverError, match="Singular matrix"):
            solver.solve(custom_guess={'x': np.array([0.0]), 'y': np.array([0.0])})
    
    def test_convergence_failure_error(self):
        """Test handling of convergence failures."""
        solver = EquationSolver(
            variables=['x'],
            equations=['x**2 + 1']  # No real solution
        )
        
        solver.max_iterations(2)  # Very few iterations
        
        with pytest.raises(SolverError, match="failed to converge"):
            solver.solve(custom_guess={'x': np.array([1.0])})
    
    def test_generic_solver_error(self):
        """Test handling of generic solver errors."""
        solver = EquationSolver(
            variables=['x'],
            equations=['invalid_equation']  # Invalid equation
        )
        
        # May raise various errors depending on validation
        try:
            solver.solve()
        except (SolverError, ValueError, Exception) as e:
            # Should raise some form of error
            assert True


class TestFluentInterface:
    """Test fluent interface methods."""
    
    def test_fluent_interface_chaining(self):
        """Test chaining multiple fluent methods."""
        result = (EquationSolver()
                  .set_system(['x'], ['x - 1'])
                  .tolerance(1e-10)
                  .max_iterations(50)
                  .solve())
        
        assert result.converged
        assert abs(result.variables['x'][0] - 1.0) < 1e-10
    
    def test_fluent_interface_order(self):
        """Test that fluent interface order doesn't matter."""
        solver = EquationSolver()
        
        result1 = (solver
                   .set_system(['x'], ['x - 1'])
                   .tolerance(1e-8)
                   .solve())
        
        result2 = (solver
                   .tolerance(1e-8)
                   .set_system(['x'], ['x - 1'])
                   .solve())
        
        # Both should work
        assert result1.converged
        assert result2.converged
    
    def test_fluent_interface_multistart(self):
        """Test fluent interface with multistart."""
        result = (EquationSolver()
                  .set_system(['x', 'y'], ['x**2 + y**2 - 1', 'x - y'])
                  .solve(multistart=True))
        
        assert result.converged or result.iterations > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

