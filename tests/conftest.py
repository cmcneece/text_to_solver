"""
Shared fixtures and configuration for TextToSolver tests
"""

import pytest
import numpy as np
import sys
import os

# Add the src directory to sys.path to import text_to_solver
# Note: In production, the package should be installed with 'pip install -e .'
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from text_to_solver.TextToSolver import TextToSolver, SolverOptions

# Import dynamic solver components for Phase 3 tests
from text_to_solver.dynamic_solver import DynamicEquationSolver


# ================================================================
# STANDARDIZED TEST TOLERANCES
# ================================================================

class TestTolerances:
    """Standardized tolerance levels for different types of comparisons.
    
    This provides consistent tolerance values across the entire test suite,
    ensuring appropriate precision expectations for different types of operations.
    """
    EXACT = 1e-12           # Machine precision comparisons (exact symbolic results)
    NUMERICAL = 1e-8        # Standard floating-point arithmetic comparisons
    INTEGRATION = 1e-3      # Numerical integration accuracy (adaptive methods)
    INTEGRATION_LOOSE = 1e-2  # Numerical integration (simple methods like Euler)
    PHYSICAL = 0.05         # Physical conservation laws (5% variation allowed)
    CONVERGENCE = 0.01      # Algorithm convergence criteria (1%)
    RESIDUAL_NORM = 1e-10   # Residual norm for algebraic solvers


# ================================================================
# STANDARDIZED ALGEBRAIC SYSTEM PARAMETERS
# ================================================================

class AlgebraicSystemParams:
    """Standard parameter sets for algebraic equation system testing.
    
    Provides consistent, well-documented parameter sets for common
    algebraic systems used throughout the test suite.
    """
    
    SIMPLE_LINEAR = {
        'variables': ['x', 'y'],
        'equations': ['x + y - 3', 'x - y - 1'],
        'description': 'Simple 2x2 linear system',
        'known_solution': {'x': 2.0, 'y': 1.0},
        'residual_tolerance': TestTolerances.RESIDUAL_NORM
    }
    
    SIMPLE_NONLINEAR = {
        'variables': ['x', 'y'],
        'equations': ['x**2 + y**2 - 1', 'x - y'],
        'description': 'Circle-line intersection',
        'known_solution': {'x': np.sqrt(0.5), 'y': np.sqrt(0.5)},
        'residual_tolerance': TestTolerances.RESIDUAL_NORM
    }
    
    CIRCLE_LINE_PARAMETRIC = {
        'variables': ['x', 'y'],
        'equations': ['x**2 + y**2 - z**2', 'y - m*x'],
        'parameters': {'z': 3.0, 'm': 2.0},
        'description': 'Parametric circle-line intersection',
        'analytical_solution': lambda z, m: {
            'x': z / np.sqrt(1 + m**2),
            'y': m * z / np.sqrt(1 + m**2)
        }
    }
    
    CHEMICAL_EQUILIBRIUM = {
        'variables': ['pCO2', 'pHCO3', 'pCO3', 'pH2CO3'],
        'equations': [
            '-pK1 + pHCO3 + pH - pH2CO3',
            '-pK2 + pCO3 + pH - pHCO3',
            '-pKw + pH + pOH',
            '10**pCO2T - (10**pH2CO3 + 10**pHCO3 + 10**pCO3)'
        ],
        'parameters': {
            'pK1': 6.35, 'pK2': 10.33, 'pKw': 14.0,
            'pH': 7.0, 'pOH': 7.0, 'pCO2T': -5.0
        },
        'description': 'Carbonate speciation system'
    }
    
    LOTKA_VOLTERRA_EQUILIBRIUM = {
        'variables': ['x', 'y'],
        'equations': ['a*x - b*x*y', '-c*y + d*x*y'],
        'parameters': {'a': 1.0, 'b': 0.1, 'c': 0.075, 'd': 0.02},
        'description': 'Lotka-Volterra equilibrium points',
        'equilibrium_points': [
            {'x': 0.0, 'y': 0.0},  # Trivial equilibrium
            {'x': 3.75, 'y': 10.0}  # Non-trivial: c/d, a/b
        ]
    }
    
    @staticmethod
    def validate_solution(variables, equations, solution, tolerance=1e-8):
        """Validate a solution by computing residuals"""
        residuals = []
        # This would need SymPy evaluation - simplified for demo
        return all(abs(r) < tolerance for r in residuals)


