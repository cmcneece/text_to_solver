#!/usr/bin/env python3
"""
Prototype Implementation of User-Friendly TextToSolver Design
Shows how to implement OOP improvements while maintaining backward compatibility
"""

from typing import List, Dict, Union, Optional, Any, Protocol
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import numpy as np
from enum import Enum

# ================================================================
# 1. CORE DOMAIN OBJECTS
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
        
        if len(self.dependent_variables) != len(self.equations):
            raise EquationSystemError.mismatched_system(
                len(self.dependent_variables), 
                len(self.equations)
            )
        
        # Check for duplicate variables
        all_vars = self.dependent_variables + self.independent_variables
        if len(all_vars) != len(set(all_vars)):
            duplicates = [v for v in set(all_vars) if all_vars.count(v) > 1]
            raise EquationSystemError.duplicate_variables(duplicates)
    
    @property
    def n_variables(self) -> int:
        return len(self.dependent_variables)
    
    @property 
    def n_equations(self) -> int:
        return len(self.equations)
    
    def with_parameters(self, new_params: Dict[str, Union[int, float]]) -> 'EquationSystem':
        """Return new system with updated parameters (immutable pattern)."""
        return EquationSystem(
            dependent_variables=self.dependent_variables,
            equations=self.equations,
            independent_variables=self.independent_variables,
            parameters={**self.parameters, **new_params}
        )

class SystemType(Enum):
    """Enumeration of detectable system types."""
    LINEAR = "linear"
    POLYNOMIAL = "polynomial" 
    CHEMICAL_EQUILIBRIUM = "chemical_equilibrium"
    LOTKA_VOLTERRA = "lotka_volterra"
    GENERAL = "general"

