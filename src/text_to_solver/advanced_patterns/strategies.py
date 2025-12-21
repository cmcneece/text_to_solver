"""
Strategy Pattern Implementation for TextToSolver

Provides pluggable algorithms for solving, line search, and convergence criteria.
This allows users to easily swap different algorithms for optimal performance.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
import numpy as np
import numpy.typing as npt
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import spsolve

# Import from parent modules
from ..TextToSolver import SolverOptions
from ..user_api import SolutionResult


@dataclass
class StrategyResult:
    """Result from a strategy execution."""
    success: bool
    value: Any
    info: Dict[str, Any]
    
    
class SolverStrategy(ABC):
    """Abstract base class for solver strategies."""
    
    @abstractmethod
    def solve(self, 
             residual_func: Callable,
             jacobian_func: Callable,
             initial_guess: Dict[str, npt.NDArray[np.float64]],
             options: SolverOptions,
             callback_manager: Optional[Any] = None) -> SolutionResult:
        """Solve the nonlinear system using this strategy.
        
        Args:
            residual_func: Function to evaluate residuals
            jacobian_func: Function to evaluate Jacobian
            initial_guess: Initial guess for variables
            options: Solver options
            callback_manager: Optional callback manager for monitoring
            
        Returns:
            SolutionResult with solution and convergence info
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get strategy name."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get strategy description."""
        pass


class NewtonRaphsonStrategy(SolverStrategy):
    """Newton-Raphson solver strategy with configurable line search."""
    
    def __init__(self, 
                 line_search: Optional['LineSearchStrategy'] = None,
                 convergence: Optional['ConvergenceStrategy'] = None):
        """Initialize Newton-Raphson strategy.
        
        Args:
            line_search: Line search strategy (default: backtracking)
            convergence: Convergence strategy (default: residual-based)
        """
        self.line_search = line_search or BacktrackingLineSearch()
        self.convergence = convergence or ResidualConvergence()
    
    def solve(self, 
             residual_func: Callable,
             jacobian_func: Callable, 
             initial_guess: Dict[str, npt.NDArray[np.float64]],
             options: SolverOptions,
             callback_manager: Optional[Any] = None) -> SolutionResult:
        """Solve using Newton-Raphson method."""
        from ..advanced_patterns.observers import SolverEvent
        import time
        
        # Convert guess to array format
        x = self._dict_to_array(initial_guess)
        variables = list(initial_guess.keys())
        
        # Initialize monitoring
        start_time = time.time()
        if callback_manager:
            callback_manager.notify_start(SolverEvent(
                'start', 0, start_time, float('inf')
            ))
        
        # Newton-Raphson iterations
        for iteration in range(options.max_iter):
            # Evaluate residual and Jacobian
            residual = residual_func(x)
            jacobian = jacobian_func(x)
            
            residual_norm = np.linalg.norm(residual)
            
            # Notify observers
            if callback_manager:
                callback_manager.notify_iteration(SolverEvent(
                    'iteration', iteration, time.time(), residual_norm
                ))
            
            # Check convergence
            if self.convergence.check_convergence(residual, x, iteration, options):
                result = self._create_success_result(
                    variables, x, residual_norm, iteration, time.time() - start_time
                )
                if callback_manager:
                    callback_manager.notify_convergence(SolverEvent(
                        'convergence', iteration, time.time(), residual_norm
                    ))
                return result
            
            # Compute Newton step
            try:
                step = spsolve(jacobian, -residual)
            except:
                result = self._create_failure_result(
                    variables, x, residual_norm, iteration, 'singular_jacobian'
                )
                if callback_manager:
                    callback_manager.notify_failure(SolverEvent(
                        'failure', iteration, time.time(), residual_norm
                    ))
                return result
            
            # Line search for step size
            step_size = self.line_search.compute_step_size(
                x, step, residual_func, residual, residual_norm
            )
            
            # Update solution
            x = x + step_size * step
        
        # Maximum iterations reached
        result = self._create_failure_result(
            variables, x, residual_norm, options.max_iter, 'max_iterations'
        )
        if callback_manager:
            callback_manager.notify_failure(SolverEvent(
                'failure', options.max_iter, time.time(), residual_norm
            ))
        return result
    
    def get_name(self) -> str:
        return "Newton-Raphson"
    
    def get_description(self) -> str:
        return f"Newton-Raphson with {self.line_search.get_name()} line search"
    
    def _dict_to_array(self, guess_dict: Dict[str, npt.NDArray[np.float64]]) -> npt.NDArray[np.float64]:
        """Convert dictionary guess to array."""
        return np.concatenate([v.flatten() for v in guess_dict.values()])
    
    def _array_to_dict(self, x: npt.NDArray[np.float64], variables: List[str]) -> Dict[str, npt.NDArray[np.float64]]:
        """Convert array solution back to dictionary."""
        n_vars = len(variables)
        chunk_size = len(x) // n_vars
        result = {}
        for i, var in enumerate(variables):
            start_idx = i * chunk_size
            end_idx = (i + 1) * chunk_size
            result[var] = x[start_idx:end_idx]
        return result
    
    def _create_success_result(self, variables: List[str], x: npt.NDArray[np.float64], 
                              residual_norm: float, iterations: int, solve_time: float) -> SolutionResult:
        """Create successful solution result."""
        solution_dict = self._array_to_dict(x, variables)
        return SolutionResult(
            variables=solution_dict,
            converged=True,
            iterations=iterations,
            residual_norm=residual_norm,
            solver_info={
                'strategy': self.get_name(),
                'solve_time': solve_time,
                'exit_flag': 1
            }
        )
    
    def _create_failure_result(self, variables: List[str], x: npt.NDArray[np.float64],
                              residual_norm: float, iterations: int, reason: str) -> SolutionResult:
        """Create failed solution result."""
        solution_dict = self._array_to_dict(x, variables)
        return SolutionResult(
            variables=solution_dict,
            converged=False,
            iterations=iterations,
            residual_norm=residual_norm,
            solver_info={
                'strategy': self.get_name(),
                'exit_flag': -1,
                'failure_reason': reason
            }
        )