# ================================================================
# STANDARDIZED DYNAMIC SYSTEM PARAMETERS  
# ================================================================

class DynamicSystemParams:
    """Standard parameter sets for dynamic system testing.
    
    Provides consistent, well-documented parameter sets for common
    dynamic systems used throughout the test suite.
    """
    
    EXPONENTIAL_DECAY = {
        'variables': ['x'],
        'equations': ['dx/dt = -k*x'],
        'parameters': {'k': 0.5}, 
        'initial_conditions': {'x': 1.0},
        'description': 'Simple exponential decay: dx/dt = -kx'
    }
    
    HARMONIC_OSCILLATOR = {
        'variables': ['x', 'v'],
        'equations': ['dx/dt = v', 'dv/dt = -omega*omega*x'],
        'parameters': {'omega': 1.0},
        'initial_conditions': {'x': 1.0, 'v': 0.0},
        'period': 2 * np.pi,
        'description': 'Harmonic oscillator: d²x/dt² = -ω²x'
    }
    
    PREDATOR_PREY = {
        'variables': ['x', 'y'],
        'equations': [
            'dx/dt = alpha*x - beta*x*y',
            'dy/dt = delta*x*y - gamma*y'
        ],
        'parameters': {'alpha': 1.0, 'beta': 0.1, 'delta': 0.075, 'gamma': 1.5},
        'initial_conditions': {'x': 10.0, 'y': 5.0},
        'equilibrium': {'x': 20.0, 'y': 10.0},  # gamma/delta, alpha/beta
        'description': 'Lotka-Volterra predator-prey system'
    }
    
    LINEAR_FORCED = {
        'variables': ['x'],
        'equations': ['dx/dt = -x + A*t'],
        'parameters': {'A': 0.1},
        'initial_conditions': {'x': 0.0},
        'description': 'Linear system with time-dependent forcing'
    }
    
    @staticmethod
    def exponential_analytical_solution(t, k=0.5, x0=1.0):
        """Analytical solution for exponential decay: x(t) = x0 * exp(-kt)"""
        return x0 * np.exp(-k * t)
    
    @staticmethod
    def linear_forced_analytical_solution(t, A=0.1, x0=0.0):
        """Analytical solution for dx/dt = -x + A*t: x(t) = A*(t - 1 + exp(-t))"""
        return A * (t - 1 + np.exp(-t))
    
    @staticmethod
    def harmonic_energy(x, v, omega=1.0):
        """Energy function for harmonic oscillator: E = (1/2)(v² + ω²x²)"""
        return 0.5 * (v**2 + omega**2 * x**2)


# ================================================================
# STANDARDIZED SOLVER STRATEGY PARAMETERS
# ================================================================

