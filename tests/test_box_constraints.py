#!/usr/bin/env python3
"""
Unit tests for BoxConstraints class

Tests the core constraint infrastructure including bounds validation,
projection, violation detection, and active constraint identification.
"""

import pytest
import numpy as np
import sys
import os

# Add the parent directory to sys.path to import text_to_solver
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from text_to_solver.TextToSolver import BoxConstraints


class TestBoxConstraintsInitialization:
    """Test BoxConstraints initialization and validation."""
    
    def test_empty_constraints(self):
        """Test initialization with empty constraints."""
        constraints = BoxConstraints({})
        assert not constraints.has_constraints()
        assert len(constraints.bounds) == 0
        assert len(constraints.lower_bounds) == 0
        assert len(constraints.upper_bounds) == 0
    
    def test_single_lower_bound(self):
        """Test constraints with only lower bound."""
        constraints = BoxConstraints({'x': (0.0, None)})
        assert constraints.has_constraints()
        assert constraints.is_constrained('x')
        assert 'x' in constraints.lower_bounds
        assert constraints.lower_bounds['x'] == 0.0
        assert 'x' not in constraints.upper_bounds
    
    def test_single_upper_bound(self):
        """Test constraints with only upper bound."""
        constraints = BoxConstraints({'x': (None, 10.0)})
        assert constraints.has_constraints()
        assert constraints.is_constrained('x')
        assert 'x' not in constraints.lower_bounds
        assert 'x' in constraints.upper_bounds
        assert constraints.upper_bounds['x'] == 10.0
    
    def test_both_bounds(self):
        """Test constraints with both lower and upper bounds."""
        constraints = BoxConstraints({'x': (0.0, 10.0)})
        assert constraints.has_constraints()
        assert 'x' in constraints.lower_bounds
        assert 'x' in constraints.upper_bounds
        assert constraints.lower_bounds['x'] == 0.0
        assert constraints.upper_bounds['x'] == 10.0
    
    def test_multiple_variables(self):
        """Test constraints with multiple variables."""
        constraints = BoxConstraints({
            'x': (0.0, 10.0),
            'y': (None, 5.0),
            'z': (-1.0, None)
        })
        assert constraints.has_constraints()
        assert constraints.is_constrained('x')
        assert constraints.is_constrained('y')
        assert constraints.is_constrained('z')
        assert not constraints.is_constrained('w')
    
    def test_invalid_bounds_raises_error(self):
        """Test that invalid bounds (lower >= upper) raise ValueError."""
        with pytest.raises(ValueError, match="Invalid bounds"):
            BoxConstraints({'x': (10.0, 0.0)})
        
        with pytest.raises(ValueError, match="Invalid bounds"):
            BoxConstraints({'x': (5.0, 5.0)})
    
    def test_none_bounds_handling(self):
        """Test that None bounds are handled correctly."""
        constraints = BoxConstraints({'x': (None, None)})
        assert constraints.has_constraints()
        assert constraints.is_constrained('x')
        assert 'x' not in constraints.lower_bounds
        assert 'x' not in constraints.upper_bounds


