#!/usr/bin/env python3
"""
Demonstration of Improved Testing Patterns for Phase 3

This file showcases the improved testing patterns implemented:
- Standardized tolerances
- Centralized test parameters  
- Validation helper functions
- Parametrized tests
- Enhanced error messages
- Performance testing
"""

import pytest
import numpy as np
import sys
import os

# Add the parent directory to sys.path to import text_to_solver
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from text_to_solver.dynamic_solver import (
    DynamicEquationSolver,
    solve_ode_system
)


# ================================================================
# IMPROVED TESTING PATTERN DEMONSTRATIONS
# ================================================================

@pytest.mark.dynamic
@pytest.mark.improved_patterns
class TestStandardizedPatterns:
    """Demonstrate improved testing patterns for dynamic systems"""
    
    def test_standardized_tolerances_example(self, simple_exponential_solver, tolerances):
        """Demonstrate standardized tolerance usage"""
        solver = simple_exponential_solver
        result = solver.integrate(time_span=(0, 1), method='RK45')
        
        assert result.success, f"Integration failed: {result.message}"
        
        # Use appropriate tolerance for each comparison type
        initial_condition = result.initial_values['x']
        assert abs(initial_condition - 1.0) < tolerances.EXACT, (
            f"Initial condition should be exact: expected 1.0, got {initial_condition}"
        )
        
        # Numerical integration comparison uses integration tolerance
        expected = np.exp(-0.5 * 1.0)  # Analytical solution
        actual = result.final_values['x']
        error = abs(actual - expected)
        
        assert error < tolerances.INTEGRATION, (
            f"Integration accuracy insufficient: "
            f"error {error:.2e} exceeds tolerance {tolerances.INTEGRATION:.2e}"
        )
    
    def test_centralized_parameters_example(self, system_params, tolerances):
        """Demonstrate centralized parameter usage"""
        # Use standardized parameters
        params = system_params.EXPONENTIAL_DECAY
        
        solver = DynamicEquationSolver()
        solver.set_system(**{k: v for k, v in params.items() 
                            if k not in ['description']})
        
        result = solver.integrate(time_span=(0, 1.5), method='RK45')
        assert result.success
        
        # Use analytical solution from parameters class
        expected = system_params.exponential_analytical_solution(1.5)
        actual = result.final_values['x']
        
        assert abs(actual - expected) < tolerances.INTEGRATION
    
    def test_validation_helpers_example(self, harmonic_oscillator_solver, 
                                       system_params, validators, tolerances):
        """Demonstrate validation helper usage"""
        solver = harmonic_oscillator_solver
        result = solver.integrate(time_span=(0, 4*np.pi), method='RK45')
        
        assert result.success
        
        # Use conservation validation helper
        x_vals = result['x']
        v_vals = result['v']
        energy = system_params.harmonic_energy(x_vals, v_vals)
        
        validators.validate_conservation(
            energy,
            tolerance=tolerances.PHYSICAL,
            description="harmonic oscillator energy"
        )
        
        # Use periodicity validation helper
        validators.validate_periodicity(
            result.time_points, x_vals,
            expected_period=2*np.pi,
            tolerance=0.1,
            description="oscillator position"
        )
    
    @pytest.mark.parametrize("system_name,time_span", [
        ('EXPONENTIAL_DECAY', (0, 2)),
        ('LINEAR_FORCED', (0, 3)),
    ])
    def test_parametrized_systems_example(self, system_name, time_span, 
                                         system_params, tolerances):
        """Demonstrate parametrized testing"""
        # Get system parameters by name
        params = getattr(system_params, system_name)
        
        solver = DynamicEquationSolver()
        solver.set_system(**{k: v for k, v in params.items() 
                            if k not in ['description']})
        
        result = solver.integrate(time_span=time_span, method='RK45')
        
        assert result.success, (
            f"{system_name} integration failed: {result.message}"
        )
        
        # Verify basic properties
        assert len(result.time_points) > 10, "Insufficient time points"
        assert all(var in result.variables for var in params['variables']), (
            "Missing variables in result"
        )
    
    def test_enhanced_error_messages_example(self, tolerances):
        """Demonstrate enhanced error message patterns"""
        solver = DynamicEquationSolver()
        
        # Test with invalid system setup
        with pytest.raises(Exception) as exc_info:
            solver.set_system(
                variables=['x', 'y'],
                equations=['dx/dt = -x'],  # Missing equation for y
                initial_conditions={'x': 1.0, 'y': 2.0}
            )
        
        # The error should be informative (we don't assert on exact message
        # since different implementations may have different error messages)
        assert str(exc_info.value), "Exception should have a descriptive message"
    
    def test_performance_validation_example(self, performance_timer, performance_limits):
        """Demonstrate performance testing patterns"""
        
        # Test solver creation performance
        with performance_timer() as get_creation_time:
            solver = DynamicEquationSolver()
            solver.set_system(
                variables=['x', 'y'],
                equations=['dx/dt = -x', 'dy/dt = -y'],
                initial_conditions={'x': 1.0, 'y': 1.0}
            )
        
        creation_time = get_creation_time()
        assert creation_time < performance_limits.MAX_SOLVER_CREATION_TIME, (
            f"Solver creation too slow: {creation_time:.3f}s exceeds "
            f"limit of {performance_limits.MAX_SOLVER_CREATION_TIME}s"
        )
        
        # Test integration performance
        with performance_timer() as get_integration_time:
            result = solver.integrate((0, 1), method='RK45')
        
        integration_time = get_integration_time()
        assert integration_time < performance_limits.MAX_SMALL_INTEGRATION_TIME, (
            f"Small integration too slow: {integration_time:.3f}s exceeds "
            f"limit of {performance_limits.MAX_SMALL_INTEGRATION_TIME}s"
        )
        
        assert result.success, "Integration should succeed"


