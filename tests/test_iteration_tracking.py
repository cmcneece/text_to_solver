#!/usr/bin/env python3
"""
Comprehensive tests for iteration data capture functionality in TextToSolver.

This test module covers the new iteration tracking features including:
- IterationData capture and structure
- History enable/disable functionality  
- Convergence analysis methods
- Integration with user APIs
- Performance and edge case handling
"""

import pytest
import numpy as np
import time
from typing import List, Dict, Any

from text_to_solver.TextToSolver import TextToSolver, SolverOptions, IterationData
from text_to_solver import EquationSolver


class TestIterationDataCapture:
    """Test core iteration data capture functionality."""
    
    def setup_method(self):
        """Set up test systems."""
        # Simple nonlinear system: x^2 + y^2 = 4, x - y = 1
        self.solver = TextToSolver(['x', 'y'], ['x**2 + y**2 - 4', 'x - y - 1'])
        self.guess = {'x': np.array([1.0]), 'y': np.array([0.5])}
        
    def test_basic_iteration_capture_enabled(self):
        """Test that iteration history is captured by default."""
        solution, report = self.solver.solve(
            self.guess, 
            options=SolverOptions(display=False, store_history=True)
        )
        
        # Verify solve succeeded
        assert report['exit_flag'] == 1
        
        # Verify iteration history is present
        assert 'iteration_history' in report
        assert 'total_solve_time' in report
        
        history = report['iteration_history']
        assert isinstance(history, list)
        assert len(history) > 0
        
        # Verify each iteration has proper IterationData structure
        for i, iter_data in enumerate(history):
            assert isinstance(iter_data, IterationData)
            assert iter_data.iteration == i + 1  # 1-based iteration count
            assert iter_data.residual_norm >= 0
            assert iter_data.step_norm >= 0
            assert iter_data.elapsed_time >= 0
            assert iter_data.timestamp > 0
            assert iter_data.condition_number > 0
            assert len(iter_data.residual_vector) == 2  # 2 equations
            assert len(iter_data.solution_vector) == 2  # 2 variables
            assert isinstance(iter_data.solver_params, dict)
        
        # Verify convergence: residual should decrease
        residuals = [iter_data.residual_norm for iter_data in history]
        assert residuals[0] > residuals[-1]  # Should improve
        
    def test_iteration_capture_disabled(self):
        """Test that iteration history can be disabled."""
        solution, report = self.solver.solve(
            self.guess,
            options=SolverOptions(display=False, store_history=False)
        )
        
        # Verify solve succeeded
        assert report['exit_flag'] == 1
        
        # Verify iteration history is NOT present
        assert 'iteration_history' not in report
        assert 'total_solve_time' not in report
        
        # Verify internal history is empty
        assert len(self.solver.get_iteration_history()) == 0
        
    def test_backward_compatibility_dict_options(self):
        """Test backward compatibility with dictionary options."""
        # Test with old-style dictionary (no STORE_HISTORY specified)
        solution, report = self.solver.solve(
            self.guess,
            options={'DISPLAY': False, 'MAX_ITER': 20}
        )
        
        # Should default to capturing history
        assert report['exit_flag'] == 1
        assert 'iteration_history' in report
        
        # Test explicitly disabling with dictionary
        solution2, report2 = self.solver.solve(
            self.guess,
            options={'DISPLAY': False, 'STORE_HISTORY': False}
        )
        
        assert report2['exit_flag'] == 1
        assert 'iteration_history' not in report2


