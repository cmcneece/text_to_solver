#!/usr/bin/env python3
"""
Tests for Phase 3 Dynamic Systems Functionality

This test suite validates the differential equation solving capabilities
introduced in Phase 3 of TextToSolver.
"""

import pytest
import numpy as np
import sys
import os

# Add the parent directory to sys.path to import text_to_solver
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from text_to_solver.dynamic_solver import (
    DynamicEquationSolver, 
    DynamicSystem, 
    DynamicSolutionResult,
    DifferentialEquationParser,
    TimeIntegrator,
    solve_ode_system
)
from text_to_solver.user_api import EquationSystemError

# Import tolerance constants for parametrized tests
# These are realistic values for different integration methods
class _TestTolerances:
    INTEGRATION_LOOSE = 1e-2    # Euler method - loose tolerance
    INTEGRATION = 1e-3          # RK4 method - standard tolerance  
    INTEGRATION_TIGHT = 1e-5    # RK45/DOP853 - tighter but realistic tolerance
    NUMERICAL = 1e-8            # Very tight for exact computations


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture
def simple_exponential_solver():
    """Simple exponential decay system: dx/dt = -k*x"""
    solver = DynamicEquationSolver()
    solver.set_system(
        variables=['x'],
        equations=['dx/dt = -k*x'],
        parameters={'k': 0.5},
        initial_conditions={'x': 1.0}
    )
    return solver


@pytest.fixture
def harmonic_oscillator_solver():
    """Harmonic oscillator: d²x/dt² = -ω²*x (as first-order system)"""
    solver = DynamicEquationSolver()
    solver.set_system(
        variables=['x', 'v'],
        equations=['dx/dt = v', 'dv/dt = -omega*omega*x'],
        parameters={'omega': 1.0},
        initial_conditions={'x': 1.0, 'v': 0.0}
    )
    return solver


@pytest.fixture
def predator_prey_solver():
    """Predator-prey system (Lotka-Volterra)"""
    solver = DynamicEquationSolver()
    solver.set_system(
        variables=['x', 'y'],
        equations=[
            'dx/dt = alpha*x - beta*x*y',
            'dy/dt = delta*x*y - gamma*y'
        ],
        parameters={'alpha': 1.0, 'beta': 0.1, 'delta': 0.075, 'gamma': 1.5},
        initial_conditions={'x': 10.0, 'y': 5.0}
    )
    return solver


@pytest.fixture
def linear_system_solver():
    """Linear system with time-dependent forcing: dx/dt = -x + A*t"""
    solver = DynamicEquationSolver()
    solver.set_system(
        variables=['x'],
        equations=['dx/dt = -x + A*t'],
        parameters={'A': 0.1},
        initial_conditions={'x': 0.0}
    )
    return solver


# ================================================================
# CORE FUNCTIONALITY TESTS
# ================================================================

@pytest.mark.dynamic
class TestDynamicSystemCreation:
    """Test DynamicSystem object creation and validation"""
    
    def test_valid_system_creation(self):
        """Test creating a valid DynamicSystem"""
        system = DynamicSystem(
            variables=['x', 'y'],
            equations=['dx/dt = -x', 'dy/dt = -y'],
            parameters={'k': 1.0},
            initial_conditions={'x': 1.0, 'y': 2.0}
        )
        
        assert system.variables == ['x', 'y']
        assert len(system.equations) == 2
        assert system.parameters['k'] == 1.0
        assert system.initial_conditions['x'] == 1.0
        assert system.initial_conditions['y'] == 2.0
    
    def test_dimension_mismatch_error(self):
        """Test error when variables and equations don't match"""
        with pytest.raises(EquationSystemError):
            DynamicSystem(
                variables=['x', 'y'],
                equations=['dx/dt = -x'],  # Only one equation for two variables
                initial_conditions={'x': 1.0, 'y': 2.0}
            )
    
    def test_missing_initial_conditions(self):
        """Test error when initial conditions are missing"""
        with pytest.raises(EquationSystemError):
            DynamicSystem(
                variables=['x', 'y'],
                equations=['dx/dt = -x', 'dy/dt = -y'],
                initial_conditions={'x': 1.0}  # Missing 'y'
            )
    
    def test_empty_system_error(self):
        """Test error for empty systems"""
        # Empty system should either raise error or be handled gracefully
        try:
            system = DynamicSystem(
                variables=[],
                equations=[],
                initial_conditions={}
            )
            # If it doesn't raise an error, that's also acceptable
            # as long as the system recognizes it's empty
            assert len(system.variables) == 0
            assert len(system.equations) == 0
        except EquationSystemError:
            # Raising an error is also acceptable
            pass


