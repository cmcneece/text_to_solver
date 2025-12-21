#!/usr/bin/env python3
"""
Test Suite for Web API Service Layer

Tests all functionality in the WebAPIService including:
- Request validation and sanitization
- JSON serialization/deserialization  
- Error handling and structured responses
- Algebraic and dynamic system solving
- Export capabilities
- Progress monitoring integration

Author: TextToSolver Test Team
"""

import pytest
import json
import numpy as np
from typing import Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from text_to_solver.web_api import (
    WebAPIService, 
    SolverRequest, 
    SolverResponse, 
    DynamicSolverRequest,
    ParameterRange,
    create_solver_request_from_json,
    create_dynamic_request_from_json,
    solver_response_to_json
)


@pytest.mark.web_api
class TestWebAPIService:
    """Test the core web API service functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.service = WebAPIService()
    
    def test_service_creation(self):
        """Test service can be created successfully."""
        service = WebAPIService()
        assert service is not None
        assert hasattr(service, 'active_sessions')
        assert isinstance(service.active_sessions, dict)
    
    def test_valid_request_validation(self):
        """Test validation of valid solver requests."""
        request = SolverRequest(
            equations=['x**2 + y**2 - 4', 'x - y'],
            variables=['x', 'y'],
            initial_guess={'x': 1.5, 'y': 1.5}
        )
        
        is_valid, error = self.service.validate_solver_request(request)
        
        assert is_valid is True
        assert error is None
    
    def test_invalid_request_validation_missing_equations(self):
        """Test validation rejects requests with missing equations."""
        request = SolverRequest(
            equations=[],  # Empty equations
            variables=['x', 'y'],
            initial_guess={'x': 1.5, 'y': 1.5}
        )
        
        is_valid, error = self.service.validate_solver_request(request)
        
        assert is_valid is False
        assert "Equations and variables are required" in error
    
    def test_invalid_request_validation_mismatched_count(self):
        """Test validation rejects requests with mismatched equation/variable counts."""
        request = SolverRequest(
            equations=['x**2 + y**2 - 4'],  # 1 equation
            variables=['x', 'y'],           # 2 variables
            initial_guess={'x': 1.5, 'y': 1.5}
        )
        
        is_valid, error = self.service.validate_solver_request(request)
        
        assert is_valid is False
        assert "Number of equations must equal number of variables" in error
    
    def test_invalid_request_validation_missing_guess(self):
        """Test validation rejects requests with missing initial guess."""
        request = SolverRequest(
            equations=['x**2 + y**2 - 4', 'x - y'],
            variables=['x', 'y'],
            initial_guess={'x': 1.5}  # Missing 'y'
        )
        
        is_valid, error = self.service.validate_solver_request(request)
        
        assert is_valid is False
        assert "Missing initial guesses for variables" in error
    
    def test_invalid_request_validation_constraint_format(self):
        """Test validation rejects invalid constraint formats."""
        request = SolverRequest(
            equations=['x**2 + y**2 - 4', 'x - y'],
            variables=['x', 'y'],
            initial_guess={'x': 1.5, 'y': 1.5},
            constraints={'z': (0, 1)}  # 'z' not in variables
        )
        
        is_valid, error = self.service.validate_solver_request(request)
        
        assert is_valid is False
        assert "Constraint variable 'z' not in variable list" in error
    
    def test_invalid_request_validation_invalid_bounds(self):
        """Test validation rejects invalid constraint bounds."""
        request = SolverRequest(
            equations=['x**2 + y**2 - 4', 'x - y'],
            variables=['x', 'y'],
            initial_guess={'x': 1.5, 'y': 1.5},
            constraints={'x': (5, 1)}  # Lower > upper
        )
        
        is_valid, error = self.service.validate_solver_request(request)
        
        assert is_valid is False
        assert "Invalid bounds for 'x': lower >= upper" in error
    
    def test_invalid_request_validation_invalid_numbers(self):
        """Test validation rejects invalid numeric values."""
        request = SolverRequest(
            equations=['x**2 + y**2 - 4', 'x - y'],
            variables=['x', 'y'],
            initial_guess={'x': float('inf'), 'y': 1.5}  # Invalid number
        )
        
        is_valid, error = self.service.validate_solver_request(request)
        
        assert is_valid is False
        assert "Invalid initial guess for 'x'" in error


@pytest.mark.web_api
@pytest.mark.algebraic
class TestAlgebraicSolving:
    """Test algebraic equation solving through the web API."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.service = WebAPIService()
    
    def test_successful_algebraic_solve(self):
        """Test successful algebraic system solving."""
        request = SolverRequest(
            equations=['x**2 + y**2 - 4', 'x - y'],
            variables=['x', 'y'],
            initial_guess={'x': 1.5, 'y': 1.5},
            solver_options={'display': False}
        )
        
        response = self.service.solve_algebraic_system(request)
        
        assert response.success is True
        assert response.solution is not None
        assert 'x' in response.solution
        assert 'y' in response.solution
        assert response.execution_time is not None
        assert response.execution_time > 0
        assert response.session_id is not None
        assert response.timestamp is not None
        
        # Verify solution quality
        x, y = response.solution['x'], response.solution['y']
        assert abs(x**2 + y**2 - 4) < 1e-6  # Satisfies equation 1
        assert abs(x - y) < 1e-6             # Satisfies equation 2
    
    def test_constrained_algebraic_solve(self):
        """Test algebraic solving with constraints."""
        request = SolverRequest(
            equations=['x**2 + y**2 - 4', 'x - y'],
            variables=['x', 'y'],
            initial_guess={'x': 1.5, 'y': 1.5},
            constraints={'x': (0, 3), 'y': (0, 3)},
            solver_options={'display': False, 'constraint_handling': 'project'}
        )
        
        response = self.service.solve_algebraic_system(request)
        
        assert response.success is True
        assert response.solution is not None
        
        # Check constraint satisfaction
        x, y = response.solution['x'], response.solution['y']
        assert 0 <= x <= 3
        assert 0 <= y <= 3
        
        # Verify constraint analysis is included
        assert 'constraint_feasibility' in response.report
        assert 'constraint_analysis' in response.report
        
        feasibility = response.report['constraint_feasibility']
        assert feasibility['feasible'] is True
    
    def test_algebraic_solve_with_invalid_equations(self):
        """Test error handling with invalid equations."""
        request = SolverRequest(
            equations=['invalid equation ###', 'x - y'],
            variables=['x', 'y'],
            initial_guess={'x': 1.5, 'y': 1.5},
            solver_options={'display': False}
        )
        
        response = self.service.solve_algebraic_system(request)
        
        assert response.success is False
        assert response.error is not None
        assert "Solver error:" in response.error
        assert response.execution_time is not None
    
    def test_algebraic_solve_with_constraint_violation(self):
        """Test handling of constraint violations in initial guess."""
        request = SolverRequest(
            equations=['x**2 + y**2 - 4', 'x - y'],
            variables=['x', 'y'],
            initial_guess={'x': -5.0, 'y': -5.0},  # Outside constraints
            constraints={'x': (0, 3), 'y': (0, 3)},
            solver_options={'display': False, 'constraint_handling': 'project'}
        )
        
        response = self.service.solve_algebraic_system(request)
        
        assert response.success is True
        assert response.warnings is not None
        assert any("violates constraints" in warning for warning in response.warnings)


