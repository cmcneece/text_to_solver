"""
Advanced Patterns Module for TextToSolver

This module implements advanced OOP design patterns to enhance the flexibility,
extensibility, and maintainability of the TextToSolver library.

Available Patterns:
- Observer Pattern: Real-time solver monitoring and event handling
- Strategy Pattern: Pluggable algorithms for solving and guess generation  
- Builder Pattern: Complex system construction with guided interfaces
- Factory Methods: Intelligent system creation and configuration
"""

# Observer Pattern Components
from .observers import (
    SolverObserver,
    ConvergenceMonitor, 
    ProgressCallback,
    EventLogger,
    CallbackManager
)

# Strategy Pattern Components
from .strategies import (
    SolverStrategy,
    NewtonRaphsonStrategy,
    BroydenStrategy,
    LineSearchStrategy,
    ArmijoLineSearch,
    BacktrackingLineSearch,
    ConvergenceStrategy,
    ResidualConvergence,
    StepSizeConvergence,
    create_robust_newton_strategy,
    create_fast_newton_strategy,
    create_conservative_strategy
)

# Builder Pattern Components  
from .builders import (
    EquationSystemBuilder
)

# Factory Method Components
from .factories import (
    SystemFactory,
    TemplateFactory,
    ConfigurationFactory
)

__all__ = [
    # Observer Pattern
    'SolverObserver',
    'ConvergenceMonitor',
    'ProgressCallback', 
    'EventLogger',
    'CallbackManager',
    
    # Strategy Pattern
    'SolverStrategy',
    'NewtonRaphsonStrategy',
    'BroydenStrategy', 
    'LineSearchStrategy',
    'ArmijoLineSearch',
    'BacktrackingLineSearch',
    'ConvergenceStrategy',
    'ResidualConvergence',
    'StepSizeConvergence',
    'create_robust_newton_strategy',
    'create_fast_newton_strategy',
    'create_conservative_strategy',
    
    # Builder Pattern
    'EquationSystemBuilder',
    
    # Factory Methods
    'SystemFactory',
    'TemplateFactory', 
    'ConfigurationFactory'
]
