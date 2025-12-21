#!/usr/bin/env python3
"""
Tests for constraint management API in TextToSolver

Tests adding, removing, clearing constraints, and constraint feasibility checking.
Also tests all constraint handling modes.
"""

import pytest
import numpy as np
import sys
import os

# Add the parent directory to sys.path to import text_to_solver
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from text_to_solver.TextToSolver import TextToSolver, SolverOptions


class TestConstraintCRUD:
    """Test constraint Create, Read, Update, Delete operations."""
    
    @pytest.fixture
    def solver(self):
        """Create a solver instance for testing."""
        return TextToSolver(
            dep_vars=['x', 'y', 'z'],
            residual=['x + y - 1', 'x - z - 0.5', 'y + z - 1.5']
        )
    
    def test_add_constraint_single(self, solver):
        """Test adding a single constraint."""
        solver.add_constraint('x', lower=0.0, upper=10.0)
        assert solver.has_constraints()
        assert solver.get_constraints().is_constrained('x')
        assert solver.get_constraints().lower_bounds['x'] == 0.0
        assert solver.get_constraints().upper_bounds['x'] == 10.0
    
    def test_add_constraint_lower_only(self, solver):
        """Test adding constraint with only lower bound."""
        solver.add_constraint('x', lower=0.0)
        assert solver.has_constraints()
        assert 'x' in solver.get_constraints().lower_bounds
        assert 'x' not in solver.get_constraints().upper_bounds
    
    def test_add_constraint_upper_only(self, solver):
        """Test adding constraint with only upper bound."""
        solver.add_constraint('x', upper=10.0)
        assert solver.has_constraints()
        assert 'x' not in solver.get_constraints().lower_bounds
        assert 'x' in solver.get_constraints().upper_bounds
    
    def test_add_constraint_none_bounds(self, solver):
        """Test adding constraint with None bounds (should merge)."""
        solver.add_constraint('x', lower=0.0, upper=10.0)
        # Adding with None should preserve existing bounds
        solver.add_constraint('x', lower=None, upper=None)
        assert solver.get_constraints().lower_bounds['x'] == 0.0
        assert solver.get_constraints().upper_bounds['x'] == 10.0
    
    def test_add_constraint_merge(self, solver):
        """Test that adding constraint merges with existing bounds."""
        solver.add_constraint('x', lower=0.0, upper=10.0)
        solver.add_constraint('x', lower=5.0, upper=15.0)
        # Should update to new bounds
        assert solver.get_constraints().lower_bounds['x'] == 5.0
        assert solver.get_constraints().upper_bounds['x'] == 15.0
    
    def test_add_constraint_invalid_variable(self, solver):
        """Test adding constraint for non-existent variable."""
        with pytest.raises(ValueError, match="not found in dependent variables"):
            solver.add_constraint('w', lower=0.0, upper=10.0)
    
    def test_add_constraint_invalid_bounds(self, solver):
        """Test adding constraint with invalid bounds."""
        with pytest.raises(ValueError, match="Invalid bounds"):
            solver.add_constraint('x', lower=10.0, upper=0.0)
    
    def test_add_constraints_batch(self, solver):
        """Test adding multiple constraints at once."""
        solver.add_constraints({
            'x': (0.0, 10.0),
            'y': (None, 5.0),
            'z': (-1.0, None)
        })
        assert solver.has_constraints()
        assert solver.get_constraints().is_constrained('x')
        assert solver.get_constraints().is_constrained('y')
        assert solver.get_constraints().is_constrained('z')
    
    def test_add_constraints_invalid_variable(self, solver):
        """Test adding constraints with invalid variable."""
        with pytest.raises(ValueError, match="not found in dependent variables"):
            solver.add_constraints({'w': (0.0, 10.0)})
    
    def test_remove_constraint(self, solver):
        """Test removing a constraint."""
        solver.add_constraint('x', lower=0.0, upper=10.0)
        assert solver.has_constraints()
        
        solver.remove_constraint('x')
        assert not solver.get_constraints().is_constrained('x')
        # Other constraints should remain if any
        solver.add_constraint('y', lower=0.0)
        solver.remove_constraint('x')  # Removing non-existent is OK
        assert solver.get_constraints().is_constrained('y')
    
    def test_clear_constraints(self, solver):
        """Test clearing all constraints."""
        solver.add_constraints({
            'x': (0.0, 10.0),
            'y': (None, 5.0),
            'z': (-1.0, None)
        })
        assert solver.has_constraints()
        
        solver.clear_constraints()
        assert not solver.has_constraints()
        assert len(solver.get_constraints().bounds) == 0
    
    def test_get_constraints(self, solver):
        """Test getting constraints."""
        assert not solver.has_constraints()
        
        solver.add_constraint('x', lower=0.0, upper=10.0)
        constraints = solver.get_constraints()
        assert constraints.is_constrained('x')
        assert constraints.lower_bounds['x'] == 0.0


