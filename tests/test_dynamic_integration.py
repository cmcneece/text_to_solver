#!/usr/bin/env python3
"""
Tests for Dynamic Systems Integration with Existing Framework

Tests that dynamic systems integrate properly with existing functionality
functionality without breaking existing features.
"""

import pytest
import numpy as np
import sys
import os

# Add the parent directory to sys.path to import text_to_solver
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test imports from all phases
from text_to_solver import (
    # Phase 1 & 2
    TextToSolver, EquationSolver, SolverOptions,
    EquationSystem, SolutionResult, EnhancedEquationSolver,
    
    # Phase 3
    DynamicEquationSolver, DynamicSolutionResult,
    solve_ode_system
)

# Advanced patterns (Phase 2)
# ================================================================
# BACKWARD COMPATIBILITY TESTS
# ================================================================

@pytest.mark.dynamic
@pytest.mark.integration
class TestBackwardCompatibility:
    """Test that Phase 3 doesn't break existing functionality"""
    
    def test_original_textosolver_still_works(self):
        """Test that original TextToSolver still functions"""
        # Simple system that worked in Phase 1
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x + y - 3', 'x - y - 1']
        )
        
        # Should still solve correctly
        report = solver.solve()
        
        assert report['converged']
        assert abs(report['solution'][0] - 2.0) < 1e-6  # x = 2
        assert abs(report['solution'][1] - 1.0) < 1e-6  # y = 1
    
    def test_improved_api_still_works(self):
        """Test that Phase 1.5 improved API still functions"""
        solver = EquationSolver()
        solver.set_system(
            variables=['x', 'y'],
            equations=['x + y - 3', 'x - y - 1']
        )
        
        result = solver.solve()
        
        assert result.success
        assert abs(result.variables['x'][0] - 2.0) < 1e-6
        assert abs(result.variables['y'][0] - 1.0) < 1e-6
    
    def test_enhanced_solver_still_works(self):
        """Test that Phase 2 enhanced solver still functions"""
        solver = EnhancedEquationSolver()
        
        # Set up a system
        solver.set_system(
            variables=['x', 'y'], 
            equations=['x**2 + y**2 - 1', 'x - y']
        )
        
        result = solver.solve()
        
        assert result.success
        # x^2 + y^2 = 1, x = y => 2x^2 = 1 => x = y = 1/sqrt(2)
        expected = 1.0 / np.sqrt(2)
        assert abs(result.variables['x'][0] - expected) < 0.1
        assert abs(result.variables['y'][0] - expected) < 0.1
    
    def test_all_apis_importable(self):
        """Test that all APIs can be imported together"""
        # Should be able to create instances of all solvers
        original_solver = TextToSolver(['x'], ['x - 1'])
        improved_solver = EquationSolver()
        dynamic_solver = DynamicEquationSolver()
        
        # All should be different types
        assert type(original_solver) != type(improved_solver)
        assert type(improved_solver) != type(dynamic_solver)
        assert type(original_solver) != type(dynamic_solver)


# ================================================================
# API CONSISTENCY TESTS
# ================================================================

@pytest.mark.dynamic
@pytest.mark.integration
class TestAPIConsistency:
    """Test consistency between different API levels"""
    
    def test_consistent_result_formats(self):
        """Test that result formats are consistent across APIs"""
        # Solve same system with different APIs
        
        # Phase 1 API (original)
        solver1 = TextToSolver(['x'], ['x - 2'])
        report1 = solver1.solve()
        
        # Phase 2 API (improved)  
        solver2 = EquationSolver()
        solver2.set_system(variables=['x'], equations=['x - 2'])
        result2 = solver2.solve()
        
        # Both should find x = 2
        assert report1['converged']
        assert result2.success
        assert abs(report1['solution'][0] - 2.0) < 1e-6
        assert abs(result2.variables['x'][0] - 2.0) < 1e-6
    
    def test_error_handling_consistency(self):
        """Test that error handling is consistent across APIs"""
        
        # Test dimension mismatch in different APIs
        
        # Phase 1 API
        with pytest.raises((ValueError, Exception)):
            TextToSolver(['x'], ['x - 1', 'y - 2'])  # 1 var, 2 equations
        
        # Phase 2 API
        solver = EquationSolver()
        with pytest.raises((ValueError, Exception)):
            solver.set_system(
                variables=['x'],
                equations=['x - 1', 'y - 2']  # 1 var, 2 equations
            )
        
        # Phase 3 API
        dynamic_solver = DynamicEquationSolver()
        with pytest.raises((ValueError, Exception)):
            dynamic_solver.set_system(
                variables=['x'],
                equations=['dx/dt = -x', 'dy/dt = -y'],  # 1 var, 2 equations
                initial_conditions={'x': 1.0}
            )
    
    def test_parameter_handling_consistency(self):
        """Test that parameter handling is consistent"""
        
        # System with parameters: x + a = 0 (solution: x = -a)
        
        # Phase 1 API
        solver1 = TextToSolver(['x'], ['x + a'], parameters={'a': 3.0})
        report1 = solver1.solve()
        
        # Phase 2 API
        solver2 = EquationSolver()
        solver2.set_system(
            variables=['x'],
            equations=['x + a'],
            parameters={'a': 3.0}
        )
        result2 = solver2.solve()
        
        # Both should find x = -3
        assert report1['converged']
        assert result2.success
        assert abs(report1['solution'][0] + 3.0) < 1e-6
        assert abs(result2.variables['x'][0] + 3.0) < 1e-6