# ================================================================
# CONVENIENCE FUNCTION TESTING WITH IMPROVED PATTERNS
# ================================================================

@pytest.mark.dynamic
@pytest.mark.convenience  
@pytest.mark.improved_patterns
class TestConvenienceWithStandardizedPatterns:
    """Test convenience functions with improved patterns"""
    
    @pytest.mark.parametrize("method,tolerance", [
        ('RK45', 1e-6),
        ('DOP853', 1e-8),
    ])
    def test_solve_ode_system_accuracy(self, method, tolerance, 
                                      system_params, validators):
        """Test solve_ode_system with different methods"""
        params = system_params.EXPONENTIAL_DECAY
        
        result = solve_ode_system(
            variables=params['variables'],
            equations=params['equations'],
            parameters=params['parameters'],
            initial_conditions=params['initial_conditions'],
            time_span=(0, 2),
            method=method
        )
        
        assert result.success, f"{method} failed: {result.message}"
        
        # Validate accuracy
        expected = system_params.exponential_analytical_solution(2.0)
        actual = result.final_values['x']
        
        validators.validate_integration_accuracy(
            actual, expected,
            method=f"solve_ode_system with {method}",
            tolerance=tolerance
        )
    
    def test_predator_prey_general_solver_with_validation(self, validators, tolerances):
        """Test predator-prey using general-purpose solver with validation"""
        from text_to_solver.dynamic_solver import DynamicEquationSolver
        
        solver = DynamicEquationSolver()
        solver.set_system(
            variables=['x', 'y'],
            equations=[
                'dx/dt = alpha*x - beta*x*y',  # Prey growth - predation
                'dy/dt = delta*x*y - gamma*y'  # Predator growth from hunting - death
            ],
            parameters={'alpha': 1.0, 'beta': 0.1, 'delta': 0.075, 'gamma': 1.5},
            initial_conditions={'x': 10, 'y': 5}
        )
        result = solver.integrate(time_span=(0, 15), method='RK45')
        
        assert result.success, f"Predator-prey failed: {result.message}"
        
        # Validate oscillatory behavior  
        prey_values = result['x']
        pred_values = result['y']
        
        # Both populations should oscillate significantly
        prey_range = np.max(prey_values) - np.min(prey_values)
        pred_range = np.max(pred_values) - np.min(pred_values)
        
        assert prey_range > 5.0, (
            f"Prey oscillation insufficient: range {prey_range:.2f} < 5.0"
        )
        assert pred_range > 2.0, (
            f"Predator oscillation insufficient: range {pred_range:.2f} < 2.0"
        )
        
        # Both populations should remain positive
        assert np.all(prey_values > 0), "Prey population went negative"
        assert np.all(pred_values > 0), "Predator population went negative"


# ================================================================
# ERROR HANDLING WITH IMPROVED PATTERNS  
# ================================================================

@pytest.mark.dynamic
@pytest.mark.error_handling
@pytest.mark.improved_patterns
class TestErrorHandlingStandardized:
    """Test error handling with improved validation patterns"""
    
    def test_dimension_mismatch_with_context(self):
        """Test dimension mismatch errors with descriptive context"""
        solver = DynamicEquationSolver()
        
        with pytest.raises(Exception) as exc_info:
            solver.set_system(
                variables=['x', 'y'],  # Two variables
                equations=['dx/dt = -x'],  # One equation
                initial_conditions={'x': 1.0, 'y': 2.0}
            )
        
        # Verify error provides useful context
        error_message = str(exc_info.value).lower()
        assert any(word in error_message for word in ['dimension', 'mismatch', 'equation', 'variable']), (
            f"Error message should mention dimension mismatch: {exc_info.value}"
        )
    
    def test_missing_initial_conditions_with_context(self):
        """Test missing initial conditions with descriptive context"""
        solver = DynamicEquationSolver()
        
        with pytest.raises(Exception) as exc_info:
            solver.set_system(
                variables=['x', 'y'],
                equations=['dx/dt = -x', 'dy/dt = -y'],
                initial_conditions={'x': 1.0}  # Missing 'y'
            )
        
        # Verify error mentions missing initial condition
        error_message = str(exc_info.value).lower()
        assert any(word in error_message for word in ['initial', 'condition', 'missing', 'y']), (
            f"Error message should mention missing initial condition: {exc_info.value}"
        )
    
    def test_invalid_integration_graceful_failure(self, tolerances):
        """Test that invalid integration attempts fail gracefully"""
        solver = DynamicEquationSolver()
        
        # Try to integrate without setting system
        result = solver.integrate((0, 1))
        
        # Should fail gracefully, not crash
        assert not result.success, "Integration without system should fail"
        assert result.message, "Failed result should have descriptive message"
        assert isinstance(result.message, str), "Message should be a string"
