#!/usr/bin/env python3
"""
User-friendly API components for TextToSolver
High-level API with backward compatibility
"""

from typing import List, Dict, Union, Optional, Any
from dataclasses import dataclass, field
import numpy as np
import numpy.typing as npt

# Import existing TextToSolver for delegation
from .TextToSolver import TextToSolver, SolverOptions


# ================================================================
# 1. IMPROVED DOMAIN OBJECTS
# ================================================================

@dataclass
class EquationSystem:
    """Well-defined representation of an equation system."""
    dependent_variables: List[str]
    equations: List[str]
    independent_variables: List[str] = field(default_factory=list)
    parameters: Dict[str, Union[int, float]] = field(default_factory=dict)

    def __post_init__(self):
        """Validate the system after creation."""
        self._validate()

    def _validate(self) -> None:
        """Comprehensive validation with helpful error messages."""
        if not isinstance(self.dependent_variables, list):
            raise EquationSystemError.invalid_variables(
                self.dependent_variables,
                "Must be a list"
            )

        if not all(isinstance(v, str) for v in self.dependent_variables):
            raise EquationSystemError.invalid_variables(
                self.dependent_variables,
                "All variables must be strings"
            )

        if not isinstance(self.equations, list):
            raise EquationSystemError.invalid_equations(
                self.equations,
                "Must be a list"
            )

        if not all(isinstance(eq, str) for eq in self.equations):
            raise EquationSystemError.invalid_equations(
                self.equations,
                "All equations must be strings"
            )

        if len(self.dependent_variables) != len(self.equations):
            raise EquationSystemError.mismatched_system(
                len(self.dependent_variables),
                len(self.equations)
            )

        # Check for duplicate variables
        all_vars = self.dependent_variables + self.independent_variables
        if len(all_vars) != len(set(all_vars)):
            dupes = [v for v in set(all_vars) if all_vars.count(v) > 1]
            raise EquationSystemError.duplicate_variables(dupes)

    @property
    def n_variables(self) -> int:
        return len(self.dependent_variables)

    @property
    def n_equations(self) -> int:
        return len(self.equations)

    def with_parameters(self, new_params: Dict[str, Union[int, float]]
                       ) -> 'EquationSystem':
        """Return new system with updated parameters (immutable pattern)."""
        return EquationSystem(
            dependent_variables=self.dependent_variables.copy(),
            equations=self.equations.copy(),
            independent_variables=self.independent_variables.copy(),
            parameters={**self.parameters, **new_params}
        )



@dataclass
class SolutionResult:
    """Rich, user-friendly solution result."""
    variables: Dict[str, npt.NDArray[np.float64]]
    converged: bool
    iterations: int
    residual_norm: float
    solver_info: Dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, var_name: str
                   ) -> Union[float, npt.NDArray[np.float64]]:
        """Enable result['x'] syntax."""
        if var_name not in self.variables:
            available = list(self.variables.keys())
            msg = f"Variable '{var_name}' not found. Available: {available}"
            raise KeyError(msg)

        values = self.variables[var_name]
        return values[0] if len(values) == 1 else values

    def __contains__(self, var_name: str) -> bool:
        """Enable 'x' in result syntax."""
        return var_name in self.variables

    @property
    def success(self) -> bool:
        """More intuitive success property."""
        return self.converged

    def to_dict(self) -> Dict[str, Union[float, npt.NDArray[np.float64]]]:
        """Convert to simple dictionary (for single-point solutions)."""
        return {k: (v[0] if len(v) == 1 else v)
                for k, v in self.variables.items()}

    def summary(self) -> str:
        """Human-readable summary."""
        status = "✅ Converged" if self.converged else "❌ Failed"
        var_keys = list(self.variables.keys())[:3]
        vars_summary = ", ".join(f"{k}={self[k]:.4g}" for k in var_keys)
        if len(self.variables) > 3:
            vars_summary += "..."
        return f"{status} in {self.iterations} iterations: {vars_summary}"

    def __repr__(self) -> str:
        return f"SolutionResult({self.summary()})"



# ================================================================
# 2. IMPROVED ERROR HANDLING
# ================================================================


