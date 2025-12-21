#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 13:09:56 2018

@author: cmcneece
"""
from pandas import DataFrame
import numpy as np
import numpy.typing as npt
import sympy as sp
from scipy.sparse import spdiags, vstack, hstack, csr_matrix
from scipy.sparse.linalg import norm, spsolve
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Tuple, Any
import re
import time


@dataclass
class SolverOptions:
    """Configuration options for the Newton solver.
    
    Attributes:
        tol_fun: Tolerance for the residual function (default: 1e-6)
        tol_x: Tolerance for the step size (default: 1e-8)
        max_iter: Maximum number of iterations (default: 20)
        display: Whether to display iteration information (default: True)
        alpha: Parameter for line search (default: 1e-4)
        min_lambda: Minimum lambda for backtracking (default: 0.1)
        max_lambda: Maximum lambda for backtracking (default: 0.5)
        store_history: Whether to store iteration history (default: True)
        constraint_handling: How to handle initial guess constraint violations
            'error' - Raise error if initial guess violates constraints
            'project' - Automatically project to feasible region with warning  
            'project_silent' - Automatically project without warning
            'ignore' - Allow infeasible initial guesses (original behavior)
        constraint_tolerance: Tolerance for detecting constraint violations (default: 1e-12)
    """
    tol_fun: float = 1e-6
    tol_x: float = 1e-8
    max_iter: int = 20
    display: bool = True
    alpha: float = 1e-4
    min_lambda: float = 0.1
    max_lambda: float = 0.5
    store_history: bool = True
    constraint_handling: str = 'project'
    constraint_tolerance: float = 1e-12


@dataclass
class BoxConstraints:
    """Box constraints for variables (lower and upper bounds).
    
    Attributes:
        bounds: Dict mapping variable names to (lower, upper) tuples
        lower_bounds: Dict of variable lower bounds (computed from bounds)
        upper_bounds: Dict of variable upper bounds (computed from bounds)
    """
    bounds: Dict[str, Tuple[Optional[float], Optional[float]]]
    
    def __post_init__(self):
        """Process bounds into separate lower/upper bound dicts."""
        self.lower_bounds = {}
        self.upper_bounds = {}
        
        for var, (lower, upper) in self.bounds.items():
            if lower is not None:
                self.lower_bounds[var] = float(lower)
            if upper is not None:
                self.upper_bounds[var] = float(upper)
                
        # Validate bounds
        for var, (lower, upper) in self.bounds.items():
            if lower is not None and upper is not None and lower >= upper:
                raise ValueError(f"Invalid bounds for {var}: lower ({lower}) >= upper ({upper})")
    
    def has_constraints(self) -> bool:
        """Check if any constraints are defined."""
        return len(self.bounds) > 0
    
    def is_constrained(self, var: str) -> bool:
        """Check if a specific variable has constraints."""
        return var in self.bounds
    
    def project_vector(self, variables: List[str], x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Project solution vector to feasible region."""
        x_projected = x.copy()
        
        for i, var in enumerate(variables):
            if var in self.lower_bounds:
                x_projected[i] = max(x_projected[i], self.lower_bounds[var])
            if var in self.upper_bounds:
                x_projected[i] = min(x_projected[i], self.upper_bounds[var])
                
        return x_projected
    
    def compute_constraint_violations(self, variables: List[str], x: npt.NDArray[np.float64]) -> Dict[str, float]:
        """Compute constraint violations for current solution."""
        violations = {}
        
        for i, var in enumerate(variables):
            violation = 0.0
            if var in self.lower_bounds:
                violation += max(0.0, self.lower_bounds[var] - x[i])
            if var in self.upper_bounds:
                violation += max(0.0, x[i] - self.upper_bounds[var])
            
            if violation > 0:
                violations[var] = violation
                
        return violations
    
    def get_active_constraints(self, variables: List[str], x: npt.NDArray[np.float64], tol: float = 1e-8) -> Dict[str, str]:
        """Get constraints that are currently active (within tolerance)."""
        active = {}
        
        for i, var in enumerate(variables):
            if var in self.lower_bounds and abs(x[i] - self.lower_bounds[var]) <= tol:
                active[var] = 'lower'
            elif var in self.upper_bounds and abs(x[i] - self.upper_bounds[var]) <= tol:
                active[var] = 'upper'
                
        return active


@dataclass
class IterationData:
    """Data captured at each solver iteration.
    
    Attributes:
        iteration: Iteration number (0-based)
        timestamp: Time when iteration occurred
        elapsed_time: Time elapsed since solver start
        residual_norm: L2 norm of residual vector
        step_norm: L2 norm of Newton step
        convergence_rate: Logarithmic convergence rate
        lambda_factor: Line search factor used
        condition_number: Approximate condition number (1/reciprocal_condition)
        residual_vector: Full residual vector at this iteration
        jacobian_matrix: Full Jacobian matrix at this iteration (optional)
        solution_vector: Current solution vector
        solver_params: Dict of solver parameters used
        constraint_violations: Dict of constraint violations at this iteration
        active_constraints: Dict of currently active constraints
        projection_applied: Whether solution was projected due to constraints
    """
    iteration: int
    timestamp: float
    elapsed_time: float
    residual_norm: float
    step_norm: float
    convergence_rate: float
    lambda_factor: float
    condition_number: float
    residual_vector: npt.NDArray[np.float64]
    solution_vector: npt.NDArray[np.float64]
    solver_params: Dict[str, Any]
    jacobian_matrix: Optional[Any] = None  # Can be large, optional storage
    constraint_violations: Dict[str, float] = field(default_factory=dict)
    active_constraints: Dict[str, str] = field(default_factory=dict)
    projection_applied: bool = False


class ValidationError(Exception):
    """Custom exception for validation errors in TextToSolver."""
    pass


class SingularMatrixError(Exception):
    """Custom exception for singular matrix errors."""
    pass