class TestConstraintHandlingModes:
    """Test different constraint handling modes."""
    
    @pytest.fixture
    def solver_with_constraints(self):
        """Create solver with constraints."""
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5'],
            constraints={'x': (0.0, 10.0), 'y': (0.0, 10.0)}
        )
        return solver
    
    def test_constraint_handling_error_mode(self, solver_with_constraints):
        """Test constraint_handling='error' mode."""
        # Create an infeasible initial guess
        guess = {'x': np.array([-1.0]), 'y': np.array([-1.0])}
        
        options = SolverOptions(constraint_handling='error', display=False)
        
        with pytest.raises(ValueError, match="Initial guess violates constraints"):
            solver_with_constraints.solve(guess=guess, options=options)
    
    def test_constraint_handling_project_mode(self, solver_with_constraints):
        """Test constraint_handling='project' mode (with warning)."""
        # Create an infeasible initial guess
        guess = {'x': np.array([-1.0]), 'y': np.array([-1.0])}
        
        options = SolverOptions(constraint_handling='project', display=False)
        
        # Should project and solve successfully (with warning printed)
        solution, report = solver_with_constraints.solve(guess=guess, options=options)
        assert report['exit_flag'] == 1
        
        # Solution should satisfy constraints
        assert solution['x'][0] >= 0.0
        assert solution['y'][0] >= 0.0
    
    def test_constraint_handling_project_silent_mode(self, solver_with_constraints):
        """Test constraint_handling='project_silent' mode (no warning)."""
        # Create an infeasible initial guess
        guess = {'x': np.array([-1.0]), 'y': np.array([-1.0])}
        
        options = SolverOptions(constraint_handling='project_silent', display=False)
        
        # Should project and solve successfully (no warning)
        solution, report = solver_with_constraints.solve(guess=guess, options=options)
        assert report['exit_flag'] == 1
        
        # Solution should satisfy constraints
        assert solution['x'][0] >= 0.0
        assert solution['y'][0] >= 0.0
    
    def test_constraint_handling_ignore_mode(self, solver_with_constraints):
        """Test constraint_handling='ignore' mode."""
        # Create an infeasible initial guess
        guess = {'x': np.array([-1.0]), 'y': np.array([-1.0])}
        
        options = SolverOptions(constraint_handling='ignore', display=False)
        
        # Should allow infeasible guess (may fail or project during solve)
        # The solver will project during iterations anyway
        solution, report = solver_with_constraints.solve(guess=guess, options=options)
        # Should still converge (projection happens during iterations)
        assert report['exit_flag'] in [1, 2]
    
    def test_constraint_tolerance(self, solver_with_constraints):
        """Test constraint_tolerance parameter."""
        # Create a guess that violates constraints
        guess = {'x': np.array([-0.1]), 'y': np.array([0.0])}
        
        # With default tolerance (1e-12), this should be detected as violation
        options = SolverOptions(
            constraint_handling='error',
            constraint_tolerance=1e-12,
            display=False
        )
        
        # Should raise error
        with pytest.raises(ValueError, match="Initial guess violates constraints"):
            solver_with_constraints.solve(guess=guess, options=options)
        
        # Note: constraint_tolerance is used for detecting violations, but the actual
        # violation amount is still computed. For a truly small violation test,
        # we'd need to modify the validation logic to use tolerance.
        # For now, test that the error mode works correctly.