class EquationSystemError(Exception):
    """Base class for equation system errors with helpful messages."""

    @classmethod
    def invalid_variables(cls, variables: Any, issue: str
                         ) -> 'EquationSystemError':
        return cls(
            f"Invalid variables: {issue}\n"
            f"  Received: {variables} (type: {type(variables).__name__})\n"
            f"  Expected: List of strings like ['x', 'y', 'z']\n"
            f"  Example: EquationSolver(['x', 'y'], ['x + y - 1', 'x - y'])"
        )

    @classmethod
    def invalid_equations(cls, equations: Any, issue: str
                         ) -> 'EquationSystemError':
        return cls(
            f"Invalid equations: {issue}\n"
            f"  Received: {equations} (type: {type(equations).__name__})\n"
            f"  Expected: List of equation strings\n"
            f"  Example: ['x**2 + y**2 - 4', 'x + y - 2']"
        )

    @classmethod
    def mismatched_system(cls, n_vars: int, n_eqs: int
                         ) -> 'EquationSystemError':
        action = ("Add more equations" if n_vars > n_eqs
                  else "Add more variables or remove equations")
        return cls(
            f"System dimension mismatch:\n"
            f"  Variables: {n_vars}\n"
            f"  Equations: {n_eqs}\n"
            f"  Requirement: Number of variables must equal equations\n"
            f"  Suggestion: {action}"
        )

    @classmethod
    def duplicate_variables(cls, duplicates: List[str]
                           ) -> 'EquationSystemError':
        return cls(
            f"Duplicate variable names found: {duplicates}\n"
            f"  Each variable name must be unique\n"
            f"  Suggestion: Rename to be distinct (e.g., x1, x2 not x, x)"
        )



class SolverError(Exception):
    """Base class for solver-related errors."""

    @classmethod
    def convergence_failed(cls, iterations: int, residual: float
                          ) -> 'SolverError':
        return cls(
            f"Solver failed to converge after {iterations} iterations\n"
            f"  Final residual: {residual:.2e}\n"
            f"  Suggestions:\n"
            f"    • Try different initial guess (use multistart=True)\n"
            f"    • Increase max_iterations\n"
            f"    • Relax tolerance settings\n"
            f"    • Check equation formulation for errors"
        )


# ================================================================
# 3. IMPROVED SOLVER FACADE
# ================================================================


