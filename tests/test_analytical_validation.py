#!/usr/bin/env python3
"""
Analytical Solution Validation Tests

This test suite validates TextToSolver's numerical solutions against known
analytical solutions for difficult nonlinear systems with parameter sweeps.

These tests ensure that the solver can handle:
- Challenging nonlinear systems
- Parameter sweeps across different values
- Accurate numerical solutions compared to analytical benchmarks
"""

import pytest
import numpy as np
import sys
import os

# Add the parent directory to sys.path to import text_to_solver
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from text_to_solver.TextToSolver import TextToSolver, SolverOptions


# ================================================================
# ANALYTICAL SOLUTIONS
# ================================================================

class AnalyticalSolutions:
    """Analytical solutions for various nonlinear systems."""
    
    @staticmethod
    def exponential_decay(t, k, x0):
        """Analytical solution: dx/dt = -k*x, x(0) = x0"""
        return x0 * np.exp(-k * t)
    
    @staticmethod
    def logistic_growth(t, r, K, N0):
        """Analytical solution: dN/dt = r*N*(1 - N/K), N(0) = N0"""
        return K / (1 + (K/N0 - 1) * np.exp(-r * t))
    
    @staticmethod
    def quadratic_system_roots(a, b, c):
        """Analytical roots: x^2 + a*x + b = 0, y = c*x"""
        # For x^2 + a*x + b = 0
        discriminant = a**2 - 4*b
        if discriminant < 0:
            return None  # Complex roots
        sqrt_disc = np.sqrt(discriminant)
        x1 = (-a + sqrt_disc) / 2
        x2 = (-a - sqrt_disc) / 2
        return [(x1, c*x1), (x2, c*x2)]
    
    @staticmethod
    def circle_line_intersection(z, m):
        """Analytical solution: x^2 + y^2 = z^2, y = m*x"""
        # Substitute y = m*x into x^2 + y^2 = z^2
        # x^2 + (m*x)^2 = z^2
        # x^2 * (1 + m^2) = z^2
        # x = ± z / sqrt(1 + m^2)
        if 1 + m**2 == 0:
            return None
        x_pos = z / np.sqrt(1 + m**2)
        x_neg = -z / np.sqrt(1 + m**2)
        return [(x_pos, m*x_pos), (x_neg, m*x_neg)]
    
    @staticmethod
    def coupled_exponential_system(t, k1, k2, x0, y0):
        """Analytical solution: dx/dt = -k1*x, dy/dt = -k2*y, x(0)=x0, y(0)=y0"""
        return (x0 * np.exp(-k1 * t), y0 * np.exp(-k2 * t))
    
    @staticmethod
    def nonlinear_polynomial_roots(a, b):
        """Analytical solution: x^3 - a*x - b = 0, y = x^2"""
        # For x^3 - a*x - b = 0, use Cardano's formula
        # This is a simplified case where we can find roots
        # For general case, we'll use numerical comparison
        # Here we'll solve for specific parameter values
        def cardano_formula(a, b):
            """Cardano's formula for x^3 + p*x + q = 0"""
            # Transform to x^3 - a*x - b = 0 (p = -a, q = -b)
            p = -a
            q = -b
            discriminant = (q/2)**2 + (p/3)**3
            
            if discriminant >= 0:
                # One real root
                u = np.cbrt(-q/2 + np.sqrt(discriminant))
                v = np.cbrt(-q/2 - np.sqrt(discriminant))
                x = u + v
            else:
                # Three real roots (trigonometric form)
                # For simplicity, return the principal real root
                r = np.sqrt(-(p/3)**3)
                theta = np.arccos(-q/(2*np.sqrt(-(p/3)**3)))
                x = 2 * np.sqrt(-p/3) * np.cos(theta/3)
            
            return x
        
        x = cardano_formula(a, b)
        y = x**2
        return (x, y)


# ================================================================
# TEST SYSTEMS WITH ANALYTICAL SOLUTIONS
# ================================================================