class TestConstraintFeasibility:
    """Test constraint feasibility checking."""
    
    @pytest.fixture
    def solver(self):
        """Create a solver with constraints."""
        return TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5'],
            constraints={'x': (0.0, 10.0), 'y': (0.0, 10.0)}
        )
    
    def test_check_constraint_feasibility_feasible(self, solver):
        """Test feasibility check with feasible solution."""
        solution = {'x': np.array([0.75]), 'y': np.array([0.25])}
        result = solver.check_constraint_feasibility(solution)
        
        assert result['feasible']
        assert len(result['violations']) == 0
        assert result['max_violation'] == 0.0
    
    def test_check_constraint_feasibility_infeasible(self, solver):
        """Test feasibility check with infeasible solution."""
        solution = {'x': np.array([-1.0]), 'y': np.array([15.0])}
        result = solver.check_constraint_feasibility(solution)
        
        assert not result['feasible']
        assert len(result['violations']) > 0
        assert 'x' in result['violations']
        assert 'y' in result['violations']
        assert result['max_violation'] > 0.0
    
    def test_check_constraint_feasibility_partial(self, solver):
        """Test feasibility check with partial violations."""
        solution = {'x': np.array([0.75]), 'y': np.array([15.0])}
        result = solver.check_constraint_feasibility(solution)
        
        assert not result['feasible']
        assert 'y' in result['violations']
        assert 'x' not in result['violations']
    
    def test_check_constraint_feasibility_no_constraints(self):
        """Test feasibility check with no constraints."""
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5']
        )
        
        solution = {'x': np.array([0.75]), 'y': np.array([0.25])}
        result = solver.check_constraint_feasibility(solution)
        
        assert result['feasible']
        assert len(result['violations']) == 0


class TestValidateInitialGuess:
    """Test validate_initial_guess method."""
    
    @pytest.fixture
    def solver(self):
        """Create a solver with constraints."""
        return TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5'],
            constraints={'x': (0.0, 10.0), 'y': (0.0, 10.0)}
        )
    
    def test_validate_initial_guess_feasible(self, solver):
        """Test validation with feasible guess."""
        guess = {'x': np.array([0.75]), 'y': np.array([0.25])}
        result = solver.validate_initial_guess(guess)
        
        assert result['valid']
        assert len(result['violations']) == 0
        assert result['max_violation'] == 0.0
        # When valid, projected_guess is None (only computed when violations exist)
        assert result['projected_guess'] is None
    
    def test_validate_initial_guess_infeasible(self, solver):
        """Test validation with infeasible guess."""
        guess = {'x': np.array([-1.0]), 'y': np.array([15.0])}
        result = solver.validate_initial_guess(guess)
        
        assert not result['valid']
        assert len(result['violations']) > 0
        assert result['max_violation'] > 0.0
        assert result['projected_guess'] is not None
        
        # Check projected guess satisfies constraints
        proj = result['projected_guess']
        assert proj['x'][0] >= 0.0
        assert proj['y'][0] <= 10.0
    
    def test_validate_initial_guess_no_constraints(self):
        """Test validation with no constraints."""
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5']
        )
        
        guess = {'x': np.array([0.75]), 'y': np.array([0.25])}
        result = solver.validate_initial_guess(guess)
        
        assert result['valid']
        assert result['message'] == 'No constraints defined'


class TestProjectInitialGuess:
    """Test project_initial_guess method."""
    
    @pytest.fixture
    def solver(self):
        """Create a solver with constraints."""
        return TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5'],
            constraints={'x': (0.0, 10.0), 'y': (0.0, 10.0)}
        )
    
    def test_project_initial_guess(self, solver):
        """Test projecting infeasible guess."""
        guess = {'x': np.array([-1.0]), 'y': np.array([15.0])}
        projected = solver.project_initial_guess(guess)
        
        assert projected['x'][0] >= 0.0
        assert projected['y'][0] <= 10.0
        assert projected['x'][0] == 0.0  # Projected to lower bound
        assert projected['y'][0] == 10.0  # Projected to upper bound
    
    def test_project_initial_guess_feasible(self, solver):
        """Test projecting feasible guess (should be unchanged)."""
        guess = {'x': np.array([0.75]), 'y': np.array([0.25])}
        projected = solver.project_initial_guess(guess)
        
        np.testing.assert_array_almost_equal(projected['x'], guess['x'])
        np.testing.assert_array_almost_equal(projected['y'], guess['y'])
    
    def test_project_initial_guess_no_constraints(self):
        """Test projection with no constraints."""
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5']
        )
        
        guess = {'x': np.array([0.75]), 'y': np.array([0.25])}
        projected = solver.project_initial_guess(guess)
        
        np.testing.assert_array_almost_equal(projected['x'], guess['x'])
        np.testing.assert_array_almost_equal(projected['y'], guess['y'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

