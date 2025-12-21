#!/usr/bin/env python3
"""
Tests for analysis methods (analyze_convergence, analyze_constraints)

Tests edge cases and different convergence patterns.
"""

import pytest
import numpy as np
import sys
import os

# Add the parent directory to sys.path to import text_to_solver
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from text_to_solver.TextToSolver import TextToSolver, SolverOptions


class TestAnalyzeConvergence:
    """Test analyze_convergence method."""
    
    @pytest.fixture
    def solver(self):
        """Create a solver instance for testing."""
        return TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5']
        )
    
    def test_analyze_convergence_no_history(self, solver):
        """Test analyze_convergence with no iteration history."""
        analysis = solver.analyze_convergence()
        
        assert 'error' in analysis
        assert analysis['error'] == "No iteration history available"
    
    def test_analyze_convergence_after_solve(self, solver):
        """Test analyze_convergence after solving."""
        guess = {'x': np.array([0.75]), 'y': np.array([0.25])}
        options = SolverOptions(store_history=True, display=False)
        
        solver.solve(guess=guess, options=options)
        analysis = solver.analyze_convergence()
        
        assert 'error' not in analysis
        assert 'total_iterations' in analysis
        assert analysis['total_iterations'] > 0
        assert 'initial_residual' in analysis
        assert 'final_residual' in analysis
        assert 'residual_reduction' in analysis
    
    def test_analyze_convergence_single_iteration(self, solver):
        """Test analyze_convergence with single iteration."""
        # System that converges in one iteration
        solver = TextToSolver(
            dep_vars=['x'],
            residual=['x - 1']
        )
        
        guess = {'x': np.array([1.0])}
        options = SolverOptions(store_history=True, display=False)
        
        solver.solve(guess=guess, options=options)
        analysis = solver.analyze_convergence()
        
        assert analysis['convergence_type'] == "single iteration"
    
    def test_analyze_convergence_two_iterations(self, solver):
        """Test analyze_convergence with two iterations."""
        guess = {'x': np.array([0.5]), 'y': np.array([0.5])}
        options = SolverOptions(store_history=True, display=False, max_iter=2)
        
        solver.solve(guess=guess, options=options)
        analysis = solver.analyze_convergence()
        
        if analysis['total_iterations'] == 2:
            assert analysis['convergence_type'] == "insufficient data (2 iterations)"
    
    def test_analyze_convergence_quadratic(self, solver):
        """Test analyze_convergence detecting quadratic convergence."""
        guess = {'x': np.array([0.75]), 'y': np.array([0.25])}
        options = SolverOptions(store_history=True, display=False)
        
        solver.solve(guess=guess, options=options)
        analysis = solver.analyze_convergence()
        
        # Should detect convergence type
        assert 'convergence_type' in analysis
        assert analysis['convergence_type'] in [
            "quadratic (excellent)",
            "superlinear (good)",
            "linear (acceptable)",
            "slow/oscillating",
            "unable to determine",
            "insufficient data (2 iterations)"
        ]
    
    def test_analyze_convergence_metrics(self, solver):
        """Test that all convergence metrics are present."""
        guess = {'x': np.array([0.75]), 'y': np.array([0.25])}
        options = SolverOptions(store_history=True, display=False)
        
        solver.solve(guess=guess, options=options)
        analysis = solver.analyze_convergence()
        
        assert 'total_iterations' in analysis
        assert 'initial_residual' in analysis
        assert 'final_residual' in analysis
        assert 'residual_reduction' in analysis
        assert 'average_convergence_rate' in analysis
        assert 'total_solve_time' in analysis
        assert 'iterations_per_second' in analysis


class TestAnalyzeConstraints:
    """Test analyze_constraints method."""
    
    @pytest.fixture
    def solver_with_constraints(self):
        """Create a solver with constraints."""
        return TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5'],
            constraints={'x': (0.0, 10.0), 'y': (0.0, 10.0)}
        )
    
    @pytest.fixture
    def solver_no_constraints(self):
        """Create a solver without constraints."""
        return TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5']
        )
    
    def test_analyze_constraints_no_constraints(self, solver_no_constraints):
        """Test analyze_constraints with no constraints."""
        analysis = solver_no_constraints.analyze_constraints()
        
        assert 'error' in analysis
        assert analysis['error'] == "No constraints defined"
    
    def test_analyze_constraints_no_history(self, solver_with_constraints):
        """Test analyze_constraints with no iteration history."""
        analysis = solver_with_constraints.analyze_constraints()
        
        assert 'error' in analysis
        assert analysis['error'] == "No iteration history available"
    
    def test_analyze_constraints_after_solve(self, solver_with_constraints):
        """Test analyze_constraints after solving."""
        guess = {'x': np.array([0.75]), 'y': np.array([0.25])}
        options = SolverOptions(store_history=True, display=False)
        
        solver_with_constraints.solve(guess=guess, options=options)
        analysis = solver_with_constraints.analyze_constraints()
        
        assert 'error' not in analysis
        assert 'total_iterations' in analysis
        assert 'projections_applied' in analysis
        assert 'iterations_with_violations' in analysis
    
    def test_analyze_constraints_with_violations(self, solver_with_constraints):
        """Test analyze_constraints when violations occur."""
        # Use infeasible initial guess
        guess = {'x': np.array([-0.5]), 'y': np.array([-0.5])}
        options = SolverOptions(
            store_history=True,
            display=False,
            constraint_handling='project'
        )
        
        solver_with_constraints.solve(guess=guess, options=options)
        analysis = solver_with_constraints.analyze_constraints()
        
        assert 'error' not in analysis
        # Should have some constraint activity
        assert 'projections_applied' in analysis


class TestAnalysisEdgeCases:
    """Test edge cases in analysis methods."""
    
    def test_analyze_convergence_store_history_false(self):
        """Test analyze_convergence when store_history=False."""
        solver = TextToSolver(
            dep_vars=['x'],
            residual=['x - 1']
        )
        
        guess = {'x': np.array([0.5])}
        options = SolverOptions(store_history=False, display=False)
        
        solver.solve(guess=guess, options=options)
        analysis = solver.analyze_convergence()
        
        assert 'error' in analysis
    
    def test_analyze_constraints_store_history_false(self):
        """Test analyze_constraints when store_history=False."""
        solver = TextToSolver(
            dep_vars=['x'],
            residual=['x - 1'],
            constraints={'x': (0.0, 10.0)}
        )
        
        guess = {'x': np.array([0.5])}
        options = SolverOptions(store_history=False, display=False)
        
        solver.solve(guess=guess, options=options)
        analysis = solver.analyze_constraints()
        
        assert 'error' in analysis
    
    def test_analyze_convergence_zero_residual(self):
        """Test analyze_convergence with zero residual."""
        solver = TextToSolver(
            dep_vars=['x'],
            residual=['x - 1']
        )
        
        # Use exact solution
        guess = {'x': np.array([1.0])}
        options = SolverOptions(store_history=True, display=False)
        
        solver.solve(guess=guess, options=options)
        analysis = solver.analyze_convergence()
        
        # Should handle zero residual
        assert 'final_residual' in analysis
        assert analysis['final_residual'] < 1e-10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

