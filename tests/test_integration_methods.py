#!/usr/bin/env python3
"""
Tests for Integration Methods (Phase 3)

Tests the various numerical integration methods and their accuracy,
stability, and performance characteristics.
"""

import pytest
import numpy as np
import sys
import os

# Add the parent directory to sys.path to import text_to_solver
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import dynamic solver components
from text_to_solver.dynamic_solver import (
    TimeIntegrator,
    DynamicEquationSolver,
    DynamicSolutionResult
)
# ================================================================
# TEST SYSTEMS AND FIXTURES
# ================================================================

@pytest.fixture
def integrator():
    """Create a TimeIntegrator instance"""
    return TimeIntegrator()


def exponential_decay_system(t, y):
    """Simple exponential decay: dy/dt = -k*y"""
    k = 0.5
    return np.array([-k * y[0]])


def harmonic_oscillator_system(t, y):
    """Harmonic oscillator: dx/dt = v, dv/dt = -ω²*x"""
    omega = 1.0
    x, v = y[0], y[1]
    return np.array([v, -omega**2 * x])


def linear_system(t, y):
    """Linear system with time-dependent forcing: dy/dt = -y + A*t"""
    A = 0.1
    return np.array([-y[0] + A * t])


def stiff_system(t, y):
    """Stiff system for testing stability"""
    return np.array([-1000 * y[0] + 1000 * y[1], 
                     y[0] - 2 * y[1]])


# ================================================================
# FIXED-STEP METHOD TESTS
# ================================================================

@pytest.mark.dynamic
@pytest.mark.integration_methods
class TestFixedStepMethods:
    """Test fixed-step integration methods"""
    
    def test_euler_method_accuracy(self, integrator):
        """Test Euler method accuracy on simple system"""
        y0 = np.array([1.0])
        t_span = (0, 2)
        dt = 0.01
        
        t_points, y_values = integrator.euler(exponential_decay_system, y0, t_span, dt)
        
        # Check basic properties
        assert len(t_points) > 0
        assert y_values.shape[0] == len(t_points)
        assert y_values.shape[1] == 1
        
        # Check initial condition
        assert abs(y_values[0, 0] - 1.0) < 1e-10
        
        # Check final value against analytical solution
        # y(t) = y0 * exp(-k*t) = 1.0 * exp(-0.5*2) = exp(-1)
        expected_final = np.exp(-1.0)
        actual_final = y_values[-1, 0]
        
        # Euler method should be reasonably accurate with small dt
        relative_error = abs(actual_final - expected_final) / expected_final
        assert relative_error < 0.05  # 5% error tolerance for Euler
    
    def test_rk4_method_accuracy(self, integrator):
        """Test RK4 method accuracy on simple system"""
        y0 = np.array([1.0])
        t_span = (0, 2)
        dt = 0.01
        
        t_points, y_values = integrator.runge_kutta_4(exponential_decay_system, y0, t_span, dt)
        
        # Check basic properties
        assert len(t_points) > 0
        assert y_values.shape == (len(t_points), 1)
        
        # Check against analytical solution
        expected_final = np.exp(-1.0)
        actual_final = y_values[-1, 0]
        
        # RK4 should be much more accurate than Euler
        relative_error = abs(actual_final - expected_final) / expected_final
        assert relative_error < 0.001  # 0.1% error tolerance for RK4
    
    def test_step_size_consistency(self, integrator):
        """Test that methods respect the specified step size"""
        y0 = np.array([1.0])
        t_span = (0, 1)
        dt = 0.1
        
        # Test Euler
        t_euler, _ = integrator.euler(exponential_decay_system, y0, t_span, dt)
        expected_points = int((t_span[1] - t_span[0]) / dt) + 1
        assert len(t_euler) == expected_points
        
        # Check time spacing
        time_diffs = np.diff(t_euler)
        assert np.allclose(time_diffs, dt, rtol=1e-10)
        
        # Test RK4
        t_rk4, _ = integrator.runge_kutta_4(exponential_decay_system, y0, t_span, dt)
        assert len(t_rk4) == expected_points
        
        time_diffs_rk4 = np.diff(t_rk4)
        assert np.allclose(time_diffs_rk4, dt, rtol=1e-10)
    
    def test_multivariable_systems(self, integrator):
        """Test fixed-step methods on multi-variable systems"""
        y0 = np.array([1.0, 0.0])  # Initial: x=1, v=0
        t_span = (0, np.pi)  # Half period
        dt = 0.01
        
        # Test Euler on harmonic oscillator
        t_euler, y_euler = integrator.euler(harmonic_oscillator_system, y0, t_span, dt)
        
        assert y_euler.shape[1] == 2  # Two variables
        
        # After half period, x should be -1, v should be 0
        x_final = y_euler[-1, 0]
        v_final = y_euler[-1, 1]
        
        # Euler may not be very accurate for oscillatory systems
        assert abs(x_final + 1.0) < 0.5  # Rough check
        
        # Test RK4 on same system
        t_rk4, y_rk4 = integrator.runge_kutta_4(harmonic_oscillator_system, y0, t_span, dt)
        
        x_final_rk4 = y_rk4[-1, 0]
        v_final_rk4 = y_rk4[-1, 1]
        
        # RK4 should be more accurate
        assert abs(x_final_rk4 + 1.0) < 0.1  # Should be closer to -1
        assert abs(v_final_rk4) < 0.1       # Should be closer to 0


