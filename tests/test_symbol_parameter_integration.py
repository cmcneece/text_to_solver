#!/usr/bin/env python3
"""
Integration Tests for Symbol Detection and Parameter Sweep Features

Tests the complete workflow from symbol detection through parameter
sweep analysis, ensuring all components work together correctly.

Author: TextToSolver Test Team  
"""

import pytest
import json
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from text_to_solver.web_api import (
    WebAPIService, 
    SolverRequest, 
    ParameterRange
)


@pytest.mark.web_api
@pytest.mark.integration
class TestSymbolParameterWorkflow:
    """Test complete symbol detection to parameter sweep workflow."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.service = WebAPIService()
    
    def test_complete_linear_system_workflow(self):
        """Test complete workflow with linear system."""
        # Step 1: Define equations with parameters
        equations = ['a*x + b*y - c', 'x + y - 1']
        
        # Step 2: Detect symbols
        symbols_result = self.service.detect_symbols(equations)
        detected = symbols_result['detected_symbols']
        
        # Should detect a, b, c, x, y
        assert len(detected) >= 5
        required_symbols = ['a', 'b', 'c', 'x', 'y']
        for sym in required_symbols:
            assert sym in detected
        
        # Step 3: Classify symbols (simulate user input)
        variables = ['x', 'y']
        parameters = ['a', 'b', 'c']
        
        # Step 4: Set up parameter ranges
        parameter_ranges = {
            'a': ParameterRange(lower=1.0, upper=2.0, increment=1.0),
            'b': ParameterRange(lower=0.5, upper=1.0, increment=0.5)
        }
        
        # Step 5: Create solver request with parameter sweep
        request = SolverRequest(
            equations=equations,
            variables=variables,
            initial_guess={'x': 1.0, 'y': 0.5},
            parameters={'c': 1.0},  # Fixed parameter
            parameter_ranges=parameter_ranges
        )
        
        # Step 6: Solve with parameter sweep
        response = self.service.solve_algebraic_system(request)
        
        # Step 7: Verify results
        assert response.success is True
        assert 'sweep_summary' in response.solution
        
        sweep_data = response.report
        expected_combinations = 2 * 2  # a: 2 values, b: 2 values
        assert sweep_data['total_combinations'] == expected_combinations
        
        # Verify all parameter combinations were tested
        sweep_results = sweep_data['sweep_results']
        assert len(sweep_results) == expected_combinations
        
        # Check that each result has the expected structure
        for result in sweep_results:
            assert 'parameters' in result
            assert 'solution' in result
            assert 'success' in result
            
            # Check parameter values are from our ranges
            assert result['parameters']['a'] in [1.0, 2.0]
            assert result['parameters']['b'] in [0.5, 1.0]
    
    def test_nonlinear_system_with_parameter_sweep(self):
        """Test parameter sweep with nonlinear equations."""
        # Nonlinear system with parameters
        equations = ['k*x**2 + m*y**2 - R', 'x + y - S']
        
        # Detect symbols
        symbols_result = self.service.detect_symbols(equations)
        detected = symbols_result['detected_symbols']
        
        expected_symbols = ['R', 'S', 'k', 'm', 'x', 'y']
        for sym in expected_symbols:
            assert sym in detected
        
        # Set up parameter ranges for nonlinear coefficients
        parameter_ranges = {
            'k': ParameterRange(lower=1.0, upper=2.0, increment=1.0),
            'm': ParameterRange(lower=0.5, upper=1.5, increment=0.5)
        }
        
        request = SolverRequest(
            equations=equations,
            variables=['x', 'y'],
            initial_guess={'x': 1.0, 'y': 1.0},
            parameters={'R': 4.0, 'S': 2.0},
            parameter_ranges=parameter_ranges
        )
        
        response = self.service.solve_algebraic_system(request)
        
        assert response.success is True
        
        sweep_data = response.report
        expected_combinations = 2 * 3  # k: 2 values, m: 3 values
        assert sweep_data['total_combinations'] == expected_combinations
        
        # Analyze success rates for nonlinear system
        successful_count = sum(1 for r in sweep_data['sweep_results'] if r['success'])
        success_rate = successful_count / expected_combinations
        
        # Nonlinear systems may have varying success rates
        assert 0 <= success_rate <= 1
        assert sweep_data['success_rate'] == success_rate
    
    def test_physics_inspired_parameter_study(self):
        """Test parameter study inspired by physics equations."""
        # Simple pendulum-inspired system: T = 2*pi*sqrt(L/g), period constraint
        equations = [
            'T - 2*pi*sqrt(L/g)',
            'omega*T - 2*pi'  # omega = 2*pi/T
        ]
        
        # Detect symbols
        symbols_result = self.service.detect_symbols(equations)
        detected = symbols_result['detected_symbols']
        
        # Should detect physical parameters and variables
        physics_symbols = ['T', 'L', 'g', 'omega']
        for sym in physics_symbols:
            assert sym in detected
        
        # Set up parameter study: vary length and gravity
        parameter_ranges = {
            'L': ParameterRange(lower=0.5, upper=2.0, increment=0.5),  # Length in meters
            'g': ParameterRange(lower=9.5, upper=10.0, increment=0.25)  # Gravity variation
        }
        
        request = SolverRequest(
            equations=equations,
            variables=['T', 'omega'],
            initial_guess={'T': 2.0, 'omega': 3.0},
            parameters={},
            parameter_ranges=parameter_ranges
        )
        
        response = self.service.solve_algebraic_system(request)
        
        assert response.success is True
        
        sweep_results = response.report['sweep_results']
        
        # Analyze physical relationships in results
        for result in sweep_results:
            if result['success']:
                L = result['parameters']['L']
                g = result['parameters']['g']
                T = result['solution']['T']
                omega = result['solution']['omega']
                
                # Verify physical relationships
                expected_T = 2 * np.pi * np.sqrt(L / g)
                expected_omega = 2 * np.pi / T
                
                # Allow for numerical tolerance
                assert abs(T - expected_T) < 0.1
                assert abs(omega - expected_omega) < 0.1
    
    def test_parameter_sensitivity_analysis(self):
        """Test parameter sensitivity analysis capabilities."""
        # System sensitive to parameter changes
        equations = ['alpha*x + beta*x**2 - gamma', 'x - reference']
        
        symbols_result = self.service.detect_symbols(equations)
        detected = symbols_result['detected_symbols']
        
        # Fine-grained parameter study to observe sensitivity
        parameter_ranges = {
            'alpha': ParameterRange(lower=0.9, upper=1.1, increment=0.05),
            'beta': ParameterRange(lower=-0.1, upper=0.1, increment=0.05)
        }
        
        request = SolverRequest(
            equations=equations,
            variables=['x'],
            initial_guess={'x': 1.0},
            parameters={'gamma': 1.0, 'reference': 1.0},
            parameter_ranges=parameter_ranges
        )
        
        response = self.service.solve_algebraic_system(request)
        
        assert response.success is True
        
        sweep_results = response.report['sweep_results']
        
        # Analyze parameter sensitivity
        successful_results = [r for r in sweep_results if r['success']]
        assert len(successful_results) > 0
        
        # Extract solutions for sensitivity analysis
        solutions = []
        alpha_values = []
        beta_values = []
        
        for result in successful_results:
            solutions.append(result['solution']['x'])
            alpha_values.append(result['parameters']['alpha'])
            beta_values.append(result['parameters']['beta'])
        
        # Check that solution varies with parameters (sensitivity)
        solution_range = max(solutions) - min(solutions)
        assert solution_range > 1e-6  # Should show some sensitivity
        
        # Verify parameter ranges were explored
        alpha_range = max(alpha_values) - min(alpha_values)
        beta_range = max(beta_values) - min(beta_values)
        
        assert alpha_range > 0.1  # Should explore alpha range
        assert beta_range > 0.05  # Should explore beta range
    
    def test_constraint_compatibility_with_parameter_sweep(self):
        """Test parameter sweep with variable constraints."""
        equations = ['scale*x**2 + y**2 - target', 'x + y - sum_constraint']
        
        symbols_result = self.service.detect_symbols(equations)
        
        # Parameter sweep with constraints
        parameter_ranges = {
            'scale': ParameterRange(lower=0.5, upper=2.0, increment=0.5),
            'target': ParameterRange(lower=4.0, upper=9.0, increment=2.5)
        }
        
        request = SolverRequest(
            equations=equations,
            variables=['x', 'y'],
            initial_guess={'x': 1.5, 'y': 1.5},
            parameters={'sum_constraint': 2.0},
            parameter_ranges=parameter_ranges,
            constraints={'x': (0, 3), 'y': (0, 3)}  # Box constraints
        )
        
        response = self.service.solve_algebraic_system(request)
        
        assert response.success is True
        
        sweep_results = response.report['sweep_results']
        
        # Verify constraint satisfaction across parameter sweep
        for result in sweep_results:
            if result['success']:
                x_val = result['solution']['x']
                y_val = result['solution']['y']
                
                # All successful solutions should satisfy constraints
                assert 0 <= x_val <= 3
                assert 0 <= y_val <= 3
    
    def test_large_parameter_space_management(self):
        """Test handling of large parameter spaces."""
        equations = ['a*x + b*y + c*z - 1']
        
        # Create parameter ranges that approach limits
        parameter_ranges = {
            'a': ParameterRange(lower=0.5, upper=2.0, increment=0.1),  # 16 values
            'b': ParameterRange(lower=0.1, upper=1.0, increment=0.1),  # 10 values  
            'c': ParameterRange(lower=-1.0, upper=1.0, increment=0.2)  # 11 values
            # Total: 16 * 10 * 11 = 1760 combinations
        }
        
        request = SolverRequest(
            equations=equations,
            variables=['x'],
            initial_guess={'x': 1.0},
            parameter_ranges=parameter_ranges
        )
        
        response = self.service.solve_algebraic_system(request)
        
        # Should handle large parameter space appropriately
        if response.success:
            # If it succeeds, should have warning about large space
            assert response.warnings is not None
            
            sweep_data = response.report
            assert sweep_data['total_combinations'] == 1760
            
            # Should complete in reasonable time
            assert response.execution_time < 30.0  # Reasonable timeout
        else:
            # If it fails, should be due to size limitations
            assert 'too large' in response.error.lower()
    
    def test_error_propagation_through_workflow(self):
        """Test error handling through complete workflow."""
        # Test with equations that will cause issues
        problematic_equations = [
            'undefined_func(x)',  # Unknown function
            '0*x - y'  # Potential singular system
        ]
        
        # Symbol detection should handle gracefully
        symbols_result = self.service.detect_symbols(problematic_equations)
        assert 'detected_symbols' in symbols_result  # Should not crash
        
        # Parameter sweep should handle solver failures gracefully
        parameter_ranges = {
            'scale': ParameterRange(lower=0.0, upper=1.0, increment=0.5)  # Include zero
        }
        
        request = SolverRequest(
            equations=['scale*x - 1'],  # Will fail when scale=0
            variables=['x'],
            initial_guess={'x': 1.0},
            parameter_ranges=parameter_ranges
        )
        
        response = self.service.solve_algebraic_system(request)
        
        # Overall sweep should succeed even with some failures
        assert response.success is True
        
        sweep_results = response.report['sweep_results']
        
        # Should record both successes and failures
        success_count = sum(1 for r in sweep_results if r['success'])
        failure_count = len(sweep_results) - success_count
        
        # Expect some failures due to scale=0
        assert failure_count > 0
        assert success_count > 0  # But some successes too


@pytest.mark.web_api  
@pytest.mark.integration
class TestPerformanceAndScalability:
    """Test performance characteristics of new functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.service = WebAPIService()
    
    def test_symbol_detection_performance(self):
        """Test symbol detection performance with large equations."""
        # Create equations with many symbols
        large_equations = []
        for i in range(10):
            equation_terms = []
            for j in range(20):
                equation_terms.append(f'a{i}_{j}*x{j}')
            large_equations.append(' + '.join(equation_terms) + ' - 1')
        
        import time
        start_time = time.time()
        
        result = self.service.detect_symbols(large_equations)
        
        end_time = time.time()
        detection_time = end_time - start_time
        
        # Should complete quickly even with many symbols
        assert detection_time < 5.0  # Should be fast
        
        # Should detect all symbols correctly
        detected = result['detected_symbols']
        assert len(detected) > 100  # Many symbols detected
    
    def test_parameter_sweep_memory_usage(self):
        """Test memory efficiency of parameter sweeps."""
        # Moderate size sweep to check memory handling
        parameter_ranges = {
            'a': ParameterRange(lower=1.0, upper=5.0, increment=1.0),  # 5 values
            'b': ParameterRange(lower=0.1, upper=0.5, increment=0.1)   # 5 values  
            # Total: 25 combinations
        }
        
        request = SolverRequest(
            equations=['a*x + b*y - 1', 'x + y - 2'],
            variables=['x', 'y'],
            initial_guess={'x': 1.0, 'y': 1.0},
            parameter_ranges=parameter_ranges
        )
        
        import psutil
        process = psutil.Process()
        memory_before = process.memory_info().rss
        
        response = self.service.solve_algebraic_system(request)
        
        memory_after = process.memory_info().rss
        memory_increase = memory_after - memory_before
        
        # Should not use excessive memory
        assert memory_increase < 50 * 1024 * 1024  # Less than 50MB increase
        
        assert response.success is True
    
    def test_concurrent_symbol_detection(self):
        """Test concurrent symbol detection requests."""
        import threading
        import time
        
        results = []
        errors = []
        
        def detect_worker(equations, worker_id):
            try:
                result = self.service.detect_symbols(equations)
                results.append((worker_id, result))
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Create multiple concurrent detection requests
        threads = []
        for i in range(5):
            equations = [f'param_{i}*x + var_{i}*y - const_{i}']
            thread = threading.Thread(target=detect_worker, args=(equations, i))
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should handle concurrent requests
        assert len(errors) == 0  # No errors
        assert len(results) == 5  # All completed
        assert total_time < 10.0  # Reasonable completion time
        
        # Each result should be correct
        for worker_id, result in results:
            detected = result['detected_symbols']
            expected_symbols = [f'param_{worker_id}', 'x', f'var_{worker_id}', 'y', f'const_{worker_id}']
            for sym in expected_symbols:
                assert sym in detected


if __name__ == "__main__":
    pytest.main([__file__])