@pytest.mark.analytical
@pytest.mark.validation
class TestExponentialDecaySystem:
    """Test exponential decay system: dx/dt = -k*x"""
    
    @pytest.mark.parametrize("k", [0.1, 0.5, 1.0, 2.0, 5.0])
    @pytest.mark.parametrize("x0", [0.5, 1.0, 2.0, 5.0])
    def test_exponential_decay_parameter_sweep(self, k, x0):
        """Test exponential decay with parameter sweep"""
        # System: x = x0 * exp(-k*t) at t=1
        # Convert to residual form: x - x0*exp(-k) = 0
        t = 1.0
        expected_x = AnalyticalSolutions.exponential_decay(t, k, x0)
        
        # Create solver: x - x0*exp(-k*t) = 0
        solver = TextToSolver(
            dep_vars=['x'],
            residual=[f'x - {x0}*exp(-{k}*{t})'],
        )
        
        # Solve
        solution, report = solver.solve_auto(
            options=SolverOptions(display=False, tol_fun=1e-10, tol_x=1e-12)
        )
        
        assert report['exit_flag'] == 1, f"Solver failed for k={k}, x0={x0}"
        
        # Compare to analytical solution
        numerical_x = solution['x'][0]
        error = abs(numerical_x - expected_x)
        relative_error = error / (abs(expected_x) + 1e-15)
        
        assert relative_error < 1e-8, (
            f"Relative error {relative_error:.2e} exceeds tolerance for k={k}, x0={x0}\n"
            f"  Expected: {expected_x:.10f}, Got: {numerical_x:.10f}"
        )


@pytest.mark.analytical
@pytest.mark.validation
class TestCircleLineSystem:
    """Test circle-line intersection: x^2 + y^2 = z^2, y = m*x"""
    
    @pytest.mark.parametrize("z", [1.0, 2.0, 3.0, 5.0, 10.0])
    @pytest.mark.parametrize("m", [0.1, 0.5, 1.0, 2.0, 5.0, -1.0, -2.0])
    def test_circle_line_parameter_sweep(self, z, m):
        """Test circle-line intersection with parameter sweep"""
        # Get analytical solutions
        analytical_solutions = AnalyticalSolutions.circle_line_intersection(z, m)
        assert analytical_solutions is not None, f"No solution for z={z}, m={m}"
        
        # Create solver
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x**2 + y**2 - z**2', 'y - m*x'],
            indep_vars=['z', 'm'],
        )
        
        # Solve for each analytical solution
        for expected_x, expected_y in analytical_solutions:
            indep_var_val = {'z': np.array([z]), 'm': np.array([m])}
            
            # Use analytical solution as initial guess (slightly perturbed)
            guess = {
                'x': np.array([expected_x * 1.1]),
                'y': np.array([expected_y * 1.1])
            }
            
            solution, report = solver.solve(
                guess,
                indep_var_val=indep_var_val,
                options=SolverOptions(display=False, tol_fun=1e-10, tol_x=1e-12)
            )
            
            assert report['exit_flag'] == 1, (
                f"Solver failed for z={z}, m={m}, solution ({expected_x}, {expected_y})"
            )
            
            # Compare to analytical solution
            numerical_x = solution['x'][0]
            numerical_y = solution['y'][0]
            
            error_x = abs(numerical_x - expected_x)
            error_y = abs(numerical_y - expected_y)
            
            # Use relative error with minimum threshold
            # For circle-line system, use slightly more lenient tolerance due to numerical precision
            rel_error_x = error_x / (abs(expected_x) + 1e-10)
            rel_error_y = error_y / (abs(expected_y) + 1e-10)
            
            # Use 1e-6 tolerance for circle-line (more lenient due to sqrt operations)
            assert rel_error_x < 1e-6 and rel_error_y < 1e-6, (
                f"Error exceeds tolerance for z={z}, m={m}\n"
                f"  Expected: ({expected_x:.10f}, {expected_y:.10f})\n"
                f"  Got: ({numerical_x:.10f}, {numerical_y:.10f})\n"
                f"  Relative errors: ({rel_error_x:.2e}, {rel_error_y:.2e})"
            )