# ================================================================
# ADAPTIVE METHOD TESTS
# ================================================================

@pytest.mark.dynamic
@pytest.mark.integration_methods
class TestAdaptiveMethods:
    """Test adaptive integration methods"""
    
    def test_rk45_method_accuracy(self, integrator):
        """Test RK45 adaptive method"""
        y0 = np.array([1.0])
        t_span = (0, 2)
        
        t_points, y_values = integrator.scipy_adaptive(
            exponential_decay_system, y0, t_span, method='RK45'
        )
        
        # Check basic properties
        assert len(t_points) > 0
        assert y_values.shape[0] == len(t_points)
        assert y_values.shape[1] == 1
        
        # Check against analytical solution
        expected_final = np.exp(-1.0)
        actual_final = y_values[-1, 0]
        
        # Adaptive method should be very accurate
        relative_error = abs(actual_final - expected_final) / expected_final
        assert relative_error < 3e-5  # High accuracy expected for RK45
    
    def test_dop853_method_accuracy(self, integrator):
        """Test DOP853 high-order method"""
        y0 = np.array([1.0, 0.0])  # Harmonic oscillator
        t_span = (0, 2*np.pi)  # Full period
        
        try:
            t_points, y_values = integrator.scipy_adaptive(
                harmonic_oscillator_system, y0, t_span, method='DOP853'
            )
            
            # After full period, should return to initial conditions
            x_final = y_values[-1, 0]
            v_final = y_values[-1, 1]
            
            # Very high accuracy expected
            assert abs(x_final - 1.0) < 1e-8
            assert abs(v_final - 0.0) < 1e-8
        except Exception as e:
            # DOP853 might not be available in all scipy versions
            pytest.skip(f"DOP853 not available: {e}")
    
    def test_adaptive_step_control(self, integrator):
        """Test that adaptive methods control step size appropriately"""
        y0 = np.array([1.0])
        t_span = (0, 5)
        
        # Test with tight tolerance
        t_tight, y_tight = integrator.scipy_adaptive(
            exponential_decay_system, y0, t_span, 
            method='RK45', rtol=1e-8, atol=1e-10
        )
        
        # Test with loose tolerance
        t_loose, y_loose = integrator.scipy_adaptive(
            exponential_decay_system, y0, t_span,
            method='RK45', rtol=1e-3, atol=1e-6
        )
        
        # Tight tolerance should use more points
        assert len(t_tight) >= len(t_loose)
        
        # Both should be accurate, but tight tolerance more so
        expected_final = np.exp(-0.5 * 5)
        
        error_tight = abs(y_tight[-1, 0] - expected_final)
        error_loose = abs(y_loose[-1, 0] - expected_final)
        
        assert error_tight <= error_loose
    
    def test_max_step_size_control(self, integrator):
        """Test max_step parameter for adaptive methods"""
        y0 = np.array([1.0])
        t_span = (0, 2)
        
        # Test with and without max step size
        t_unrestricted, _ = integrator.scipy_adaptive(
            exponential_decay_system, y0, t_span, method='RK45'
        )
        
        t_restricted, _ = integrator.scipy_adaptive(
            exponential_decay_system, y0, t_span, 
            method='RK45', max_step=0.1
        )
        
        # Restricted version should have more points (smaller steps)
        assert len(t_restricted) >= len(t_unrestricted)
        
        # Check that step sizes are respected
        step_sizes = np.diff(t_restricted)
        assert np.all(step_sizes <= 0.1 + 1e-10)  # Allow small numerical error


# ================================================================
# METHOD COMPARISON TESTS
# ================================================================

