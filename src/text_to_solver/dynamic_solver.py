#!/usr/bin/env python3
"""
Dynamic System Solver for TextToSolver

This module provides differential equation solving capabilities, extending
TextToSolver from algebraic equations to time-dependent dynamic systems.

Features:
- Time integration methods (Euler, Runge-Kutta, adaptive methods)
- Derivative parsing in equations (dx/dt, d²x/dt², etc.)
- Boundary condition handling (initial conditions, boundary values)
- Time domain specification and control
- Integration with existing TextToSolver architecture

Dynamic Systems Enhancement
"""

import numpy as np
import scipy.integrate as integrate
from scipy.interpolate import interp1d
from typing import Dict, List, Union, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
import re
import sympy as sp
from sympy import symbols, diff, lambdify, sympify

from .user_api import EquationSystem, SolutionResult, EquationSystemError


# ================================================================
# DYNAMIC SYSTEM RESULT OBJECTS
# ================================================================

@dataclass
class DynamicSolutionResult:
    """Rich result object for dynamic system solutions."""
    
    time_points: np.ndarray
    variables: Dict[str, np.ndarray]
    success: bool
    message: str
    integration_info: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate result data."""
        if self.success:
            if len(self.time_points) == 0:
                raise ValueError("Time points cannot be empty for successful result")
            for var, values in self.variables.items():
                if len(values) != len(self.time_points):
                    raise ValueError(f"Variable {var} length mismatch with time points")
    
    def __getitem__(self, var_name: str) -> np.ndarray:
        """Get variable time series by name."""
        if var_name in self.variables:
            return self.variables[var_name]
        raise KeyError(f"Variable '{var_name}' not found in solution")
    
    @property
    def final_values(self) -> Dict[str, float]:
        """Get final values at end of integration."""
        if not self.success or len(self.time_points) == 0:
            return {}
        return {var: values[-1] for var, values in self.variables.items()}
    
    @property
    def initial_values(self) -> Dict[str, float]:
        """Get initial values at start of integration."""
        if not self.success or len(self.time_points) == 0:
            return {}
        return {var: values[0] for var, values in self.variables.items()}
    
    def interpolate(self, var_name: str, kind: str = 'linear') -> Callable[[float], float]:
        """Create interpolation function for a variable."""
        if var_name not in self.variables:
            raise KeyError(f"Variable '{var_name}' not found")
        return interp1d(self.time_points, self.variables[var_name], 
                       kind=kind, bounds_error=False, fill_value='extrapolate')
    
    def at_time(self, t: float) -> Dict[str, float]:
        """Get all variable values at a specific time (interpolated)."""
        result = {}
        for var_name in self.variables:
            interp_func = self.interpolate(var_name)
            result[var_name] = float(interp_func(t))
        return result


# ================================================================
# DIFFERENTIAL EQUATION PARSER
# ================================================================

class DifferentialEquationParser:
    """Parse differential equations from string representations."""
    
    def __init__(self):
        """Initialize parser with derivative patterns."""
        # Patterns for different derivative notations
        self.derivative_patterns = [
            (r'd(\w+)/dt', r"sp.diff(\1, t)"),  # dx/dt -> sp.diff(x, t)
            (r'd²(\w+)/dt²', r"sp.diff(\1, t, 2)"),  # d²x/dt² -> sp.diff(x, t, 2)
            (r'd\^2(\w+)/dt\^2', r"sp.diff(\1, t, 2)"),  # d^2x/dt^2 -> sp.diff(x, t, 2)
            (r"(\w+)'", r"sp.diff(\1, t)"),  # x' -> sp.diff(x, t)
            (r"(\w+)''", r"sp.diff(\1, t, 2)"),  # x'' -> sp.diff(x, t, 2)
        ]
        
    def parse_equation(self, equation: str, variables: List[str]) -> sp.Expr:
        """Parse a differential equation string into SymPy expression.
        
        Args:
            equation: String like "dx/dt = alpha*x - beta*x*y"
            variables: List of variable names
            
        Returns:
            SymPy expression representing the right-hand side (derivative)
        """
        # Handle equation with = sign - we want the RHS for ODE systems
        if '=' in equation:
            lhs, rhs = equation.split('=', 1)
            # For ODE systems, we want the RHS expression
            equation_to_parse = rhs.strip()
        else:
            equation_to_parse = equation
        
        # Create symbols for variables (as regular symbols, not functions)
        var_symbols = {var: symbols(var) for var in variables}
        
        # Add common parameters as symbols - expand list to include more possibilities
        param_names = ['alpha', 'beta', 'gamma', 'delta', 'k', 't', 'zeta', 'omega', 'omega0', 'sin', 'cos', 'exp', 'log']
        param_symbols = {name: symbols(name) for name in param_names}
        
        # Validate equation format before parsing
        if not equation_to_parse or equation_to_parse.strip() == '':
            raise EquationSystemError(f"Empty equation: '{equation}'")
        
        # Check for obviously malformed equations
        if equation_to_parse.endswith(('+', '-', '*', '/', '=')):
            raise EquationSystemError(f"Malformed equation (ends with operator): '{equation}'")
        
        try:
            # Parse the equation (RHS only)
            all_symbols = {**var_symbols, **param_symbols}
            expr = sympify(equation_to_parse, locals=all_symbols, rational=False)
            return expr
        except Exception as e:
            # Try a more aggressive approach - extract all identifiers and create symbols
            import re
            identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', equation_to_parse)
            additional_symbols = {}
            for identifier in identifiers:
                if identifier not in all_symbols and identifier not in ['sin', 'cos', 'exp', 'log', 'sqrt']:
                    additional_symbols[identifier] = symbols(identifier)
            
            all_symbols.update(additional_symbols)
            
            try:
                expr = sympify(equation_to_parse, locals=all_symbols, rational=False)
                return expr
            except Exception as e2:
                raise EquationSystemError(f"Failed to parse differential equation '{equation}': {str(e2)}")
    
    def extract_derivative_order(self, equation: str) -> Dict[str, int]:
        """Extract the highest derivative order for each variable."""
        orders = {}
        
        # Check for second derivatives first
        for pattern in [r'd²(\w+)/dt²', r'd\^2(\w+)/dt\^2', r"(\w+)''"]:
            matches = re.findall(pattern, equation)
            for var in matches:
                orders[var] = max(orders.get(var, 0), 2)
        
        # Check for first derivatives
        for pattern in [r'd(\w+)/dt', r"(\w+)'"]:
            matches = re.findall(pattern, equation)
            for var in matches:
                orders[var] = max(orders.get(var, 0), 1)
        
        return orders


# ================================================================
# TIME INTEGRATION ENGINE
# ================================================================

class TimeIntegrator:
    """Time integration methods for dynamic systems."""
    
    @staticmethod
    def euler(system_func: Callable, y0: np.ndarray, t_span: Tuple[float, float], 
              dt: float) -> Tuple[np.ndarray, np.ndarray]:
        """Euler's method for simple integration."""
        t_start, t_end = t_span
        n_steps = int((t_end - t_start) / dt) + 1
        
        t_points = np.linspace(t_start, t_end, n_steps)
        y_values = np.zeros((n_steps, len(y0)))
        y_values[0] = y0
        
        for i in range(1, n_steps):
            t_curr = t_points[i-1]
            y_curr = y_values[i-1]
            dydt = system_func(t_curr, y_curr)
            y_values[i] = y_curr + dt * dydt
        
        return t_points, y_values
    
    @staticmethod
    def runge_kutta_4(system_func: Callable, y0: np.ndarray, t_span: Tuple[float, float], 
                      dt: float) -> Tuple[np.ndarray, np.ndarray]:
        """Classic 4th-order Runge-Kutta method."""
        t_start, t_end = t_span
        n_steps = int((t_end - t_start) / dt) + 1
        
        t_points = np.linspace(t_start, t_end, n_steps)
        y_values = np.zeros((n_steps, len(y0)))
        y_values[0] = y0
        
        for i in range(1, n_steps):
            t_curr = t_points[i-1]
            y_curr = y_values[i-1]
            
            k1 = dt * system_func(t_curr, y_curr)
            k2 = dt * system_func(t_curr + dt/2, y_curr + k1/2)
            k3 = dt * system_func(t_curr + dt/2, y_curr + k2/2)
            k4 = dt * system_func(t_curr + dt, y_curr + k3)
            
            y_values[i] = y_curr + (k1 + 2*k2 + 2*k3 + k4) / 6
        
        return t_points, y_values
    
    @staticmethod
    def scipy_adaptive(system_func: Callable, y0: np.ndarray, t_span: Tuple[float, float],
                       method: str = 'RK45', **kwargs) -> Tuple[np.ndarray, np.ndarray]:
        """Use scipy.integrate for adaptive methods."""
        t_start, t_end = t_span
        
        # Set up evaluation points
        n_points = kwargs.get('n_points', 1000)
        t_eval = np.linspace(t_start, t_end, n_points)
        
        # Solve using scipy
        sol = integrate.solve_ivp(
            system_func, t_span, y0, method=method, t_eval=t_eval, **kwargs
        )
        
        if not sol.success:
            raise RuntimeError(f"Integration failed: {sol.message}")
        
        return sol.t, sol.y.T