class BroydenStrategy(SolverStrategy):
    """Broyden's method (quasi-Newton) solver strategy."""
    
    def __init__(self, 
                 update_method: str = 'good',
                 convergence: Optional['ConvergenceStrategy'] = None):
        """Initialize Broyden strategy.
        
        Args:
            update_method: 'good' or 'bad' Broyden update
            convergence: Convergence strategy
        """
        self.update_method = update_method
        self.convergence = convergence or ResidualConvergence()
    
    def solve(self, residual_func, jacobian_func, initial_guess, options, callback_manager=None):
        """Solve using Broyden's method."""
        # Simplified implementation - would need full quasi-Newton implementation
        # For now, delegate to Newton-Raphson
        newton_strategy = NewtonRaphsonStrategy(convergence=self.convergence)
        return newton_strategy.solve(residual_func, jacobian_func, initial_guess, options, callback_manager)
    
    def get_name(self) -> str:
        return f"Broyden-{self.update_method.title()}"
    
    def get_description(self) -> str:
        return f"Broyden's {self.update_method} method (quasi-Newton)"


class LineSearchStrategy(ABC):
    """Abstract base class for line search strategies."""
    
    @abstractmethod
    def compute_step_size(self, 
                         x: npt.NDArray[np.float64],
                         direction: npt.NDArray[np.float64], 
                         func: Callable,
                         f_val: npt.NDArray[np.float64],
                         f_norm: float) -> float:
        """Compute optimal step size.
        
        Args:
            x: Current point
            direction: Search direction  
            func: Function to evaluate
            f_val: Current function value
            f_norm: Current function norm
            
        Returns:
            Optimal step size
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get strategy name."""
        pass


class BacktrackingLineSearch(LineSearchStrategy):
    """Backtracking line search strategy."""
    
    def __init__(self, 
                 alpha: float = 1e-4,
                 rho: float = 0.5,
                 max_backtracks: int = 20):
        """Initialize backtracking line search.
        
        Args:
            alpha: Armijo parameter
            rho: Backtracking factor
            max_backtracks: Maximum backtracking steps
        """
        self.alpha = alpha
        self.rho = rho
        self.max_backtracks = max_backtracks
    
    def compute_step_size(self, x, direction, func, f_val, f_norm):
        """Compute step size using backtracking."""
        step_size = 1.0
        
        for _ in range(self.max_backtracks):
            x_new = x + step_size * direction
            try:
                f_new = func(x_new)
                f_new_norm = np.linalg.norm(f_new)
                
                # Armijo condition (sufficient decrease)
                if f_new_norm <= (1 - self.alpha * step_size) * f_norm:
                    return step_size
                    
            except:
                # Function evaluation failed, reduce step size
                pass
            
            step_size *= self.rho
        
        return step_size
    
    def get_name(self) -> str:
        return "Backtracking"