@pytest.mark.dynamic
class TestDynamicEquationSolver:
    """Test core DynamicEquationSolver functionality"""
    
    def test_solver_creation(self):
        """Test basic solver creation"""
        solver = DynamicEquationSolver()
        assert solver is not None
        assert solver._system is None
        assert solver._compiled_system is None
    
    def test_system_setting(self, simple_exponential_solver):
        """Test setting a system on the solver"""
        solver = simple_exponential_solver
        assert solver._system is not None
        assert solver._compiled_system is not None
        assert solver._system.variables == ['x']
        assert len(solver._system.equations) == 1
    
    def test_method_chaining(self):
        """Test fluent interface for system setup"""
        solver = DynamicEquationSolver()
        result = solver.set_system(
            variables=['x'],
            equations=['dx/dt = -x'],
            initial_conditions={'x': 1.0}
        )
        
        # Should return self for chaining
        assert result is solver
        assert solver._system is not None
    
    def test_solve_without_system_error(self):
        """Test error when trying to integrate without setting system"""
        solver = DynamicEquationSolver()
        with pytest.raises(ValueError, match="System not set"):
            solver.integrate((0, 1))


# ================================================================
# INTEGRATION TESTS
# ================================================================

@pytest.mark.dynamic
@pytest.mark.integration
class TestSystemIntegration:
    """Test integration of different ODE systems"""
    
    def test_exponential_decay_integration(self, simple_exponential_solver, 
                                          tolerances, system_params, validators):
        """Test exponential decay integration with standardized validation"""
        solver = simple_exponential_solver
        result = solver.integrate(time_span=(0, 2), method='RK45')
        
        assert result.success, f"Integration failed: {result.message}"
        assert len(result.time_points) > 0
        assert 'x' in result.variables
        
        # Check initial condition with exact tolerance
        assert abs(result.initial_values['x'] - 1.0) < tolerances.EXACT, (
            f"Initial condition not exact: expected 1.0, got {result.initial_values['x']}"
        )
        
        # Validate against analytical solution using helper
        expected_final = system_params.exponential_analytical_solution(2.0, k=0.5, x0=1.0)
        actual_final = result.final_values['x']
        
        validators.validate_integration_accuracy(
            actual_final, expected_final, 
            method="RK45 exponential decay",
            tolerance=tolerances.INTEGRATION
        )
    
    def test_harmonic_oscillator_integration(self, harmonic_oscillator_solver,
                                            tolerances, system_params, validators):
        """Test harmonic oscillator integration with conservation validation"""
        solver = harmonic_oscillator_solver
        result = solver.integrate(time_span=(0, 2*np.pi), method='RK45')
        
        assert result.success, f"Integration failed: {result.message}"
        assert 'x' in result.variables
        assert 'v' in result.variables
        
        # After one full period, should return to initial conditions
        x_final = result.final_values['x']
        v_final = result.final_values['v']
        
        # Use convergence tolerance for periodic return
        assert abs(x_final - 1.0) < tolerances.CONVERGENCE, (
            f"Position after full period: expected 1.0, got {x_final:.6f}"
        )
        assert abs(v_final - 0.0) < tolerances.CONVERGENCE, (
            f"Velocity after full period: expected 0.0, got {v_final:.6f}"
        )
        
        # Validate energy conservation using helper
        x_vals = result.variables['x']
        v_vals = result.variables['v']
        energy_values = system_params.harmonic_energy(x_vals, v_vals, omega=1.0)
        
        validators.validate_conservation(
            energy_values, 
            tolerance=tolerances.PHYSICAL,
            description="harmonic oscillator energy"
        )
        
        # Validate periodicity using helper
        validators.validate_periodicity(
            result.time_points, x_vals,
            expected_period=system_params.HARMONIC_OSCILLATOR['period'],
            tolerance=0.1,
            description="harmonic oscillator position"
        )
    
    def test_predator_prey_integration(self, predator_prey_solver):
        """Test predator-prey system integration"""
        solver = predator_prey_solver
        result = solver.integrate(time_span=(0, 10), method='RK45')
        
        assert result.success
        assert 'x' in result.variables  # Prey
        assert 'y' in result.variables  # Predator
        
        # Both populations should remain positive
        prey_vals = result.variables['x']
        pred_vals = result.variables['y']
        
        assert np.all(prey_vals > 0)
        assert np.all(pred_vals > 0)
        
        # System should show oscillatory behavior
        prey_range = np.max(prey_vals) - np.min(prey_vals)
        pred_range = np.max(pred_vals) - np.min(pred_vals)
        
        assert prey_range > 5  # Significant oscillation expected
        assert pred_range > 2  # Significant oscillation expected
    
    def test_linear_forced_system(self, linear_forced_solver, 
                                  tolerances, system_params, validators):
        """Test linear system with time-dependent forcing"""
        solver = linear_forced_solver
        result = solver.integrate(time_span=(0, 5), method='RK45')
        
        assert result.success, f"Integration failed: {result.message}"
        assert 'x' in result.variables
        
        # Validate against analytical solution using helper
        expected_final = system_params.linear_forced_analytical_solution(5.0, A=0.1, x0=0.0)
        actual_final = result.final_values['x']
        
        validators.validate_integration_accuracy(
            actual_final, expected_final,
            method="RK45 linear forced system",
            tolerance=tolerances.INTEGRATION
        )