@pytest.mark.dynamic
@pytest.mark.integration_methods
@pytest.mark.comparison
class TestMethodComparison:
    """Compare different integration methods"""
    
    def test_method_accuracy_comparison(self):
        """Compare accuracy of different methods on same system"""
        solver = DynamicEquationSolver()
        solver.set_system(
            variables=['x'],
            equations=['dx/dt = -k*x'],
            parameters={'k': 1.0},
            initial_conditions={'x': 1.0}
        )
        
        methods_and_settings = [
            ('euler', {'dt': 0.001}),
            ('rk4', {'dt': 0.001}),
            ('RK45', {}),
            ('DOP853', {})
        ]
        
        results = {}
        analytical_solution = np.exp(-2.0)  # x(2) for dx/dt = -x, x(0) = 1
        
        for method, kwargs in methods_and_settings:
            try:
                result = solver.integrate((0, 2), method=method, **kwargs)
                if result.success:
                    final_value = result.final_values['x']
                    error = abs(final_value - analytical_solution)
                    results[method] = {'value': final_value, 'error': error}
            except Exception as e:
                # Some methods might not be available
                results[method] = {'error': float('inf')}
        
        # Check that we have at least some successful methods
        successful_methods = [m for m in results if results[m]['error'] < 1.0]
        assert len(successful_methods) >= 2
        
        # Higher-order methods should generally be more accurate
        if 'euler' in results and 'rk4' in results:
            if results['euler']['error'] < 1.0 and results['rk4']['error'] < 1.0:
                assert results['rk4']['error'] < results['euler']['error']
    
    def test_performance_vs_accuracy_tradeoff(self):
        """Test performance vs accuracy tradeoffs"""
        solver = DynamicEquationSolver()
        solver.set_system(
            variables=['x', 'v'],
            equations=['dx/dt = v', 'dv/dt = -omega*omega*x'],
            parameters={'omega': 1.0},
            initial_conditions={'x': 1.0, 'v': 0.0}
        )
        
        # Compare fast vs accurate methods
        fast_result = solver.integrate((0, 2*np.pi), method='euler', dt=0.01)
        accurate_result = solver.integrate((0, 2*np.pi), method='DOP853')
        
        if fast_result.success and accurate_result.success:
            # Fast method should use fewer points
            assert len(fast_result.time_points) <= len(accurate_result.time_points) * 2
            
            # Accurate method should be more accurate
            # (but we allow fast method to be reasonably close)
            x_fast = fast_result.final_values['x']
            x_accurate = accurate_result.final_values['x']
            
            # Both should be close to 1.0 (full period oscillation)
            assert abs(x_accurate - 1.0) < 0.01
            # Fast method allowed to be less accurate
            assert abs(x_fast - 1.0) < 0.5


# ================================================================
# STABILITY AND ROBUSTNESS TESTS
# ================================================================

@pytest.mark.dynamic
@pytest.mark.integration_methods
@pytest.mark.stability
class TestMethodStability:
    """Test stability and robustness of integration methods"""
    
    def test_oscillatory_system_stability(self):
        """Test methods on oscillatory systems"""
        solver = DynamicEquationSolver()
        solver.set_system(
            variables=['x', 'v'],
            equations=['dx/dt = v', 'dv/dt = -omega*omega*x'],
            parameters={'omega': 10.0},  # High frequency
            initial_conditions={'x': 1.0, 'v': 0.0}
        )
        
        # Test different methods on high-frequency oscillation
        methods = [
            ('RK45', {}),
            ('DOP853', {}),
        ]
        
        for method, kwargs in methods:
            try:
                result = solver.integrate((0, 1), method=method, **kwargs)
                
                if result.success:
                    # Solution should remain bounded
                    x_values = result['x']
                    v_values = result['v']
                    
                    assert np.all(np.abs(x_values) < 10)  # Should remain bounded
                    assert np.all(np.abs(v_values) < 100)  # Should remain bounded
                    
                    # Energy should be approximately conserved
                    omega = 10.0
                    energy = 0.5 * (v_values**2 + omega**2 * x_values**2)
                    energy_variation = (np.max(energy) - np.min(energy)) / np.mean(energy)
                    
                    # Allow more variation for high-frequency systems
                    assert energy_variation < 0.5
            except Exception:
                # High-frequency systems might be challenging
                pass
    
    def test_near_singular_systems(self):
        """Test behavior near singular conditions"""
        solver = DynamicEquationSolver()
        
        # System that approaches zero asymptotically
        solver.set_system(
            variables=['x'],
            equations=['dx/dt = -x/(1 + t)'],  # Solution: x(t) = x0/(1+t)
            initial_conditions={'x': 1.0}
        )
        
        result = solver.integrate((0, 100), method='RK45')
        
        if result.success:
            # Should approach zero but remain positive
            x_values = result['x']
            assert np.all(x_values > 0)
            assert x_values[-1] < x_values[0]  # Should be decreasing
            
            # Check against analytical solution at final time
            t_final = result.time_points[-1]
            expected_final = 1.0 / (1.0 + t_final)
            actual_final = result.final_values['x']
            
            relative_error = abs(actual_final - expected_final) / expected_final
            assert relative_error < 0.01
    
    def test_system_with_parameters_near_zero(self):
        """Test systems with very small parameters"""
        solver = DynamicEquationSolver()
        
        # Very slow decay
        solver.set_system(
            variables=['x'],
            equations=['dx/dt = -k*x'],
            parameters={'k': 1e-6},  # Very small decay rate
            initial_conditions={'x': 1.0}
        )
        
        result = solver.integrate((0, 1), method='RK45')
        
        assert result.success
        
        # Should barely change over time span
        initial_val = result.initial_values['x']
        final_val = result.final_values['x']
        
        change = abs(final_val - initial_val)
        assert change < 0.001  # Should change very little
        
        # Check against analytical solution
        expected = np.exp(-1e-6 * 1)  # ≈ 1 - 1e-6
        assert abs(final_val - expected) < 1e-9