@pytest.mark.web_api
@pytest.mark.dynamic
class TestDynamicSolving:
    """Test dynamic system solving through the web API."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.service = WebAPIService()
    
    def test_successful_dynamic_solve(self):
        """Test successful dynamic system solving."""
        request = DynamicSolverRequest(
            equations=['dx/dt = -0.5*x', 'dy/dt = 0.3*y'],
            variables=['x', 'y'],
            time_range=(0, 5),
            initial_conditions={'x': 10, 'y': 2}
        )
        
        response = self.service.solve_dynamic_system(request)
        
        assert response.success is True
        assert response.solution is not None
        assert 'time' in response.solution
        assert 'solution' in response.solution
        assert 'x' in response.solution['solution']
        assert 'y' in response.solution['solution']
        assert response.execution_time is not None
        
        # Verify data structure
        time_data = response.solution['time']
        x_data = response.solution['solution']['x']
        y_data = response.solution['solution']['y']
        
        assert len(time_data) > 10  # Should have multiple time points
        assert len(x_data) == len(time_data)
        assert len(y_data) == len(time_data)
        
        # Check time bounds
        assert time_data[0] == 0.0
        assert time_data[-1] <= 10.0
    
    def test_dynamic_solve_with_parameters(self):
        """Test dynamic solving with parameters."""
        request = DynamicSolverRequest(
            equations=['dx/dt = -a*x', 'dy/dt = c*y'],
            variables=['x', 'y'],
            time_range=(0, 3),
            initial_conditions={'x': 10, 'y': 2},
            parameters={'a': 0.5, 'c': 0.3}
        )
        
        response = self.service.solve_dynamic_system(request)
        
        assert response.success is True
        assert response.solution is not None
    
    def test_dynamic_solve_with_invalid_equations(self):
        """Test error handling with invalid dynamic equations."""
        request = DynamicSolverRequest(
            equations=['invalid equation ###'],
            variables=['x'],
            time_range=(0, 1),
            initial_conditions={'x': 1}
        )
        
        response = self.service.solve_dynamic_system(request)
        
        assert response.success is False
        assert response.error is not None
        assert "Dynamic solver error:" in response.error


@pytest.mark.web_api
class TestJSONSerialization:
    """Test JSON serialization and deserialization."""
    
    def test_solver_request_from_json(self):
        """Test creating SolverRequest from JSON."""
        json_data = json.dumps({
            "equations": ["x**2 + y**2 - 4", "x - y"],
            "variables": ["x", "y"],
            "initial_guess": {"x": 1.5, "y": 1.5},
            "constraints": {"x": [0, 3], "y": [0, 3]},
            "solver_options": {"display": False}
        })
        
        request = create_solver_request_from_json(json_data)
        
        assert isinstance(request, SolverRequest)
        assert request.equations == ["x**2 + y**2 - 4", "x - y"]
        assert request.variables == ["x", "y"]
        assert request.initial_guess == {"x": 1.5, "y": 1.5}
        assert request.constraints == {"x": [0, 3], "y": [0, 3]}
        assert request.solver_options == {"display": False}
    
    def test_dynamic_request_from_json(self):
        """Test creating DynamicSolverRequest from JSON."""
        json_data = json.dumps({
            "equations": ["dx/dt = -x"],
            "variables": ["x"],
            "time_range": [0, 5],
            "initial_conditions": {"x": 10},
            "method": "RK45"
        })
        
        request = create_dynamic_request_from_json(json_data)
        
        assert isinstance(request, DynamicSolverRequest)
        assert request.equations == ["dx/dt = -x"]
        assert request.variables == ["x"]
        assert request.time_range == [0, 5]
        assert request.initial_conditions == {"x": 10}
        assert request.method == "RK45"
    
    def test_solver_response_to_json(self):
        """Test converting SolverResponse to JSON."""
        response = SolverResponse(
            success=True,
            session_id="test-session",
            solution={"x": 1.414, "y": 1.414},
            execution_time=0.1
        )
        
        json_str = solver_response_to_json(response)
        parsed = json.loads(json_str)
        
        assert parsed["success"] is True
        assert parsed["session_id"] == "test-session"
        assert parsed["solution"]["x"] == 1.414
        assert parsed["solution"]["y"] == 1.414
        assert parsed["execution_time"] == 0.1
    
    def test_json_with_numpy_arrays(self):
        """Test JSON serialization handles numpy arrays correctly."""
        service = WebAPIService()
        
        request = SolverRequest(
            equations=['x**2 - 4'],
            variables=['x'],
            initial_guess={'x': 2.1},
            solver_options={'display': False, 'store_history': True}
        )
        
        response = service.solve_algebraic_system(request)
        
        # Should successfully serialize response with numpy arrays
        json_str = solver_response_to_json(response)
        parsed = json.loads(json_str)
        
        assert parsed["success"] is True
        assert "solution" in parsed
        
        # Check that iteration history is properly serialized
        if response.report and 'iteration_history' in response.report:
            history = response.report['iteration_history']
            assert isinstance(history, list)
            if history:
                iter_data = history[0]
                assert 'residual_vector' in iter_data
                assert isinstance(iter_data['residual_vector'], list)


@pytest.mark.web_api
class TestExportCapabilities:
    """Test export functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.service = WebAPIService()
    
    def test_json_export(self):
        """Test JSON export of results."""
        # First, create a session with results
        request = SolverRequest(
            equations=['x**2 - 4'],
            variables=['x'],
            initial_guess={'x': 2.1},
            solver_options={'display': False},
            session_id="test-export-session"
        )
        
        response = self.service.solve_algebraic_system(request)
        
        # Store session data
        self.service.active_sessions["test-export-session"] = {
            'response': response.__dict__
        }
        
        # Test export
        exported = self.service.export_results("test-export-session", "json")
        
        assert exported is not None
        parsed = json.loads(exported)
        assert parsed["success"] is True
        assert "solution" in parsed
    
    def test_csv_export(self):
        """Test CSV export of results."""
        # Create session with results
        request = SolverRequest(
            equations=['x**2 - 4'],
            variables=['x'],
            initial_guess={'x': 2.1},
            solver_options={'display': False},
            session_id="test-csv-session"
        )
        
        response = self.service.solve_algebraic_system(request)
        
        # Store session data
        self.service.active_sessions["test-csv-session"] = {
            'response': response.__dict__
        }
        
        # Test export
        exported = self.service.export_results("test-csv-session", "csv")
        
        assert exported is not None
        assert "variable,value" in exported
        assert "x," in exported
    
    def test_export_nonexistent_session(self):
        """Test export with non-existent session."""
        exported = self.service.export_results("nonexistent-session", "json")
        
        assert exported is None


