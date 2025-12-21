#!/usr/bin/env python3
"""
Tests for SolverOptions configuration

Tests all SolverOptions parameters including alpha, min_lambda, max_lambda,
store_history, and option validation.
"""

import pytest
import numpy as np
import sys
import os

# Add the parent directory to sys.path to import text_to_solver
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from text_to_solver.TextToSolver import TextToSolver, SolverOptions


class TestSolverOptionsBasic:
    """Test basic SolverOptions functionality."""
    
    @pytest.fixture
    def solver(self):
        """Create a solver instance for testing."""
        return TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5']
        )
    
    def test_default_options(self):
        """Test default SolverOptions values."""
        options = SolverOptions()
        
        assert options.tol_fun == 1e-6
        assert options.tol_x == 1e-8
        assert options.max_iter == 20
        assert options.display == True
        assert options.alpha == 1e-4
        assert options.min_lambda == 0.1
        assert options.max_lambda == 0.5
        assert options.store_history == True
        assert options.constraint_handling == 'project'
        assert options.constraint_tolerance == 1e-12
    
    def test_custom_options(self):
        """Test creating custom SolverOptions."""
        options = SolverOptions(
            tol_fun=1e-8,
            tol_x=1e-10,
            max_iter=50,
            display=False,
            alpha=1e-3,
            min_lambda=0.05,
            max_lambda=0.8,
            store_history=False
        )
        
        assert options.tol_fun == 1e-8
        assert options.tol_x == 1e-10
        assert options.max_iter == 50
        assert options.display == False
        assert options.alpha == 1e-3
        assert options.min_lambda == 0.05
        assert options.max_lambda == 0.8
        assert options.store_history == False
    
    def test_options_as_dict(self, solver):
        """Test passing options as dictionary."""
        guess = {'x': np.array([0.75]), 'y': np.array([0.25])}
        
        options_dict = {
            'tol_fun': 1e-8,
            'tol_x': 1e-10,
            'max_iter': 50,
            'display': False
        }
        
        solution, report = solver.solve(guess=guess, options=options_dict)
        
        assert report['exit_flag'] == 1
    
    def test_options_as_dataclass(self, solver):
        """Test passing options as SolverOptions dataclass."""
        guess = {'x': np.array([0.75]), 'y': np.array([0.25])}
        
        options = SolverOptions(
            tol_fun=1e-8,
            tol_x=1e-10,
            max_iter=50,
            display=False
        )
        
        solution, report = solver.solve(guess=guess, options=options)
        
        assert report['exit_flag'] == 1


class TestSolverOptionsParameters:
    """Test individual SolverOptions parameters."""
    
    @pytest.fixture
    def solver(self):
        """Create a solver instance for testing."""
        return TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5']
        )
    
    @pytest.mark.parametrize("alpha", [1e-5, 1e-4, 1e-3, 0.01])
    def test_alpha_parameter(self, solver, alpha):
        """Test alpha parameter (line search parameter)."""
        guess = {'x': np.array([0.5]), 'y': np.array([0.5])}
        options = SolverOptions(alpha=alpha, display=False)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # Should converge with different alpha values
        assert report['exit_flag'] == 1
    
    @pytest.mark.parametrize("min_lambda", [0.01, 0.1, 0.2, 0.5])
    def test_min_lambda_parameter(self, solver, min_lambda):
        """Test min_lambda parameter (minimum step size)."""
        guess = {'x': np.array([0.5]), 'y': np.array([0.5])}
        options = SolverOptions(min_lambda=min_lambda, display=False)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # Should converge with different min_lambda values
        assert report['exit_flag'] in [1, 2]
    
    @pytest.mark.parametrize("max_lambda", [0.3, 0.5, 0.7, 0.9])
    def test_max_lambda_parameter(self, solver, max_lambda):
        """Test max_lambda parameter (maximum step size)."""
        guess = {'x': np.array([0.5]), 'y': np.array([0.5])}
        options = SolverOptions(max_lambda=max_lambda, display=False)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # Should converge with different max_lambda values
        assert report['exit_flag'] in [1, 2]
    
    def test_tol_fun_parameter(self, solver):
        """Test tol_fun parameter (residual tolerance)."""
        guess = {'x': np.array([0.5]), 'y': np.array([0.5])}
        
        # Tight tolerance
        options = SolverOptions(tol_fun=1e-10, display=False)
        solution, report = solver.solve(guess=guess, options=options)
        assert report['exit_flag'] == 1
        assert report['res_norm'] < 1e-10
        
        # Loose tolerance
        options = SolverOptions(tol_fun=1e-3, display=False)
        solution, report = solver.solve(guess=guess, options=options)
        assert report['exit_flag'] == 1
        assert report['res_norm'] < 1e-3
    
    def test_tol_x_parameter(self, solver):
        """Test tol_x parameter (step size tolerance)."""
        guess = {'x': np.array([0.5]), 'y': np.array([0.5])}
        
        # Tight tolerance
        options = SolverOptions(tol_x=1e-12, display=False)
        solution, report = solver.solve(guess=guess, options=options)
        assert report['exit_flag'] in [1, 2]
        
        # Loose tolerance
        options = SolverOptions(tol_x=1e-6, display=False)
        solution, report = solver.solve(guess=guess, options=options)
        assert report['exit_flag'] in [1, 2]
    
    def test_max_iter_parameter(self, solver):
        """Test max_iter parameter."""
        guess = {'x': np.array([0.5]), 'y': np.array([0.5])}
        
        # Very few iterations
        options = SolverOptions(max_iter=2, display=False)
        solution, report = solver.solve(guess=guess, options=options)
        assert report['iter_count'] <= 2
        
        # Many iterations
        options = SolverOptions(max_iter=100, display=False)
        solution, report = solver.solve(guess=guess, options=options)
        assert report['iter_count'] <= 100