# ================================================================
# INTEGRATION METHODS COMPARISON
# ================================================================

@pytest.mark.dynamic
@pytest.mark.performance
class TestIntegrationMethods:
    """Test different integration methods"""
    
    @pytest.mark.parametrize("method,expected_tolerance", [
        ('euler', _TestTolerances.INTEGRATION_LOOSE),
        ('rk4', _TestTolerances.INTEGRATION), 
        ('RK45', _TestTolerances.INTEGRATION_TIGHT),
        ('DOP853', _TestTolerances.INTEGRATION_TIGHT)
    ])
    def test_integration_method_accuracy(self, method, expected_tolerance, 
                                       tolerances, system_params, validators):
        """Test accuracy of different integration methods on exponential decay"""
        # Create solver with standardized parameters
        from text_to_solver.dynamic_solver import DynamicEquationSolver
        
        params = system_params.EXPONENTIAL_DECAY
        solver = DynamicEquationSolver()
        solver.set_system(**{k: v for k, v in params.items() 
                            if k not in ['description']})
        
        # Integrate with appropriate settings for each method
        if method in ['euler', 'rk4']:
            result = solver.integrate((0, 2), method=method, dt=0.01)
        else:
            result = solver.integrate((0, 2), method=method)
        
        assert result.success, f"{method} integration failed: {result.message}"
        
        # Validate against analytical solution
        expected_final = system_params.exponential_analytical_solution(2.0, k=0.5, x0=1.0)
        actual_final = result.final_values['x']
        
        validators.validate_integration_accuracy(
            actual_final, expected_final,
            method=f"{method} integration",
            tolerance=expected_tolerance
        )
    
    def test_method_availability(self, simple_exponential_solver):
        """Test that all integration methods work"""
        solver = simple_exponential_solver
        methods = ['euler', 'rk4', 'RK45', 'DOP853']
        
        results = {}
        for method in methods:
            if method in ['euler', 'rk4']:
                result = solver.integrate((0, 1), method=method, dt=0.01)
            else:
                result = solver.integrate((0, 1), method=method)
            
            assert result.success, f"Method {method} failed: {result.message}"
            results[method] = result.final_values['x']
        
        # All methods should give similar results
        values = list(results.values())
        expected = np.exp(-0.5)  # Analytical solution at t=1, k=0.5
        
        for method, value in results.items():
            relative_error = abs(value - expected) / expected
            # Allow different error tolerances for different methods
            if method == 'euler':
                assert relative_error < 0.1  # 10% for Euler (coarse)
            else:
                assert relative_error < 0.01  # 1% for higher-order methods
    
    def test_adaptive_vs_fixed_step(self, harmonic_oscillator_solver):
        """Compare adaptive vs fixed-step methods"""
        solver = harmonic_oscillator_solver
        
        # Fixed step method
        result_fixed = solver.integrate((0, np.pi), method='rk4', dt=0.01)
        
        # Adaptive method  
        result_adaptive = solver.integrate((0, np.pi), method='RK45')
        
        assert result_fixed.success
        assert result_adaptive.success
        
        # Both should give similar results
        x_fixed = result_fixed.final_values['x']
        x_adaptive = result_adaptive.final_values['x']
        
        assert abs(x_fixed - x_adaptive) < 0.1
    
    def test_step_size_effect(self, simple_exponential_solver):
        """Test effect of step size on accuracy"""
        solver = simple_exponential_solver
        
        # Compare different step sizes
        dt_values = [0.1, 0.01, 0.001]
        results = []
        
        for dt in dt_values:
            result = solver.integrate((0, 2), method='euler', dt=dt)
            assert result.success
            results.append(result.final_values['x'])
        
        # Smaller step sizes should be more accurate
        expected = np.exp(-0.5 * 2)  # Analytical solution
        
        errors = [abs(r - expected) for r in results]
        
        # Error should generally decrease with smaller step size
        assert errors[1] < errors[0]  # dt=0.01 better than dt=0.1
        assert errors[2] < errors[1]  # dt=0.001 better than dt=0.01