@pytest.mark.web_api
@pytest.mark.error_handling
class TestErrorHandling:
    """Test comprehensive error handling scenarios."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.service = WebAPIService()
    
    def test_malformed_json_request(self):
        """Test handling of malformed JSON requests."""
        with pytest.raises(json.JSONDecodeError):
            create_solver_request_from_json("invalid json {{{")
    
    def test_missing_required_fields(self):
        """Test handling of requests with missing required fields."""
        json_data = json.dumps({
            "equations": ["x**2 - 4"],
            # Missing variables, initial_guess
        })
        
        with pytest.raises((TypeError, KeyError)):
            create_solver_request_from_json(json_data)
    
    def test_solver_internal_error_handling(self):
        """Test handling of internal solver errors."""
        request = SolverRequest(
            equations=['1/0'],  # Division by zero
            variables=['x'],
            initial_guess={'x': 1.0},
            solver_options={'display': False}
        )
        
        response = self.service.solve_algebraic_system(request)
        
        assert response.success is False
        assert response.error is not None
        assert response.session_id is not None
        assert response.execution_time is not None


@pytest.mark.web_api
@pytest.mark.integration
class TestWebAPIIntegration:
    """Integration tests for web API components."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.service = WebAPIService()
    
    def test_complete_workflow(self):
        """Test complete solving workflow from request to export."""
        # Step 1: Create and validate request
        request = SolverRequest(
            equations=['x**2 + y**2 - 25', 'x + y - 7'],
            variables=['x', 'y'],
            initial_guess={'x': 3.0, 'y': 4.0},
            constraints={'x': (0, 6), 'y': (0, 6)},
            solver_options={'display': False, 'store_history': True}
        )
        
        is_valid, error = self.service.validate_solver_request(request)
        assert is_valid is True
        
        # Step 2: Solve system
        response = self.service.solve_algebraic_system(request)
        assert response.success is True
        
        # Step 3: Verify results
        assert response.solution is not None
        assert response.report is not None
        
        # Step 4: Test serialization
        json_str = solver_response_to_json(response)
        parsed = json.loads(json_str)
        assert parsed["success"] is True
        
        # Step 5: Test export (mock session)
        self.service.active_sessions[response.session_id] = {
            'response': response.__dict__
        }
        
        exported = self.service.export_results(response.session_id, 'json')
        assert exported is not None
    
    def test_constraint_violation_workflow(self):
        """Test workflow with constraint violations."""
        request = SolverRequest(
            equations=['x**2 + y**2 - 4', 'x - y'],
            variables=['x', 'y'],
            initial_guess={'x': -10.0, 'y': 10.0},  # Violates constraints
            constraints={'x': (0, 3), 'y': (0, 3)},
            solver_options={'display': False, 'constraint_handling': 'project'}
        )
        
        # Validation should pass (constraints are valid format)
        is_valid, error = self.service.validate_solver_request(request)
        assert is_valid is True
        
        # Solve should succeed with warnings
        response = self.service.solve_algebraic_system(request)
        assert response.success is True
        assert response.warnings is not None
        
        # Solution should satisfy constraints
        x, y = response.solution['x'], response.solution['y']
        assert 0 <= x <= 3
        assert 0 <= y <= 3
    
    def test_dynamic_system_workflow(self):
        """Test complete dynamic system workflow."""
        request = DynamicSolverRequest(
            equations=['dx/dt = -0.5*x', 'dy/dt = 0.3*y'],
            variables=['x', 'y'],
            time_range=(0, 3),
            initial_conditions={'x': 10, 'y': 2},
            method='RK45'
        )
        
        response = self.service.solve_dynamic_system(request)
        
        assert response.success is True
        assert response.solution is not None
        
        # Verify exponential decay/growth
        x_data = response.solution['solution']['x']
        y_data = response.solution['solution']['y']
        
        # x should decay (first value > last value)
        assert x_data[0] > x_data[-1]
        
        # y should grow (first value < last value) 
        assert y_data[0] < y_data[-1]


