#!/usr/bin/env python3
"""
Unit tests for internal helper methods in TextToSolver

Tests unpack_inputs, resegment_x, package_x, calculate_step, and other helpers.
"""

import pytest
import numpy as np
import sys
import os

# Add the parent directory to sys.path to import text_to_solver
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from text_to_solver.TextToSolver import TextToSolver
from scipy.sparse import csr_matrix


class TestUnpackInputs:
    """Test unpack_inputs method."""
    
    @pytest.fixture
    def solver(self):
        """Create a solver instance for testing."""
        return TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5'],
            indep_vars=['t']
        )
    
    def test_unpack_inputs_basic(self, solver):
        """Test basic unpack_inputs functionality."""
        guess = {'x': np.array([0.5]), 'y': np.array([0.5])}
        indep_var_val = {'t': np.array([1.0])}
        
        guess_list, indep_list = solver.unpack_inputs(guess, indep_var_val)
        
        assert len(guess_list) == 2
        assert len(indep_list) == 1
        np.testing.assert_array_equal(guess_list[0], np.array([0.5]))
        np.testing.assert_array_equal(guess_list[1], np.array([0.5]))
        np.testing.assert_array_equal(indep_list[0], np.array([1.0]))
    
    def test_unpack_inputs_no_indep_vars(self, solver):
        """Test unpack_inputs with no independent variables."""
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5']
        )
        
        guess = {'x': np.array([0.5]), 'y': np.array([0.5])}
        indep_var_val = {}
        
        guess_list, indep_list = solver.unpack_inputs(guess, indep_var_val)
        
        assert len(guess_list) == 2
        assert len(indep_list) == 0
    
    def test_unpack_inputs_array_values(self, solver):
        """Test unpack_inputs with array values."""
        guess = {
            'x': np.array([0.5, 1.0, 1.5]),
            'y': np.array([0.25, 0.5, 0.75])
        }
        indep_var_val = {'t': np.array([1.0, 2.0, 3.0])}
        
        guess_list, indep_list = solver.unpack_inputs(guess, indep_var_val)
        
        assert len(guess_list) == 2
        assert guess_list[0].shape == (3,)
        assert guess_list[1].shape == (3,)


class TestResegmentX:
    """Test resegment_x method."""
    
    @pytest.fixture
    def solver(self):
        """Create a solver instance for testing."""
        return TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5']
        )
    
    def test_resegment_x_basic(self, solver):
        """Test basic resegment_x functionality."""
        # Create a flattened array: [x1, x2, y1, y2] for 2 points
        x = np.array([0.5, 1.0, 0.25, 0.5])
        
        x_list = solver.resegment_x(x)
        
        assert len(x_list) == 2
        np.testing.assert_array_equal(x_list[0], np.array([0.5, 1.0]))
        np.testing.assert_array_equal(x_list[1], np.array([0.25, 0.5]))
    
    def test_resegment_x_single_point(self, solver):
        """Test resegment_x with single point."""
        x = np.array([0.5, 0.25])
        
        x_list = solver.resegment_x(x)
        
        assert len(x_list) == 2
        np.testing.assert_array_equal(x_list[0], np.array([0.5]))
        np.testing.assert_array_equal(x_list[1], np.array([0.25]))
    
    def test_resegment_x_multiple_points(self, solver):
        """Test resegment_x with multiple points."""
        # 3 points: [x1, x2, x3, y1, y2, y3]
        x = np.array([0.5, 1.0, 1.5, 0.25, 0.5, 0.75])
        
        x_list = solver.resegment_x(x)
        
        assert len(x_list) == 2
        assert x_list[0].shape == (3,)
        assert x_list[1].shape == (3,)


class TestPackageX:
    """Test package_x method."""
    
    @pytest.fixture
    def solver(self):
        """Create a solver instance for testing."""
        return TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5']
        )
    
    def test_package_x_basic(self, solver):
        """Test basic package_x functionality."""
        x = np.array([0.5, 0.25])
        
        x_dict = solver.package_x(x)
        
        assert 'x' in x_dict
        assert 'y' in x_dict
        np.testing.assert_array_equal(x_dict['x'], np.array([0.5]))
        np.testing.assert_array_equal(x_dict['y'], np.array([0.25]))
    
    def test_package_x_multiple_points(self, solver):
        """Test package_x with multiple points."""
        x = np.array([0.5, 1.0, 0.25, 0.5])
        
        x_dict = solver.package_x(x)
        
        assert 'x' in x_dict
        assert 'y' in x_dict
        np.testing.assert_array_equal(x_dict['x'], np.array([0.5, 1.0]))
        np.testing.assert_array_equal(x_dict['y'], np.array([0.25, 0.5]))


class TestCalculateStep:
    """Test calculate_step method."""
    
    @pytest.fixture
    def solver(self):
        """Create a solver instance for testing."""
        return TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5']
        )
    
    def test_calculate_step_basic(self, solver):
        """Test basic calculate_step functionality."""
        # Create residual and jacobian
        guess = {'x': np.array([0.5]), 'y': np.array([0.5])}
        res, jac = solver.evaluate_res_jac(
            [np.array([0.5]), np.array([0.5])],
            {}
        )
        
        dx = solver.calculate_step(res, jac)
        
        assert dx.shape == res.shape
        assert not np.any(np.isnan(dx))
        assert not np.any(np.isinf(dx))
    
    def test_calculate_step_shape(self, solver):
        """Test that calculate_step returns correct shape."""
        guess = {'x': np.array([0.5]), 'y': np.array([0.5])}
        res, jac = solver.evaluate_res_jac(
            [np.array([0.5]), np.array([0.5])],
            {}
        )
        
        dx = solver.calculate_step(res, jac)
        
        # Step should have same shape as residual
        assert dx.shape == res.shape


class TestEvaluateResJac:
    """Test evaluate_res_jac method."""
    
    @pytest.fixture
    def solver(self):
        """Create a solver instance for testing."""
        return TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5']
        )
    
    def test_evaluate_res_jac_basic(self, solver):
        """Test basic evaluate_res_jac functionality."""
        guess_list = [np.array([0.5]), np.array([0.5])]
        indep_list = []
        
        res, jac = solver.evaluate_res_jac(guess_list, {})
        
        assert res.shape == (2,)  # 2 equations
        assert jac.shape == (2, 2)  # 2x2 Jacobian
        assert not np.any(np.isnan(res))
        assert not np.any(np.isnan(jac.data)) if hasattr(jac, 'data') else True
    
    def test_evaluate_res_jac_with_indep_vars(self):
        """Test evaluate_res_jac with independent variables."""
        solver = TextToSolver(
            dep_vars=['x'],
            residual=['x - t'],
            indep_vars=['t']
        )
        
        guess_list = [np.array([1.0])]
        indep_var_val = {'t': np.array([1.0])}
        
        res, jac = solver.evaluate_res_jac(guess_list, indep_var_val)
        
        assert res.shape == (1,)
        assert jac.shape == (1, 1)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