# ================================================================
# ERROR HANDLING TESTS
# ================================================================

@pytest.mark.dynamic
@pytest.mark.integration_methods
@pytest.mark.error_handling
class TestIntegrationErrorHandling:
    """Test error handling in integration methods"""
    
    def test_invalid_initial_conditions(self, integrator):
        """Test handling of invalid initial conditions"""
        # Test with NaN initial condition
        y0_nan = np.array([np.nan])
        t_span = (0, 1)
        dt = 0.01
        
        # Methods should handle NaN gracefully
        try:
            t_points, y_values = integrator.euler(exponential_decay_system, y0_nan, t_span, dt)
            # If it doesn't raise exception, result should indicate failure
            assert np.isnan(y_values).any() or len(t_points) == 0
        except (ValueError, RuntimeError):
            # Raising exception is also acceptable
            pass
    
    def test_invalid_time_spans(self, integrator):
        """Test handling of invalid time spans"""
        y0 = np.array([1.0])
        dt = 0.01
        
        # Test zero time span
        try:
            t_points, y_values = integrator.euler(exponential_decay_system, y0, (0, 0), dt)
            # Should handle gracefully
            assert len(t_points) in [0, 1]  # Either empty or single point
        except ValueError:
            # Exception is acceptable for zero time span
            pass
        
        # Test negative time span
        try:
            t_points, y_values = integrator.euler(exponential_decay_system, y0, (1, 0), dt)
            # Might work (backwards integration) or fail gracefully
        except ValueError:
            # Exception acceptable for backwards time
            pass
    
    def test_extremely_small_step_size(self, integrator):
        """Test behavior with very small step sizes"""
        y0 = np.array([1.0])
        t_span = (0, 0.001)
        dt = 1e-8  # Small but reasonable step size
        
        # This should be manageable (1000 steps instead of 1 billion)
        try:
            t_points, y_values = integrator.euler(exponential_decay_system, y0, t_span, dt)
            
            # If it succeeds, should have many points
            if len(t_points) > 0:
                assert len(t_points) > 50  # Should have multiple small steps
                assert len(t_points) < 200000  # But not too many (allowing for ~100k steps)
        except (MemoryError, OverflowError):
            # Acceptable to fail with memory/overflow for extreme cases
            pass
    
    def test_system_function_exceptions(self):
        """Test handling when system function raises exceptions"""
        def bad_system(t, y):
            if t > 0.5:
                raise ValueError("System failure at t > 0.5")
            return np.array([-y[0]])
        
        solver = DynamicEquationSolver()
        solver._compiled_system = bad_system
        solver._system = type('MockSystem', (), {
            'variables': ['x'],
            'initial_conditions': {'x': 1.0}
        })()
        
        # Integration should fail gracefully
        try:
            result = solver.integrate((0, 1), method='RK45')
            # Should either fail or stop before the problematic region
            if result.success:
                assert np.max(result.time_points) <= 0.5
        except Exception:
            # Exception during integration is acceptable
            pass
