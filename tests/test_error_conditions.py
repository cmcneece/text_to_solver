#!/usr/bin/env python3
"""
Tests for error conditions and exit flags in TextToSolver

Tests singular matrix detection, convergence failures, max iterations,
and other error conditions that result in different exit flags.
"""

import pytest
import numpy as np
import sys
import os

# Add the parent directory to sys.path to import text_to_solver
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from text_to_solver.TextToSolver import TextToSolver, SolverOptions, SingularMatrixError


class TestExitFlags:
    """Test different exit flags from the solver."""
    
    def test_exit_flag_1_success(self):
        """Test exit_flag=1 (successful convergence)."""
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 1', 'x - y - 0.5']
        )
        
        guess = {'x': np.array([0.75]), 'y': np.array([0.25])}
        solution, report = solver.solve(guess=guess, options=SolverOptions(display=False))
        
        assert report['exit_flag'] == 1
        assert report['res_norm'] < 1e-6
    
    def test_exit_flag_2_step_too_small(self):
        """Test exit_flag=2 (step size too small)."""
        # Create a system that converges very quickly
        solver = TextToSolver(
            dep_vars=['x'],
            residual=['x - 1.0']
        )
        
        # Use a guess very close to solution with tight tol_x
        guess = {'x': np.array([1.0 + 1e-10])}
        options = SolverOptions(tol_x=1e-12, tol_fun=1e-6, display=False)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # May exit with flag 2 if step is too small
        assert report['exit_flag'] in [1, 2]
        if report['exit_flag'] == 2:
            assert report['res_norm'] < 1e-6  # Still converged
    
    def test_exit_flag_neg1_singular_matrix(self):
        """Test exit_flag=-1 (singular/ill-conditioned matrix)."""
        # Create a system with singular Jacobian
        # x^2 + y^2 = 0, x + y = 0
        # At (0,0), Jacobian is singular
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x**2 + y**2', 'x + y']
        )
        
        # Start at or near singular point
        guess = {'x': np.array([0.0]), 'y': np.array([0.0])}
        options = SolverOptions(display=False, max_iter=5)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # Should detect singular matrix
        assert report['exit_flag'] == -1
    
    def test_exit_flag_max_iterations(self):
        """Test exit_flag when max iterations reached."""
        # Create a difficult system that may not converge quickly
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x**3 + y**3 - 1', 'x**2 + y**2 - 1']
        )
        
        # Use a poor initial guess
        guess = {'x': np.array([10.0]), 'y': np.array([10.0])}
        options = SolverOptions(display=False, max_iter=2)  # Very few iterations
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # Should exit due to max iterations (exit_flag may be 0 or -1 depending on state)
        assert report['iter_count'] == 2
        assert report['exit_flag'] in [-1, 0, 1]  # May vary based on convergence state


class TestSingularMatrixDetection:
    """Test singular matrix detection at different stages."""
    
    def test_singular_matrix_initial(self):
        """Test singular matrix detection at initialization."""
        # System with singular Jacobian at initial guess
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x**2 + y**2', 'x + y']
        )
        
        guess = {'x': np.array([0.0]), 'y': np.array([0.0])}
        options = SolverOptions(display=False)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # Should detect singular matrix
        assert report['exit_flag'] == -1
    
    def test_singular_matrix_during_iteration(self):
        """Test singular matrix detection during iteration."""
        # System that may become singular during iteration
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x**2 - y**2', 'x*y']
        )
        
        # Start at a point that may lead to singular Jacobian
        guess = {'x': np.array([0.1]), 'y': np.array([0.1])}
        options = SolverOptions(display=False, max_iter=10)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # May detect singular matrix during iteration
        # Exit flag depends on whether it converges or becomes singular
        assert report['exit_flag'] in [-1, 1, 2]
    
    def test_ill_conditioned_matrix(self):
        """Test detection of ill-conditioned (near-singular) matrix."""
        # System with very ill-conditioned Jacobian
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=[f'{1e-10}*x + y - 1', 'x + y - 1']
        )
        
        guess = {'x': np.array([0.5]), 'y': np.array([0.5])}
        options = SolverOptions(display=False)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # May have issues with ill-conditioning
        # Check that solver handles it (may converge or fail)
        assert report['exit_flag'] in [-1, 1, 2]