class TestStoreHistory:
    """Test store_history parameter."""
    
    @pytest.fixture
    def solver(self):
        """Create a solver instance for testing."""
        return TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5']
        )
    
    def test_store_history_true(self, solver):
        """Test with store_history=True (default)."""
        guess = {'x': np.array([0.75]), 'y': np.array([0.25])}
        options = SolverOptions(store_history=True, display=False)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        assert 'iteration_history' in report
        assert len(report['iteration_history']) > 0
        assert len(solver.get_iteration_history()) > 0
    
    def test_store_history_false(self, solver):
        """Test with store_history=False."""
        guess = {'x': np.array([0.75]), 'y': np.array([0.25])}
        options = SolverOptions(store_history=False, display=False)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # History should not be stored
        # Note: iteration_history may still be in report but empty
        assert len(solver.get_iteration_history()) == 0
    
    def test_history_access_with_store_false(self, solver):
        """Test accessing history methods when store_history=False."""
        guess = {'x': np.array([0.75]), 'y': np.array([0.25])}
        options = SolverOptions(store_history=False, display=False)
        
        solver.solve(guess=guess, options=options)
        
        # History methods should return empty lists
        assert len(solver.get_iteration_history()) == 0
        assert len(solver.get_residual_history()) == 0
        assert len(solver.get_convergence_history()) == 0
        assert len(solver.get_step_history()) == 0


class TestDisplayOption:
    """Test display parameter."""
    
    @pytest.fixture
    def solver(self):
        """Create a solver instance for testing."""
        return TextToSolver(
            dep_vars=['x'],
            residual=['x - 1']
        )
    
    def test_display_true(self, solver, capsys):
        """Test with display=True (should print iteration info)."""
        guess = {'x': np.array([0.5])}
        options = SolverOptions(display=True)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # Check that output was printed
        captured = capsys.readouterr()
        assert 'iter_count' in captured.out or len(captured.out) > 0
    
    def test_display_false(self, solver, capsys):
        """Test with display=False (should not print iteration table)."""
        guess = {'x': np.array([0.5])}
        options = SolverOptions(display=False)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # Check that no iteration table was printed
        captured = capsys.readouterr()
        # With display=False, should not have iteration table
        assert 'iter_count' not in captured.out or captured.out.strip() == ''


class TestOptionCombinations:
    """Test combinations of options."""
    
    @pytest.fixture
    def solver(self):
        """Create a solver instance for testing."""
        return TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5']
        )
    
    def test_tight_tolerances(self, solver):
        """Test with very tight tolerances."""
        guess = {'x': np.array([0.75]), 'y': np.array([0.25])}
        options = SolverOptions(
            tol_fun=1e-12,
            tol_x=1e-14,
            max_iter=100,
            display=False
        )
        
        solution, report = solver.solve(guess=guess, options=options)
        
        assert report['exit_flag'] in [1, 2]
        assert report['res_norm'] < 1e-12
    
    def test_loose_tolerances(self, solver):
        """Test with loose tolerances."""
        guess = {'x': np.array([0.75]), 'y': np.array([0.25])}
        options = SolverOptions(
            tol_fun=1e-3,
            tol_x=1e-5,
            max_iter=10,
            display=False
        )
        
        solution, report = solver.solve(guess=guess, options=options)
        
        assert report['exit_flag'] in [1, 2]
        assert report['res_norm'] < 1e-3
    
    def test_aggressive_line_search(self, solver):
        """Test with aggressive line search parameters."""
        guess = {'x': np.array([0.5]), 'y': np.array([0.5])}
        options = SolverOptions(
            alpha=1e-2,  # Larger alpha
            min_lambda=0.2,  # Larger min step
            max_lambda=0.9,  # Larger max step
            display=False
        )
        
        solution, report = solver.solve(guess=guess, options=options)
        
        assert report['exit_flag'] in [1, 2]
    
    def test_conservative_line_search(self, solver):
        """Test with conservative line search parameters."""
        guess = {'x': np.array([0.5]), 'y': np.array([0.5])}
        options = SolverOptions(
            alpha=1e-5,  # Smaller alpha
            min_lambda=0.05,  # Smaller min step
            max_lambda=0.3,  # Smaller max step
            display=False
        )
        
        solution, report = solver.solve(guess=guess, options=options)
        
        assert report['exit_flag'] in [1, 2]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

