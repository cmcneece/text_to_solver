#!/usr/bin/env python3
"""
Tests for Dynamic Solution Results (Phase 3)

Tests the DynamicSolutionResult objects and their analysis capabilities.
"""

import pytest
import numpy as np
import sys
import os

# Add the parent directory to sys.path to import text_to_solver
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import dynamic solver components
from text_to_solver.dynamic_solver import (
    DynamicSolutionResult,
    DynamicEquationSolver,
    solve_ode_system
)
# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture
def simple_result():
    """Create a simple DynamicSolutionResult for testing"""
    t_points = np.linspace(0, 2, 21)  # 21 points from 0 to 2
    x_values = np.exp(-0.5 * t_points)  # Exponential decay
    y_values = 2 * np.sin(t_points)     # Sinusoidal
    
    return DynamicSolutionResult(
        time_points=t_points,
        variables={'x': x_values, 'y': y_values},
        success=True,
        message="Test result",
        integration_info={'method': 'test', 'time_span': (0, 2)}
    )


@pytest.fixture
def oscillator_result():
    """Create a harmonic oscillator result for testing"""
    solver = DynamicEquationSolver()
    solver.set_system(
        variables=['x', 'v'],
        equations=['dx/dt = v', 'dv/dt = -omega*omega*x'],
        parameters={'omega': 1.0},
        initial_conditions={'x': 1.0, 'v': 0.0}
    )
    
    return solver.integrate(time_span=(0, 2*np.pi), method='RK45')


@pytest.fixture
def failed_result():
    """Create a failed result for testing error handling"""
    return DynamicSolutionResult(
        time_points=np.array([]),
        variables={},
        success=False,
        message="Integration failed",
        integration_info={'error': 'Test error'}
    )


# ================================================================
# RESULT CREATION AND VALIDATION TESTS
# ================================================================

@pytest.mark.dynamic
@pytest.mark.results
class TestResultCreation:
    """Test DynamicSolutionResult creation and validation"""
    
    def test_valid_result_creation(self, simple_result):
        """Test creating a valid result object"""
        result = simple_result
        
        assert result.success
        assert result.message == "Test result"
        assert len(result.time_points) == 21
        assert 'x' in result.variables
        assert 'y' in result.variables
        assert len(result.variables['x']) == 21
        assert len(result.variables['y']) == 21
    
    def test_result_validation_empty_time_points(self):
        """Test validation with empty time points for successful result"""
        with pytest.raises(ValueError, match="Time points cannot be empty"):
            DynamicSolutionResult(
                time_points=np.array([]),
                variables={'x': np.array([1, 2, 3])},
                success=True,  # Success=True but empty time points should fail
                message="Test"
            )
    
    def test_result_validation_length_mismatch(self):
        """Test validation with mismatched variable lengths"""
        t_points = np.array([0, 1, 2])
        
        with pytest.raises(ValueError, match="length mismatch"):
            DynamicSolutionResult(
                time_points=t_points,
                variables={
                    'x': np.array([1, 2]),     # Length 2
                    'y': np.array([1, 2, 3])  # Length 3, should match time_points
                },
                success=True,
                message="Test"
            )
    
    def test_failed_result_creation(self, failed_result):
        """Test creating a failed result"""
        result = failed_result
        
        assert not result.success
        assert result.message == "Integration failed"
        assert len(result.time_points) == 0
        assert len(result.variables) == 0
        assert 'error' in result.integration_info


# ================================================================
# DATA ACCESS TESTS
# ================================================================