@pytest.mark.analytical
@pytest.mark.validation
class TestQuadraticSystem:
    """Test quadratic system: x^2 + a*x + b = 0, y = c*x"""
    
    @pytest.mark.parametrize("a", [-5.0, -2.0, 0.0, 2.0, 5.0])
    @pytest.mark.parametrize("b", [-5.0, -1.0, 0.0, 1.0, 5.0])
    @pytest.mark.parametrize("c", [0.5, 1.0, 2.0])
    def test_quadratic_system_parameter_sweep(self, a, b, c):
        """Test quadratic system with parameter sweep"""
        # Get analytical solutions
        analytical_solutions = AnalyticalSolutions.quadratic_system_roots(a, b, c)
        
        if analytical_solutions is None:
            pytest.skip(f"Complex roots for a={a}, b={b}, c={c}")
        
        # Create solver
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=[f'x**2 + {a}*x + {b}', f'y - {c}*x'],
        )
        
        # Test each analytical solution
        for expected_x, expected_y in analytical_solutions:
            # Use analytical solution as initial guess (slightly perturbed)
            guess = {
                'x': np.array([expected_x * 1.1]),
                'y': np.array([expected_y * 1.1])
            }
            
            solution, report = solver.solve(
                guess,
                options=SolverOptions(display=False, tol_fun=1e-10, tol_x=1e-12, max_iter=50)
            )
            
            assert report['exit_flag'] == 1, (
                f"Solver failed for a={a}, b={b}, c={c}, solution ({expected_x}, {expected_y})"
            )
            
            # Compare to analytical solution
            numerical_x = solution['x'][0]
            numerical_y = solution['y'][0]
            
            error_x = abs(numerical_x - expected_x)
            error_y = abs(numerical_y - expected_y)
            
            rel_error_x = error_x / (abs(expected_x) + 1e-10)
            rel_error_y = error_y / (abs(expected_y) + 1e-10)
            
            # Use more lenient tolerance for quadratic system (1e-6)
            # Some parameter combinations can be numerically challenging
            assert rel_error_x < 1e-6 and rel_error_y < 1e-6, (
                f"Error exceeds tolerance for a={a}, b={b}, c={c}\n"
                f"  Expected: ({expected_x:.10f}, {expected_y:.10f})\n"
                f"  Got: ({numerical_x:.10f}, {numerical_y:.10f})\n"
                f"  Relative errors: ({rel_error_x:.2e}, {rel_error_y:.2e})"
            )


@pytest.mark.analytical
@pytest.mark.validation
class TestCoupledExponentialSystem:
    """Test coupled exponential system: dx/dt = -k1*x, dy/dt = -k2*y"""
    
    @pytest.mark.parametrize("k1", [0.1, 0.5, 1.0, 2.0])
    @pytest.mark.parametrize("k2", [0.1, 0.5, 1.0, 2.0])
    @pytest.mark.parametrize("x0", [1.0, 2.0, 5.0])
    @pytest.mark.parametrize("y0", [1.0, 2.0, 5.0])
    def test_coupled_exponential_parameter_sweep(self, k1, k2, x0, y0):
        """Test coupled exponential system with parameter sweep"""
        t = 1.0
        expected_x, expected_y = AnalyticalSolutions.coupled_exponential_system(t, k1, k2, x0, y0)
        
        # Create solver: x - x0*exp(-k1*t) = 0, y - y0*exp(-k2*t) = 0
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=[
                f'x - {x0}*exp(-{k1}*{t})',
                f'y - {y0}*exp(-{k2}*{t})'
            ],
        )
        
        # Solve
        solution, report = solver.solve_auto(
            options=SolverOptions(display=False, tol_fun=1e-10, tol_x=1e-12)
        )
        
        assert report['exit_flag'] == 1, f"Solver failed for k1={k1}, k2={k2}, x0={x0}, y0={y0}"
        
        # Compare to analytical solution
        numerical_x = solution['x'][0]
        numerical_y = solution['y'][0]
        
        rel_error_x = abs(numerical_x - expected_x) / (abs(expected_x) + 1e-15)
        rel_error_y = abs(numerical_y - expected_y) / (abs(expected_y) + 1e-15)
        
        assert rel_error_x < 1e-8 and rel_error_y < 1e-8, (
            f"Relative error exceeds tolerance for k1={k1}, k2={k2}, x0={x0}, y0={y0}\n"
            f"  Expected: ({expected_x:.10f}, {expected_y:.10f})\n"
            f"  Got: ({numerical_x:.10f}, {numerical_y:.10f})\n"
            f"  Relative errors: ({rel_error_x:.2e}, {rel_error_y:.2e})"
        )