class EquationSolver:
    """Improved, user-friendly equation solver with clean API."""

    def __init__(self,
                 variables: Optional[List[str]] = None,
                 equations: Optional[List[str]] = None,
                 parameters: Optional[Dict[str, Union[int, float]]] = None,
                 independent_variables: Optional[List[str]] = None):
        """
        Initialize solver with optional immediate setup.

        Args:
            variables: List of dependent variable names
            equations: List of equation strings
            parameters: Parameter values dict
            independent_variables: List of independent variable names
        """
        self._system: Optional[EquationSystem] = None
        self._tolerance = 1e-8
        self._max_iterations = 50
        self._display_progress = False
        self._guess_strategy = 'auto'

        # If provided, create system immediately
        if variables and equations:
            self.set_system(variables, equations, parameters,
                           independent_variables)
    
    def set_system(self, 
                  variables: List[str], 
                  equations: List[str],
                  parameters: Optional[Dict[str, Union[int, float]]] = None,
                  independent_variables: Optional[List[str]] = None) -> 'EquationSolver':
        """Set up the equation system (fluent interface)."""
        self._system = EquationSystem(
            dependent_variables=variables,
            equations=equations,
            independent_variables=independent_variables or [],
            parameters=parameters or {}
        )
        return self
    
    def tolerance(self, tol: float) -> 'EquationSolver':
        """Set convergence tolerance (fluent interface)."""
        self._tolerance = tol
        return self
    
    def max_iterations(self, max_iter: int) -> 'EquationSolver':
        """Set maximum iterations (fluent interface).""" 
        self._max_iterations = max_iter
        return self
    
    def show_progress(self, show: bool = True) -> 'EquationSolver':
        """Enable/disable progress display (fluent interface)."""
        self._display_progress = show
        return self
    
    def guess_strategy(self, strategy: str) -> 'EquationSolver':
        """Set initial guess strategy (fluent interface)."""
        self._guess_strategy = strategy
        return self
    
    def with_parameters(self, params: Dict[str, Union[int, float]]) -> 'EquationSolver':
        """Update parameters (fluent interface)."""
        if self._system is None:
            raise ValueError("System not set. Call set_system() first.")
        
        self._system = self._system.with_parameters(params)
        return self
    
    def solve(self, 
             multistart: bool = False,
             custom_guess: Optional[Dict[str, npt.NDArray[np.float64]]] = None) -> SolutionResult:
        """
        Solve the equation system.
        
        Args:
            multistart: Use multiple starting points for robustness
            custom_guess: User-provided initial guess
            
        Returns:
            Rich SolutionResult object
        """
        if self._system is None:
            raise ValueError("No equation system set. Call set_system() first.")
        
        # Delegate to existing TextToSolver (backward compatibility)
        try:
            legacy_solver = TextToSolver(
                dep_vars=self._system.dependent_variables,
                residual=self._system.equations,
                indep_vars=self._system.independent_variables,
                parameters=self._system.parameters
            )
            
            # Configure options
            options = SolverOptions(
                tol_fun=self._tolerance,
                max_iter=self._max_iterations,
                display=self._display_progress
            )
            
            # Solve using appropriate method
            if custom_guess:
                solution, report = legacy_solver.solve(custom_guess, options=options)
            else:
                solution, report = legacy_solver.solve_auto(
                    options=options,
                    multistart=multistart,
                    guess_strategy=self._guess_strategy
                )
            
            # Check for singular matrix or convergence failure BEFORE returning
            from text_to_solver.TextToSolver import SingularMatrixError
            if report['exit_flag'] == -1:
                raise SolverError(
                    f"Singular matrix encountered - system may be ill-conditioned\n"
                    f"Suggestions: Try multistart=True or check equation formulation"
                )
            elif report['exit_flag'] == 0 and report['res_norm'] > self._tolerance:
                raise SolverError.convergence_failed(self._max_iterations, report['res_norm'])
            
            # Convert to user-friendly result format
            # Consider exit_flag 2 as success if residual is small (step size convergence)
            converged = (report['exit_flag'] == 1) or (report['exit_flag'] == 2 and report['res_norm'] < 1e-6)
            return SolutionResult(
                variables=solution,
                converged=converged,
                iterations=report['iter_count'],
                residual_norm=report['res_norm'],
                solver_info=report
            )
            
        except SolverError:
            # Re-raise SolverError as-is
            raise
        except Exception as e:
            # Convert to more helpful error messages
            from text_to_solver.TextToSolver import SingularMatrixError
            error_msg = str(e).lower()
            if isinstance(e, SingularMatrixError) or "singular" in error_msg:
                raise SolverError(
                    f"Singular matrix encountered - system may be ill-conditioned\n"
                    f"Original error: {e}\n"
                    f"Suggestions: Try multistart=True or check equation formulation"
                )
            elif "convergence" in error_msg or "exit_flag" in error_msg:
                raise SolverError.convergence_failed(self._max_iterations, 0.0)
            else:
                raise SolverError(f"Solver failed: {e}")
    
    @classmethod
    def solve_equations(cls, 
                       variables: List[str],
                       equations: List[str], 
                       parameters: Optional[Dict[str, Union[int, float]]] = None,
                       tolerance: float = 1e-8,
                       multistart: bool = False) -> SolutionResult:
        """One-liner for simple equation solving."""
        return (cls()
                .set_system(variables, equations, parameters)
                .tolerance(tolerance)
                .solve(multistart=multistart))
    
    def parameter_sweep(self, 
                       parameter_name: str,
                       values: List[Union[int, float]]) -> List[SolutionResult]:
        """Efficiently solve for multiple parameter values with robust convergence.""" 
        if self._system is None:
            raise ValueError("No equation system set. Call set_system() first.")
            
        results = []
        for value in values:
            try:
                # Use multistart for better robustness in parameter sweeps
                result = self.with_parameters({parameter_name: value}).solve(multistart=True)
                results.append(result)
            except Exception as e:
                # Create failed result for consistency
                failed_result = SolutionResult(
                    variables={var: np.array([np.nan]) for var in self._system.dependent_variables},
                    converged=False,
                    iterations=0,
                    residual_norm=np.inf,
                    solver_info={'error': str(e)}
                )
                results.append(failed_result)
        
        return results

# ================================================================
# GENERAL-PURPOSE SOLVER - NO DOMAIN-SPECIFIC ASSUMPTIONS
# ================================================================
# Note: Domain-specific knowledge (chemistry, physics, etc.) should be
# implemented as user extensions or examples, not built into the core solver