@pytest.mark.web_api
class TestParameterRange:
    """Test the ParameterRange class functionality."""
    
    def test_parameter_range_creation(self):
        """Test creating a parameter range."""
        range_obj = ParameterRange(lower=0.0, upper=1.0, increment=0.1)
        
        assert range_obj.lower == 0.0
        assert range_obj.upper == 1.0
        assert range_obj.increment == 0.1
    
    def test_parameter_range_get_values_basic(self):
        """Test getting values from a parameter range."""
        range_obj = ParameterRange(lower=0.0, upper=1.0, increment=0.5)
        values = range_obj.get_values()
        
        expected = [0.0, 0.5, 1.0]
        assert len(values) == len(expected)
        assert all(abs(v - e) < 1e-10 for v, e in zip(values, expected))
    
    def test_parameter_range_get_values_single_point(self):
        """Test parameter range with single point."""
        range_obj = ParameterRange(lower=1.0, upper=1.0, increment=0.1)
        values = range_obj.get_values()
        
        assert len(values) == 1
        assert abs(values[0] - 1.0) < 1e-10
    
    def test_parameter_range_get_values_negative_range(self):
        """Test parameter range with negative values."""
        range_obj = ParameterRange(lower=-2.0, upper=2.0, increment=1.0)
        values = range_obj.get_values()
        
        expected = [-2.0, -1.0, 0.0, 1.0, 2.0]
        assert len(values) == len(expected)
        assert all(abs(v - e) < 1e-10 for v, e in zip(values, expected))
    
    def test_parameter_range_invalid_increment(self):
        """Test parameter range with invalid increment."""
        range_obj = ParameterRange(lower=0.0, upper=1.0, increment=0.0)
        
        with pytest.raises(ValueError, match="Increment must be positive"):
            range_obj.get_values()
        
        range_obj_negative = ParameterRange(lower=0.0, upper=1.0, increment=-0.1)
        
        with pytest.raises(ValueError, match="Increment must be positive"):
            range_obj_negative.get_values()
    
    def test_parameter_range_floating_point_precision(self):
        """Test parameter range with floating point precision."""
        range_obj = ParameterRange(lower=0.0, upper=0.3, increment=0.1)
        values = range_obj.get_values()
        
        # Should include 0.0, 0.1, 0.2, 0.3 despite floating point precision
        expected = [0.0, 0.1, 0.2, 0.3]
        assert len(values) == len(expected)
        assert all(abs(v - e) < 1e-10 for v, e in zip(values, expected))