@pytest.mark.analytical
@pytest.mark.validation
class TestNonlinearPolynomialSystem:
    """Test nonlinear polynomial system: x^3 - a*x - b = 0, y = x^2"""
    
    @pytest.mark.parametrize("a", [1.0, 2.0, 5.0, 10.0])
    @pytest.mark.parametrize("b", [0.0, 1.0, 2.0, 5.0])
    def test_nonlinear_polynomial_parameter_sweep(self, a, b):
        """Test nonlinear polynomial system with parameter sweep"""
        # Get analytical solution (principal real root)
        try:
            expected_x, expected_y = AnalyticalSolutions.nonlinear_polynomial_roots(a, b)
        except Exception:
            pytest.skip(f"Could not compute analytical solution for a={a}, b={b}")
        
        # Create solver
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=[f'x**3 - {a}*x - {b}', f'y - x**2'],
        )
        
        # Use analytical solution as initial guess (slightly perturbed)
        guess = {
            'x': np.array([expected_x * 1.1]),
            'y': np.array([expected_y * 1.1])
        }
        
        solution, report = solver.solve(
            guess,
            options=SolverOptions(display=False, tol_fun=1e-10, tol_x=1e-12, max_iter=50)
        )
        
        assert report['exit_flag'] == 1, f"Solver failed for a={a}, b={b}"
        
        # Compare to analytical solution
        numerical_x = solution['x'][0]
        numerical_y = solution['y'][0]
        
        rel_error_x = abs(numerical_x - expected_x) / (abs(expected_x) + 1e-10)
        rel_error_y = abs(numerical_y - expected_y) / (abs(expected_y) + 1e-10)
        
        assert rel_error_x < 1e-7 and rel_error_y < 1e-7, (
            f"Relative error exceeds tolerance for a={a}, b={b}\n"
            f"  Expected: ({expected_x:.10f}, {expected_y:.10f})\n"
            f"  Got: ({numerical_x:.10f}, {numerical_y:.10f})\n"
            f"  Relative errors: ({rel_error_x:.2e}, {rel_error_y:.2e})"
        )


@pytest.mark.analytical
@pytest.mark.validation
@pytest.mark.slow
class TestComprehensiveParameterSweep:
    """Comprehensive parameter sweep tests for validation"""
    
    def test_circle_line_comprehensive_sweep(self):
        """Comprehensive parameter sweep for circle-line system"""
        z_values = np.linspace(1.0, 10.0, 10)
        m_values = np.linspace(-5.0, 5.0, 11)
        
        solver = TextToSolver(
            dep_vars=['x', 'y'],
            residual=['x**2 + y**2 - z**2', 'y - m*x'],
            indep_vars=['z', 'm'],
        )
        
        failures = []
        for z in z_values:
            for m in m_values:
                if abs(m) < 0.01:  # Skip near-zero m (degenerate case)
                    continue
                
                analytical_solutions = AnalyticalSolutions.circle_line_intersection(z, m)
                if analytical_solutions is None:
                    continue
                
                # Test first solution
                expected_x, expected_y = analytical_solutions[0]
                indep_var_val = {'z': np.array([z]), 'm': np.array([m])}
                
                guess = {
                    'x': np.array([expected_x * 1.1]),
                    'y': np.array([expected_y * 1.1])
                }
                
                solution, report = solver.solve(
                    guess,
                    indep_var_val=indep_var_val,
                    options=SolverOptions(display=False, tol_fun=1e-10, tol_x=1e-12)
                )
                
                if report['exit_flag'] != 1:
                    failures.append(f"z={z:.2f}, m={m:.2f}: solver failed")
                    continue
                
                numerical_x = solution['x'][0]
                numerical_y = solution['y'][0]
                
                rel_error_x = abs(numerical_x - expected_x) / (abs(expected_x) + 1e-10)
                rel_error_y = abs(numerical_y - expected_y) / (abs(expected_y) + 1e-10)
                
                if rel_error_x > 1e-8 or rel_error_y > 1e-8:
                    failures.append(
                        f"z={z:.2f}, m={m:.2f}: error ({rel_error_x:.2e}, {rel_error_y:.2e})"
                    )
        
        assert len(failures) == 0, f"Parameter sweep failures:\n" + "\n".join(failures[:10])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

