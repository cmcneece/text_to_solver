#!/usr/bin/env python3
"""
Web API Service Layer for TextToSolver

This module provides a clean, stateless service layer designed for web applications.
It handles JSON serialization, input validation, and provides RESTful-style interfaces
suitable for HTTP endpoints.

Key Features:
- JSON serialization of all solver inputs/outputs
- Stateless operation for web scalability  
- Comprehensive input validation and sanitization
- Progress monitoring support for real-time updates
- Export capabilities for visualization
- Error handling with structured responses

Author: TextToSolver Development Team
"""

import json
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np
import numpy.typing as npt
import sympy as sp
import re

from .TextToSolver import TextToSolver, SolverOptions
from .dynamic_solver import DynamicEquationSolver, DynamicSystem, DynamicSolutionResult, solve_ode_system


@dataclass
class ParameterRange:
    """Defines a range for parameter sweeping."""
    lower: float
    upper: float 
    increment: float
    
    def get_values(self) -> List[float]:
        """Generate list of parameter values in the range."""
        if self.increment <= 0:
            raise ValueError("Increment must be positive")
        values = []
        current = self.lower
        while current <= self.upper + 1e-12:  # Small tolerance for floating point
            values.append(current)
            current += self.increment
        return values


@dataclass
class SolverRequest:
    """Data transfer object for solver requests."""
    equations: List[str]
    variables: List[str]
    initial_guess: Dict[str, float]
    constraints: Optional[Dict[str, Tuple[Optional[float], Optional[float]]]] = None
    parameters: Optional[Dict[str, Union[int, float]]] = None
    parameter_ranges: Optional[Dict[str, ParameterRange]] = None  # For parameter sweeps
    independent_variables: Optional[Dict[str, float]] = None
    solver_options: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


@dataclass
class SolverResponse:
    """Data transfer object for solver responses."""
    success: bool
    session_id: str
    solution: Optional[Dict[str, float]] = None
    report: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    warnings: Optional[List[str]] = None
    execution_time: Optional[float] = None
    timestamp: Optional[str] = None


@dataclass
class DynamicSolverRequest:
    """Data transfer object for dynamic solver requests."""
    equations: List[str]
    variables: List[str]
    time_range: Tuple[float, float]
    initial_conditions: Dict[str, float]
    parameters: Optional[Dict[str, Union[int, float]]] = None
    method: str = 'RK45'
    max_step: Optional[float] = None
    rtol: float = 1e-3
    atol: float = 1e-6
    session_id: Optional[str] = None


@dataclass
class ProgressUpdate:
    """Data transfer object for progress updates."""
    session_id: str
    iteration: int
    residual_norm: float
    elapsed_time: float
    status: str
    timestamp: str