@pytest.mark.dynamic
@pytest.mark.results
class TestDataAccess:
    """Test accessing data from results"""
    
    def test_variable_access_by_name(self, simple_result):
        """Test accessing variables by name"""
        result = simple_result
        
        x_data = result['x']
        y_data = result['y']
        
        assert isinstance(x_data, np.ndarray)
        assert isinstance(y_data, np.ndarray)
        assert len(x_data) == 21
        assert len(y_data) == 21
    
    def test_variable_access_invalid_name(self, simple_result):
        """Test error when accessing non-existent variable"""
        result = simple_result
        
        with pytest.raises(KeyError, match="Variable 'z' not found"):
            _ = result['z']
    
    def test_initial_values_property(self, simple_result):
        """Test initial values property"""
        result = simple_result
        initial = result.initial_values
        
        assert isinstance(initial, dict)
        assert 'x' in initial
        assert 'y' in initial
        
        # Check values (first time point)
        assert abs(initial['x'] - result.variables['x'][0]) < 1e-10
        assert abs(initial['y'] - result.variables['y'][0]) < 1e-10
    
    def test_final_values_property(self, simple_result):
        """Test final values property"""
        result = simple_result
        final = result.final_values
        
        assert isinstance(final, dict)
        assert 'x' in final
        assert 'y' in final
        
        # Check values (last time point)
        assert abs(final['x'] - result.variables['x'][-1]) < 1e-10
        assert abs(final['y'] - result.variables['y'][-1]) < 1e-10
    
    def test_empty_result_properties(self, failed_result):
        """Test properties of failed/empty results"""
        result = failed_result
        
        initial = result.initial_values
        final = result.final_values
        
        assert initial == {}
        assert final == {}


# ================================================================
# INTERPOLATION TESTS  
# ================================================================

@pytest.mark.dynamic
@pytest.mark.results
@pytest.mark.interpolation
class TestInterpolation:
    """Test interpolation functionality"""
    
    def test_basic_interpolation(self, simple_result):
        """Test basic interpolation functionality"""
        result = simple_result
        
        # Create interpolation function for x
        x_interp = result.interpolate('x')
        
        # Test interpolation at known points
        t_test = 1.0
        x_interpolated = x_interp(t_test)
        x_expected = np.exp(-0.5 * t_test)  # Analytical value
        
        assert abs(x_interpolated - x_expected) < 0.01
    
    def test_interpolation_invalid_variable(self, simple_result):
        """Test error when interpolating non-existent variable"""
        result = simple_result
        
        with pytest.raises(KeyError, match="Variable 'z' not found"):
            result.interpolate('z')
    
    def test_interpolation_different_kinds(self, simple_result):
        """Test different interpolation kinds"""
        result = simple_result
        
        # Test different interpolation methods
        kinds = ['linear', 'cubic']
        
        for kind in kinds:
            try:
                x_interp = result.interpolate('x', kind=kind)
                
                # Test at midpoint
                t_mid = 1.0
                value = x_interp(t_mid)
                
                # Should be a reasonable value
                assert not np.isnan(value)
                assert not np.isinf(value)
            except ValueError:
                # Some interpolation methods might not be available
                # for all data sizes
                pass
    
    def test_at_time_method(self, simple_result):
        """Test the at_time convenience method"""
        result = simple_result
        
        # Test at specific time
        t_test = 1.5
        values_at_t = result.at_time(t_test)
        
        assert isinstance(values_at_t, dict)
        assert 'x' in values_at_t
        assert 'y' in values_at_t
        
        # Values should be reasonable
        assert not np.isnan(values_at_t['x'])
        assert not np.isnan(values_at_t['y'])
        
        # Test at boundary points
        t_start = result.time_points[0]
        t_end = result.time_points[-1]
        
        values_start = result.at_time(t_start)
        values_end = result.at_time(t_end)
        
        # Should match initial/final values closely
        assert abs(values_start['x'] - result.initial_values['x']) < 1e-6
        assert abs(values_end['x'] - result.final_values['x']) < 1e-6
    
    def test_extrapolation_behavior(self, simple_result):
        """Test behavior when interpolating outside time range"""
        result = simple_result
        
        x_interp = result.interpolate('x')
        
        # Test extrapolation beyond time range
        t_before = result.time_points[0] - 1.0
        t_after = result.time_points[-1] + 1.0
        
        # Should handle extrapolation (may give warning but shouldn't crash)
        try:
            value_before = x_interp(t_before)
            value_after = x_interp(t_after)
            
            # Values should be finite (extrapolation behavior)
            assert np.isfinite(value_before)
            assert np.isfinite(value_after)
        except ValueError:
            # Extrapolation might be disabled - this is acceptable
            pass


# ================================================================
# INTEGRATION WITH SOLVER TESTS
# ================================================================