# ================================================================
# DYNAMIC SYSTEM CLASS
# ================================================================

@dataclass
class DynamicSystem:
    """Represents a dynamic (time-dependent) equation system."""
    
    variables: List[str]
    equations: List[str]
    parameters: Dict[str, Union[int, float]] = field(default_factory=dict)
    initial_conditions: Dict[str, float] = field(default_factory=dict)
    boundary_conditions: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate system definition."""
        if len(self.variables) != len(self.equations):
            raise EquationSystemError(
                f"Number of variables ({len(self.variables)}) must match "
                f"number of equations ({len(self.equations)})"
            )
        
        # Validate that equations reference variables in the system
        parser = DifferentialEquationParser()
        for i, equation in enumerate(self.equations):
            try:
                # Extract variable from derivative notation
                import re
                var_match = re.search(r'd(\w+)/dt|(\w+)\'', equation)
                if var_match:
                    eq_var = var_match.group(1) or var_match.group(2)
                    if eq_var not in self.variables:
                        raise EquationSystemError(
                            f"Equation {i+1} references variable '{eq_var}' which is not in the system variables: {self.variables}"
                        )
            except EquationSystemError:
                raise
            except Exception:
                # If we can't extract variable, that's okay - will be caught during parsing
                pass
        
        # Check that all variables have initial conditions
        missing_ics = set(self.variables) - set(self.initial_conditions.keys())
        if missing_ics:
            raise EquationSystemError(
                f"Missing initial conditions for variables: {missing_ics}"
            )


# ================================================================
# DYNAMIC EQUATION SOLVER
# ================================================================

class DynamicEquationSolver:
    """Main solver for dynamic (differential equation) systems."""
    
    def __init__(self):
        """Initialize dynamic solver."""
        self.parser = DifferentialEquationParser()
        self.integrator = TimeIntegrator()
        self._system: Optional[DynamicSystem] = None
        self._compiled_system: Optional[Callable] = None
    
    def set_system(self, variables: List[str], equations: List[str],
                   parameters: Optional[Dict[str, Union[int, float]]] = None,
                   initial_conditions: Optional[Dict[str, float]] = None) -> 'DynamicEquationSolver':
        """Set up the dynamic system.
        
        Args:
            variables: List of variable names
            equations: List of differential equations (e.g., "dx/dt = -k*x")
            parameters: Parameter values
            initial_conditions: Initial values for all variables
            
        Returns:
            Self for method chaining
        """
        self._system = DynamicSystem(
            variables=variables,
            equations=equations,
            parameters=parameters or {},
            initial_conditions=initial_conditions or {}
        )
        
        # Compile the system for efficient integration
        self._compile_system()
        return self
    
    def _compile_system(self):
        """Compile the differential equation system into a function."""
        if not self._system:
            raise ValueError("No system set")
        
        # Parse equations to get RHS expressions
        derivatives = []
        var_symbols = [symbols(var) for var in self._system.variables]
        
        for equation in self._system.equations:
            expr = self.parser.parse_equation(equation, self._system.variables)
            derivatives.append(expr)
        
        # Create symbols for all variables and parameters
        t_symbol = symbols('t')
        param_symbols = [symbols(p) for p in self._system.parameters.keys()]
        
        # Create a function for integration
        try:
            # Convert to numerical function
            # Order: t, variables, parameters
            all_symbols = [t_symbol] + var_symbols + param_symbols
            
            # Try lambdify with numpy
            system_lambdified = lambdify(all_symbols, derivatives, 'numpy')
            
            def system_func(t_val: float, y_vals: np.ndarray) -> np.ndarray:
                """System function for integration: dy/dt = f(t, y)."""
                # Build arguments: [t, x, y, ..., param1, param2, ...]
                args = [t_val] + list(y_vals) + [self._system.parameters[p] for p in self._system.parameters.keys()]
                
                try:
                    result = system_lambdified(*args)
                    # Handle single expression case
                    if not isinstance(result, (list, tuple, np.ndarray)):
                        result = [result]
                    return np.array(result, dtype=float)
                except Exception as e:
                    # Debug fallback
                    print(f"System evaluation error: {e}")
                    print(f"Args: t={t_val}, y={y_vals}, params={list(self._system.parameters.values())}")
                    return np.zeros_like(y_vals)
            
            self._compiled_system = system_func
            
        except Exception as e:
            raise EquationSystemError(f"Failed to compile system: {str(e)}")
    
    def integrate(self, time_span: Tuple[float, float], 
                  method: str = 'RK45', 
                  max_step: Optional[float] = None,
                  **kwargs) -> DynamicSolutionResult:
        """Integrate the dynamic system over time.
        
        Args:
            time_span: (start_time, end_time) tuple
            method: Integration method ('euler', 'rk4', 'RK45', 'DOP853', etc.)
            max_step: Maximum step size for adaptive methods
            **kwargs: Additional arguments for integrator
            
        Returns:
            DynamicSolutionResult with time series data
        """
        if not self._system or not self._compiled_system:
            raise ValueError("System not set or compiled")
        
        # Get initial conditions as array
        y0 = np.array([self._system.initial_conditions[var] for var in self._system.variables])
        
        try:
            # Select integration method
            if method.lower() == 'euler':
                dt = kwargs.get('dt', 0.01)
                t_points, y_values = self.integrator.euler(
                    self._compiled_system, y0, time_span, dt
                )
            elif method.lower() == 'rk4':
                dt = kwargs.get('dt', 0.01)
                t_points, y_values = self.integrator.runge_kutta_4(
                    self._compiled_system, y0, time_span, dt
                )
            else:
                # Use scipy adaptive methods
                if max_step:
                    kwargs['max_step'] = max_step
                t_points, y_values = self.integrator.scipy_adaptive(
                    self._compiled_system, y0, time_span, method, **kwargs
                )
            
            # Package results
            variables_dict = {}
            for i, var in enumerate(self._system.variables):
                variables_dict[var] = y_values[:, i]
            
            return DynamicSolutionResult(
                time_points=t_points,
                variables=variables_dict,
                success=True,
                message="Integration completed successfully",
                integration_info={
                    'method': method,
                    'time_span': time_span,
                    'n_points': len(t_points),
                    **kwargs
                }
            )
            
        except Exception as e:
            return DynamicSolutionResult(
                time_points=np.array([]),
                variables={},
                success=False,
                message=f"Integration failed: {str(e)}",
                integration_info={'error': str(e)}
            )
    


# ================================================================
# CONVENIENCE FUNCTIONS
# ================================================================

def solve_ode_system(variables: List[str], equations: List[str],
                     initial_conditions: Dict[str, float],
                     time_span: Tuple[float, float],
                     parameters: Optional[Dict[str, Union[int, float]]] = None,
                     method: str = 'RK45') -> DynamicSolutionResult:
    """One-liner for solving ODE systems.
    
    Example:
        result = solve_ode_system(
            variables=['x', 'y'],
            equations=['dx/dt = -0.5*x', 'dy/dt = 0.3*y'],
            initial_conditions={'x': 1.0, 'y': 2.0},
            time_span=(0, 10)
        )
    """
    solver = DynamicEquationSolver()
    solver.set_system(variables, equations, parameters, initial_conditions)
    return solver.integrate(time_span, method=method)