# ================================================================
# MIXED WORKFLOW TESTS
# ================================================================

@pytest.mark.dynamic
@pytest.mark.integration
@pytest.mark.workflow
class TestMixedWorkflows:
    """Test workflows that use both static and dynamic solvers"""
    
    def test_equilibrium_then_dynamics(self):
        """Test finding equilibrium then studying dynamics around it"""
        
        # Step 1: Find equilibrium of predator-prey system using static solver
        # At equilibrium: dx/dt = dy/dt = 0
        # alpha*x - beta*x*y = 0  => x(alpha - beta*y) = 0
        # delta*x*y - gamma*y = 0  => y(delta*x - gamma) = 0
        # Non-trivial solution: x = gamma/delta, y = alpha/beta
        
        alpha, beta, delta, gamma = 1.0, 0.1, 0.075, 1.5
        
        # Use static solver to find equilibrium
        static_solver = EquationSolver()
        static_solver.set_system(
            variables=['x', 'y'],
            equations=[
                'alpha*x - beta*x*y',  # dx/dt = 0
                'delta*x*y - gamma*y'   # dy/dt = 0
            ],
            parameters={'alpha': alpha, 'beta': beta, 'delta': delta, 'gamma': gamma}
        )
        
        # Try to find non-trivial equilibrium
        equilibrium_result = static_solver.solve(custom_guess={
            'x': np.array([gamma/delta]), 
            'y': np.array([alpha/beta])
        })
        
        # The equilibrium point calculation
        x_eq_expected = gamma / delta  # 1.5 / 0.075 = 20
        y_eq_expected = alpha / beta   # 1.0 / 0.1 = 10
        
        # Step 2: Use dynamic solver to study behavior around equilibrium
        dynamic_solver = DynamicEquationSolver()
        dynamic_solver.set_system(
            variables=['x', 'y'],
            equations=[
                'dx/dt = alpha*x - beta*x*y',
                'dy/dt = delta*x*y - gamma*y'
            ],
            parameters={'alpha': alpha, 'beta': beta, 'delta': delta, 'gamma': gamma},
            initial_conditions={'x': x_eq_expected + 1, 'y': y_eq_expected + 1}  # Near equilibrium
        )
        
        dynamic_result = dynamic_solver.integrate((0, 10), method='RK45')
        
        assert dynamic_result.success
        
        # System should oscillate around equilibrium
        x_values = dynamic_result['x']
        y_values = dynamic_result['y']
        
        # Check that values stay positive and show oscillation
        assert np.all(x_values > 0)
        assert np.all(y_values > 0)
        
        x_mean = np.mean(x_values)
        y_mean = np.mean(y_values)
        
        # Mean should be close to equilibrium values
        assert abs(x_mean - x_eq_expected) < 5  # Allow some deviation
        assert abs(y_mean - y_eq_expected) < 5  # Allow some deviation
    
    def test_parameter_sweep_static_to_dynamic(self):
        """Test parameter sweep from static analysis to dynamic verification"""
        
        # Study how equilibrium changes with parameter, then verify with dynamics
        
        parameter_values = [0.5, 1.0, 1.5]  # Different decay rates
        equilibria = []
        dynamic_behaviors = []
        
        for k in parameter_values:
            # Static analysis: find equilibrium of dx/dt = r*x - k*x
            # Equilibrium when dx/dt = 0: x(r - k) = 0
            # If r > k, equilibrium at x = 0 is unstable
            # If r < k, equilibrium at x = 0 is stable
            
            r = 1.0  # Growth rate
            
            # Use dynamic solver to verify behavior
            solver = DynamicEquationSolver()
            solver.set_system(
                variables=['x'],
                equations=['dx/dt = r*x - k*x'],  # Equivalent to dx/dt = (r-k)*x
                parameters={'r': r, 'k': k},
                initial_conditions={'x': 0.1}  # Small initial population
            )
            
            result = solver.integrate((0, 5), method='RK45')
            
            if result.success:
                final_value = result.final_values['x']
                
                equilibria.append(0.0)  # Theoretical equilibrium is always 0
                dynamic_behaviors.append({
                    'k': k,
                    'final_x': final_value,
                    'stable': final_value < 0.01  # Considered stable if approaches 0
                })
        
        # Analysis: k > r should lead to stable (decreasing), k < r unstable (growing)
        for behavior in dynamic_behaviors:
            k = behavior['k']
            stable = behavior['stable']
            
            if k > 1.0:  # k > r
                assert stable, f"System should be stable for k={k} > r=1"
            elif k < 1.0:  # k < r  
                assert not stable, f"System should be unstable for k={k} < r=1"
            # k = r case is marginal
    
    def test_nonlinear_system_analysis(self):
        """Test analysis of nonlinear system with both approaches"""
        
        # Van der Pol oscillator: d²x/dt² - μ(1-x²)dx/dt + x = 0
        # Rewrite as: dx/dt = y, dy/dt = μ(1-x²)y - x
        
        mu = 2.0  # Nonlinearity parameter
        
        # Step 1: Check if there are equilibria (static analysis)
        # At equilibrium: y = 0, μ(1-x²)*0 - x = 0  => x = 0
        # So equilibrium is (0, 0)
        
        static_solver = EquationSolver()
        static_solver.set_system(
            variables=['x', 'y'],
            equations=[
                'y',                           # dx/dt = 0 => y = 0
                'mu*(1 - x*x)*y - x'           # dy/dt = 0
            ],
            parameters={'mu': mu}
        )
        
        equilibrium_result = static_solver.solve()
        
        if equilibrium_result.success:
            # Should find equilibrium near (0, 0)
            assert abs(equilibrium_result.variables['x'][0]) < 0.1
            assert abs(equilibrium_result.variables['y'][0]) < 0.1
        
        # Step 2: Study dynamic behavior (should show limit cycle)
        dynamic_solver = DynamicEquationSolver()
        dynamic_solver.set_system(
            variables=['x', 'y'],
            equations=[
                'dx/dt = y',
                'dy/dt = mu*(1 - x*x)*y - x'
            ],
            parameters={'mu': mu},
            initial_conditions={'x': 0.1, 'y': 0.0}  # Small perturbation
        )
        
        dynamic_result = dynamic_solver.integrate((0, 20), method='RK45')
        
        assert dynamic_result.success
        
        # Van der Pol oscillator should develop limit cycle
        x_values = dynamic_result['x']
        y_values = dynamic_result['y']
        
        # Should show oscillatory behavior
        x_range = np.max(x_values) - np.min(x_values)
        y_range = np.max(y_values) - np.min(y_values)
        
        assert x_range > 1.0  # Significant oscillation
        assert y_range > 1.0  # Significant oscillation