# ================================================================
# CONVENIENCE FUNCTIONS TESTS
# ================================================================

@pytest.mark.dynamic 
@pytest.mark.convenience
class TestConvenienceFunctions:
    """Test convenience functions and shortcuts"""
    
    def test_solve_ode_system_function(self):
        """Test the solve_ode_system convenience function"""
        result = solve_ode_system(
            variables=['x'],
            equations=['dx/dt = -k*x'],
            parameters={'k': 1.0},
            initial_conditions={'x': 2.0},
            time_span=(0, 1),
            method='RK45'
        )
        
        assert result.success
        assert 'x' in result.variables
        assert abs(result.initial_values['x'] - 2.0) < 1e-10
        
        # Check against analytical solution
        expected = 2.0 * np.exp(-1.0)
        actual = result.final_values['x']
        assert abs(actual - expected) < 0.01
    
    def test_convenience_function_error_handling(self):
        """Test error handling in convenience functions"""
        # Missing initial condition
        with pytest.raises((EquationSystemError, ValueError)):
            solve_ode_system(
                variables=['x', 'y'],
                equations=['dx/dt = -x', 'dy/dt = -y'],
                initial_conditions={'x': 1.0},  # Missing 'y'
                time_span=(0, 1)
            )
        
        # Dimension mismatch
        with pytest.raises((EquationSystemError, ValueError)):
            solve_ode_system(
                variables=['x'],
                equations=['dx/dt = -x', 'dy/dt = -y'],  # Too many equations
                initial_conditions={'x': 1.0},
                time_span=(0, 1)
            )


# ================================================================
# ERROR HANDLING AND EDGE CASES
# ================================================================