class TestBoxConstraintsMethods:
    """Test BoxConstraints methods."""
    
    @pytest.fixture
    def constraints(self):
        """Create a constraints instance for testing."""
        return BoxConstraints({
            'x': (0.0, 10.0),
            'y': (None, 5.0),
            'z': (-1.0, None)
        })
    
    def test_has_constraints(self, constraints):
        """Test has_constraints() method."""
        assert constraints.has_constraints()
        
        empty = BoxConstraints({})
        assert not empty.has_constraints()
    
    def test_is_constrained(self, constraints):
        """Test is_constrained() method."""
        assert constraints.is_constrained('x')
        assert constraints.is_constrained('y')
        assert constraints.is_constrained('z')
        assert not constraints.is_constrained('w')
    
    def test_project_vector(self, constraints):
        """Test project_vector() method."""
        variables = ['x', 'y', 'z']
        
        # Test vector within bounds
        x = np.array([5.0, 2.0, 0.0])
        x_proj = constraints.project_vector(variables, x)
        np.testing.assert_array_equal(x_proj, x)
        
        # Test vector with violations
        x = np.array([-1.0, 10.0, -5.0])  # x too low, y too high, z too low
        x_proj = constraints.project_vector(variables, x)
        expected = np.array([0.0, 5.0, -1.0])  # Projected to bounds
        np.testing.assert_array_equal(x_proj, expected)
        
        # Test vector at bounds
        x = np.array([0.0, 5.0, -1.0])
        x_proj = constraints.project_vector(variables, x)
        np.testing.assert_array_equal(x_proj, x)
    
    def test_project_vector_single_bound(self):
        """Test projection with single bounds."""
        constraints = BoxConstraints({'x': (0.0, None)})
        variables = ['x']
        
        x = np.array([-1.0])
        x_proj = constraints.project_vector(variables, x)
        np.testing.assert_array_equal(x_proj, np.array([0.0]))
        
        constraints = BoxConstraints({'x': (None, 10.0)})
        x = np.array([15.0])
        x_proj = constraints.project_vector(variables, x)
        np.testing.assert_array_equal(x_proj, np.array([10.0]))
    
    def test_compute_constraint_violations(self, constraints):
        """Test compute_constraint_violations() method."""
        variables = ['x', 'y', 'z']
        
        # Test no violations
        x = np.array([5.0, 2.0, 0.0])
        violations = constraints.compute_constraint_violations(variables, x)
        assert len(violations) == 0
        
        # Test violations
        x = np.array([-1.0, 10.0, -5.0])
        violations = constraints.compute_constraint_violations(variables, x)
        assert 'x' in violations
        assert violations['x'] == 1.0  # 0.0 - (-1.0) = 1.0
        assert 'y' in violations
        assert violations['y'] == 5.0  # 10.0 - 5.0 = 5.0
        assert 'z' in violations
        assert violations['z'] == 4.0  # -1.0 - (-5.0) = 4.0
    
    def test_compute_constraint_violations_partial(self, constraints):
        """Test violation computation with partial violations."""
        variables = ['x', 'y', 'z']
        x = np.array([5.0, 10.0, 0.0])  # Only y violates
        violations = constraints.compute_constraint_violations(variables, x)
        assert 'y' in violations
        assert violations['y'] == 5.0
        assert 'x' not in violations
        assert 'z' not in violations
    
    def test_get_active_constraints(self, constraints):
        """Test get_active_constraints() method."""
        variables = ['x', 'y', 'z']
        
        # Test no active constraints
        x = np.array([5.0, 2.0, 0.0])
        active = constraints.get_active_constraints(variables, x)
        assert len(active) == 0
        
        # Test active lower bound
        x = np.array([0.0, 2.0, 0.0])  # x at lower bound
        active = constraints.get_active_constraints(variables, x, tol=1e-8)
        assert 'x' in active
        assert active['x'] == 'lower'
        
        # Test active upper bound
        x = np.array([10.0, 2.0, 0.0])  # x at upper bound
        active = constraints.get_active_constraints(variables, x, tol=1e-8)
        assert 'x' in active
        assert active['x'] == 'upper'
        
        # Test active with tolerance
        x = np.array([0.0 + 1e-9, 2.0, 0.0])  # x very close to lower bound
        active = constraints.get_active_constraints(variables, x, tol=1e-8)
        assert 'x' in active
        assert active['x'] == 'lower'
        
        # Test not active with larger tolerance gap
        x = np.array([0.0 + 1e-7, 2.0, 0.0])  # x further from lower bound
        active = constraints.get_active_constraints(variables, x, tol=1e-8)
        assert 'x' not in active
    
    def test_get_active_constraints_single_bound(self):
        """Test active constraints with single bounds."""
        constraints = BoxConstraints({'x': (0.0, None)})
        variables = ['x']
        
        x = np.array([0.0])
        active = constraints.get_active_constraints(variables, x, tol=1e-8)
        assert 'x' in active
        assert active['x'] == 'lower'
        
        constraints = BoxConstraints({'x': (None, 10.0)})
        x = np.array([10.0])
        active = constraints.get_active_constraints(variables, x, tol=1e-8)
        assert 'x' in active
        assert active['x'] == 'upper'


class TestBoxConstraintsEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_zero_bounds(self):
        """Test constraints with zero bounds (should raise error)."""
        # This should raise ValueError due to invalid bounds
        with pytest.raises(ValueError, match="Invalid bounds"):
            BoxConstraints({'x': (0.0, 0.0)})
    
    def test_negative_bounds(self):
        """Test constraints with negative bounds."""
        constraints = BoxConstraints({'x': (-10.0, -5.0)})
        variables = ['x']
        x = np.array([-7.0])
        assert not constraints.compute_constraint_violations(variables, x)
        
        x = np.array([-15.0])  # Below lower bound
        violations = constraints.compute_constraint_violations(variables, x)
        assert 'x' in violations
    
    def test_large_bounds(self):
        """Test constraints with very large bounds."""
        constraints = BoxConstraints({'x': (0.0, 1e10)})
        variables = ['x']
        x = np.array([1e9])
        assert not constraints.compute_constraint_violations(variables, x)
    
    def test_small_bounds(self):
        """Test constraints with very small bounds."""
        constraints = BoxConstraints({'x': (0.0, 1e-10)})
        variables = ['x']
        x = np.array([1e-11])
        assert not constraints.compute_constraint_violations(variables, x)
    
    def test_mixed_variable_order(self):
        """Test that variable order doesn't affect constraint application."""
        constraints = BoxConstraints({'x': (0.0, 10.0), 'y': (None, 5.0)})
        
        # Test with different variable orders
        variables1 = ['x', 'y']
        variables2 = ['y', 'x']
        
        x1 = np.array([5.0, 2.0])
        x2 = np.array([2.0, 5.0])  # Same values, different order
        
        violations1 = constraints.compute_constraint_violations(variables1, x1)
        violations2 = constraints.compute_constraint_violations(variables2, x2)
        
        # Should have same violations but for different variables
        assert len(violations1) == len(violations2)
    
    def test_unconstrained_variable_in_list(self):
        """Test that unconstrained variables in variable list are handled."""
        constraints = BoxConstraints({'x': (0.0, 10.0)})
        variables = ['x', 'y', 'z']  # y and z are not constrained
        
        x = np.array([5.0, 100.0, -100.0])
        violations = constraints.compute_constraint_violations(variables, x)
        assert 'y' not in violations
        assert 'z' not in violations


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

