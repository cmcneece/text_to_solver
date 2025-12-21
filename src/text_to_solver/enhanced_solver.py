"""
Enhanced EquationSolver with Advanced Pattern Support

Integrates Observer patterns, Strategy patterns, Builders, and Factories
with the existing EquationSolver API for maximum flexibility.
"""

from typing import List, Dict, Union, Optional, Any, Callable
import numpy as np
import numpy.typing as npt

# Import existing components
from .user_api import EquationSolver as BaseEquationSolver, SolutionResult
from .TextToSolver import SolverOptions

# Import advanced patterns
from .advanced_patterns.observers import (
    SolverObserver, ConvergenceMonitor, ProgressCallback, EventLogger, 
    CallbackManager, create_progress_monitor
)
from .advanced_patterns.strategies import (
    SolverStrategy, NewtonRaphsonStrategy, BroydenStrategy,
    create_robust_newton_strategy, create_fast_newton_strategy
)
from .advanced_patterns.builders import (
    EquationSystemBuilder, ChemicalSystemBuilder, OptimizationProblemBuilder
)
from .advanced_patterns.factories import (
    SystemFactory, TemplateFactory, ChemicalFactory, ConfigurationFactory
)


class EnhancedEquationSolver(BaseEquationSolver):
    """Enhanced EquationSolver with advanced pattern support."""
    
    def __init__(self, 
                 variables: Optional[List[str]] = None,
                 equations: Optional[List[str]] = None,
                 parameters: Optional[Dict[str, Union[int, float]]] = None,
                 independent_variables: Optional[List[str]] = None):
        """Initialize enhanced equation solver.
        
        Args:
            variables: List of dependent variable names
            equations: List of equation strings
            parameters: Parameter values dict
            independent_variables: List of independent variable names
        """
        super().__init__(variables, equations, parameters, independent_variables)
        
        # Advanced pattern components
        self._callback_manager = CallbackManager()
        self._solver_strategy: Optional[SolverStrategy] = None
        self._convergence_monitor: Optional[ConvergenceMonitor] = None
        self._progress_enabled = False
        self._template_factory = TemplateFactory()
    
    # ================================================================
    # Observer Pattern Integration
    # ================================================================
    
    def add_observer(self, observer: SolverObserver) -> 'EnhancedEquationSolver':
        """Add an observer to monitor solver progress.
        
        Args:
            observer: Observer to add
            
        Returns:
            Self for method chaining
        """
        self._callback_manager.add_observer(observer)
        
        # Special handling for convergence monitor
        if isinstance(observer, ConvergenceMonitor):
            self._convergence_monitor = observer
        
        return self
    
    def remove_observer(self, observer: SolverObserver) -> 'EnhancedEquationSolver':
        """Remove an observer.
        
        Args:
            observer: Observer to remove
            
        Returns:
            Self for method chaining
        """
        self._callback_manager.remove_observer(observer)
        
        if observer is self._convergence_monitor:
            self._convergence_monitor = None
        
        return self
    
    def enable_progress_monitoring(self, 
                                  show_progress: bool = True,
                                  track_convergence: bool = True,
                                  log_to_file: Optional[str] = None) -> 'EnhancedEquationSolver':
        """Enable standard progress monitoring.
        
        Args:
            show_progress: Show iteration progress
            track_convergence: Track convergence history
            log_to_file: Optional log file path
            
        Returns:
            Self for method chaining
        """
        observers = create_progress_monitor(show_progress, track_convergence, log_to_file)
        for observer in observers:
            self.add_observer(observer)
        
        self._progress_enabled = True
        return self
    
    def get_convergence_history(self) -> Optional[List[Dict[str, Any]]]:
        """Get convergence history if monitoring is enabled."""
        if self._convergence_monitor:
            return self._convergence_monitor.get_convergence_history()
        return None
    
    def plot_convergence(self) -> None:
        """Plot convergence history if available."""
        if self._convergence_monitor:
            self._convergence_monitor.plot_convergence()
        else:
            print("No convergence monitor active. Enable with enable_progress_monitoring()")
    
    # ================================================================
    # Strategy Pattern Integration  
    # ================================================================
    
    def solver_strategy(self, strategy: Union[str, SolverStrategy]) -> 'EnhancedEquationSolver':
        """Set solver strategy.
        
        Args:
            strategy: Strategy name or SolverStrategy instance
            
        Returns:
            Self for method chaining
        """
        if isinstance(strategy, str):
            strategy_map = {
                'newton': create_robust_newton_strategy(),
                'newton_fast': create_fast_newton_strategy(),
                'newton_robust': create_robust_newton_strategy(),
                'broyden': BroydenStrategy(),
                'broyden_good': BroydenStrategy('good'),
                'broyden_bad': BroydenStrategy('bad')
            }
            
            if strategy not in strategy_map:
                available = ', '.join(strategy_map.keys())
                raise ValueError(f"Unknown strategy '{strategy}'. Available: {available}")
            
            self._solver_strategy = strategy_map[strategy]
        else:
            self._solver_strategy = strategy
        
        return self
    
    def get_solver_strategy(self) -> Optional[SolverStrategy]:
        """Get current solver strategy."""
        return self._solver_strategy
    
    # ================================================================
    # Enhanced Solving with Pattern Support
    # ================================================================
    
    def solve(self, 
             multistart: bool = False,
             custom_guess: Optional[Dict[str, npt.NDArray[np.float64]]] = None,
             use_strategy: bool = True) -> SolutionResult:
        """Solve with enhanced monitoring and strategy support.
        
        Args:
            multistart: Use multiple starting points for robustness
            custom_guess: User-provided initial guess
            use_strategy: Use custom solver strategy if available
            
        Returns:
            Rich SolutionResult object
        """
        # Use custom strategy if available and requested
        if use_strategy and self._solver_strategy:
            return self._solve_with_strategy(multistart, custom_guess)
        else:
            # Fall back to base implementation with monitoring
            return self._solve_with_monitoring(multistart, custom_guess)
    
    def _solve_with_strategy(self, multistart: bool, custom_guess: Optional[Dict]) -> SolutionResult:
        """Solve using custom solver strategy."""
        if self._system is None:
            raise ValueError("No equation system set. Call set_system() first.")
        
        # This would integrate the strategy pattern with the actual solving
        # For now, fall back to monitored solving
        return self._solve_with_monitoring(multistart, custom_guess)
    
    def _solve_with_monitoring(self, multistart: bool, custom_guess: Optional[Dict]) -> SolutionResult:
        """Solve with observer monitoring."""
        # Call base solve method
        result = super().solve(multistart, custom_guess)
        
        # TODO: Integrate actual monitoring with TextToSolver
        # This would require modifying TextToSolver to support callbacks
        # For now, just return the result
        
        return result
    
    # ================================================================
    # Builder Pattern Integration
    # ================================================================
    
    @classmethod
    def builder(cls) -> EquationSystemBuilder:
        """Get equation system builder.
        
        Returns:
            EquationSystemBuilder instance
        """
        return EquationSystemBuilder()
    
    @classmethod
    def chemical_builder(cls) -> ChemicalSystemBuilder:
        """Get chemical system builder.
        
        Returns:
            ChemicalSystemBuilder instance
        """
        return ChemicalSystemBuilder()
    
    @classmethod
    def optimization_builder(cls) -> OptimizationProblemBuilder:
        """Get optimization problem builder.
        
        Returns:
            OptimizationProblemBuilder instance
        """
        return OptimizationProblemBuilder()
    
    def from_builder(self, builder: Any) -> 'EnhancedEquationSolver':
        """Set system from builder.
        
        Args:
            builder: System builder instance
            
        Returns:
            Self for method chaining
        """
        system = builder.build()
        return self.set_system(
            system.dependent_variables,
            system.equations,
            system.parameters,
            system.independent_variables
        )
    
    # ================================================================
    # Factory Method Integration
    # ================================================================
    
    @classmethod
    def from_pattern(cls, pattern_name: str, **parameters) -> 'EnhancedEquationSolver':
        """Create solver from known pattern.
        
        Args:
            pattern_name: Pattern name
            **parameters: Pattern parameters
            
        Returns:
            Configured EnhancedEquationSolver
        """
        system = SystemFactory.from_pattern(pattern_name, **parameters)
        return cls().set_system(
            system.dependent_variables,
            system.equations,  
            system.parameters,
            system.independent_variables
        )
    
    @classmethod
    def from_template(cls, template_name: str, **parameters) -> 'EnhancedEquationSolver':
        """Create solver from template.
        
        Args:
            template_name: Template name
            **parameters: Template parameters
            
        Returns:
            Configured EnhancedEquationSolver
        """
        factory = TemplateFactory()
        system = factory.create_from_template(template_name, **parameters)
        return cls().set_system(
            system.dependent_variables,
            system.equations,
            system.parameters,
            system.independent_variables
        )
    
    @classmethod
    def from_equations_enhanced(cls, equations: List[str], 
                               variables: Optional[List[str]] = None,
                               auto_detect: bool = True,
                               **kwargs) -> 'EnhancedEquationSolver':
        """Create solver with enhanced pattern detection.
        
        Args:
            equations: Equation strings
            variables: Variable names (auto-detected if None)
            auto_detect: Enable pattern detection
            **kwargs: Additional parameters
            
        Returns:
            Configured EnhancedEquationSolver
        """
        system = SystemFactory.from_equations(equations, variables, auto_detect, **kwargs)
        return cls().set_system(
            system.dependent_variables,
            system.equations,
            system.parameters,
            system.independent_variables
        )
    
    # ================================================================
    # Chemical System Shortcuts
    # ================================================================
    
    @classmethod
    def create_acid_base_system(cls, pKa: float, pH: float = 7.0, 
                               total_concentration: float = 1e-3) -> 'EnhancedEquationSolver':
        """Create acid-base equilibrium system.
        
        Args:
            pKa: Acid dissociation constant
            pH: Solution pH
            total_concentration: Total acid concentration
            
        Returns:
            Configured solver
        """
        system = ChemicalFactory.create_acid_base_system(pKa, pH, total_concentration)
        return cls().set_system(
            system.dependent_variables,
            system.equations,
            system.parameters,
            system.independent_variables
        )
    
    @classmethod
    def create_carbonate_system(cls, pH: float = 8.1, total_co2: float = 1e-3,
                               temperature: float = 25.0) -> 'EnhancedEquationSolver':
        """Create carbonate equilibrium system.
        
        Args:
            pH: Solution pH
            total_co2: Total CO2 concentration
            temperature: Temperature in Celsius
            
        Returns:
            Configured solver
        """
        system = ChemicalFactory.create_carbonate_system(pH, total_co2, temperature)
        return cls().set_system(
            system.dependent_variables,
            system.equations,
            system.parameters,
            system.independent_variables
        )
    
    # ================================================================
    # Advanced Analysis Methods
    # ================================================================
    
    def analyze_system(self) -> Dict[str, Any]:
        """Analyze equation system characteristics.
        
        Returns:
            Analysis results dictionary
        """
        if self._system is None:
            raise ValueError("No equation system set")
        
        analysis = {
            'n_variables': len(self._system.dependent_variables),
            'n_equations': len(self._system.equations),
            'n_parameters': len(self._system.parameters),
            'system_type': 'unknown',
            'difficulty_estimate': 'medium',
            'recommended_strategy': 'newton_robust'
        }
        
        # Pattern detection
        patterns = SystemFactory._detect_patterns(self._system.equations)
        analysis['detected_patterns'] = patterns
        
        if patterns.get('linear'):
            analysis['system_type'] = 'linear'
            analysis['difficulty_estimate'] = 'easy'
            analysis['recommended_strategy'] = 'newton_fast'
        elif patterns.get('chemical'):
            analysis['system_type'] = 'chemical_equilibrium'
            analysis['difficulty_estimate'] = 'medium'
            analysis['recommended_strategy'] = 'newton_robust'
        elif patterns.get('geometric'):
            analysis['system_type'] = 'geometric'
            analysis['difficulty_estimate'] = 'easy'
            analysis['recommended_strategy'] = 'newton_fast'
        
        return analysis
    
    def get_recommended_settings(self) -> Dict[str, Any]:
        """Get recommended solver settings based on system analysis.
        
        Returns:
            Recommended settings dictionary
        """
        analysis = self.analyze_system()
        
        settings = {
            'tolerance': 1e-8,
            'max_iterations': 50,
            'multistart': False,
            'progress_monitoring': True,
            'solver_strategy': analysis['recommended_strategy']
        }
        
        # Adjust based on difficulty
        if analysis['difficulty_estimate'] == 'hard':
            settings.update({
                'tolerance': 1e-6,
                'max_iterations': 100,
                'multistart': True,
                'solver_strategy': 'newton_robust'
            })
        elif analysis['difficulty_estimate'] == 'easy':
            settings.update({
                'tolerance': 1e-10,
                'max_iterations': 20,
                'solver_strategy': 'newton_fast'
            })
        
        return settings
    
    def auto_configure(self) -> 'EnhancedEquationSolver':
        """Auto-configure solver based on system analysis.
        
        Returns:
            Self for method chaining
        """
        settings = self.get_recommended_settings()
        
        # Apply settings
        self.tolerance(settings['tolerance'])
        self.max_iterations(settings['max_iterations'])
        self.solver_strategy(settings['solver_strategy'])
        
        if settings['progress_monitoring']:
            self.enable_progress_monitoring()
        
        return self


# Convenience functions for creating enhanced solvers
def create_monitored_solver(equations: List[str], variables: Optional[List[str]] = None,
                           **kwargs) -> EnhancedEquationSolver:
    """Create solver with monitoring enabled."""
    return (EnhancedEquationSolver.from_equations_enhanced(equations, variables, **kwargs)
            .enable_progress_monitoring()
            .auto_configure())


def create_chemical_solver(system_type: str = 'acid_base', **params) -> EnhancedEquationSolver:
    """Create chemical system solver with monitoring."""
    if system_type == 'acid_base':
        return (EnhancedEquationSolver.create_acid_base_system(**params)
                .enable_progress_monitoring()
                .solver_strategy('newton_robust'))
    elif system_type == 'carbonate':
        return (EnhancedEquationSolver.create_carbonate_system(**params)
                .enable_progress_monitoring()
                .solver_strategy('newton_robust'))
    else:
        return (EnhancedEquationSolver.from_pattern('chemical_equilibrium', type=system_type, **params)
                .enable_progress_monitoring()
                .solver_strategy('newton_robust'))