class WebAPIService:
    """
    Stateless service layer for web applications.
    
    Provides clean interfaces for:
    - Algebraic equation solving
    - Dynamic system integration  
    - Progress monitoring
    - Result export
    - Input validation
    """
    
    def __init__(self):
        """Initialize the web API service."""
        self.active_sessions: Dict[str, Any] = {}
        
    def validate_solver_request(self, request: SolverRequest) -> Tuple[bool, Optional[str]]:
        """
        Validate solver request data.
        
        Args:
            request: Solver request to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Basic structure validation
            if not request.equations or not request.variables:
                return False, "Equations and variables are required"
                
            if len(request.equations) != len(request.variables):
                return False, "Number of equations must equal number of variables"
                
            if not request.initial_guess:
                return False, "Initial guess is required"
                
            # Check that all variables have initial guesses
            missing_vars = set(request.variables) - set(request.initial_guess.keys())
            if missing_vars:
                return False, f"Missing initial guesses for variables: {missing_vars}"
                
            # Validate constraint format
            if request.constraints:
                for var, bounds in request.constraints.items():
                    if var not in request.variables:
                        return False, f"Constraint variable '{var}' not in variable list"
                    if len(bounds) != 2:
                        return False, f"Constraint bounds must be (lower, upper) tuples"
                    lower, upper = bounds
                    if lower is not None and upper is not None and lower >= upper:
                        return False, f"Invalid bounds for '{var}': lower >= upper"
                        
            # Validate numeric values
            for var, val in request.initial_guess.items():
                if not isinstance(val, (int, float)) or np.isnan(val) or np.isinf(val):
                    return False, f"Invalid initial guess for '{var}': {val}"
                    
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def solve_algebraic_system(self, request: SolverRequest) -> SolverResponse:
        """
        Solve algebraic equation system with full error handling.
        
        Args:
            request: Validated solver request
            
        Returns:
            SolverResponse with results or error information
        """
        session_id = request.session_id or str(uuid.uuid4())
        start_time = datetime.now()
        warnings = []
        
        try:
            # Validate request
            is_valid, error_msg = self.validate_solver_request(request)
            if not is_valid:
                return SolverResponse(
                    success=False,
                    session_id=session_id,
                    error=error_msg,
                    timestamp=start_time.isoformat()
                )
            
            # Create solver
            solver = TextToSolver(
                dep_vars=request.variables,
                residual=request.equations,
                indep_vars=list(request.independent_variables.keys()) if request.independent_variables else None,
                parameters=request.parameters,
                constraints=request.constraints
            )
            
            # Prepare initial guess in correct format
            guess = {var: np.array([val]) for var, val in request.initial_guess.items()}
            
            # Validate initial guess against constraints
            if solver.has_constraints():
                validation = solver.validate_initial_guess(guess)
                if not validation['valid']:
                    warnings.append(f"Initial guess violates constraints: {validation['message']}")
            
            # Configure solver options
            options = SolverOptions(**(request.solver_options or {}))
            
            # Prepare independent variables
            indep_vars = {}
            if request.independent_variables:
                indep_vars = {var: np.array([val]) for var, val in request.independent_variables.items()}
            
            # Check if parameter sweep is requested
            if request.parameter_ranges:
                return self._solve_with_parameter_sweep(solver, request, guess, indep_vars, options, session_id, start_time, warnings)
            
            # Solve system
            solution, report = solver.solve(guess, indep_vars, options)
            
            # Convert solution to simple dict
            solution_dict = {var: float(val[0]) for var, val in solution.items()}
            
            # Serialize report (convert numpy types to Python types)
            serialized_report = self._serialize_report(report)
            
            # Add constraint analysis if constraints exist
            if solver.has_constraints():
                feasibility = solver.check_constraint_feasibility(solution)
                constraint_analysis = solver.analyze_constraints()
                serialized_report['constraint_feasibility'] = feasibility
                serialized_report['constraint_analysis'] = constraint_analysis
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return SolverResponse(
                success=True,
                session_id=session_id,
                solution=solution_dict,
                report=serialized_report,
                warnings=warnings if warnings else None,
                execution_time=execution_time,
                timestamp=start_time.isoformat()
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return SolverResponse(
                success=False,
                session_id=session_id,
                error=f"Solver error: {str(e)}",
                warnings=warnings if warnings else None,
                execution_time=execution_time,
                timestamp=start_time.isoformat()
            )
    
    def _solve_with_parameter_sweep(
        self, 
        solver: TextToSolver, 
        request: SolverRequest, 
        initial_guess: Dict[str, np.ndarray],
        indep_vars: Dict[str, np.ndarray],
        options: SolverOptions,
        session_id: str,
        start_time: datetime,
        warnings: List[str]
    ) -> SolverResponse:
        """
        Perform parameter sweep analysis.
        
        Args:
            solver: Configured TextToSolver instance
            request: Original solver request with parameter_ranges
            initial_guess: Initial guess for variables
            indep_vars: Independent variables
            options: Solver options
            session_id: Session identifier
            start_time: Start time for timing
            warnings: Accumulated warnings
            
        Returns:
            SolverResponse with sweep results
        """
        try:
            import itertools
            
            # Generate all parameter combinations
            param_names = list(request.parameter_ranges.keys())
            param_values = [request.parameter_ranges[name].get_values() for name in param_names]
            
            sweep_results = []
            total_combinations = 1
            for values in param_values:
                total_combinations *= len(values)
            
            if total_combinations > 1000:  # Reasonable limit
                warnings.append(f"Parameter sweep would generate {total_combinations} combinations. Consider reducing ranges.")
                if total_combinations > 10000:
                    return SolverResponse(
                        success=False,
                        session_id=session_id,
                        error=f"Parameter sweep too large: {total_combinations} combinations exceeds limit of 10000",
                        warnings=warnings,
                        execution_time=(datetime.now() - start_time).total_seconds(),
                        timestamp=start_time.isoformat()
                    )
            
            # Perform sweep
            for i, param_combination in enumerate(itertools.product(*param_values)):
                # Create parameter dict for this combination
                current_params = dict(zip(param_names, param_combination))
                
                # Update solver parameters (merge with any existing parameters)
                all_params = (request.parameters or {}).copy()
                all_params.update(current_params)
                
                # Create a new solver with updated parameters
                sweep_solver = TextToSolver(
                    dep_vars=request.variables,
                    residual=request.equations,
                    indep_vars=list(request.independent_variables.keys()) if request.independent_variables else None,
                    parameters=all_params,
                    constraints=request.constraints
                )
                
                try:
                    # Solve for this parameter combination
                    solution, report = sweep_solver.solve(initial_guess, indep_vars, options)
                    
                    # Convert solution to simple dict
                    solution_dict = {var: float(val[0]) for var, val in solution.items()}
                    
                    sweep_results.append({
                        'parameters': current_params,
                        'solution': solution_dict,
                        'success': report.get('exit_flag', 0) > 0,
                        'residual_norm': report.get('res_norm', None),
                        'iterations': report.get('iter_count', None)
                    })
                    
                except Exception as solve_error:
                    sweep_results.append({
                        'parameters': current_params,
                        'solution': None,
                        'success': False,
                        'error': str(solve_error),
                        'residual_norm': None,
                        'iterations': None
                    })
            
            # Aggregate results
            successful_solves = sum(1 for r in sweep_results if r['success'])
            
            # Create summary report
            sweep_report = {
                'total_combinations': total_combinations,
                'successful_solves': successful_solves,
                'success_rate': successful_solves / total_combinations if total_combinations > 0 else 0,
                'parameter_ranges': {name: {
                    'min': prange.lower, 
                    'max': prange.upper, 
                    'increment': prange.increment,
                    'count': len(prange.get_values())
                } for name, prange in request.parameter_ranges.items()},
                'sweep_results': sweep_results
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return SolverResponse(
                success=True,
                session_id=session_id,
                solution={'sweep_summary': sweep_report},
                report=sweep_report,
                warnings=warnings if warnings else None,
                execution_time=execution_time,
                timestamp=start_time.isoformat()
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return SolverResponse(
                success=False,
                session_id=session_id,
                error=f"Parameter sweep error: {str(e)}",
                warnings=warnings if warnings else None,
                execution_time=execution_time,
                timestamp=start_time.isoformat()
            )
    
    def solve_dynamic_system(self, request: DynamicSolverRequest) -> SolverResponse:
        """
        Solve dynamic equation system.
        
        Args:
            request: Dynamic solver request
            
        Returns:
            SolverResponse with time series results
        """
        session_id = request.session_id or str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Solve using standalone function
            result = solve_ode_system(
                variables=request.variables,
                equations=request.equations,
                initial_conditions=request.initial_conditions,
                time_span=request.time_range,
                parameters=request.parameters or {},
                method=request.method
            )
            
            # Serialize results for web transport
            solution_data = self._serialize_dynamic_result(result)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return SolverResponse(
                success=True,
                session_id=session_id,
                solution=solution_data,
                execution_time=execution_time,
                timestamp=start_time.isoformat()
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return SolverResponse(
                success=False,
                session_id=session_id,
                error=f"Dynamic solver error: {str(e)}",
                execution_time=execution_time,
                timestamp=start_time.isoformat()
            )
    
    def get_iteration_progress(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time iteration progress for active session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Progress information or None if session not found
        """
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if 'solver' in session and hasattr(session['solver'], 'get_iteration_history'):
                history = session['solver'].get_iteration_history()
                if history:
                    latest = history[-1]
                    return {
                        'session_id': session_id,
                        'iteration': latest.iteration,
                        'residual_norm': float(latest.residual_norm),
                        'elapsed_time': float(latest.elapsed_time),
                        'convergence_rate': float(latest.convergence_rate),
                        'constraint_violations': latest.constraint_violations,
                        'active_constraints': latest.active_constraints,
                        'timestamp': datetime.now().isoformat()
                    }
        return None
    
    def export_results(self, session_id: str, format: str = 'json') -> Optional[str]:
        """
        Export results in specified format.
        
        Args:
            session_id: Session identifier
            format: Export format ('json', 'csv')
            
        Returns:
            Serialized results or None if session not found
        """
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if format.lower() == 'json':
                return json.dumps(session['response'], indent=2, default=str)
            elif format.lower() == 'csv':
                return self._convert_to_csv(session['response'])
        return None
    
    def _serialize_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Convert report with numpy types to JSON-serializable format."""
        serialized = {}
        for key, value in report.items():
            if isinstance(value, np.ndarray):
                serialized[key] = value.tolist()
            elif isinstance(value, (np.integer, np.floating)):
                serialized[key] = value.item()
            elif key == 'iteration_history':
                # Serialize iteration history
                if value:
                    serialized[key] = [self._serialize_iteration_data(item) for item in value]
                else:
                    serialized[key] = []
            else:
                serialized[key] = value
        return serialized
    
    def _serialize_iteration_data(self, iter_data) -> Dict[str, Any]:
        """Serialize IterationData for JSON transport."""
        return {
            'iteration': iter_data.iteration,
            'timestamp': iter_data.timestamp,
            'elapsed_time': iter_data.elapsed_time,
            'residual_norm': float(iter_data.residual_norm),
            'step_norm': float(iter_data.step_norm),
            'convergence_rate': float(iter_data.convergence_rate),
            'lambda_factor': float(iter_data.lambda_factor),
            'condition_number': float(iter_data.condition_number),
            'residual_vector': iter_data.residual_vector.tolist(),
            'solution_vector': iter_data.solution_vector.tolist(),
            'solver_params': iter_data.solver_params,
            'constraint_violations': iter_data.constraint_violations,
            'active_constraints': iter_data.active_constraints,
            'projection_applied': iter_data.projection_applied
        }
    
    def _serialize_dynamic_result(self, result: DynamicSolutionResult) -> Dict[str, Any]:
        """Serialize dynamic solution result for JSON transport."""
        return {
            'time': result.time_points.tolist(),
            'solution': {var: values.tolist() for var, values in result.variables.items()},
            'success': result.success,
            'message': result.message,
            'integration_info': result.integration_info
        }
    
    def _convert_to_csv(self, response: Dict[str, Any]) -> str:
        """Convert solution to CSV format."""
        if not response.get('solution'):
            return "No solution data available"
            
        lines = ["variable,value"]
        for var, val in response['solution'].items():
            lines.append(f"{var},{val}")
        return "\n".join(lines)
    
    def detect_symbols(self, equations: List[str]) -> Dict[str, List[str]]:
        """
        Detect all symbols in a list of equations.
        
        Args:
            equations: List of equation strings
            
        Returns:
            Dict with detected symbols categorized by type
        """
        all_symbols = set()
        
        for equation in equations:
            try:
                # Parse the equation with SymPy
                expr = sp.sympify(equation)
                # Extract symbols
                symbols = expr.free_symbols
                all_symbols.update(str(s) for s in symbols)
            except (sp.SympifyError, ValueError):
                # Fallback: use regex to find symbol-like patterns
                # Look for variables (letter followed by letters/digits/underscores)
                pattern = r'[a-zA-Z][a-zA-Z0-9_]*'
                matches = re.findall(pattern, equation)
                # Filter out common mathematical functions
                math_functions = {
                    'sin', 'cos', 'tan', 'exp', 'log', 'ln', 'sqrt', 'abs',
                    'sinh', 'cosh', 'tanh', 'arcsin', 'arccos', 'arctan',
                    'asin', 'acos', 'atan', 'atan2', 'pi', 'e'
                }
                symbols = [m for m in matches if m not in math_functions]
                all_symbols.update(symbols)
        
        # Convert to sorted list for consistent ordering
        symbols_list = sorted(list(all_symbols))
        
        return {
            'detected_symbols': symbols_list,
            'suggested_variables': [],  # User will classify these
            'suggested_parameters': []  # User will classify these
        }


# Utility functions for web integration
def create_solver_request_from_json(json_data: str) -> SolverRequest:
    """Create SolverRequest from JSON string."""
    data = json.loads(json_data)
    return SolverRequest(**data)


def solver_response_to_json(response: SolverResponse) -> str:
    """Convert SolverResponse to JSON string."""
    return json.dumps(asdict(response), indent=2, default=str)


def create_dynamic_request_from_json(json_data: str) -> DynamicSolverRequest:
    """Create DynamicSolverRequest from JSON string."""
    data = json.loads(json_data)
    return DynamicSolverRequest(**data)


# Example usage and testing
if __name__ == "__main__":
    # Example usage of the web API service
    service = WebAPIService()
    
    # Test algebraic system
    request = SolverRequest(
        equations=['x**2 + y**2 - 4', 'x - y'],
        variables=['x', 'y'],
        initial_guess={'x': 1.5, 'y': 1.5},
        constraints={'x': (0, 3), 'y': (0, 3)},
        solver_options={'constraint_handling': 'project', 'display': False}
    )
    
    response = service.solve_algebraic_system(request)
    print("Algebraic System Response:")
    print(solver_response_to_json(response))
    
    # Test dynamic system  
    dynamic_request = DynamicSolverRequest(
        equations=['dx/dt = -0.1*x + 0.05*x*y', 'dy/dt = 0.1*y - 0.05*x*y'],
        variables=['x', 'y'],
        time_range=(0, 20),
        initial_conditions={'x': 10, 'y': 5}
    )
    
    dynamic_response = service.solve_dynamic_system(dynamic_request)
    print("\nDynamic System Response:")
    print(f"Success: {dynamic_response.success}")
    if dynamic_response.solution:
        print(f"Time points: {len(dynamic_response.solution['time'])}")
        print(f"Variables: {list(dynamic_response.solution['solution'].keys())}")