class TextToSolver:
    """TextToSolver class, instatiates the system of equations object.

    This class accept a list of strings representing the residual of a system
    of equations. The class uses sympy to generate the analytic Jacobian and
    the system and appropriate lambdas for use in slope based solvers.

    Args:
        dep_vars (list): A list of strings representing the dependent variables
        residual (list): A list of strings representing the residual of the
            system of equations.

    Optional Args:
        indep_vars (list): A list of strings representing the independent
            variables.
        parameters: (dict): A dictionary holding the name of parameters in the
            system of equations as a key, and the value to be subsituted as the
            value.
        constraints: (dict): A dictionary mapping variable names to (lower, upper)
            bound tuples. Use None for unbounded directions. Example:
            {'x': (0, 10), 'y': (None, 5)} constrains x ∈ [0,10] and y ≤ 5.

    Returns:
        object: The TextToSolver object with tools for the solution of the
            system of equations.

    Attributes:
        residual_string (list): A list of strings representing the system of
            equations after parameter values have been substituted.
        variables_string (list): A list of strings representing the dependent
            variables of the system of equations.
        indep_variables_string (list): A list of strings representing the
            independent variables of the system of equations.
        parameters (dict): A dictionary holding the name of parameters in the
            system of equations as a key, and the value to be subsituted as the
            value.
        residual_symb (list): A list of the residual as symbolic functions.
        residual_func (list): A list of the residual as lambda functions
        jacoabian_string (DataFrame): A DataFrame of the Jacobian as a strings.
        jacobian_symb (DataFrame): A DataFrame of the Jacobian as a symbolic
            functions.
        jacobian_func (DataFrame): A DataFrame of the Jacobian as a lambda
            functions.
    """
    def __init__(self, 
                 dep_vars: List[str], 
                 residual: List[str], 
                 indep_vars: Optional[List[str]] = None, 
                 parameters: Optional[Dict[str, Union[int, float]]] = None,
                 constraints: Optional[Dict[str, Tuple[Optional[float], Optional[float]]]] = None) -> None:
        if indep_vars is None:
                indep_vars = []
        if parameters is None:
                parameters = {}
        
        # Input validation
        self._validate_inputs(dep_vars, residual, indep_vars, parameters)
        
        self.residual_string = residual
        self.variables_string = dep_vars
        self.indep_vars = indep_vars
        self.parameters = parameters

        # Constraint handling
        if constraints is None:
            constraints = {}
        self.constraints = BoxConstraints(constraints) if constraints else BoxConstraints({})
        
        # Validate constraints against variables
        if self.constraints.has_constraints():
            for var in self.constraints.bounds.keys():
                if var not in dep_vars:
                    raise ValueError(f"Constraint variable '{var}' not found in dependent variables: {dep_vars}")

        # Iteration history storage
        self._iteration_history: List[IterationData] = []
        self._solve_start_time: Optional[float] = None

        self.generate_symbolic()
        self.functionalize()

    @property
    def dep_vars(self) -> List[str]:
        """Backward compatibility property for variables_string."""
        return self.variables_string

    @classmethod
    def from_equations(cls,
                      equations: List[str],
                      variables: Optional[List[str]] = None,
                      parameters: Optional[Dict[str, Union[int, float]]] = None,
                      indep_vars: Optional[List[str]] = None,
                      constraints: Optional[Dict[str, Tuple[Optional[float], Optional[float]]]] = None) -> 'TextToSolver':
        """
        Create a TextToSolver instance from equation strings.
        
        Args:
            equations: List of equation strings (e.g., ['x + y = 3', 'x - y = 1'])
            variables: Optional list of dependent variable names (auto-detected if None)
            parameters: Optional dictionary of parameter values
            indep_vars: Optional list of independent variable names
            constraints: Optional dictionary of variable constraints
            
        Returns:
            TextToSolver instance
        """
        import re
        
        # Validate equations have equals signs (required for from_equations)
        for eq in equations:
            if '=' not in eq:
                raise ValidationError(f"Equations must contain '=' sign. Got: {eq}")
        
        # Convert equations to residual form (move everything to LHS)
        residuals = []
        for eq in equations:
            if '=' in eq:
                # Split on = and move to residual form
                lhs, rhs = eq.split('=', 1)
                residual = f"({lhs.strip()}) - ({rhs.strip()})"
            else:
                # Should not reach here due to validation above, but handle gracefully
                residual = eq.strip()
            residuals.append(residual)
        
        # Auto-detect variables if not provided
        if variables is None:
            variables = set()
            excluded = {'sin', 'cos', 'tan', 'exp', 'log', 'sqrt', 'pi', 'e',
                       'log10', 'abs', 'max', 'min', 'sum', 'np', 'abs'}
            
            for eq in residuals:
                # Find potential variable names
                matches = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_]*\b', eq)
                for match in matches:
                    if match not in excluded:
                        variables.add(match)
            
            # Remove parameters if provided
            if parameters:
                variables = variables - set(parameters.keys())
            
            # Remove independent variables if provided
            if indep_vars:
                variables = variables - set(indep_vars)
            
            variables = sorted(list(variables))
        
        if not variables:
            raise ValidationError("No dependent variables found")
        
        return cls(
            dep_vars=variables,
            residual=residuals,
            indep_vars=indep_vars or [],
            parameters=parameters or {},
            constraints=constraints
        )

    def get_variables(self) -> List[str]:
        '''Return the variables as a list of strings.'''
        return self.variables_string

    def get_residual(self) -> List[Any]:
        '''Resturn the residual as a list of strings.'''
        return self.residual_symb

    def get_jacobian(self) -> DataFrame:
        '''Return the Jacobian as a DataFrame of strings.'''
        return self.jacobian_string

    def get_parameters(self) -> Dict[str, Union[int, float]]:
        '''Return the parameters as a dictionary.'''
        return self.parameters
    
    def get_constraints(self) -> BoxConstraints:
        '''Return the current constraints object.'''
        return self.constraints
    
    def add_constraint(self, variable: str, lower: Optional[float] = None, upper: Optional[float] = None) -> None:
        """Add or update constraint for a single variable.
        
        Args:
            variable: Variable name to constrain
            lower: Lower bound (None for no lower bound)  
            upper: Upper bound (None for no upper bound)
        """
        if variable not in self.variables_string:
            raise ValueError(f"Variable '{variable}' not found in dependent variables: {self.variables_string}")
        
        if lower is not None and upper is not None and lower >= upper:
            raise ValueError(f"Invalid bounds for {variable}: lower ({lower}) >= upper ({upper})")
        
        # Update constraints - merge with existing bounds if they exist
        new_bounds = self.constraints.bounds.copy()
        if variable in new_bounds:
            existing_lower, existing_upper = new_bounds[variable]
            # Preserve existing bounds if new ones are None
            merged_lower = lower if lower is not None else existing_lower
            merged_upper = upper if upper is not None else existing_upper
            new_bounds[variable] = (merged_lower, merged_upper)
        else:
            new_bounds[variable] = (lower, upper)
        self.constraints = BoxConstraints(new_bounds)
    
    def add_constraints(self, constraints: Dict[str, Tuple[Optional[float], Optional[float]]]) -> None:
        """Add or update constraints for multiple variables.
        
        Args:
            constraints: Dict mapping variable names to (lower, upper) bound tuples
        """
        # Validate all variables first
        for var in constraints.keys():
            if var not in self.variables_string:
                raise ValueError(f"Constraint variable '{var}' not found in dependent variables: {self.variables_string}")
        
        # Update constraints
        new_bounds = self.constraints.bounds.copy()
        new_bounds.update(constraints)
        self.constraints = BoxConstraints(new_bounds)
    
    def remove_constraint(self, variable: str) -> None:
        """Remove constraint for a variable.
        
        Args:
            variable: Variable name to unconstrain
        """
        if variable in self.constraints.bounds:
            new_bounds = self.constraints.bounds.copy()
            del new_bounds[variable]
            self.constraints = BoxConstraints(new_bounds)
    
    def clear_constraints(self) -> None:
        """Remove all constraints."""
        self.constraints = BoxConstraints({})
    
    def has_constraints(self) -> bool:
        """Check if any constraints are defined."""
        return self.constraints.has_constraints()
    
    def check_constraint_feasibility(self, solution: Dict[str, npt.NDArray[np.float64]]) -> Dict[str, Any]:
        """Check if a solution satisfies all constraints.
        
        Args:
            solution: Solution dictionary from solve methods
            
        Returns:
            Dict with feasibility information
        """
        if not self.has_constraints():
            return {'feasible': True, 'violations': {}, 'max_violation': 0.0}
        
        # Convert solution to vector format
        x = np.array([solution[var][0] for var in self.variables_string])
        
        violations = self.constraints.compute_constraint_violations(self.variables_string, x)
        max_violation = max(violations.values()) if violations else 0.0
        
        return {
            'feasible': len(violations) == 0,
            'violations': violations,
            'max_violation': max_violation,
            'active_constraints': self.constraints.get_active_constraints(self.variables_string, x)
        }

    def get_iteration_history(self) -> List[IterationData]:
        """Get the complete iteration history from the last solve.
        
        Returns:
            List of IterationData objects capturing solver progress
        """
        return self._iteration_history.copy()

    def get_residual_history(self) -> List[float]:
        """Get residual norm values from iteration history.
        
        Returns:
            List of residual norms at each iteration
        """
        return [iter_data.residual_norm for iter_data in self._iteration_history]

    def get_convergence_history(self) -> List[float]:
        """Get convergence rate values from iteration history.
        
        Returns:
            List of convergence rates at each iteration
        """
        return [iter_data.convergence_rate for iter_data in self._iteration_history]

    def get_step_history(self) -> List[float]:
        """Get step norm values from iteration history.
        
        Returns:
            List of step norms at each iteration
        """
        return [iter_data.step_norm for iter_data in self._iteration_history]

    def analyze_convergence(self) -> Dict[str, Any]:
        """Analyze convergence behavior from iteration history.
        
        Returns:
            Dictionary with convergence analysis metrics
        """
        if not self._iteration_history:
            return {"error": "No iteration history available"}
        
        residuals = self.get_residual_history()
        convergence_rates = self.get_convergence_history()
        
        analysis = {
            "total_iterations": len(self._iteration_history),
            "initial_residual": residuals[0] if residuals else None,
            "final_residual": residuals[-1] if residuals else None,
            "residual_reduction": residuals[0] / residuals[-1] if len(residuals) > 1 and residuals[-1] > 0 else float('inf'),
            "average_convergence_rate": np.mean(convergence_rates) if convergence_rates else 0.0,
            "total_solve_time": self._iteration_history[-1].elapsed_time if self._iteration_history else 0.0,
            "iterations_per_second": len(self._iteration_history) / self._iteration_history[-1].elapsed_time if self._iteration_history and self._iteration_history[-1].elapsed_time > 0 else 0.0
        }
        
        # Determine convergence pattern
        if len(residuals) >= 3:
            # Check for quadratic convergence (Newton's method ideal behavior)
            ratios = []
            for i in range(2, len(residuals)):
                if residuals[i-1] > 0 and residuals[i-2] > 0:
                    ratio = (residuals[i] / residuals[i-1]) / (residuals[i-1] / residuals[i-2])
                    ratios.append(ratio)
            
            if ratios:
                avg_ratio = np.mean(ratios)
                if avg_ratio < 0.1:
                    analysis["convergence_type"] = "quadratic (excellent)"
                elif avg_ratio < 0.5:
                    analysis["convergence_type"] = "superlinear (good)"
                elif avg_ratio < 0.9:
                    analysis["convergence_type"] = "linear (acceptable)"
                else:
                    analysis["convergence_type"] = "slow/oscillating"
            else:
                analysis["convergence_type"] = "unable to determine"
        elif len(residuals) == 1:
            analysis["convergence_type"] = "single iteration"
        elif len(residuals) == 2:
            analysis["convergence_type"] = "insufficient data (2 iterations)"
        else:
            analysis["convergence_type"] = "no data available"
        
        return analysis
    
    def analyze_constraints(self) -> Dict[str, Any]:
        """Analyze constraint behavior from iteration history.
        
        Returns:
            Dictionary with constraint analysis metrics
        """
        if not self.has_constraints():
            return {"error": "No constraints defined"}
        
        if not self._iteration_history:
            return {"error": "No iteration history available"}
        
        # Analyze constraint activity through iterations
        total_iterations = len(self._iteration_history)
        projections_applied = sum(1 for iter_data in self._iteration_history if iter_data.projection_applied)
        iterations_with_violations = sum(1 for iter_data in self._iteration_history if iter_data.constraint_violations)
        
        # Track which constraints were active
        all_active_constraints = set()
        constraint_activity = {}
        
        for iter_data in self._iteration_history:
            for var, bound_type in iter_data.active_constraints.items():
                constraint_key = f"{var}_{bound_type}"
                all_active_constraints.add(constraint_key)
                if constraint_key not in constraint_activity:
                    constraint_activity[constraint_key] = 0
                constraint_activity[constraint_key] += 1
        
        # Final constraint status
        final_iter = self._iteration_history[-1]
        final_violations = final_iter.constraint_violations
        final_active = final_iter.active_constraints
        
        analysis = {
            "total_iterations": total_iterations,
            "projections_applied": projections_applied,
            "projection_rate": projections_applied / total_iterations if total_iterations > 0 else 0.0,
            "iterations_with_violations": iterations_with_violations,
            "constraint_activity": constraint_activity,
            "final_active_constraints": final_active,
            "final_violations": final_violations,
            "max_violation_during_solve": 0.0,
            "constraints_satisfied": len(final_violations) == 0
        }
        
        # Find maximum violation during solve
        max_violation = 0.0
        for iter_data in self._iteration_history:
            if iter_data.constraint_violations:
                iter_max = max(iter_data.constraint_violations.values())
                max_violation = max(max_violation, iter_max)
        
        analysis["max_violation_during_solve"] = max_violation
        
        # Classify constraint behavior
        if projections_applied == 0:
            constraint_behavior = "unconstrained (no projections needed)"
        elif final_active:
            constraint_behavior = "active constraints at solution"
        elif final_violations:
            constraint_behavior = "constraint violations at solution"
        else:
            constraint_behavior = "constraints satisfied (projections helped)"
            
        analysis["constraint_behavior"] = constraint_behavior
        
        return analysis
    
    def validate_initial_guess(self, guess: Dict[str, npt.NDArray[np.float64]]) -> Dict[str, Any]:
        """Validate that initial guess satisfies constraints.
        
        Args:
            guess: Initial guess dictionary with variable names as keys
            
        Returns:
            Dict with validation results
        """
        if not self.has_constraints():
            return {
                'valid': True,
                'violations': {},
                'max_violation': 0.0,
                'message': 'No constraints defined'
            }
        
        # Convert guess to array format
        x_guess = np.array([guess[var][0] for var in self.variables_string])
        
        # Check constraint violations
        violations = self.constraints.compute_constraint_violations(self.variables_string, x_guess)
        max_violation = max(violations.values()) if violations else 0.0
        
        result = {
            'valid': len(violations) == 0,
            'violations': violations,
            'max_violation': max_violation,
            'projected_guess': None
        }
        
        if violations:
            # Compute what the projected guess would be
            x_projected = self.constraints.project_vector(self.variables_string, x_guess)
            projected_guess = {var: np.array([x_projected[i]]) for i, var in enumerate(self.variables_string)}
            result['projected_guess'] = projected_guess
            
            violation_details = []
            for var, violation in violations.items():
                violation_details.append(f"{var}: violation = {violation:.6f}")
            
            result['message'] = f"Initial guess violates constraints: {', '.join(violation_details)}"
        else:
            result['message'] = 'Initial guess satisfies all constraints'
        
        return result
    
    def project_initial_guess(self, guess: Dict[str, npt.NDArray[np.float64]]) -> Dict[str, npt.NDArray[np.float64]]:
        """Project initial guess to satisfy constraints.
        
        Args:
            guess: Initial guess dictionary with variable names as keys
            
        Returns:
            Projected guess that satisfies all constraints
        """
        if not self.has_constraints():
            return guess.copy()
        
        # Convert to array format
        x_guess = np.array([guess[var][0] for var in self.variables_string])
        
        # Project to feasible region
        x_projected = self.constraints.project_vector(self.variables_string, x_guess)
        
        # Convert back to dictionary format
        projected_guess = {var: np.array([x_projected[i]]) for i, var in enumerate(self.variables_string)}
        
        return projected_guess

    def functionalize(self):
        '''Turn the symbolic residual and Jacobian into lambda functions.'''

        residual = self.residual_string
        variables = self.variables_string
        jacobian = self.jacobian_string

        # functionalize the residual
        residual_func = [sp.lambdify(self.indep_vars + variables, eq, np)
                         for eq in self.residual_string]

        # functionalize the jacobian
        jacobian_func = DataFrame(index=residual, columns=variables)
        for row in residual:
            for col in variables:
                jacobian_func.loc[row, col] = sp.lambdify(
                    self.indep_vars + variables, jacobian.loc[row, col], np)

        self.jacobian_func = jacobian_func
        self.residual_func = residual_func

    def generate_symbolic(self):
        '''Turn the string of residual and Jacobian into symbolic functions.'''

        # pull out residual information from self
        # Make a copy to avoid modifying the original equations
        sys_string = self.residual_string.copy()
        var_string = self.variables_string
        parameters = self.parameters

        # generate symbolic variables
        # turn the variable string list into a list of symbolics
        var_symb = [sp.symbols(var) for var in var_string]

        # substitute the parameter values into the equation string
        num_eqs = len(sys_string)
        for key, val in parameters.items():
            for index in range(num_eqs):
                # Use word boundary replacement to prevent partial matches
                sys_string[index] = re.sub(r'\b' + re.escape(key) + r'\b', str(val), sys_string[index])

        # Process equations with equals signs to convert to residual form
        sys_string = [self._process_equation_format(eq) for eq in sys_string]

        # turn the equation strings into symbolic functions
        # Catch parsing errors and provide helpful messages
        sys_symb = []
        for eq in sys_string:
            try:
                sys_symb.append(sp.sympify(eq))
            except Exception as e:
                # Check if this might be an equation without equals sign
                if '=' not in eq and any(char in eq for char in ['+', '-', '*', '/', '**']):
                    raise ValidationError(f"Error parsing equation: {eq}. Equations must contain '=' sign")
                else:
                    raise ValidationError(f"Error parsing equation: {eq}. {str(e)}")

        # build the jacobian
        jacobian_symb = DataFrame(index=sys_string, columns=var_string)
        for var_ind, var in enumerate(var_symb):
            for eq_ind, eq in enumerate(sys_symb):
                jacobian_symb.loc[sys_string[eq_ind], var_string[var_ind]] = \
                 sp.diff(eq, var)

        # convert symbolic jacobian into strings
        jacobian_string = DataFrame(index=sys_string, columns=var_string)
        for row in sys_string:
            for col in var_string:
                jacobian_string.loc[row, col] = \
                 str(jacobian_symb.loc[row, col])

        # put information back into self
        self.jacobian_string = jacobian_string
        self.jacobian_symb = jacobian_symb
        self.residual_string = sys_string
        self.variables_string = var_string
        self.variables_symb = var_symb
        self.residual_symb = sys_symb

    def _process_equation_format(self, equation_str):
        """Convert equation format (x + y = 3) to residual format (x + y - 3)."""
        if '=' in equation_str:
            # Split on equals sign and convert to residual form
            left, right = equation_str.split('=', 1)
            left = left.strip()
            right = right.strip()
            # Create residual: left - right
            return f"({left}) - ({right})"
        else:
            # Already in residual form
            return equation_str

    def _validate_inputs(self, 
                         dep_vars: List[str], 
                         residual: List[str], 
                         indep_vars: List[str], 
                         parameters: Dict[str, Union[int, float]]) -> None:
        """Validate input arguments to TextToSolver constructor."""
        # Validate dep_vars
        if not isinstance(dep_vars, list):
            raise ValidationError("dep_vars must be a list of strings")
        if not dep_vars:
            raise ValidationError("dep_vars cannot be empty")
        if not all(isinstance(var, str) for var in dep_vars):
            raise ValidationError("dep_vars must be a list of strings")
        
        # Validate residual
        if not isinstance(residual, list):
            raise ValidationError("residual must be a list of strings")
        if not residual:
            raise ValidationError("residual cannot be empty")
        if not all(isinstance(eq, str) for eq in residual):
            raise ValidationError("residual must be a list of strings")
        
        # Check length matching
        if len(dep_vars) != len(residual):
            raise ValidationError(
                f"Number of dependent variables ({len(dep_vars)}) must match "
                f"number of residual equations ({len(residual)})"
            )
        
        # Validate indep_vars
        if not isinstance(indep_vars, list):
            raise ValidationError("indep_vars must be a list of strings")
        if not all(isinstance(var, str) for var in indep_vars):
            raise ValidationError("indep_vars must be a list of strings")
        
        # Validate parameters
        if not isinstance(parameters, dict):
            raise ValidationError("parameters must be a dictionary")
        
        # Check for duplicate variable names
        all_vars = dep_vars + indep_vars
        if len(all_vars) != len(set(all_vars)):
            raise ValidationError("Variable names must be unique")

    def solve(self, 
              guess: Optional[Dict[str, npt.NDArray[np.float64]]] = None, 
              indep_var_val: Dict[str, npt.NDArray[np.float64]] = {}, 
              options: Union[Dict[str, Any], 'SolverOptions'] = {},
              input_options: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, npt.NDArray[np.float64]], Dict[str, Any]]:
        '''Pass the independent variable values to the Newton solver.

        Solves the system of equations given an initial guess for the dependent
        variables. If independent variables are specified, the solver will
        evaluate the system of equations with the provided values.

        Args:
            guess (dict): A dictionary of the dependent variables as keys and
                a value of the initial guess as the value. If independent
                variables are specified, and are arrays, the guess value must
                be an array of the same shape. If None, will use solve_auto().

        Optional Args:
            indep_vars (dict): A dictionary of the independent variables as
                keys and the values at which they are to be evaulated as
                values. The solver accepts single values of arrays.
            options (dict): A dictionary with options for the Newton solver.
                'DISPLAY': boolean, togles printing iter information (True)
                'TOL_X': tolerance in the Netwon step (1e-8)
                'TOL_FUN': tolerance of the residual function (1e-6)
                'MAX_ITER': maximum number of iterations before exiting (20)
                'ALPHA': parameter for decrease in step size
                'MIN_LAMBDA': minimum value of lamdba (0.1)
                'MAX_LAMBDA': maximum values of lambda (0.5)
            input_options (dict): Backward compatibility - merged into options if provided

        Returns:
            solution (dict): A dictionary containing the depedent variable
                names as keys, with the solution as values.
            report (dict): A dictionary with the diagnostic report of the
                solver including total iterations, value of the residual norm,
                the exit flag, and the resiprical condition of the Jacobian on
                the final step.
                    exit_flag:
                        2: step is too close to previous guess
                        1: solver converged
                        -1: Jacobian matrix may be singular
            '''
        
        # Handle backward compatibility: merge input_options into options
        if input_options is not None:
            if isinstance(options, dict):
                options = {**options, **input_options}
            else:
                # Convert SolverOptions to dict, merge, then convert back
                options_dict = {k: getattr(options, k) for k in dir(options) if not k.startswith('_')}
                options_dict.update(input_options)
                options = SolverOptions(**options_dict)
        
        # If no guess provided, use solve_auto
        if guess is None:
            return self.solve_auto(options=options, multistart=False, indep_var_val=indep_var_val)
        
        # Handle constraint validation for initial guess
        processed_guess = guess
        if self.has_constraints():
            # Convert options to SolverOptions if needed
            if isinstance(options, dict):
                solver_options = SolverOptions(**options)
            else:
                solver_options = options
                
            # Validate initial guess
            validation = self.validate_initial_guess(guess)
            
            if not validation['valid']:
                if solver_options.constraint_handling == 'error':
                    raise ValueError(f"Initial guess violates constraints: {validation['message']}. "
                                   f"Use solver.project_initial_guess(guess) to project to feasible region, "
                                   f"or set options.constraint_handling='project' for automatic projection.")
                                   
                elif solver_options.constraint_handling == 'project':
                    processed_guess = validation['projected_guess']
                    print(f"Warning: Initial guess violates constraints (max violation: {validation['max_violation']:.2e}). "
                          f"Automatically projected to feasible region.")
                    
                elif solver_options.constraint_handling == 'project_silent':
                    processed_guess = validation['projected_guess']
                    
                # For 'ignore', do nothing and use original guess
        
        x, report = self.newton_solver(processed_guess, indep_var_val=indep_var_val,
                                       options=options)
        x_dict = self.package_x(x)

        return x_dict, report

    def solve_auto(self, 
                   options: Union[Dict[str, Any], 'SolverOptions'] = {}, 
                   multistart: bool = False, 
                   guess_strategy: Optional[str] = None,
                   indep_var_val: Dict[str, npt.NDArray[np.float64]] = {}) -> Tuple[Dict[str, npt.NDArray[np.float64]], Dict[str, Any]]:
        """
        Automatically solve with intelligent guess generation.
        
        Args:
            options: Dictionary of solver options
            multistart: Use multiple starting points
            guess_strategy: Strategy for guess generation (unused for now)
            
        Returns:
            Tuple of (solution_dict, report_dict)
        """
        # Generate a constraint-aware automatic guess
        
        if self.has_constraints():
            # Generate guess that satisfies constraints
            auto_guess = {}
            for var in self.variables_string:
                if var in self.constraints.bounds:
                    lower, upper = self.constraints.bounds[var]
                    if lower is not None and upper is not None:
                        # Use midpoint of bounds
                        guess_val = (lower + upper) / 2.0
                    elif lower is not None:
                        # Use lower bound + 1
                        guess_val = lower + 1.0
                    elif upper is not None:
                        # Use upper bound - 1  
                        guess_val = upper - 1.0
                    else:
                        guess_val = 1.0
                else:
                    guess_val = 1.0
                auto_guess[var] = np.array([guess_val])
        else:
            # Default guess when no constraints
            auto_guess = {var: np.array([1.0]) for var in self.variables_string}
        
        if multistart:
            # Generate multiple constraint-aware starting points
            guesses = []
            
            if self.has_constraints():
                # Create diverse but feasible guesses
                for multiplier in [0.25, 0.5, 0.75, 1.0, 1.5]:
                    guess = {}
                    for var in self.variables_string:
                        if var in self.constraints.bounds:
                            lower, upper = self.constraints.bounds[var]
                            if lower is not None and upper is not None:
                                # Use different points along the feasible range
                                range_size = upper - lower
                                guess_val = lower + multiplier * range_size / 2.0
                                guess_val = max(lower, min(upper, guess_val))  # Clamp to bounds
                            elif lower is not None:
                                guess_val = lower + multiplier
                            elif upper is not None:
                                guess_val = upper - multiplier
                            else:
                                guess_val = multiplier
                        else:
                            guess_val = multiplier
                        guess[var] = np.array([guess_val])
                    guesses.append(guess)
            else:
                # Default multistart guesses when no constraints
                guesses = [
                    {var: np.array([1.0]) for var in self.variables_string},
                    {var: np.array([0.1]) for var in self.variables_string},
                    {var: np.array([10.0]) for var in self.variables_string},
                ]
            
            for i, guess in enumerate(guesses):
                try:
                    solution, report = self.solve(guess, indep_var_val=indep_var_val, options=options)
                    if report.get('exit_flag') == 1:  # Successful convergence
                        return solution, report
                except Exception:
                    continue
            
            # If all fail, try the first guess and let it fail normally
            return self.solve(guesses[0], indep_var_val=indep_var_val, options=options)
        else:
            # Single attempt with automatic guess
            return self.solve(auto_guess, indep_var_val=indep_var_val, options=options)

    def solve_multistart(self,
                        options: Union[Dict[str, Any], 'SolverOptions'] = {},
                        indep_var_val: Dict[str, npt.NDArray[np.float64]] = {}) -> Tuple[Dict[str, npt.NDArray[np.float64]], Dict[str, Any]]:
        """
        Solve using multiple starting points for robustness.
        
        Args:
            options: Solver options
            indep_var_val: Independent variable values
            
        Returns:
            Tuple of (solution_dict, report_dict)
        """
        return self.solve_auto(options=options, multistart=True, indep_var_val=indep_var_val)

    def generate_initial_guess(self,
                               strategy: str = 'auto',
                               indep_var_val: Optional[Dict[str, npt.NDArray[np.float64]]] = None) -> Dict[str, npt.NDArray[np.float64]]:
        """
        Generate an initial guess for the solver.
        
        Args:
            strategy: Guess generation strategy ('auto', 'zero', 'ones', 'random')
            indep_var_val: Optional independent variable values
            
        Returns:
            Dictionary mapping variable names to guess arrays
        """
        if indep_var_val is None:
            indep_var_val = {}
        
        if strategy == 'auto':
            # Use constraint-aware guess if constraints exist
            if self.has_constraints():
                guess = {}
                for var in self.variables_string:
                    if var in self.constraints.bounds:
                        lower, upper = self.constraints.bounds[var]
                        if lower is not None and upper is not None:
                            guess_val = (lower + upper) / 2.0
                        elif lower is not None:
                            guess_val = lower + 1.0
                        elif upper is not None:
                            guess_val = upper - 1.0
                        else:
                            guess_val = 1.0
                    else:
                        guess_val = 1.0
                    guess[var] = np.array([guess_val])
                return guess
            else:
                strategy = 'ones'
        
        if strategy == 'zero':
            return {var: np.array([0.0]) for var in self.variables_string}
        elif strategy == 'ones':
            return {var: np.array([1.0]) for var in self.variables_string}
        elif strategy == 'random':
            return {var: np.array([np.random.uniform(0.1, 10.0)]) for var in self.variables_string}
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def package_x(self, x):
        '''
        Turn solution array into a dictionary sorted by variable.
        '''

        x_list = self.resegment_x(x)
        temp_x = {var: x_list[ind] for ind, var in
                  enumerate(self.variables_string)}

        return temp_x

    def newton_solver(self, guess, indep_var_val, options):
        '''Newton solver for the system of equations.'''

        default_options = {'DISPLAY': True, 'MAX_ITER': 20,
                          'TOL_FUN': 1e-6, 'TOL_X': 1e-8,
                          'ALPHA': 1e-4, 'MIN_LAMBDA': 0.1,
                          'MAX_LAMBDA': 0.5}
        
        # Handle both SolverOptions dataclass and dictionary inputs
        if hasattr(options, '__dict__'):  # SolverOptions dataclass
            default_options.update({
                'DISPLAY': options.display,
                'MAX_ITER': options.max_iter,
                'TOL_FUN': options.tol_fun,
                'TOL_X': options.tol_x,
                'ALPHA': options.alpha,
                'MIN_LAMBDA': options.min_lambda,
                'MAX_LAMBDA': options.max_lambda,
                'STORE_HISTORY': getattr(options, 'store_history', True)
            })
        else:  # Dictionary
            default_options.update(options)
            # Ensure store_history is set if not provided
            if 'STORE_HISTORY' not in default_options:
                default_options['STORE_HISTORY'] = True
        
        options = default_options
        TOL_X = options['TOL_X']
        TOL_FUN = options['TOL_FUN']
        DISPLAY = options['DISPLAY']
        MAX_ITER = options['MAX_ITER']
        MIN_LAMBDA = options['MIN_LAMBDA']
        STORE_HISTORY = options['STORE_HISTORY']

        # Initialize iteration tracking
        if STORE_HISTORY:
            self._iteration_history.clear()
            self._solve_start_time = time.time()

        # get values out of the inputs
        guess, indep_var_val = self.unpack_inputs(guess, indep_var_val)
        x = np.vstack(guess).flatten()

        # evaluate residual and jacobian
        res, jac = self.evaluate_res_jac(guess, indep_var_val)
        f = np.dot(res.T, res)
        f2 = f

        # check if defined
        jac_sum = csr_matrix.sum(jac.tocsr())
        if np.isnan(jac_sum) or np.isinf(jac_sum):
            exit_flag = -1  # matrix may be singular
        else:
            exit_flag = 1  # normal exit

        # check the reciprocal condition, approximation to condition number
        resip_cond = 1/norm(jac)

        # check norm of residual
        res_norm = np.linalg.norm(res)

        # dummy values
        dx = np.zeros(res.shape)
        convergence = np.inf
        step_norm = np.inf
        projection_applied = False  # Initialize constraint projection flag

        # start counter
        iter_count = 0
        # backtracking
        lam = 1
        lam_1 = 1
        lam_2 = 1

        if DISPLAY:
            self.__print_newton_step(iter_count, res_norm, convergence,
                                     resip_cond, step_norm, first=True)
        # run the solver
        while (res_norm > TOL_FUN or lam < 1) and \
                exit_flag >= 0 and iter_count <= MAX_ITER:
            if lam == 1:
                # Newton-Raphson solver
                iter_count += 1  # increment counter
                dx = self.calculate_step(res, jac)  # calculate step
                g = res.T @ jac  # gradient of res_norm
                slope = np.dot(g, dx)  # slope of gradient
                f_old = np.dot(res.T, res)  # objective function
                x_old = x  # initial value
                lam_min = TOL_X/np.amax(np.abs(dx)/np.maximum(np.abs(x_old),
                                                              1))

            if lam < lam_min:
                exit_flag = 2  # x is too close to X_OLD
                break
            elif np.any(np.isnan(dx)) or np.any(np.isinf(dx)):
                exit_flag = -1  # matrix may be singular
                break

            x = x_old + dx * lam  # next guess
            
            # Apply constraint projection if constraints are defined
            projection_applied = False
            if self.has_constraints():
                x_before_projection = x.copy()
                x = self.constraints.project_vector(self.variables_string, x)
                projection_applied = not np.allclose(x_before_projection, x, atol=1e-12)
            
            x_list = self.resegment_x(x)
            res, jac = self.evaluate_res_jac(x_list, indep_var_val)
            f = np.dot(res.T, res)  # new objective function

            lam, lam_1 = self.__calculate_lambda(lam, f, f_old, slope, options,
                                                 f2, lam_1, lam_2)

            if lam < 1:
                lam_2 = lam_1
                f2 = f  # save 2nd most previous value
                lam = np.amax([lam, MIN_LAMBDA*lam_1])  # minimum step length
                continue

            res_norm_0 = res_norm  # old resnorm
            res_norm = np.linalg.norm(res)  # calculate new res_norm
            # calculate convergence rate
            convergence = np.log(res_norm_0/(res_norm + np.finfo(float).eps))
            step_norm = np.linalg.norm(dx)  # norm of the step

            # Capture iteration data
            if STORE_HISTORY:
                current_time = time.time()
                
                # Compute constraint information
                constraint_violations = {}
                active_constraints = {}
                if self.has_constraints():
                    constraint_violations = self.constraints.compute_constraint_violations(self.variables_string, x)
                    active_constraints = self.constraints.get_active_constraints(self.variables_string, x)
                
                iteration_data = IterationData(
                    iteration=iter_count,
                    timestamp=current_time,
                    elapsed_time=current_time - self._solve_start_time,
                    residual_norm=res_norm,
                    step_norm=step_norm,
                    convergence_rate=convergence,
                    lambda_factor=lam,
                    condition_number=1/resip_cond if resip_cond > 0 else float('inf'),
                    residual_vector=res.copy(),
                    solution_vector=x.copy(),
                    solver_params={
                        'tol_fun': TOL_FUN,
                        'tol_x': TOL_X,
                        'max_iter': MAX_ITER,
                        'alpha': options.get('ALPHA', 1e-4),
                        'min_lambda': MIN_LAMBDA
                    },
                    jacobian_matrix=jac.copy() if STORE_HISTORY else None,
                    constraint_violations=constraint_violations,
                    active_constraints=active_constraints,
                    projection_applied=projection_applied if 'projection_applied' in locals() else False
                )
                self._iteration_history.append(iteration_data)

            # display
            if DISPLAY:
                self.__print_newton_step(iter_count, res_norm, convergence,
                                         resip_cond, step_norm, first=False)

            jac_sum = csr_matrix.sum(jac.tocsr())
            if np.isnan(jac_sum) or np.isinf(jac_sum):
                exit_flag = -1  # matrix may be singular
                break
            # check the reciprocal condition, approximation to condition number
            resip_cond = 1/norm(jac)
        if DISPLAY:
            print('\n')

        report = {'exit_flag': exit_flag, 'res_norm': res_norm,
                  'iter_count': iter_count, 'resip_cond': resip_cond}
        
        # Add iteration history to report if captured
        if STORE_HISTORY:
            report['iteration_history'] = self._iteration_history.copy()
            report['total_solve_time'] = time.time() - self._solve_start_time if self._solve_start_time else 0.0
        
        return x, report

    def __calculate_lambda(self, lam, f, f_old, slope, options, f2, lam_1,
                           lam_2):
        # check for convergence
        lam_1 = lam  # save previous lambda
        if f > f_old + options['ALPHA']*lam*slope:
            if lam == 1:
                lam = -slope/2/(f-f_old-slope)  # calculate lambda
            else:
                A = 1/(lam_1 - lam_2)
                B = np.asarray([[1/lam_1 ** 2, -1/lam_2 ** 2],
                               [-lam_2/lam_1 ** 2, lam_1/lam_2 ** 2]],
                               dtype=float)
                C = np.asarray([f-f_old-lam_1*slope, f2-f_old-lam_2*slope],
                               dtype=float)
                coeff = A * np.dot(B, C)
                a, b = coeff[0], coeff[1]
                if a == 0:
                    lam = -slope/2/b
                else:
                    discriminant = b ** 2 - 3*a*slope
                    if discriminant < 0:
                        lam = options['MAX_LAMBDA']*lam_1
                    elif b <= 0:
                        lam = (-b+np.sqrt(discriminant))/3/a
                    else:
                        lam = -slope/(b+np.sqrt(discriminant))

            # minimum step length
            lam = np.amin([lam, options['MAX_LAMBDA']*lam_1])
        elif np.isnan(f) or np.isinf(f):
            # limit undefined evaluation or overflow
            lam = options['MAX_LAMBDA']*lam_1
        else:
            lam = 1  # fraction of Newton step

        return lam, lam_1

    def __print_newton_step(self, iter_count, res_norm, convergence,
                            resip_cond, step_norm, first):
            if first:
                print('{:<10}{:>20}{:>20}{:>20}{:>20}'.format('iter_count',
                                                              'res_norm',
                                                              'convergence',
                                                              'resip_cond',
                                                              'step_norm'))
                print('-'*90)

            print('{:<10d}{:>20.2e}{:>20.2e}{:>20.2e}{:>20.2e}'.format(
                                                                iter_count,
                                                                res_norm,
                                                                convergence,
                                                                resip_cond,
                                                                step_norm))

    def unpack_inputs(self, guess, indep_var_val):
        '''Turn a list of variable value arrays into a single array.'''

        # unpack input
        guess_list = [np.array(guess[var]) for var in self.variables_string]