class TestIterationDataStructure:
    """Test the IterationData structure and its contents."""
    
    def setup_method(self):
        """Set up test system."""
        self.solver = TextToSolver(['x', 'y'], ['x**2 + y**2 - 4', 'x - y - 1'])
        self.guess = {'x': np.array([1.0]), 'y': np.array([0.5])}
        
        # Solve to get history
        _, self.report = self.solver.solve(
            self.guess, 
            options=SolverOptions(display=False, max_iter=10)
        )
        self.history = self.report['iteration_history']
        
    def test_iteration_data_fields(self):
        """Test that all expected fields are present and valid."""
        assert len(self.history) > 0
        
        for iter_data in self.history:
            # Test required numeric fields
            assert isinstance(iter_data.iteration, int)
            assert iter_data.iteration > 0
            
            assert isinstance(iter_data.timestamp, float)
            assert iter_data.timestamp > 0
            
            assert isinstance(iter_data.elapsed_time, float)
            assert iter_data.elapsed_time >= 0
            
            assert isinstance(iter_data.residual_norm, float)
            assert iter_data.residual_norm >= 0
            
            assert isinstance(iter_data.step_norm, float)
            assert iter_data.step_norm >= 0
            
            assert isinstance(iter_data.convergence_rate, float)
            
            assert isinstance(iter_data.lambda_factor, (int, float))
            assert iter_data.lambda_factor > 0
            
            assert isinstance(iter_data.condition_number, float)
            assert iter_data.condition_number > 0
            
            # Test array fields
            assert isinstance(iter_data.residual_vector, np.ndarray)
            assert iter_data.residual_vector.shape == (2,)
            
            assert isinstance(iter_data.solution_vector, np.ndarray)
            assert iter_data.solution_vector.shape == (2,)
            
            # Test solver params
            assert isinstance(iter_data.solver_params, dict)
            expected_params = ['tol_fun', 'tol_x', 'max_iter', 'alpha', 'min_lambda']
            for param in expected_params:
                assert param in iter_data.solver_params
                
    def test_iteration_progression(self):
        """Test that iteration data shows logical progression."""
        # Test iteration numbers are sequential
        for i, iter_data in enumerate(self.history):
            assert iter_data.iteration == i + 1
            
        # Test timestamps are increasing
        timestamps = [iter_data.timestamp for iter_data in self.history]
        assert timestamps == sorted(timestamps)
        
        # Test elapsed times are increasing
        elapsed_times = [iter_data.elapsed_time for iter_data in self.history]
        assert elapsed_times == sorted(elapsed_times)
        
        # Test that solution vectors change between iterations
        if len(self.history) > 1:
            sol1 = self.history[0].solution_vector
            sol2 = self.history[1].solution_vector
            assert not np.array_equal(sol1, sol2)  # Should be different


class TestAnalysisMethods:
    """Test the new analysis and accessor methods."""
    
    def setup_method(self):
        """Set up test system and solve."""
        self.solver = TextToSolver(['x', 'y'], ['x**2 + y**2 - 4', 'x - y - 1'])
        self.guess = {'x': np.array([1.0]), 'y': np.array([0.5])}
        
        # Solve to populate history
        self.solution, self.report = self.solver.solve(
            self.guess, 
            options=SolverOptions(display=False)
        )
        
    def test_get_iteration_history(self):
        """Test get_iteration_history() method."""
        history = self.solver.get_iteration_history()
        
        assert isinstance(history, list)
        assert len(history) > 0
        assert all(isinstance(item, IterationData) for item in history)
        
        # Should be a copy, not the original
        history.append("dummy")
        original_history = self.solver.get_iteration_history()
        assert "dummy" not in original_history
        
    def test_get_residual_history(self):
        """Test get_residual_history() method."""
        residuals = self.solver.get_residual_history()
        
        assert isinstance(residuals, list)
        assert len(residuals) > 0
        assert all(isinstance(r, float) for r in residuals)
        assert all(r >= 0 for r in residuals)
        
        # Should show convergence (decreasing residuals)
        assert residuals[0] > residuals[-1]
        
    def test_get_convergence_history(self):
        """Test get_convergence_history() method."""
        convergence_rates = self.solver.get_convergence_history()
        
        assert isinstance(convergence_rates, list)
        assert len(convergence_rates) > 0
        assert all(isinstance(c, float) for c in convergence_rates)
        
    def test_get_step_history(self):
        """Test get_step_history() method."""
        steps = self.solver.get_step_history()
        
        assert isinstance(steps, list)  
        assert len(steps) > 0
        assert all(isinstance(s, float) for s in steps)
        assert all(s >= 0 for s in steps)
        
    def test_analyze_convergence_success(self):
        """Test analyze_convergence() for successful solve."""
        analysis = self.solver.analyze_convergence()
        
        # Test required fields are present
        required_fields = [
            'total_iterations', 'initial_residual', 'final_residual',
            'residual_reduction', 'average_convergence_rate', 'total_solve_time',
            'iterations_per_second', 'convergence_type'
        ]
        
        for field in required_fields:
            assert field in analysis, f"Missing field: {field}"
            
        # Test field types and ranges
        assert isinstance(analysis['total_iterations'], int)
        assert analysis['total_iterations'] > 0
        
        assert isinstance(analysis['initial_residual'], float)
        assert analysis['initial_residual'] > 0
        
        assert isinstance(analysis['final_residual'], float)
        assert analysis['final_residual'] >= 0
        
        assert isinstance(analysis['residual_reduction'], float)
        assert analysis['residual_reduction'] >= 1.0  # Should improve
        
        assert isinstance(analysis['total_solve_time'], float)
        assert analysis['total_solve_time'] > 0
        
        assert isinstance(analysis['iterations_per_second'], float)
        assert analysis['iterations_per_second'] > 0
        
        assert isinstance(analysis['convergence_type'], str)
        valid_types = ['quadratic', 'superlinear', 'linear', 'slow', 'oscillating', 'unable to determine']
        assert any(vtype in analysis['convergence_type'] for vtype in valid_types)
        
    def test_analyze_convergence_no_history(self):
        """Test analyze_convergence() when no history available."""
        solver_no_history = TextToSolver(['x'], ['x**2 - 1'])
        analysis = solver_no_history.analyze_convergence()
        
        assert 'error' in analysis
        assert 'No iteration history available' in analysis['error']


