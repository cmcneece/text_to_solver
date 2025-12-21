"""
TextToSolver Package

Enhanced symbolic equation solver with intelligent guess generation,
multi-start capabilities, and intuitive user experience.

Available APIs:
- Original: TextToSolver, SolverOptions (backward compatible)
- Improved: EquationSolver, ChemicalEquilibrium (new user-friendly API)
- Enhanced: EnhancedEquationSolver with advanced patterns
- Dynamic: DynamicEquationSolver for time-dependent systems

Advanced Patterns:
- Observer Pattern: Real-time monitoring and event handling
- Strategy Pattern: Pluggable algorithms and customizable solving
- Builder Pattern: Guided system construction with domain expertise
- Factory Methods: Intelligent system creation and templates

Dynamic Systems:
- Differential Equation Parsing: Handle derivatives (dx/dt, d²x/dt², etc.)
- Time Integration: Euler, Runge-Kutta, adaptive methods
- Boundary Conditions: Initial values and constraints
- Time Domain Analysis: Integration over specified time ranges
"""

# Original API (backward compatibility)
from .TextToSolver import TextToSolver, SolverOptions, ValidationError, SingularMatrixError

# User-friendly API (high-level interface) 
from .user_api import (
    EquationSolver,
    EquationSystem,
    SolutionResult,
    EquationSystemError,
    SolverError
)

# Enhanced API with Advanced Patterns
from .enhanced_solver import (
    EnhancedEquationSolver,
    create_monitored_solver,
    create_chemical_solver
)

# Dynamic Systems API
from .dynamic_solver import (
    DynamicEquationSolver,
    DynamicSystem,
    DynamicSolutionResult,
    DifferentialEquationParser,
    TimeIntegrator,
    solve_ode_system
)

# Advanced Patterns
from .advanced_patterns import (
    # Observer Pattern
    SolverObserver,
    ConvergenceMonitor,
    ProgressCallback,
    EventLogger,
    CallbackManager,
    
    # Strategy Pattern
    SolverStrategy,
    NewtonRaphsonStrategy,
    BroydenStrategy,
    LineSearchStrategy,
    ConvergenceStrategy,
    
    # Builder Pattern
    EquationSystemBuilder,
    
    # Factory Methods
    SystemFactory,
    TemplateFactory,
    ConfigurationFactory
)

# Web API Components (for web application integration)
try:
    from .web_api import (
        WebAPIService,
        SolverRequest, 
        SolverResponse,
        DynamicSolverRequest
    )
    from .session_manager import (
        SessionManager,
        SessionConfig,
        SessionState,
        WebSocketProgressManager
    )
    from .visualization_utils import (
        VisualizationUtils,
        PlotData,
        ChartConfig
    )
    _WEB_API_AVAILABLE = True
except ImportError as e:
    _WEB_API_AVAILABLE = False
    print(f"Web API components not available: {e}")

# Version info
__version__ = "3.0.0"  # Comprehensive equation solver with dynamic systems and web APIs
__author__ = "Colin McNeece"

# Expose APIs at package level
__all__ = [
    # Original API
    'TextToSolver',
    'SolverOptions', 
    'ValidationError',
    'SingularMatrixError',
    
    # User-friendly API
    'EquationSolver',
    'EquationSystem', 
    'SolutionResult',
    'EquationSystemError',
    'SolverError',
    
    # Enhanced API
    'EnhancedEquationSolver',
    'create_monitored_solver',
    'create_chemical_solver'
]

# Dynamic Systems
__all__.extend([
    'DynamicEquationSolver',
    'DynamicSystem', 
    'DynamicSolutionResult',
    'DifferentialEquationParser',
    'TimeIntegrator',
    'solve_ode_system'
])

# Advanced Patterns
__all__.extend([
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
    'ConvergenceStrategy',
    
    # Builder Pattern
    'EquationSystemBuilder',
    
    # Factory Methods
    'SystemFactory',
    'TemplateFactory',
    'ConfigurationFactory'
])

# Web API Components (if available)
if _WEB_API_AVAILABLE:
    __all__.extend([
        # Web API Service Layer
        'WebAPIService',
        'SolverRequest', 
        'SolverResponse',
        'DynamicSolverRequest',
        
        # Session Management
        'SessionManager',
        'SessionConfig',
        'SessionState',
        'WebSocketProgressManager',
        
        # Visualization Utilities
        'VisualizationUtils',
        'PlotData',
        'ChartConfig'
    ])