#        pdb.set_trace()
        ind_var_list = [np.array(indep_var_val[var]) for
                        var in self.indep_vars]

        return guess_list, ind_var_list

    def resegment_x(self, x):
        '''
        Turn an array variable value arrays a list of arrays segmented by
        variable.
        '''

        len_res = len(self.variables_string)
        len_input = len(x)/len_res
        x = np.reshape(x, (int(len_res), int(len_input)))
        temp_x = [x[i, :] for i in range(len_res)]

        return temp_x

    def evaluate_res_jac(self, guess, ind_var_val):
        '''Evaluate the residual and Jacobian at specified values.'''

        # determine size of system
        num_res = len(self.residual_string)
        num_val = 1 if (not ind_var_val) else len(ind_var_val[0])

        # build empty df for jacobian
        jac = DataFrame(index=self.residual_string,
                        columns=self.variables_string)

        # evaluate residual
        res = [eq(*ind_var_val, *guess) for eq in self.residual_func]
        residual = np.asarray(res).flatten()

        # evaluate jacobian
        for eq in self.residual_string:
            for var in self.variables_string:
                temp = self.jacobian_func.loc[eq, var](*ind_var_val,
                                                       *guess)*np.ones(num_val)
                jac.loc[eq, var] = spdiags(temp, 0, num_val, num_val)
        jac_mat = jac.values
        jacobian = [hstack(jac_mat[ind, :]) for ind in range(num_res)]
        jacobian = vstack(jacobian[:])

        return residual, jacobian

    def calculate_step(self, residual, jacobian):
        '''Calculate the Newton iteration step by inverting the Jacobian.'''

        dx = spsolve(-jacobian.tocsr(), residual)
        return dx