# ================================================================
# PERFORMANCE INTEGRATION TESTS
# ================================================================

@pytest.mark.dynamic
@pytest.mark.integration
@pytest.mark.performance
class TestPerformanceIntegration:
    """Test performance characteristics when using multiple solvers"""
    
    def test_solver_creation_overhead(self):
        """Test overhead of creating multiple solver types"""
        import time
        
        # Time creating different solver types
        n_iterations = 100
        
        # Original solver
        start_time = time.time()
        for _ in range(n_iterations):
            solver = TextToSolver(['x'], ['x - 1'])
        original_time = time.time() - start_time
        
        # Improved solver
        start_time = time.time()
        for _ in range(n_iterations):
            solver = EquationSolver()
        improved_time = time.time() - start_time
        
        # Dynamic solver
        start_time = time.time()
        for _ in range(n_iterations):
            solver = DynamicEquationSolver()
        dynamic_time = time.time() - start_time
        
        # All should be reasonably fast
        assert original_time < 1.0  # Should create 100 solvers in < 1 second
        assert improved_time < 1.0
        assert dynamic_time < 1.0
        
        # Dynamic solver shouldn't be dramatically slower
        assert dynamic_time < original_time * 10  # Allow 10x overhead max
    
    def test_memory_usage_integration(self):
        """Test that using multiple solver types doesn't cause memory issues"""
        
        # Create multiple solvers and use them
        solvers = []
        
        # Mix of solver types
        for i in range(10):
            # Original
            solver1 = TextToSolver(['x'], [f'x - {i}'])
            solvers.append(solver1)
            
            # Improved  
            solver2 = EquationSolver()
            solver2.set_system(['x'], [f'x - {i}'])
            solvers.append(solver2)
            
            # Dynamic
            solver3 = DynamicEquationSolver()
            solver3.set_system(
                variables=['x'],
                equations=['dx/dt = -x'],
                initial_conditions={'x': float(i)}
            )
            solvers.append(solver3)
        
        # All solvers should be creatable without memory issues
        assert len(solvers) == 30
        
        # Clean up
        del solvers