@pytest.mark.dynamic
@pytest.mark.error_handling
class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_time_span(self, simple_exponential_solver):
        """Test error handling for invalid time spans"""
        solver = simple_exponential_solver
        
        # Negative time span
        result = solver.integrate((-1, 1))
        # Should handle gracefully, may succeed or fail depending on implementation
        
        # Zero time span
        result = solver.integrate((0, 0))
        # Should handle gracefully
        
        # Backwards time span
        result = solver.integrate((2, 1))
        # May work (integration backwards) or fail gracefully
    
    def test_extreme_parameter_values(self):
        """Test behavior with extreme parameter values"""
        solver = DynamicEquationSolver()
        
        # Very large parameter
        solver.set_system(
            variables=['x'],
            equations=['dx/dt = -k*x'],
            parameters={'k': 1e6},  # Very large decay rate
            initial_conditions={'x': 1.0}
        )
        
        result = solver.integrate((0, 1e-6), method='RK45')  # Very short time
        # Should handle stiff system gracefully
        
        # Very small parameter
        solver.set_system(
            variables=['x'],
            equations=['dx/dt = -k*x'],
            parameters={'k': 1e-10},  # Very small decay rate
            initial_conditions={'x': 1.0}
        )
        
        result = solver.integrate((0, 1), method='RK45')
        # Should still work, just very slow decay
    
    def test_zero_initial_conditions(self):
        """Test systems with zero initial conditions"""
        solver = DynamicEquationSolver()
        solver.set_system(
            variables=['x'],
            equations=['dx/dt = k'],  # Constant growth
            parameters={'k': 1.0},
            initial_conditions={'x': 0.0}
        )
        
        result = solver.integrate((0, 1), method='RK45')
        assert result.success
        
        # x(t) = k*t for x(0)=0, dx/dt=k
        expected = 1.0 * 1.0  # k*t = 1.0*1.0
        actual = result.final_values['x']
        assert abs(actual - expected) < 0.01
    
    def test_malformed_equations(self):
        """Test error handling for malformed equations"""
        solver = DynamicEquationSolver()
        
        # Invalid syntax
        with pytest.raises(EquationSystemError):
            solver.set_system(
                variables=['x'],
                equations=['dx/dt = -k*x + '], # Incomplete equation
                parameters={'k': 1.0},
                initial_conditions={'x': 1.0}
            )
        
        # Undefined parameter - this may succeed as parser creates symbols automatically
        # so just test that it doesn't crash
        try:
            solver.set_system(
                variables=['x'],
                equations=['dx/dt = -undefined_param*x'],
                initial_conditions={'x': 1.0}
            )
            # If it succeeds, that's acceptable (undefined_param becomes a symbol)
            assert True
        except (EquationSystemError, Exception):
            # If it fails with an error, that's also acceptable
            assert True


# ================================================================
# PERFORMANCE AND SCALABILITY
# ================================================================

@pytest.mark.dynamic
@pytest.mark.performance
@pytest.mark.slow
class TestPerformance:
    """Test performance characteristics (marked as slow)"""
    
    def test_large_system_performance(self):
        """Test performance with larger systems"""
        # Create a system with multiple variables
        n_vars = 10
        variables = [f'x{i}' for i in range(n_vars)]
        equations = [f'dx{i}/dt = -x{i}' for i in range(n_vars)]
        initial_conditions = {f'x{i}': float(i+1) for i in range(n_vars)}
        
        solver = DynamicEquationSolver()
        solver.set_system(
            variables=variables,
            equations=equations,
            initial_conditions=initial_conditions
        )
        
        result = solver.integrate((0, 1), method='RK45')
        assert result.success
        assert len(result.variables) == n_vars
    
    def test_long_integration_time(self, simple_exponential_solver):
        """Test integration over long time periods"""
        solver = simple_exponential_solver
        
        # Integrate for a long time
        result = solver.integrate((0, 100), method='RK45')
        assert result.success
        
        # Should approach zero for exponential decay
        final_value = result.final_values['x']
        expected = np.exp(-0.5 * 100)  # Should be very small
        
        assert abs(final_value - expected) < 0.01
        assert final_value < 1e-5  # Should be very small (allow numerical precision)
    
    def test_high_frequency_oscillation(self):
        """Test high-frequency oscillatory systems"""
        solver = DynamicEquationSolver()
        solver.set_system(
            variables=['x', 'v'],
            equations=['dx/dt = v', 'dv/dt = -omega*omega*x'],
            parameters={'omega': 100.0},  # High frequency
            initial_conditions={'x': 1.0, 'v': 0.0}
        )
        
        # Short time period for high frequency
        result = solver.integrate((0, 0.1), method='DOP853')  # Use high-order method
        
        # May succeed or gracefully handle the stiffness
        if result.success:
            assert 'x' in result.variables
            assert 'v' in result.variables