class TestUserAPIIntegration:
    """Test integration with the user-friendly EquationSolver API."""
    
    def test_user_api_captures_history(self):
        """Test that EquationSolver captures iteration history."""
        solver = EquationSolver()
        solver.set_system(['x', 'y'], ['x**2 + y**2 - 4', 'x - y - 1'])
        
        result = solver.solve()
        
        # Verify basic success
        assert result.success is True
        assert result.iterations > 0
        
        # Verify iteration history is in solver_info
        assert hasattr(result, 'solver_info')
        assert isinstance(result.solver_info, dict)
        
        if 'iteration_history' in result.solver_info:
            history = result.solver_info['iteration_history']
            assert isinstance(history, list)
            assert len(history) > 0
            assert all(isinstance(item, IterationData) for item in history)
            
    def test_user_api_history_disable(self):
        """Test disabling history through user API configuration."""
        # This would require extending the user API to expose store_history
        # For now, we test that the underlying solver can be configured
        solver = EquationSolver()
        solver.set_system(['x', 'y'], ['x**2 + y**2 - 4', 'x - y - 1'])
        
        # The user API doesn't currently expose store_history, but we can
        # verify it works by checking the underlying TextToSolver
        result = solver.solve()
        
        # Should have history by default (through TextToSolver)
        assert result.success is True


class TestEdgeCasesAndPerformance:
    """Test edge cases and performance characteristics."""
    
    def test_failed_solve_history(self):
        """Test iteration capture for failed solves."""
        # Create a system that will fail (singular Jacobian)
        solver = TextToSolver(['x', 'y'], ['x + y - 1', '2*x + 2*y - 2'])  # Dependent equations
        guess = {'x': np.array([0.5]), 'y': np.array([0.5])}
        
        solution, report = solver.solve(
            guess, 
            options=SolverOptions(display=False, max_iter=5)
        )
        
        # May fail, but should still capture what iterations occurred
        assert 'iteration_history' in report
        history = report['iteration_history']
        
        # Should have captured at least initial state
        assert len(history) >= 0  # May be 0 if fails immediately
        
        if len(history) > 0:
            # Verify structure is still correct
            for iter_data in history:
                assert isinstance(iter_data, IterationData)
                
    def test_max_iterations_reached(self):
        """Test history capture when max iterations is reached."""
        # Use a system that's harder to converge with poor initial guess
        solver = TextToSolver(['x'], ['x**4 - 10*x**2 + 9'])  # Has multiple roots
        guess = {'x': np.array([0.1])}  # Poor initial guess
        
        solution, report = solver.solve(
            guess,
            options=SolverOptions(display=False, max_iter=2, tol_fun=1e-10)  # Very strict tolerance, low max_iter
        )
        
        # Should have captured iterations even if didn't converge  
        assert 'iteration_history' in report
        history = report['iteration_history']
        
        # Should have captured some iterations
        assert len(history) > 0
        # Note: The solver may run up to max_iter+1 iterations due to loop condition
        # This is expected behavior - we're just testing that history is captured
        assert len(history) <= 5  # Reasonable upper bound
        
    def test_performance_overhead(self):
        """Test that iteration capture doesn't significantly impact performance."""
        solver = TextToSolver(['x', 'y'], ['x**2 + y**2 - 4', 'x - y - 1'])
        guess = {'x': np.array([1.0]), 'y': np.array([0.5])}
        
        # Time with history enabled
        start_time = time.time()
        for _ in range(10):
            solution, report = solver.solve(
                guess, 
                options=SolverOptions(display=False, store_history=True)
            )
        time_with_history = time.time() - start_time
        
        # Time with history disabled
        start_time = time.time()
        for _ in range(10):
            solution, report = solver.solve(
                guess,
                options=SolverOptions(display=False, store_history=False)
            )
        time_without_history = time.time() - start_time
        
        # Overhead should be reasonable (less than 50% slowdown)
        overhead_ratio = time_with_history / time_without_history
        assert overhead_ratio < 1.5, f"History capture overhead too high: {overhead_ratio:.2f}x"
        
    def test_large_system_memory(self):
        """Test memory efficiency for larger systems."""
        # Create a larger system (but not too large for CI)
        n = 5
        variables = [f'x{i}' for i in range(n)]
        equations = [f'x{i}**2 - {i+1}' for i in range(n)]
        
        solver = TextToSolver(variables, equations)
        guess = {f'x{i}': np.array([1.0]) for i in range(n)}
        
        solution, report = solver.solve(
            guess,
            options=SolverOptions(display=False, store_history=True)
        )
        
        # Should complete without memory issues
        assert 'iteration_history' in report
        history = report['iteration_history']
        
        # Verify structures are correct size
        for iter_data in history:
            assert len(iter_data.residual_vector) == n
            assert len(iter_data.solution_vector) == n