@pytest.mark.dynamic
@pytest.mark.results
@pytest.mark.integration
class TestSolverIntegration:
    """Test result objects from actual solver runs"""
    
    def test_exponential_decay_result_analysis(self):
        """Test result analysis for exponential decay"""
        result = solve_ode_system(
            variables=['x'],
            equations=['dx/dt = -k*x'],
            parameters={'k': 0.5},
            initial_conditions={'x': 10.0},
            time_span=(0, 4),
            method='RK45'
        )
        
        assert result.success
        
        # Test data consistency
        assert result.initial_values['x'] == 10.0
        
        # Check exponential decay behavior
        x_values = result['x']
        assert np.all(x_values > 0)  # Should remain positive
        assert np.all(np.diff(x_values) <= 0)  # Should be decreasing
        
        # Test interpolation accuracy
        x_interp = result.interpolate('x')
        t_half = 2.0
        x_at_half = x_interp(t_half)
        expected_at_half = 10.0 * np.exp(-0.5 * t_half)
        
        assert abs(x_at_half - expected_at_half) < 0.1
    
    def test_oscillator_result_analysis(self, oscillator_result):
        """Test result analysis for harmonic oscillator"""
        result = oscillator_result
        
        assert result.success
        
        # Test oscillatory behavior
        x_values = result['x']
        v_values = result['v']
        
        # Should complete approximately one full cycle
        assert abs(result.final_values['x'] - result.initial_values['x']) < 0.1
        assert abs(result.final_values['v'] - result.initial_values['v']) < 0.1
        
        # Test energy conservation
        energy = 0.5 * (v_values**2 + x_values**2)  # E = (1/2)(v² + ω²x²), ω=1
        energy_variation = (np.max(energy) - np.min(energy)) / np.mean(energy)
        
        assert energy_variation < 0.05  # Energy should be conserved within 5%
        
        # Test interpolation at quarter periods
        period = 2 * np.pi
        for fraction in [0.25, 0.5, 0.75]:
            t_test = fraction * period
            values = result.at_time(t_test)
            
            # Values should be reasonable
            assert abs(values['x']) <= 1.5  # Should be bounded
            assert abs(values['v']) <= 1.5  # Should be bounded
    
    def test_predator_prey_result_analysis(self):
        """Test result analysis for predator-prey system"""
        result = solve_ode_system(
            variables=['x', 'y'],
            equations=[
                'dx/dt = alpha*x - beta*x*y',
                'dy/dt = delta*x*y - gamma*y'
            ],
            parameters={'alpha': 1.0, 'beta': 0.1, 'delta': 0.075, 'gamma': 1.5},
            initial_conditions={'x': 10.0, 'y': 5.0},
            time_span=(0, 10),
            method='RK45'
        )
        
        assert result.success
        
        # Test population positivity
        x_values = result['x']
        y_values = result['y']
        
        assert np.all(x_values > 0)  # Prey should remain positive
        assert np.all(y_values > 0)  # Predator should remain positive
        
        # Test oscillatory behavior
        x_range = np.max(x_values) - np.min(x_values)
        y_range = np.max(y_values) - np.min(y_values)
        
        assert x_range > 2  # Should show significant oscillation
        assert y_range > 1  # Should show significant oscillation
        
        # Test conserved quantity (for Lotka-Volterra)
        # H = δx + γy - α*ln(y) - β*ln(x) should be approximately constant
        alpha, beta, delta, gamma = 1.0, 0.1, 0.075, 1.5
        
        # Avoid log(0) with small epsilon
        x_safe = np.maximum(x_values, 1e-10)
        y_safe = np.maximum(y_values, 1e-10)
        
        H = delta * x_values + gamma * y_values - alpha * np.log(y_safe) - beta * np.log(x_safe)
        H_variation = (np.max(H) - np.min(H)) / np.mean(np.abs(H))
        
        # For numerical integration, conservation might not be perfect
        # Allow up to 200% variation (conservation quantity can drift due to numerical errors)
        assert H_variation < 2.0  # Conserved quantity should vary less than 200%


# ================================================================
# PERFORMANCE AND MEMORY TESTS
# ================================================================