@dataclass
class SolutionResult:
    """Rich, user-friendly solution result."""
    variables: Dict[str, np.ndarray]
    converged: bool
    iterations: int
    residual_norm: float
    system_type: Optional[SystemType] = None
    solver_info: Dict[str, Any] = field(default_factory=dict)
    
    def __getitem__(self, var_name: str) -> Union[float, np.ndarray]:
        """Enable result['x'] syntax."""
        if var_name not in self.variables:
            available = list(self.variables.keys())
            raise KeyError(f"Variable '{var_name}' not found. Available: {available}")
        
        values = self.variables[var_name]
        return values[0] if len(values) == 1 else values
    
    def __contains__(self, var_name: str) -> bool:
        """Enable 'x' in result syntax."""
        return var_name in self.variables
    
    @property
    def success(self) -> bool:
        """More intuitive success property."""
        return self.converged
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to simple dictionary (for single-point solutions)."""
        return {k: v[0] if len(v) == 1 else v for k, v in self.variables.items()}
    
    def summary(self) -> str:
        """Human-readable summary."""
        status = "✅ Converged" if self.converged else "❌ Failed"
        vars_summary = ", ".join(f"{k}={self[k]:.4g}" for k in self.variables.keys())
        return f"{status} in {self.iterations} iterations: {vars_summary}"
    
    def __repr__(self) -> str:
        return f"SolutionResult({self.summary()})"

# ================================================================
# 2. ENHANCED ERROR HANDLING
# ================================================================

class EquationSystemError(Exception):
    """Base class for equation system errors with helpful messages."""
    
    @classmethod
    def invalid_variables(cls, variables: Any, issue: str) -> 'EquationSystemError':
        return cls(
            f"Invalid variables: {issue}\n"
            f"  Received: {variables} (type: {type(variables).__name__})\n"
            f"  Expected: List of strings like ['x', 'y', 'z']\n"
            f"  Example: solver = TextToSolver(['x', 'y'], ['x + y - 1', 'x - y'])"
        )
    
    @classmethod
    def mismatched_system(cls, n_vars: int, n_eqs: int) -> 'EquationSystemError':
        return cls(
            f"System dimension mismatch:\n"
            f"  Variables: {n_vars}\n"
            f"  Equations: {n_eqs}\n"
            f"  Requirement: Number of variables must equal number of equations\n"
            f"  Suggestion: {'Add more equations' if n_vars > n_eqs else 'Add more variables or remove equations'}"
        )
    
    @classmethod
    def duplicate_variables(cls, duplicates: List[str]) -> 'EquationSystemError':
        return cls(
            f"Duplicate variable names found: {duplicates}\n"
            f"  Each variable name must be unique\n"
            f"  Suggestion: Rename variables to be distinct (e.g., x1, x2 instead of x, x)"
        )

class SolverError(Exception):
    """Base class for solver-related errors."""
    
    @classmethod
    def convergence_failed(cls, iterations: int, residual: float) -> 'SolverError':
        return cls(
            f"Solver failed to converge after {iterations} iterations\n"
            f"  Final residual: {residual:.2e}\n"
            f"  Suggestions:\n"
            f"    • Try a different initial guess (use multistart=True)\n"
            f"    • Increase max_iterations\n"
            f"    • Relax tolerance settings\n"
            f"    • Check equation formulation for errors"
        )

# ================================================================
# 3. STRATEGY PATTERN FOR INITIAL GUESSES
# ================================================================

class InitialGuessStrategy(ABC):
    """Abstract strategy for initial guess generation."""
    
    @abstractmethod
    def generate(self, system: EquationSystem, n_points: int = 1) -> Dict[str, np.ndarray]:
        """Generate initial guess for the system."""
        pass
    
    @abstractmethod
    def can_handle(self, system: EquationSystem) -> bool:
        """Check if this strategy can handle the given system."""
        pass
    
    @property
    @abstractmethod 
    def name(self) -> str:
        """Human-readable strategy name."""
        pass

class HeuristicGuessStrategy(InitialGuessStrategy):
    """General-purpose heuristic guess generation."""
    
    def generate(self, system: EquationSystem, n_points: int = 1) -> Dict[str, np.ndarray]:
        """Generate reasonable initial guesses."""
        guess = {}
        for var in system.dependent_variables:
            if any(pattern in var.lower() for pattern in ['ph', 'poh']):
                # Chemical systems - use neutral pH region
                guess[var] = np.full(n_points, 7.0)
            elif var.lower().startswith('p'):
                # Log-scale variables
                guess[var] = np.full(n_points, 2.0)
            else:
                # General variables
                guess[var] = np.full(n_points, 1.0)
        return guess
    
    def can_handle(self, system: EquationSystem) -> bool:
        return True  # Always available as fallback
    
    @property
    def name(self) -> str:
        return "heuristic"

class ScaledGuessStrategy(InitialGuessStrategy):
    """Scaled initial guess based on system characteristics."""
    
    def generate(self, system: EquationSystem, n_points: int = 1) -> Dict[str, np.ndarray]:
        guess = {}
        for var in system.dependent_variables:
            # Scale based on variable naming patterns
            if 'concentration' in var.lower() or var.startswith('c_'):
                scale = 1e-3  # Typical concentration scale
            elif var.lower() in ['ph', 'poh']:
                scale = 7.0   # Neutral pH
            elif var.startswith('p') and len(var) > 1:
                scale = 3.0   # Log scale
            else:
                scale = 1.0
                
            # Add small random perturbation for multipoint
            base_value = np.full(n_points, scale)
            if n_points > 1:
                perturbation = np.random.normal(0, scale * 0.1, n_points)
                guess[var] = base_value + perturbation
            else:
                guess[var] = base_value
                
        return guess
    
    def can_handle(self, system: EquationSystem) -> bool:
        return True
    
    @property
    def name(self) -> str:
        return "scaled"

class GuessStrategyFactory:
    """Factory for creating and selecting guess strategies."""
    
    _strategies = {
        'heuristic': HeuristicGuessStrategy(),
        'scaled': ScaledGuessStrategy(),
        # Could add more strategies here
    }
    
    @classmethod
    def get_strategy(cls, name: str) -> InitialGuessStrategy:
        """Get strategy by name."""
        if name not in cls._strategies:
            available = list(cls._strategies.keys())
            raise ValueError(f"Unknown strategy '{name}'. Available: {available}")
        return cls._strategies[name]
    
    @classmethod
    def auto_select(cls, system: EquationSystem) -> InitialGuessStrategy:
        """Automatically select best strategy for system."""
        # Simple auto-selection logic
        equations_text = ' '.join(system.equations).lower()
        
        if any(pattern in equations_text for pattern in ['ph', 'poh', 'pk']):
            return cls._strategies['scaled']  # Better for chemical systems
        else:
            return cls._strategies['heuristic']  # General fallback

# ================================================================
# 4. USER-FRIENDLY SOLVER FACADE
# ================================================================

class UserTextToSolver:
    """User-friendly TextToSolver with better API design."""
    
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
            self.set_system(variables, equations, parameters, independent_variables)
    
    def set_system(self, 
                  variables: List[str], 
                  equations: List[str],
                  parameters: Optional[Dict[str, Union[int, float]]] = None,
                  independent_variables: Optional[List[str]] = None) -> 'UserTextToSolver':
        """Set up the equation system (fluent interface)."""
        self._system = EquationSystem(
            dependent_variables=variables,
            equations=equations,
            independent_variables=independent_variables or [],
            parameters=parameters or {}
        )
        return self
    
    def tolerance(self, tol: float) -> 'UserTextToSolver':
        """Set convergence tolerance (fluent interface)."""
        self._tolerance = tol
        return self
    
    def max_iterations(self, max_iter: int) -> 'UserTextToSolver':
        """Set maximum iterations (fluent interface).""" 
        self._max_iterations = max_iter
        return self
    
    def show_progress(self, show: bool = True) -> 'UserTextToSolver':
        """Enable/disable progress display (fluent interface)."""
        self._display_progress = show
        return self
    
    def guess_strategy(self, strategy: str) -> 'UserTextToSolver':
        """Set initial guess strategy (fluent interface)."""
        self._guess_strategy = strategy
        return self
    
    def with_parameters(self, params: Dict[str, Union[int, float]]) -> 'UserTextToSolver':
        """Update parameters (fluent interface)."""
        if self._system is None:
            raise ValueError("System not set. Call set_system() first.")
        
        self._system = self._system.with_parameters(params)
        return self
    
    def solve(self, 
             multistart: bool = False,
             custom_guess: Optional[Dict[str, np.ndarray]] = None) -> SolutionResult:
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
        
        # Use the existing TextToSolver internally (delegation pattern)
        from text_to_solver.TextToSolver import TextToSolver, SolverOptions
        
        # Create legacy solver
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
        
        try:
            if custom_guess:
                solution, report = legacy_solver.solve(custom_guess, options=options)
            else:
                solution, report = legacy_solver.solve_auto(
                    options=options,
                    multistart=multistart,
                    guess_strategy=self._guess_strategy
                )
            
            # Convert to user-friendly result format
            return SolutionResult(
                variables=solution,
                converged=report['exit_flag'] == 1,
                iterations=report['iter_count'],
                residual_norm=report['res_norm'],
                solver_info=report
            )
            
        except Exception as e:
            # Convert to more helpful error messages
            if "singular" in str(e).lower():
                raise SolverError(
                    f"Singular matrix encountered - system may be ill-conditioned\n"
                    f"Suggestions: Try multistart=True or check equation formulation"
                )
            else:
                raise SolverError(f"Solver failed: {e}")
    
    @classmethod
    def quick_solve(cls, 
                   variables: List[str],
                   equations: List[str], 
                   parameters: Optional[Dict[str, Union[int, float]]] = None,
                   tolerance: float = 1e-8) -> SolutionResult:
        """One-liner for simple equation solving."""
        return (cls()
                .set_system(variables, equations, parameters)
                .tolerance(tolerance)
                .solve())
    
    def parameter_sweep(self, 
                       parameter_name: str,
                       values: List[Union[int, float]]) -> List[SolutionResult]:
        """Efficiently solve for multiple parameter values.""" 
        if self._system is None:
            raise ValueError("No equation system set.")
            
        results = []
        for value in values:
            try:
                result = self.with_parameters({parameter_name: value}).solve()
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
# 5. DOMAIN-SPECIFIC HELPERS
# ================================================================

class ChemicalEquilibrium:
    """Domain-specific helpers for chemical equilibrium problems."""
    
    @staticmethod
    def water_autoionization(pH: float = 7.0, temperature_c: float = 25.0) -> SolutionResult:
        """Solve water autoionization equilibrium."""
        # Temperature-dependent Kw (simplified)
        kw_exponent = 14.0 if temperature_c == 25.0 else 14.0 + (temperature_c - 25.0) * 0.01
        
        return UserTextToSolver.quick_solve(
            variables=['pH', 'pOH'],
            equations=[f'-{kw_exponent} + pH + pOH', f'pH - {pH}']
        )
    
    @staticmethod
    def buffer_system(pka: float, total_conc: float, pH: float) -> SolutionResult:
        """Solve acid-base buffer equilibrium."""
        return UserTextToSolver.quick_solve(
            variables=['pA', 'pHA'],
            equations=[
                f'-{pka} + pA + {pH} - pHA',
                f'log10(10**pA + 10**pHA) - {np.log10(total_conc)}'
            ]
        )

# ================================================================
# 6. DEMONSTRATION
# ================================================================

def demo_user_api():
    """Demonstrate the user-friendly API design."""
    print("🚀 User-Friendly TextToSolver API Demo")
    print("=" * 40)
    
    # Method 1: Fluent interface
    print("\n1️⃣ Fluent Interface:")
    result = (UserTextToSolver()
              .set_system(['x', 'y'], ['x**2 + y**2 - 4', 'x + y - 2'])
              .tolerance(1e-10)
              .guess_strategy('scaled')
              .solve())
    
    print(f"   {result}")
    print(f"   Solution: x={result['x']:.4f}, y={result['y']:.4f}")
    
    # Method 2: One-liner
    print("\n2️⃣ One-liner:")
    water_result = ChemicalEquilibrium.water_autoionization(pH=6.5)
    print(f"   {water_result}")
    
    # Method 3: Parameter sweep
    print("\n3️⃣ Parameter Sweep:")
    solver = UserTextToSolver(['pH', 'pOH'], ['-14 + pH + pOH', 'pH - target_pH'])
    
    ph_results = solver.parameter_sweep('target_pH', [6.0, 7.0, 8.0])
    for i, result in enumerate(ph_results):
        pH_target = [6.0, 7.0, 8.0][i]
        if result.success:
            print(f"   pH {pH_target} → pOH = {result['pOH']:.3f}")
    
    print(f"\n✨ Key Improvements:")
    print(f"   • Fluent interface for easy configuration")
    print(f"   • Rich result objects with direct access")
    print(f"   • Better error messages and validation")
    print(f"   • Domain-specific helper functions")
    print(f"   • Efficient parameter sweep utilities")

if __name__ == "__main__":
    demo_user_api()