class ArmijoLineSearch(LineSearchStrategy):
    """Armijo line search strategy."""
    
    def __init__(self, c1: float = 1e-4, max_iter: int = 20):
        """Initialize Armijo line search.
        
        Args:
            c1: Armijo parameter
            max_iter: Maximum iterations
        """
        self.c1 = c1
        self.max_iter = max_iter
    
    def compute_step_size(self, x, direction, func, f_val, f_norm):
        """Compute step size using Armijo rule."""
        # Simplified Armijo - similar to backtracking for this implementation
        return BacktrackingLineSearch(alpha=self.c1).compute_step_size(
            x, direction, func, f_val, f_norm
        )
    
    def get_name(self) -> str:
        return "Armijo"


class ConvergenceStrategy(ABC):
    """Abstract base class for convergence strategies."""
    
    @abstractmethod
    def check_convergence(self, 
                         residual: npt.NDArray[np.float64],
                         x: npt.NDArray[np.float64],
                         iteration: int,
                         options: SolverOptions) -> bool:
        """Check if convergence criteria are met.
        
        Args:
            residual: Current residual vector
            x: Current solution vector
            iteration: Current iteration number
            options: Solver options
            
        Returns:
            True if converged, False otherwise
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get strategy name."""
        pass


class ResidualConvergence(ConvergenceStrategy):
    """Residual-based convergence strategy."""
    
    def __init__(self, relative_tolerance: Optional[float] = None):
        """Initialize residual convergence.
        
        Args:
            relative_tolerance: Optional relative tolerance
        """
        self.relative_tolerance = relative_tolerance
    
    def check_convergence(self, residual, x, iteration, options):
        """Check residual norm convergence."""
        residual_norm = np.linalg.norm(residual)
        
        # Absolute tolerance check
        if residual_norm < options.tol_fun:
            return True
        
        # Relative tolerance check (if specified)
        if self.relative_tolerance and iteration > 0:
            # Would need previous residual for relative check
            # Simplified for now
            pass
        
        return False
    
    def get_name(self) -> str:
        return "Residual"


class StepSizeConvergence(ConvergenceStrategy):
    """Step size-based convergence strategy."""
    
    def __init__(self, step_tolerance: Optional[float] = None):
        """Initialize step size convergence.
        
        Args:
            step_tolerance: Step size tolerance
        """
        self.step_tolerance = step_tolerance
        self.previous_x = None
    
    def check_convergence(self, residual, x, iteration, options):
        """Check step size convergence."""
        if self.previous_x is not None:
            step_norm = np.linalg.norm(x - self.previous_x)
            tolerance = self.step_tolerance or getattr(options, 'tol_x', 1e-6)
            
            if step_norm < tolerance:
                return True
        
        self.previous_x = x.copy()
        return False
    
    def get_name(self) -> str:
        return "StepSize"


class CombinedConvergence(ConvergenceStrategy):
    """Combined convergence strategy using multiple criteria."""
    
    def __init__(self, strategies: List[ConvergenceStrategy], require_all: bool = False):
        """Initialize combined convergence.
        
        Args:
            strategies: List of convergence strategies
            require_all: If True, all strategies must converge; if False, any one
        """
        self.strategies = strategies
        self.require_all = require_all
    
    def check_convergence(self, residual, x, iteration, options):
        """Check combined convergence criteria."""
        results = [strategy.check_convergence(residual, x, iteration, options) 
                  for strategy in self.strategies]
        
        if self.require_all:
            return all(results)
        else:
            return any(results)
    
    def get_name(self) -> str:
        strategy_names = [s.get_name() for s in self.strategies]
        connector = " AND " if self.require_all else " OR "
        return connector.join(strategy_names)


# Factory functions for creating common strategy combinations
def create_robust_newton_strategy() -> NewtonRaphsonStrategy:
    """Create a robust Newton-Raphson strategy with backtracking."""
    return NewtonRaphsonStrategy(
        line_search=BacktrackingLineSearch(alpha=1e-4, rho=0.5),
        convergence=CombinedConvergence([
            ResidualConvergence(),
            StepSizeConvergence()
        ], require_all=False)
    )


def create_fast_newton_strategy() -> NewtonRaphsonStrategy:
    """Create a fast Newton-Raphson strategy for well-conditioned problems."""
    return NewtonRaphsonStrategy(
        line_search=BacktrackingLineSearch(alpha=1e-2, rho=0.8),
        convergence=ResidualConvergence()
    )


def create_conservative_strategy() -> NewtonRaphsonStrategy:
    """Create a conservative strategy for difficult problems."""
    return NewtonRaphsonStrategy(
        line_search=BacktrackingLineSearch(alpha=1e-6, rho=0.1, max_backtracks=50),
        convergence=CombinedConvergence([
            ResidualConvergence(),
            StepSizeConvergence()
        ], require_all=True)
    )