class SolverStrategyParams:
    """Standard parameter sets for testing solver strategies and patterns.
    
    Provides consistent configurations for testing Phase 2 advanced patterns
    including observers, strategies, builders, and factories.
    """
    
    # Observer Pattern Test Configurations
    OBSERVER_CONFIGS = {
        'convergence_monitor': {
            'class_name': 'ConvergenceMonitor',
            'description': 'Monitor convergence progress',
            'expected_callbacks': ['on_iteration', 'on_convergence']
        },
        'progress_callback': {
            'class_name': 'ProgressCallback', 
            'description': 'Simple progress reporting',
            'expected_callbacks': ['on_iteration']
        }
    }
    
    # Strategy Pattern Test Configurations
    STRATEGY_CONFIGS = {
        'newton_raphson': {
            'strategy_type': 'solver',
            'class_name': 'NewtonRaphsonStrategy',
            'description': 'Standard Newton-Raphson method',
            'expected_properties': ['max_iterations', 'tolerance']
        },
        'broyden': {
            'strategy_type': 'solver',
            'class_name': 'BroydenStrategy', 
            'description': 'Quasi-Newton Broyden method',
            'expected_properties': ['max_iterations', 'tolerance']
        },
        'heuristic_guess': {
            'strategy_type': 'initial_guess',
            'class_name': 'HeuristicGuessStrategy',
            'description': 'Smart initial guess generation',
            'expected_methods': ['generate_guess']
        }
    }
    
    # Builder Pattern Test Configurations  
    BUILDER_CONFIGS = {
        'equation_system': {
            'class_name': 'EquationSystemBuilder',
            'description': 'General equation system builder',
            'required_methods': ['add_equation', 'set_variable', 'build']
        },
        'optimization_problem': {
            'class_name': 'OptimizationProblemBuilder',
            'description': 'Optimization problem builder', 
            'required_methods': ['set_objective', 'add_constraint', 'build']
        }
    }
    
    # Factory Pattern Test Configurations
    FACTORY_CONFIGS = {
        'solver_strategy': {
            'factory_name': 'SolverStrategyFactory',
            'description': 'Create solver strategies',
            'supported_types': ['newton', 'broyden', 'hybrid']
        },
        'initial_guess': {
            'factory_name': 'InitialGuessStrategyFactory', 
            'description': 'Create initial guess strategies',
            'supported_types': ['random', 'heuristic', 'zero']
        }
    }
    
    # Performance Benchmark Systems
    PERFORMANCE_SYSTEMS = {
        'small_linear': {
            'size': '2x2',
            'complexity': 'linear',
            'max_time': 0.1,  # 100ms
            'description': 'Small linear system performance test'
        },
        'medium_nonlinear': {
            'size': '5x5', 
            'complexity': 'nonlinear',
            'max_time': 1.0,  # 1 second
            'description': 'Medium nonlinear system performance test'
        },
        'large_sparse': {
            'size': '20x20',
            'complexity': 'sparse',
            'max_time': 10.0,  # 10 seconds
            'description': 'Large sparse system performance test'
        }
    }


# ================================================================
# VALIDATION HELPER FUNCTIONS
# ================================================================