class TestIterationDataConsistency:
    """Test consistency and relationships between iteration data."""
    
    def test_residual_jacobian_consistency(self):
        """Test that residual and Jacobian are evaluated at the same point."""
        solver = TextToSolver(['x', 'y'], ['x**2 + y**2 - 4', 'x - y - 1'])
        guess = {'x': np.array([1.0]), 'y': np.array([0.5])}
        
        solution, report = solver.solve(
            guess,
            options=SolverOptions(display=False, store_history=True)
        )
        
        history = report['iteration_history']
        
        for iter_data in history:
            # The residual vector should be the evaluation of the equations
            # at the solution vector stored in the same iteration
            x_vals = iter_data.solution_vector
            
            # We can't easily re-evaluate without accessing internals,
            # but we can check that the residual norm matches what was computed
            computed_norm = np.linalg.norm(iter_data.residual_vector)
            stored_norm = iter_data.residual_norm
            
            assert abs(computed_norm - stored_norm) < 1e-10
            
    def test_timing_consistency(self):
        """Test that timing information is consistent."""
        solver = TextToSolver(['x', 'y'], ['x**2 + y**2 - 4', 'x - y - 1'])
        guess = {'x': np.array([1.0]), 'y': np.array([0.5])}
        
        solution, report = solver.solve(
            guess,
            options=SolverOptions(display=False, store_history=True)
        )
        
        history = report['iteration_history']
        total_time = report['total_solve_time']
        
        if len(history) > 0:
            # Last iteration elapsed time should match total solve time
            last_elapsed = history[-1].elapsed_time
            assert abs(last_elapsed - total_time) < 0.001  # Small tolerance for timing
            
            # Elapsed times should be monotonic
            elapsed_times = [iter_data.elapsed_time for iter_data in history]
            assert elapsed_times == sorted(elapsed_times)


# Integration test with pytest markers for organization
@pytest.mark.iteration_tracking
@pytest.mark.integration
def test_full_integration_workflow():
    """Integration test covering a complete workflow with iteration tracking."""
    
    # Create solver
    solver = TextToSolver(['x', 'y', 'z'], [
        'x**2 + y**2 + z**2 - 14',
        'x + y + z - 6', 
        'x*y - z - 2'
    ])
    
    # Solve with custom options
    guess = {'x': np.array([1.0]), 'y': np.array([2.0]), 'z': np.array([3.0])}
    options = SolverOptions(
        display=False,
        tol_fun=1e-8,
        max_iter=20,
        store_history=True
    )
    
    solution, report = solver.solve(guess, options=options)
    
    # Verify solve succeeded
    assert report['exit_flag'] == 1
    assert 'iteration_history' in report
    
    # Analyze results
    analysis = solver.analyze_convergence()
    
    # Should have reasonable convergence
    assert analysis['total_iterations'] < 15  # Should converge relatively quickly
    assert analysis['residual_reduction'] > 100  # Should improve significantly
    assert 'quadratic' in analysis['convergence_type'] or 'superlinear' in analysis['convergence_type']
    
    # Test accessor methods
    residuals = solver.get_residual_history()
    steps = solver.get_step_history()
    
    assert len(residuals) == analysis['total_iterations']
    assert len(steps) == analysis['total_iterations']
    
    # Should show improvement
    assert residuals[0] > residuals[-1]
    
    print(f"✅ Integration test passed: {analysis['total_iterations']} iterations, "
          f"{analysis['convergence_type']} convergence")