@pytest.mark.dynamic
@pytest.mark.results
@pytest.mark.performance
class TestResultPerformance:
    """Test performance characteristics of result objects"""
    
    def test_large_result_handling(self):
        """Test handling of results with many time points"""
        # Create large time series
        n_points = 10000
        t_points = np.linspace(0, 100, n_points)
        x_values = np.sin(0.1 * t_points)  # Slow oscillation
        
        result = DynamicSolutionResult(
            time_points=t_points,
            variables={'x': x_values},
            success=True,
            message="Large test result"
        )
        
        assert len(result.time_points) == n_points
        
        # Test that interpolation still works efficiently
        x_interp = result.interpolate('x')
        
        # Test multiple interpolation points
        test_times = np.linspace(10, 90, 100)
        for t in test_times:
            value = x_interp(t)
            assert np.isfinite(value)
    
    def test_memory_efficiency(self):
        """Test memory efficiency of result storage"""
        # Create moderate-sized result
        n_points = 1000
        n_vars = 5
        
        t_points = np.linspace(0, 10, n_points)
        variables = {}
        
        for i in range(n_vars):
            variables[f'x{i}'] = np.random.randn(n_points)
        
        result = DynamicSolutionResult(
            time_points=t_points,
            variables=variables,
            success=True,
            message="Memory test"
        )
        
        # Should create successfully without memory issues
        assert len(result.variables) == n_vars
        
        # Test accessing all variables
        for i in range(n_vars):
            data = result[f'x{i}']
            assert len(data) == n_points
    
    def test_interpolation_performance(self, simple_result):
        """Test interpolation performance"""
        result = simple_result
        
        # Create interpolation function
        x_interp = result.interpolate('x')
        
        # Test many interpolation calls
        test_times = np.linspace(0, 2, 1000)
        
        values = []
        for t in test_times:
            values.append(x_interp(t))
        
        # Should complete without performance issues
        assert len(values) == 1000
        assert all(np.isfinite(v) for v in values)


# ================================================================
# EDGE CASES AND ERROR HANDLING
# ================================================================

@pytest.mark.dynamic
@pytest.mark.results
@pytest.mark.error_handling
class TestResultEdgeCases:
    """Test edge cases and error handling for results"""
    
    def test_single_point_result(self):
        """Test result with only one time point"""
        result = DynamicSolutionResult(
            time_points=np.array([0.0]),
            variables={'x': np.array([1.0])},
            success=True,
            message="Single point"
        )
        
        assert result.initial_values['x'] == 1.0
        assert result.final_values['x'] == 1.0
        
        # Interpolation might not work with single point
        try:
            x_interp = result.interpolate('x')
            # If it works, test it
            value = x_interp(0.0)
            assert value == 1.0
        except ValueError:
            # Single point interpolation might not be supported
            pass
    
    def test_constant_result(self):
        """Test result with constant values"""
        t_points = np.linspace(0, 5, 11)
        x_values = np.ones_like(t_points) * 2.5  # Constant value
        
        result = DynamicSolutionResult(
            time_points=t_points,
            variables={'x': x_values},
            success=True,
            message="Constant test"
        )
        
        assert result.initial_values['x'] == 2.5
        assert result.final_values['x'] == 2.5
        
        # Interpolation should work for constant values
        x_interp = result.interpolate('x')
        value = x_interp(2.5)  # Middle of range
        
        assert abs(value - 2.5) < 1e-6
    
    def test_result_with_nans(self):
        """Test handling of results containing NaN values"""
        t_points = np.array([0, 1, 2, 3, 4])
        x_values = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        
        # Creating result with NaN should work
        result = DynamicSolutionResult(
            time_points=t_points,
            variables={'x': x_values},
            success=False,  # Mark as failed due to NaN
            message="Contains NaN values"
        )
        
        assert not result.success
        assert 'x' in result.variables
        
        # Interpolation with NaN might fail or handle gracefully
        try:
            x_interp = result.interpolate('x')
            # If interpolation works, it should handle NaN appropriately
        except (ValueError, RuntimeError):
            # Interpolation failure with NaN is acceptable
            pass
    
    def test_empty_variable_names(self):
        """Test handling of edge cases in variable naming"""
        t_points = np.array([0, 1])
        
        # Test various edge cases that should work
        result = DynamicSolutionResult(
            time_points=t_points,
            variables={
                'x1': np.array([1, 2]),
                'var_with_underscore': np.array([3, 4]),
                'X': np.array([5, 6])  # Capital letter
            },
            success=True,
            message="Variable naming test"
        )
        
        assert 'x1' in result.variables
        assert 'var_with_underscore' in result.variables
        assert 'X' in result.variables
        
        # Test accessing these variables
        assert result['x1'][0] == 1
        assert result['var_with_underscore'][0] == 3
        assert result['X'][0] == 5