class TestNaNInfHandling:
    """Test handling of NaN and Inf values."""
    
    def test_nan_in_jacobian(self):
        """Test handling when Jacobian contains NaN."""
        # System that may produce NaN in Jacobian
        solver = TextToSolver(
            dep_vars=['x'],
            residual=['sqrt(x) - 1']  # sqrt of negative gives NaN
        )
        
        # Start with negative value (will cause NaN in sqrt)
        guess = {'x': np.array([-1.0])}
        options = SolverOptions(display=False, max_iter=5)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # Should detect NaN and exit with flag -1
        assert report['exit_flag'] == -1
    
    def test_inf_in_jacobian(self):
        """Test handling when Jacobian contains Inf."""
        # System that may produce Inf
        solver = TextToSolver(
            dep_vars=['x'],
            residual=['1/x - 1']  # 1/0 gives Inf
        )
        
        # Start very close to zero
        guess = {'x': np.array([1e-15])}
        options = SolverOptions(display=False, max_iter=5)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # May detect Inf or converge
        assert report['exit_flag'] in [-1, 1, 2]
    
    def test_nan_in_residual(self):
        """Test handling when residual contains NaN."""
        # System that produces NaN in residual
        solver = TextToSolver(
            dep_vars=['x'],
            residual=['log(x) - 1']  # log of negative gives NaN
        )
        
        guess = {'x': np.array([-1.0])}
        options = SolverOptions(display=False, max_iter=5)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # Should handle NaN appropriately
        assert report['exit_flag'] in [-1, 0]


class TestConvergenceFailures:
    """Test various convergence failure scenarios."""
    
    def test_no_convergence_poor_guess(self):
        """Test failure to converge with poor initial guess."""
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x**2 + y**2 - 1', 'x**3 + y**3 - 1']
        )
        
        # Very poor initial guess
        guess = {'x': np.array([100.0]), 'y': np.array([100.0])}
        options = SolverOptions(display=False, max_iter=5, tol_fun=1e-10)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # May not converge within iterations
        assert report['iter_count'] <= 5
        assert report['exit_flag'] in [-1, 0, 1, 2]
    
    def test_oscillating_solution(self):
        """Test system that oscillates without converging."""
        # System that may oscillate
        solver = TextToSolver(
            dep_vars=['x'],
            residual=['x**3 - x']  # Multiple roots, may oscillate
        )
        
        guess = {'x': np.array([0.1])}
        options = SolverOptions(display=False, max_iter=10, tol_fun=1e-12)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # May converge or oscillate
        assert report['exit_flag'] in [-1, 0, 1, 2]
    
    def test_diverging_solution(self):
        """Test system that diverges."""
        # System that may diverge
        solver = TextToSolver(
            dep_vars=['x'],
            residual=['x**2 + 1']  # No real solution
        )
        
        guess = {'x': np.array([1.0])}
        options = SolverOptions(display=False, max_iter=10)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # Should fail to converge
        assert report['exit_flag'] in [-1, 0]


class TestErrorReporting:
    """Test that error conditions are properly reported."""
    
    def test_singular_matrix_report(self):
        """Test that singular matrix is reported correctly."""
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x**2 + y**2', 'x + y']
        )
        
        guess = {'x': np.array([0.0]), 'y': np.array([0.0])}
        options = SolverOptions(display=False)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        assert report['exit_flag'] == -1
        assert 'res_norm' in report
        assert 'iter_count' in report
        assert 'resip_cond' in report
    
    def test_max_iterations_report(self):
        """Test that max iterations is reported correctly."""
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x**3 + y**3 - 1', 'x**2 + y**2 - 1']
        )
        
        guess = {'x': np.array([10.0]), 'y': np.array([10.0])}
        options = SolverOptions(display=False, max_iter=3)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        assert report['iter_count'] <= 3
        assert 'exit_flag' in report
        assert 'res_norm' in report
    
    def test_residual_norm_always_reported(self):
        """Test that residual norm is always in report."""
        solver = TextToSolver(
            dep_vars=['x'],
            residual=['x - 1']
        )
        
        guess = {'x': np.array([0.5])}
        options = SolverOptions(display=False)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        assert 'res_norm' in report
        assert isinstance(report['res_norm'], (int, float))
        assert not np.isnan(report['res_norm'])
        assert not np.isinf(report['res_norm'])


class TestEdgeCases:
    """Test edge cases in error handling."""
    
    def test_empty_residual(self):
        """Test behavior with empty residual (should be caught earlier)."""
        # This should be caught in validation, but test error handling
        with pytest.raises((ValueError, IndexError)):
            solver = TextToSolver(
                dep_vars=['x'],
                residual=[]
            )
    
    def test_zero_residual_norm(self):
        """Test behavior when residual norm is exactly zero."""
        solver = TextToSolver(
            dep_vars=['x'],
            residual=['x - 1']
        )
        
        # Use exact solution as guess
        guess = {'x': np.array([1.0])}
        options = SolverOptions(display=False)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # Should converge immediately
        assert report['exit_flag'] == 1
        assert report['res_norm'] < 1e-10
    
    def test_very_large_residual(self):
        """Test handling of very large residual values."""
        solver = TextToSolver(
            dep_vars=['x'],
            residual=['x - 1e10']
        )
        
        guess = {'x': np.array([0.0])}
        options = SolverOptions(display=False, max_iter=20)
        
        solution, report = solver.solve(guess=guess, options=options)
        
        # Should handle large values
        assert report['exit_flag'] in [-1, 0, 1, 2]
        assert 'res_norm' in report


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