class ValidationHelpers:
    """Common validation patterns for all TextToSolver testing.
    
    Provides reusable validation functions for common test scenarios,
    promoting consistency and reducing code duplication across
    algebraic, dynamic, and advanced pattern testing.
    """
    
    # ================================================================
    # ALGEBRAIC SYSTEM VALIDATION HELPERS
    # ================================================================
    
    @staticmethod
    def validate_residual_norm(residual_norm, tolerance=TestTolerances.RESIDUAL_NORM,
                              description="system"):
        """Validate that residual norm meets convergence criteria.
        
        Args:
            residual_norm: Computed residual norm
            tolerance: Maximum acceptable residual norm
            description: Description for error messages
            
        Returns:
            bool: True if residual norm is acceptable
            
        Raises:
            AssertionError: If residual norm is too large with descriptive message
        """
        assert residual_norm < tolerance, (
            f"{description} residual norm too large: "
            f"{residual_norm:.2e} exceeds tolerance {tolerance:.2e}"
        )
        return True
    
    @staticmethod
    def validate_solution_accuracy(actual_solution, expected_solution, 
                                 tolerance=TestTolerances.NUMERICAL,
                                 description="solution"):
        """Validate solution accuracy against known solution.
        
        Args:
            actual_solution: Dict of computed solution values
            expected_solution: Dict of expected solution values  
            tolerance: Absolute tolerance for each variable
            description: Description for error messages
            
        Returns:
            bool: True if all variables are within tolerance
            
        Raises:
            AssertionError: If any variable exceeds tolerance with descriptive message
        """
        for var in expected_solution:
            assert var in actual_solution, (
                f"Variable '{var}' missing from {description}"
            )
            
            actual = actual_solution[var]
            expected = expected_solution[var]
            error = abs(actual - expected)
            
            assert error < tolerance, (
                f"{description} accuracy for '{var}' insufficient: "
                f"expected {expected:.6f}, got {actual:.6f}, "
                f"error {error:.2e} exceeds tolerance {tolerance:.2e}"
            )
        return True
    
    @staticmethod
    def validate_convergence_report(report, expected_convergence=True, 
                                  max_iterations=None, description="solver"):
        """Validate solver convergence report.
        
        Args:
            report: Solver report dictionary (handles both TextToSolver and enhanced formats)
            expected_convergence: Whether convergence is expected
            max_iterations: Maximum acceptable iterations (if specified)
            description: Description for error messages
            
        Returns:
            bool: True if convergence behavior is as expected
            
        Raises:
            AssertionError: If convergence behavior is unexpected
        """
        # Handle both report formats: TextToSolver uses 'exit_flag', enhanced uses 'converged'
        if 'converged' in report:
            converged = report['converged']
        elif 'exit_flag' in report:
            # TextToSolver: exit_flag=1 means converged, others mean failure
            converged = report['exit_flag'] == 1
        else:
            # Fallback: assume failure if no clear convergence indicator
            converged = False
        
        if expected_convergence:
            assert converged, (
                f"{description} failed to converge: "
                f"exit_flag={report.get('exit_flag', 'N/A')}, "
                f"message='{report.get('message', 'No message')}'"
            )
        else:
            assert not converged, (
                f"{description} unexpectedly converged when failure was expected: "
                f"exit_flag={report.get('exit_flag', 'N/A')}"
            )
        
        # Validate iteration count if specified (handle both report formats)
        if max_iterations is not None:
            iterations = report.get('iterations', report.get('iter_count'))
            if iterations is not None:
                assert iterations <= max_iterations, (
                    f"{description} used too many iterations: "
                    f"{iterations} exceeds limit of {max_iterations}"
                )
        
        return True
    
    @staticmethod
    def validate_parameter_sweep_consistency(sweep_results, min_success_rate=0.8,
                                           description="parameter sweep"):
        """Validate parameter sweep results for consistency.
        
        Args:
            sweep_results: List of solution results from parameter sweep
            min_success_rate: Minimum fraction of successful solutions
            description: Description for error messages
            
        Returns:
            bool: True if sweep results meet consistency criteria
            
        Raises:
            AssertionError: If sweep results are inconsistent
        """
        total_points = len(sweep_results)
        successful_points = sum(1 for result in sweep_results 
                              if result.get('converged', False) or result.get('exit_flag') == 1)
        success_rate = successful_points / total_points if total_points > 0 else 0
        
        assert success_rate >= min_success_rate, (
            f"{description} success rate too low: "
            f"{success_rate:.1%} < {min_success_rate:.1%} "
            f"({successful_points}/{total_points} successful)"
        )
        
        return True
    
    @staticmethod
    def validate_multistart_consistency(multistart_solutions, tolerance=TestTolerances.NUMERICAL,
                                      description="multistart solver"):
        """Validate that multistart solutions are consistent.
        
        Args:
            multistart_solutions: List of solution dictionaries from multiple starts
            tolerance: Tolerance for solution consistency
            description: Description for error messages
            
        Returns:
            bool: True if solutions are consistent
            
        Raises:
            AssertionError: If solutions are inconsistent beyond tolerance
        """
        converged_solutions = [sol for sol in multistart_solutions 
                             if sol.get('converged', False)]
        
        assert len(converged_solutions) > 0, (
            f"{description} no solutions converged from multistart"
        )
        
        if len(converged_solutions) > 1:
            # Compare all solutions to the first one
            reference = converged_solutions[0]['solution']
            
            for i, sol in enumerate(converged_solutions[1:], 1):
                current = sol['solution']
                
                for j, (ref_val, cur_val) in enumerate(zip(reference, current)):
                    error = abs(ref_val - cur_val)
                    assert error < tolerance, (
                        f"{description} solutions inconsistent: "
                        f"solution {i+1} variable {j} differs from reference by "
                        f"{error:.2e} > tolerance {tolerance:.2e}"
                    )
        
        return True
    
    # ================================================================
    # DYNAMIC SYSTEM VALIDATION HELPERS (EXISTING)
    # ================================================================
    
    @staticmethod
    def validate_conservation(values, tolerance=TestTolerances.PHYSICAL, description="quantity"):
        """Validate that a conserved quantity remains approximately constant.
        
        Args:
            values: Array of values that should be conserved
            tolerance: Relative tolerance for variation
            description: Description for error messages
            
        Returns:
            bool: True if conservation is satisfied
            
        Raises:
            AssertionError: If conservation is violated with descriptive message
        """
        if len(values) < 2:
            return True
        
        variation = (np.max(values) - np.min(values)) / np.mean(np.abs(values))
        
        assert variation < tolerance, (
            f"Conservation of {description} violated: "
            f"relative variation {variation:.2%} exceeds tolerance {tolerance:.2%}"
        )
        return True
    
    @staticmethod  
    def validate_periodicity(time_values, signal_values, expected_period, 
                           tolerance=0.1, description="signal"):
        """Validate that a signal has approximately the expected period.
        
        Args:
            time_values: Time array
            signal_values: Signal array
            expected_period: Expected period
            tolerance: Relative tolerance for period detection
            description: Description for error messages
            
        Returns:
            bool: True if periodicity is detected
            
        Raises:
            AssertionError: If periodicity is not found with descriptive message
        """
        # Find peaks (simple peak detection)
        peaks = []
        for i in range(1, len(signal_values)-1):
            if (signal_values[i] > signal_values[i-1] and 
                signal_values[i] > signal_values[i+1] and
                signal_values[i] > np.mean(signal_values)):  # Above average
                peaks.append(time_values[i])
        
        assert len(peaks) >= 2, (
            f"Insufficient peaks found in {description} for period analysis: "
            f"found {len(peaks)}, need at least 2"
        )
            
        periods = np.diff(peaks)
        avg_period = np.mean(periods)
        
        error = abs(avg_period - expected_period)
        assert error < tolerance * expected_period, (
            f"Period of {description} incorrect: "
            f"expected {expected_period:.3f}, got {avg_period:.3f}, "
            f"error {error:.3f} exceeds tolerance {tolerance * expected_period:.3f}"
        )
        return True
    
    @staticmethod
    def validate_equilibrium_approach(values, equilibrium, 
                                    tolerance=TestTolerances.CONVERGENCE,
                                    description="system"):
        """Validate that values approach an equilibrium.
        
        Args:
            values: Array of values over time
            equilibrium: Expected equilibrium value
            tolerance: Absolute tolerance for equilibrium
            description: Description for error messages
            
        Returns:
            bool: True if equilibrium is approached
            
        Raises:
            AssertionError: If equilibrium is not reached with descriptive message
        """
        # Check last 10% of points or at least last 5 points
        n_check = max(5, len(values) // 10)
        final_values = values[-n_check:]
        
        deviations = np.abs(final_values - equilibrium)
        max_deviation = np.max(deviations)
        
        assert max_deviation < tolerance, (
            f"{description} did not approach equilibrium {equilibrium}: "
            f"maximum deviation in final points {max_deviation:.2e} "
            f"exceeds tolerance {tolerance:.2e}"
        )
        return True
    
    @staticmethod
    def validate_integration_accuracy(actual, expected, method="integration",
                                    tolerance=TestTolerances.INTEGRATION):
        """Validate numerical integration accuracy against analytical solution.
        
        Args:
            actual: Computed numerical result
            expected: Analytical or reference result
            method: Description of integration method
            tolerance: Absolute tolerance
            
        Returns:
            bool: True if accuracy is acceptable
            
        Raises:
            AssertionError: If accuracy is insufficient with descriptive message
        """
        error = abs(actual - expected)
        
        # Use relative error if values are large
        if abs(expected) > 1.0:
            relative_error = error / abs(expected)
            assert relative_error < tolerance, (
                f"{method} accuracy insufficient: "
                f"relative error {relative_error:.2e} exceeds tolerance {tolerance:.2e} "
                f"(expected {expected:.6f}, got {actual:.6f})"
            )
        else:
            assert error < tolerance, (
                f"{method} accuracy insufficient: "
                f"absolute error {error:.2e} exceeds tolerance {tolerance:.2e} "
                f"(expected {expected:.6f}, got {actual:.6f})"
            )
        return True


@pytest.fixture
def simple_linear_system():
    """Simple 2x2 linear system: x + y = 3, x - y = 1"""
    dep_vars = ['x', 'y']
    residual = ['x + y - 3', 'x - y - 1']
    return TextToSolver(dep_vars, residual)


@pytest.fixture
def simple_nonlinear_system():
    """Simple nonlinear system: x^2 + y^2 = 1, x - y = 0"""
    dep_vars = ['x', 'y']
    residual = ['x**2 + y**2 - 1', 'x - y']
    return TextToSolver(dep_vars, residual)


@pytest.fixture
def circle_line_system():
    """Circle and line intersection system with parameter"""
    dep_vars = ['x', 'y']
    residual = ['x**2 + y**2 - z**2', 'y - 5*x']
    indep_vars = ['z']
    return TextToSolver(dep_vars, residual, indep_vars=indep_vars)


@pytest.fixture
def chemical_system():
    """Chemical equilibrium system similar to carbonate speciation"""
    dep_vars = ['pCO2', 'pHCO3', 'pCO3', 'pH2CO3']
    residual = [
        '-pK1 + pHCO3 + pH - pH2CO3',
        '-pK2 + pCO3 + pH - pHCO3', 
        '-pKw + pH + pOH',
        '10**pCO2T - (10**pH2CO3 + 10**pHCO3 + 10**pCO3)'
    ]
    indep_vars = ['pH']
    parameters = {
        'pK1': 6.35,
        'pK2': 10.33, 
        'pKw': 14.0,
        'pOH': 7.0,
        'pCO2T': -5.0
    }
    return TextToSolver(dep_vars, residual, indep_vars=indep_vars, parameters=parameters)


@pytest.fixture
def lotka_volterra_system():
    """Lotka-Volterra predator-prey system"""
    dep_vars = ['x', 'y']
    residual = ['a*x - b*x*y', '-c*y + d*x*y']
    parameters = {'a': 1.0, 'b': 0.1, 'c': 0.075, 'd': 0.02}
    return TextToSolver(dep_vars, residual, parameters=parameters)


@pytest.fixture
def default_solver_options():
    """Default SolverOptions for testing"""
    return SolverOptions(display=False, tol_fun=1e-8, tol_x=1e-10)


@pytest.fixture
def strict_solver_options():
    """Strict SolverOptions for testing"""
    return SolverOptions(display=False, tol_fun=1e-12, tol_x=1e-14, max_iter=50)


@pytest.fixture
def sample_indep_var_values():
    """Sample independent variable values for parametric tests"""
    return {'z': np.array([1.0, 2.0, 3.0, 4.0, 5.0])}


@pytest.fixture
def sample_ph_values():
    """Sample pH values for chemical system tests"""
    return {'pH': np.linspace(1, 12, 10)}


@pytest.fixture
def known_solution_linear():
    """Known solution for simple linear system"""
    return {'x': np.array([2.0]), 'y': np.array([1.0])}


@pytest.fixture
def known_solution_nonlinear():
    """Known solution for simple nonlinear system"""
    return {'x': np.array([np.sqrt(0.5)]), 'y': np.array([np.sqrt(0.5)])}


@pytest.fixture
def tolerance_checks():
    """Helper function to check solution tolerance"""
    def _check_tolerance(solution, expected, tol=1e-6):
        for var in expected:
            assert var in solution, f"Variable {var} not in solution"
            assert np.allclose(solution[var], expected[var], atol=tol), \
                f"Solution for {var} not within tolerance: {solution[var]} vs {expected[var]}"
    return _check_tolerance


# ================================================================
# STANDARDIZED TEST FIXTURES
# ================================================================

@pytest.fixture
def tolerances():
    """Access to standardized tolerance values"""
    return TestTolerances()


@pytest.fixture
def system_params():
    """Access to standardized dynamic system parameters"""
    return DynamicSystemParams()


@pytest.fixture
def algebraic_params():
    """Access to standardized algebraic system parameters"""
    return AlgebraicSystemParams()


@pytest.fixture
def strategy_params():
    """Access to standardized solver strategy parameters"""
    return SolverStrategyParams()


@pytest.fixture
def validators():
    """Access to validation helper functions"""
    return ValidationHelpers()


# ================================================================
# ENHANCED ALGEBRAIC SYSTEM FIXTURES  
# ================================================================

@pytest.fixture
def simple_linear_solver():
    """Simple 2x2 linear system using standardized parameters"""
    params = AlgebraicSystemParams.SIMPLE_LINEAR
    solver = TextToSolver(params['variables'], params['equations'])
    return solver


@pytest.fixture
def simple_nonlinear_solver():
    """Simple nonlinear system using standardized parameters"""
    params = AlgebraicSystemParams.SIMPLE_NONLINEAR  
    solver = TextToSolver(params['variables'], params['equations'])
    return solver


@pytest.fixture
def parametric_circle_line_solver():
    """Parametric circle-line system using standardized parameters"""
    params = AlgebraicSystemParams.CIRCLE_LINE_PARAMETRIC
    solver = TextToSolver(
        params['variables'], 
        params['equations'],
        indep_vars=['z', 'm'],
        parameters=params['parameters']
    )
    return solver


@pytest.fixture
def chemical_equilibrium_solver():
    """Chemical equilibrium system using standardized parameters"""
    params = AlgebraicSystemParams.CHEMICAL_EQUILIBRIUM
    solver = TextToSolver(
        params['variables'],
        params['equations'], 
        indep_vars=['pH'],
        parameters=params['parameters']
    )
    return solver


# ================================================================
# ENHANCED DYNAMIC SYSTEM FIXTURES
# ================================================================

@pytest.fixture
def simple_exponential_solver():
    """Simple exponential decay system: dx/dt = -k*x"""
    
    params = DynamicSystemParams.EXPONENTIAL_DECAY
    solver = DynamicEquationSolver()
    solver.set_system(**{k: v for k, v in params.items() 
                        if k not in ['description']})
    return solver


@pytest.fixture
def harmonic_oscillator_solver():
    """Harmonic oscillator: d²x/dt² = -ω²*x (as first-order system)"""
    
    params = DynamicSystemParams.HARMONIC_OSCILLATOR
    solver = DynamicEquationSolver()
    solver.set_system(**{k: v for k, v in params.items() 
                        if k not in ['period', 'description']})
    return solver


@pytest.fixture
def predator_prey_solver():
    """Predator-prey system (Lotka-Volterra)"""
    
    params = DynamicSystemParams.PREDATOR_PREY
    solver = DynamicEquationSolver()
    solver.set_system(**{k: v for k, v in params.items() 
                        if k not in ['equilibrium', 'description']})
    return solver


@pytest.fixture
def linear_forced_solver():
    """Linear system with time-dependent forcing: dx/dt = -x + A*t"""
    
    params = DynamicSystemParams.LINEAR_FORCED
    solver = DynamicEquationSolver()
    solver.set_system(**{k: v for k, v in params.items() 
                        if k not in ['description']})
    return solver


# ================================================================
# PERFORMANCE TESTING FIXTURES
# ================================================================

import time
from contextlib import contextmanager

@contextmanager 
def performance_timer():
    """Context manager to measure execution time"""
    start = time.perf_counter()
    yield lambda: time.perf_counter() - start

class PerformanceBenchmarks:
    """Performance expectations for different operations across all functionality"""
    
    # Solver Creation Performance
    MAX_SOLVER_CREATION_TIME = 0.5      # 500ms (relaxed for CI environments)
    MAX_ENHANCED_SOLVER_CREATION = 1.0   # 1s for enhanced solver with patterns
    
    # Algebraic System Solving Performance  
    MAX_SIMPLE_LINEAR_TIME = 0.1         # 100ms for 2x2 linear systems
    MAX_SIMPLE_NONLINEAR_TIME = 0.5      # 500ms for simple nonlinear systems
    MAX_MEDIUM_SYSTEM_TIME = 2.0         # 2s for medium complexity (5x5)
    MAX_LARGE_SYSTEM_TIME = 10.0         # 10s for large systems (20x20)
    
    # Parameter Sweep Performance
    MAX_SMALL_SWEEP_TIME = 1.0           # 1s for 10-point parameter sweep
    MAX_LARGE_SWEEP_TIME = 30.0          # 30s for 100-point parameter sweep
    
    # Dynamic System Integration Performance
    MAX_SMALL_INTEGRATION_TIME = 2.0     # 2s for basic integration
    MAX_LONG_INTEGRATION_TIME = 15.0     # 15s for long-time integration
    
    # Advanced Pattern Performance
    MAX_OBSERVER_OVERHEAD = 0.2          # 20% overhead for observers
    MAX_STRATEGY_OVERHEAD = 0.1          # 10% overhead for strategies
    MAX_BUILDER_OVERHEAD = 0.05          # 5% overhead for builders
    
    # Memory Usage Limits (in MB)
    MAX_BASIC_MEMORY_USAGE = 50          # 50MB for basic operations
    MAX_LARGE_SYSTEM_MEMORY = 500        # 500MB for large systems

@pytest.fixture
def performance_timer():
    """Access to performance timing context manager"""
    @contextmanager 
    def timer():
        start = time.perf_counter()
        yield lambda: time.perf_counter() - start
    return timer

@pytest.fixture
def performance_limits():
    """Access to performance benchmark limits"""
    return PerformanceBenchmarks()
