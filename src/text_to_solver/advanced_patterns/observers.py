"""
Observer Pattern Implementation for TextToSolver

Provides real-time monitoring capabilities for solver progress, convergence
tracking, and custom event handling during equation solving.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable, Optional, Tuple
from dataclasses import dataclass, field
import time
import numpy as np
from collections import deque


@dataclass
class SolverEvent:
    """Data class representing a solver event."""
    event_type: str
    iteration: int
    timestamp: float
    residual_norm: float
    step_norm: Optional[float] = None
    solver_info: Dict[str, Any] = field(default_factory=dict)


class SolverObserver(ABC):
    """Abstract base class for solver observers."""
    
    @abstractmethod
    def on_iteration(self, event: SolverEvent) -> None:
        """Called after each solver iteration."""
        pass
    
    @abstractmethod
    def on_start(self, event: SolverEvent) -> None:
        """Called when solving starts."""
        pass
    
    @abstractmethod
    def on_convergence(self, event: SolverEvent) -> None:
        """Called when solver converges."""
        pass
    
    @abstractmethod
    def on_failure(self, event: SolverEvent) -> None:
        """Called when solver fails to converge."""
        pass


class ConvergenceMonitor(SolverObserver):
    """Monitors and records solver convergence history."""
    
    def __init__(self, max_history: int = 1000):
        """Initialize convergence monitor.
        
        Args:
            max_history: Maximum number of iterations to store
        """
        self.max_history = max_history
        self.history: deque = deque(maxlen=max_history)
        self.start_time: Optional[float] = None
        self.total_time: Optional[float] = None
        self.final_status: Optional[str] = None
    
    def on_start(self, event: SolverEvent) -> None:
        """Record solver start."""
        self.start_time = event.timestamp
        self.history.clear()
        self.final_status = None
        self.total_time = None
    
    def on_iteration(self, event: SolverEvent) -> None:
        """Record iteration data."""
        self.history.append({
            'iteration': event.iteration,
            'residual_norm': event.residual_norm,
            'step_norm': event.step_norm,
            'timestamp': event.timestamp,
            'elapsed_time': event.timestamp - (self.start_time or event.timestamp)
        })
    
    def on_convergence(self, event: SolverEvent) -> None:
        """Record convergence."""
        self.final_status = 'converged'
        self.total_time = event.timestamp - (self.start_time or event.timestamp)
    
    def on_failure(self, event: SolverEvent) -> None:
        """Record failure."""
        self.final_status = 'failed'
        self.total_time = event.timestamp - (self.start_time or event.timestamp)
    
    def get_convergence_history(self) -> List[Dict[str, Any]]:
        """Get complete convergence history."""
        return list(self.history)
    
    def get_residual_history(self) -> List[float]:
        """Get residual norm history."""
        return [h['residual_norm'] for h in self.history]
    
    def get_convergence_rate(self) -> Optional[float]:
        """Calculate convergence rate (if converged)."""
        if len(self.history) < 2 or self.final_status != 'converged':
            return None
        
        residuals = self.get_residual_history()
        if len(residuals) < 3:
            return None
            
        # Calculate linear convergence rate: |r_{k+1}| / |r_k|
        ratios = []
        for i in range(1, len(residuals)):
            if residuals[i-1] > 0 and residuals[i] > 0:
                ratios.append(residuals[i] / residuals[i-1])
        
        return np.mean(ratios) if ratios else None
    
    def plot_convergence(self):
        """Plot convergence history (requires matplotlib)."""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("matplotlib not available for plotting")
            return
        
        if not self.history:
            print("No convergence history to plot")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Residual norm vs iteration
        iterations = [h['iteration'] for h in self.history]
        residuals = [h['residual_norm'] for h in self.history]
        
        ax1.semilogy(iterations, residuals, 'b-o', markersize=4)
        ax1.set_xlabel('Iteration')
        ax1.set_ylabel('Residual Norm')
        ax1.set_title('Convergence History')
        ax1.grid(True, alpha=0.3)
        
        # Residual norm vs time
        times = [h['elapsed_time'] for h in self.history]
        ax2.semilogy(times, residuals, 'r-o', markersize=4)
        ax2.set_xlabel('Time (seconds)')
        ax2.set_ylabel('Residual Norm')
        ax2.set_title('Convergence vs Time')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        # Print summary
        if self.final_status:
            rate = self.get_convergence_rate()
            print(f"\nConvergence Summary:")
            print(f"Status: {self.final_status}")
            print(f"Iterations: {len(self.history)}")
            print(f"Total time: {self.total_time:.4f}s")
            if rate:
                print(f"Convergence rate: {rate:.4f}")


class ProgressCallback(SolverObserver):
    """Executes user-defined callbacks during solving."""
    
    def __init__(self, 
                 iteration_callback: Optional[Callable[[int, float], None]] = None,
                 start_callback: Optional[Callable[[], None]] = None,
                 end_callback: Optional[Callable[[str], None]] = None):
        """Initialize progress callback.
        
        Args:
            iteration_callback: Called with (iteration, residual_norm) each iteration
            start_callback: Called when solving starts
            end_callback: Called when solving ends with status
        """
        self.iteration_callback = iteration_callback
        self.start_callback = start_callback  
        self.end_callback = end_callback
    
    def on_start(self, event: SolverEvent) -> None:
        """Execute start callback."""
        if self.start_callback:
            self.start_callback()
    
    def on_iteration(self, event: SolverEvent) -> None:
        """Execute iteration callback."""
        if self.iteration_callback:
            self.iteration_callback(event.iteration, event.residual_norm)
    
    def on_convergence(self, event: SolverEvent) -> None:
        """Execute end callback with success."""
        if self.end_callback:
            self.end_callback('converged')
    
    def on_failure(self, event: SolverEvent) -> None:
        """Execute end callback with failure."""
        if self.end_callback:
            self.end_callback('failed')


class EventLogger(SolverObserver):
    """Logs solver events to console or file."""
    
    def __init__(self, 
                 log_level: str = 'INFO',
                 log_file: Optional[str] = None,
                 log_iterations: bool = True):
        """Initialize event logger.
        
        Args:
            log_level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
            log_file: Optional file to write logs to
            log_iterations: Whether to log each iteration
        """
        self.log_level = log_level
        self.log_file = log_file
        self.log_iterations = log_iterations
        self._log_handle = None
        
        if log_file:
            self._log_handle = open(log_file, 'w')
    
    def __del__(self):
        """Close log file if open."""
        if self._log_handle:
            self._log_handle.close()
    
    def _log(self, message: str, level: str = 'INFO') -> None:
        """Write log message."""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f"[{timestamp}] {level}: {message}"
        
        print(formatted_message)
        if self._log_handle:
            self._log_handle.write(formatted_message + '\n')
            self._log_handle.flush()
    
    def on_start(self, event: SolverEvent) -> None:
        """Log solver start."""
        self._log("Solver started", 'INFO')
    
    def on_iteration(self, event: SolverEvent) -> None:
        """Log iteration progress."""
        if self.log_iterations:
            self._log(f"Iteration {event.iteration}: residual = {event.residual_norm:.2e}", 'DEBUG')
    
    def on_convergence(self, event: SolverEvent) -> None:
        """Log convergence."""
        self._log(f"Solver converged in {event.iteration} iterations, "
                 f"residual = {event.residual_norm:.2e}", 'INFO')
    
    def on_failure(self, event: SolverEvent) -> None:
        """Log failure."""
        self._log(f"Solver failed after {event.iteration} iterations, "
                 f"residual = {event.residual_norm:.2e}", 'WARNING')


class CallbackManager:
    """Manages multiple observers for a solver."""
    
    def __init__(self):
        """Initialize callback manager."""
        self.observers: List[SolverObserver] = []
    
    def add_observer(self, observer: SolverObserver) -> None:
        """Add an observer."""
        self.observers.append(observer)
    
    def remove_observer(self, observer: SolverObserver) -> None:
        """Remove an observer."""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def clear_observers(self) -> None:
        """Remove all observers."""
        self.observers.clear()
    
    def notify_start(self, event: SolverEvent) -> None:
        """Notify all observers of solver start."""
        for observer in self.observers:
            try:
                observer.on_start(event)
            except Exception as e:
                print(f"Observer {type(observer).__name__} failed on start: {e}")
    
    def notify_iteration(self, event: SolverEvent) -> None:
        """Notify all observers of iteration."""
        for observer in self.observers:
            try:
                observer.on_iteration(event)
            except Exception as e:
                print(f"Observer {type(observer).__name__} failed on iteration: {e}")
    
    def notify_convergence(self, event: SolverEvent) -> None:
        """Notify all observers of convergence."""
        for observer in self.observers:
            try:
                observer.on_convergence(event)
            except Exception as e:
                print(f"Observer {type(observer).__name__} failed on convergence: {e}")
    
    def notify_failure(self, event: SolverEvent) -> None:
        """Notify all observers of failure."""
        for observer in self.observers:
            try:
                observer.on_failure(event)
            except Exception as e:
                print(f"Observer {type(observer).__name__} failed on failure: {e}")


# Convenience functions for creating common observers
def create_progress_monitor(show_progress: bool = True, 
                          track_convergence: bool = True,
                          log_to_file: Optional[str] = None) -> List[SolverObserver]:
    """Create a standard set of monitoring observers.
    
    Args:
        show_progress: Show iteration progress
        track_convergence: Track convergence history
        log_to_file: Optional log file path
        
    Returns:
        List of configured observers
    """
    observers = []
    
    if track_convergence:
        observers.append(ConvergenceMonitor())
    
    if show_progress:
        observers.append(ProgressCallback(
            iteration_callback=lambda i, r: print(f"  Iteration {i}: {r:.2e}")
        ))
    
    if log_to_file:
        observers.append(EventLogger(log_file=log_to_file))
    
    return observers