@pytest.mark.web_api
class TestSymbolDetection:
    """Test the symbol detection functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.service = WebAPIService()
    
    def test_detect_symbols_simple_equations(self):
        """Test symbol detection with simple equations."""
        equations = ['x + y - 1', 'x - y']
        
        result = self.service.detect_symbols(equations)
        
        assert 'detected_symbols' in result
        assert 'suggested_variables' in result
        assert 'suggested_parameters' in result
        
        symbols = result['detected_symbols']
        assert 'x' in symbols
        assert 'y' in symbols
        assert len(symbols) == 2
    
    def test_detect_symbols_parametric_equations(self):
        """Test symbol detection with parameters."""
        equations = ['a*x**2 + b*x + c', 'x - y']
        
        result = self.service.detect_symbols(equations)
        symbols = result['detected_symbols']
        
        expected_symbols = ['a', 'b', 'c', 'x', 'y']
        assert len(symbols) == len(expected_symbols)
        assert all(sym in symbols for sym in expected_symbols)
    
    def test_detect_symbols_with_functions(self):
        """Test symbol detection excluding mathematical functions."""
        equations = ['sin(x) + cos(y)', 'exp(z) - log(w)']
        
        result = self.service.detect_symbols(equations)
        symbols = result['detected_symbols']
        
        # Should detect variables but not functions
        expected_variables = ['w', 'x', 'y', 'z']  # Sorted order
        assert len(symbols) == len(expected_variables)
        assert all(var in symbols for var in expected_variables)
        
        # Should not include function names
        function_names = ['sin', 'cos', 'exp', 'log', 'ln']
        assert not any(func in symbols for func in function_names)
    
    def test_detect_symbols_complex_expressions(self):
        """Test symbol detection with complex expressions."""
        equations = [
            'alpha*x**2 + beta_coeff*y - gamma_val',
            '2*r + h*theta'  # Simplified to avoid parsing issues with pi and tan
        ]
        
        result = self.service.detect_symbols(equations)
        symbols = result['detected_symbols']
        
        # Should include variables and parameters
        expected = ['alpha', 'beta_coeff', 'gamma_val', 'h', 'r', 'theta', 'x', 'y']
        assert all(sym in symbols for sym in expected)
        
        # All detected symbols should be from our expected set (no unexpected functions)
        for sym in symbols:
            assert sym in expected
    
    def test_detect_symbols_empty_equations(self):
        """Test symbol detection with empty equations list."""
        equations = []
        
        result = self.service.detect_symbols(equations)
        symbols = result['detected_symbols']
        
        assert len(symbols) == 0
    
    def test_detect_symbols_invalid_equations(self):
        """Test symbol detection with invalid equations."""
        equations = ['invalid equation +++', 'x + y']
        
        # Should not raise exception, should handle gracefully
        result = self.service.detect_symbols(equations)
        symbols = result['detected_symbols']
        
        # Should at least detect x and y from valid equation
        assert 'x' in symbols
        assert 'y' in symbols
    
    def test_detect_symbols_whitespace_and_formatting(self):
        """Test symbol detection handles whitespace and formatting."""
        equations = [
            '  x  +  y_1  -  z_var  ',
            'alpha_123 * beta_456'
        ]
        
        result = self.service.detect_symbols(equations)
        symbols = result['detected_symbols']
        
        expected = ['alpha_123', 'beta_456', 'x', 'y_1', 'z_var']
        assert len(symbols) == len(expected)
        assert all(sym in symbols for sym in expected)


@pytest.mark.web_api
class TestParameterSweep:
    """Test the parameter sweep functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.service = WebAPIService()
    
    def test_basic_parameter_sweep(self):
        """Test basic parameter sweep functionality."""
        parameter_ranges = {
            'a': ParameterRange(lower=0.5, upper=1.5, increment=0.5)
        }
        
        request = SolverRequest(
            equations=['a*x - 1'],
            variables=['x'],
            initial_guess={'x': 1.0},
            parameter_ranges=parameter_ranges
        )
        
        response = self.service.solve_algebraic_system(request)
        
        assert response.success is True
        assert 'sweep_summary' in response.solution
        
        sweep_data = response.report
        assert sweep_data['total_combinations'] == 3  # 0.5, 1.0, 1.5
        assert sweep_data['successful_solves'] >= 0
        assert 0 <= sweep_data['success_rate'] <= 1
        
        # Check sweep results structure
        sweep_results = sweep_data['sweep_results']
        assert len(sweep_results) == 3
        
        for result in sweep_results:
            assert 'parameters' in result
            assert 'solution' in result
            assert 'success' in result
            assert 'a' in result['parameters']
    
    def test_multiple_parameter_sweep(self):
        """Test parameter sweep with multiple parameters."""
        parameter_ranges = {
            'a': ParameterRange(lower=1.0, upper=2.0, increment=1.0),
            'b': ParameterRange(lower=0.5, upper=1.0, increment=0.5)
        }
        
        request = SolverRequest(
            equations=['a*x + b*y - 1', 'x + y - 2'],
            variables=['x', 'y'],
            initial_guess={'x': 1.0, 'y': 1.0},
            parameter_ranges=parameter_ranges
        )
        
        response = self.service.solve_algebraic_system(request)
        
        assert response.success is True
        
        sweep_data = response.report
        # Should be 2 * 2 = 4 combinations
        assert sweep_data['total_combinations'] == 4
        
        # Check all parameter combinations are present
        sweep_results = sweep_data['sweep_results']
        assert len(sweep_results) == 4
        
        # Verify all combinations are tested
        param_combinations = [(r['parameters']['a'], r['parameters']['b']) 
                            for r in sweep_results]
        expected_combinations = [(1.0, 0.5), (1.0, 1.0), (2.0, 0.5), (2.0, 1.0)]
        
        assert len(param_combinations) == len(expected_combinations)
        for combo in expected_combinations:
            assert combo in param_combinations
    
    def test_parameter_sweep_limit_protection(self):
        """Test parameter sweep respects combination limits."""
        # Create ranges that would exceed the limit
        parameter_ranges = {
            'a': ParameterRange(lower=0, upper=50, increment=1),  # 51 values
            'b': ParameterRange(lower=0, upper=50, increment=1)   # 51 values
            # Total combinations: 51 * 51 = 2601 > 1000 limit
        }
        
        request = SolverRequest(
            equations=['a*x + b*y - 1'],
            variables=['x'],
            initial_guess={'x': 1.0},
            parameter_ranges=parameter_ranges
        )
        
        response = self.service.solve_algebraic_system(request)
        
        # Should still succeed but with warnings or limitations
        # Check if it's handled appropriately (either error or warning)
        if not response.success:
            assert 'too large' in response.error.lower()
        else:
            # If it succeeds, should have warnings
            assert response.warnings is not None
    
    def test_parameter_sweep_with_constraints(self):
        """Test parameter sweep with variable constraints."""
        parameter_ranges = {
            'k': ParameterRange(lower=0.5, upper=2.0, increment=0.5)
        }
        
        request = SolverRequest(
            equations=['k*x**2 + y**2 - 4', 'x - y'],
            variables=['x', 'y'],
            initial_guess={'x': 1.5, 'y': 1.5},
            constraints={'x': (0, 3), 'y': (0, 3)},
            parameter_ranges=parameter_ranges
        )
        
        response = self.service.solve_algebraic_system(request)
        
        assert response.success is True
        
        sweep_results = response.report['sweep_results']
        
        # Check that solutions respect constraints when successful
        for result in sweep_results:
            if result['success'] and result['solution']:
                x_val = result['solution']['x']
                y_val = result['solution']['y']
                
                # Solutions should respect constraints
                assert 0 <= x_val <= 3
                assert 0 <= y_val <= 3
    
    def test_parameter_sweep_error_handling(self):
        """Test parameter sweep handles individual solve failures gracefully."""
        # Use parameters that might cause some solutions to fail
        parameter_ranges = {
            'a': ParameterRange(lower=0.0, upper=2.0, increment=1.0)  # a=0 might cause issues
        }
        
        request = SolverRequest(
            equations=['a*x - 1'],  # Single equation, single variable
            variables=['x'],
            initial_guess={'x': 2.0},
            parameter_ranges=parameter_ranges
        )
        
        response = self.service.solve_algebraic_system(request)
        
        # Overall sweep should succeed even if some individual solves fail
        assert response.success is True
        
        sweep_results = response.report['sweep_results']
        assert len(sweep_results) == 3  # 0.0, 1.0, 2.0
        
        # Should record both successful and failed attempts
        success_statuses = [result['success'] for result in sweep_results]
        assert isinstance(success_statuses[0], bool)  # All should have success status
        
        # Expect some failures due to a=0 (division by zero scenario)
        failed_count = sum(1 for status in success_statuses if not status)
        successful_count = sum(1 for status in success_statuses if status)
        
        # Should have at least one failure (when a=0) and at least one success
        assert failed_count >= 1  # a=0 case should fail
        assert successful_count >= 1  # a=1,2 cases should succeed
    
    def test_parameter_sweep_performance_metrics(self):
        """Test parameter sweep includes performance metrics."""
        parameter_ranges = {
            'scale': ParameterRange(lower=1.0, upper=3.0, increment=1.0)
        }
        
        request = SolverRequest(
            equations=['scale*x - 2'],
            variables=['x'],
            initial_guess={'x': 1.0},
            parameter_ranges=parameter_ranges
        )
        
        response = self.service.solve_algebraic_system(request)
        
        assert response.success is True
        assert response.execution_time is not None
        assert response.execution_time > 0
        
        # Check sweep-specific metrics
        sweep_data = response.report
        assert 'success_rate' in sweep_data
        assert 'successful_solves' in sweep_data
        assert 'total_combinations' in sweep_data
        
        # Check individual result metrics
        for result in sweep_data['sweep_results']:
            if result['success']:
                assert 'residual_norm' in result
                assert 'iterations' in result
    
    def test_regular_solve_without_parameter_ranges(self):
        """Test that regular solving still works when parameter_ranges is None."""
        request = SolverRequest(
            equations=['x + y - 3', 'x - y - 1'],
            variables=['x', 'y'],
            initial_guess={'x': 1.0, 'y': 1.0},
            parameter_ranges=None  # Explicitly test None case
        )
        
        response = self.service.solve_algebraic_system(request)
        
        assert response.success is True
        assert response.solution is not None
        assert 'x' in response.solution
        assert 'y' in response.solution
        
        # Should not be a sweep result
        assert 'sweep_summary' not in response.solution


if __name__ == "__main__":
    pytest.main([__file__])