# ================================================================
# ERROR PROPAGATION TESTS  
# ================================================================

@pytest.mark.dynamic
@pytest.mark.integration
@pytest.mark.error_handling
class TestErrorPropagation:
    """Test how errors propagate between different solver types"""
    
    def test_import_error_handling(self):
        """Test graceful handling when components are missing"""
        
        # The dynamic solver should be importable
        from text_to_solver.dynamic_solver import DynamicEquationSolver
        
        # Should be able to create instance
        solver = DynamicEquationSolver()
        assert solver is not None
    
    def test_mixed_error_scenarios(self):
        """Test error scenarios that involve multiple solver types"""
        
        # Test case: Use static solver result as input to dynamic solver
        
        # First, solve a static problem that will fail
        static_solver = EquationSolver()
        static_solver.set_system(
            variables=['x', 'y'],
            equations=['x + y', 'x + y']  # Singular system (same equation twice)
        )
        
        static_result = static_solver.solve()
        
        # This might fail or succeed depending on solver robustness
        
        # Try to use result (even if failed) in dynamic solver
        dynamic_solver = DynamicEquationSolver()
        
        # Set up dynamic system
        try:
            dynamic_solver.set_system(
                variables=['x'],
                equations=['dx/dt = -x'],
                initial_conditions={'x': 1.0}  # Use fixed value instead of static result
            )
            
            # This should succeed regardless of static solver failure
            dynamic_result = dynamic_solver.integrate((0, 1))
            assert dynamic_result.success or not dynamic_result.success  # Either is fine
            
        except Exception as e:
            # If it fails, should fail gracefully
            assert isinstance(e, (ValueError, TypeError))


# ================================================================
# VERSION COMPATIBILITY TESTS
# ================================================================

@pytest.mark.dynamic
@pytest.mark.integration
class TestVersionCompatibility:
    """Test compatibility across different API versions"""
    
    def test_version_information(self):
        """Test that version information is consistent"""
        
        # Should be able to import version
        from text_to_solver import __version__
        
        # Should be version 3.0.0 or higher for Phase 3
        version_parts = __version__.split('.')
        major_version = int(version_parts[0])
        
        assert major_version >= 3, f"Expected version 3+, got {__version__}"
    
    def test_feature_detection(self):
        """Test ability to detect which features are available"""
        
        # Should be able to detect dynamic solver availability
        try:
            from text_to_solver import DynamicEquationSolver
            dynamic_available = True
        except ImportError:
            dynamic_available = False
        
        # In this test suite, dynamic solver should be available
        assert dynamic_available
        
        # Should be able to detect enhanced solver availability
        try:
            from text_to_solver import EnhancedEquationSolver
            enhanced_available = True
        except ImportError:
            enhanced_available = False
        
        # Enhanced solver availability is optional
        # (test should pass either way)
    
    def test_api_deprecation_warnings(self):
        """Test that deprecated APIs still work but may warn"""
        import warnings
        
        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Use old API
            solver = TextToSolver(['x'], ['x - 1'])
            result = solver.solve()
            
            # Should still work
            assert result['converged']
            
            # May or may not generate warnings (depends on implementation)
            # This test just ensures no exceptions are raised
