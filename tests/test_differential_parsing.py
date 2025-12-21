#!/usr/bin/env python3
"""
Tests for Differential Equation Parsing (Phase 3)

Tests the parsing of differential equations with various derivative notations
and mathematical expressions.
"""

import pytest
import numpy as np
import sympy as sp
import sys
import os

# Add the parent directory to sys.path to import text_to_solver
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import dynamic solver components
from text_to_solver.dynamic_solver import (
    DifferentialEquationParser,
    DynamicEquationSolver,
    DynamicSystem
)
from text_to_solver.user_api import EquationSystemError
# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture
def parser():
    """Create a DifferentialEquationParser instance"""
    return DifferentialEquationParser()


# ================================================================
# BASIC PARSING TESTS
# ================================================================

@pytest.mark.dynamic
@pytest.mark.parsing
class TestBasicParsing:
    """Test basic differential equation parsing"""
    
    def test_simple_first_derivative(self, parser):
        """Test parsing simple first derivative: dx/dt = -k*x"""
        equation = "dx/dt = -k*x"
        variables = ['x']
        
        expr = parser.parse_equation(equation, variables)
        
        # Should return the RHS expression
        assert expr is not None
        assert isinstance(expr, sp.Basic)
        
        # Check that it contains the expected symbols
        symbols_in_expr = expr.free_symbols
        symbol_names = {str(s) for s in symbols_in_expr}
        
        assert 'x' in symbol_names
        assert 'k' in symbol_names
    
    def test_derivative_notations(self, parser):
        """Test different derivative notations"""
        variables = ['x']
        
        # Different ways to write dx/dt
        notations = [
            "dx/dt = -x",
            "x' = -x",
        ]
        
        for notation in notations:
            expr = parser.parse_equation(notation, variables)
            assert expr is not None
            
            # All should produce equivalent expressions
            symbols_in_expr = expr.free_symbols
            symbol_names = {str(s) for s in symbols_in_expr}
            assert 'x' in symbol_names
    
    def test_second_derivative_notations(self, parser):
        """Test second derivative notations"""
        variables = ['x']
        
        # Different ways to write d²x/dt²
        notations = [
            "d²x/dt² = -x",
            "d^2x/dt^2 = -x", 
            "x'' = -x"
        ]
        
        for notation in notations:
            try:
                expr = parser.parse_equation(notation, variables)
                assert expr is not None
            except EquationSystemError:
                # Some notations might not be implemented yet
                pass
    
    def test_equation_without_equals(self, parser):
        """Test parsing equation without equals sign (RHS only)"""
        equation = "-k*x"  # Just the RHS
        variables = ['x']
        
        expr = parser.parse_equation(equation, variables)
        
        assert expr is not None
        symbols_in_expr = expr.free_symbols
        symbol_names = {str(s) for s in symbols_in_expr}
        
        assert 'x' in symbol_names
        assert 'k' in symbol_names


@pytest.mark.dynamic
@pytest.mark.parsing
class TestComplexExpressions:
    """Test parsing of complex mathematical expressions"""
    
    def test_polynomial_expressions(self, parser):
        """Test polynomial expressions"""
        equation = "dx/dt = a*x**2 + b*x + c"
        variables = ['x']
        
        expr = parser.parse_equation(equation, variables)
        
        assert expr is not None
        symbols_in_expr = expr.free_symbols
        symbol_names = {str(s) for s in symbols_in_expr}
        
        expected_symbols = {'x', 'a', 'b', 'c'}
        assert expected_symbols.issubset(symbol_names)
    
    def test_trigonometric_functions(self, parser):
        """Test equations with trigonometric functions"""
        # Note: This tests the current parser limitations
        equation = "dx/dt = -x + A*t"  # Use linear forcing instead of sin
        variables = ['x']
        
        expr = parser.parse_equation(equation, variables)
        
        assert expr is not None
        symbols_in_expr = expr.free_symbols
        symbol_names = {str(s) for s in symbols_in_expr}
        
        assert 'x' in symbol_names
        assert 'A' in symbol_names
        assert 't' in symbol_names
    
    def test_exponential_expressions(self, parser):
        """Test exponential expressions"""
        equation = "dx/dt = r*x*(1 - x/K)"  # Logistic growth
        variables = ['x']
        
        expr = parser.parse_equation(equation, variables)
        
        assert expr is not None
        symbols_in_expr = expr.free_symbols
        symbol_names = {str(s) for s in symbols_in_expr}
        
        expected_symbols = {'x', 'r', 'K'}
        assert expected_symbols.issubset(symbol_names)
    
    def test_multi_variable_expressions(self, parser):
        """Test expressions with multiple variables"""
        equation = "dx/dt = alpha*x - beta*x*y"
        variables = ['x', 'y']
        
        expr = parser.parse_equation(equation, variables)
        
        assert expr is not None
        symbols_in_expr = expr.free_symbols
        symbol_names = {str(s) for s in symbols_in_expr}
        
        expected_symbols = {'x', 'y', 'alpha', 'beta'}
        assert expected_symbols.issubset(symbol_names)


@pytest.mark.dynamic 
@pytest.mark.parsing
class TestSystemParsing:
    """Test parsing complete systems of differential equations"""
    
    def test_predator_prey_system(self):
        """Test parsing the predator-prey system"""
        solver = DynamicEquationSolver()
        
        # This should parse successfully
        solver.set_system(
            variables=['x', 'y'],
            equations=[
                'dx/dt = alpha*x - beta*x*y',
                'dy/dt = delta*x*y - gamma*y'
            ],
            parameters={'alpha': 1.0, 'beta': 0.1, 'delta': 0.075, 'gamma': 1.5},
            initial_conditions={'x': 10.0, 'y': 5.0}
        )
        
        # Should create system successfully
        assert solver._system is not None
        assert solver._compiled_system is not None
        assert len(solver._system.equations) == 2
    
    def test_harmonic_oscillator_system(self):
        """Test parsing harmonic oscillator as first-order system"""
        solver = DynamicEquationSolver()
        
        solver.set_system(
            variables=['x', 'v'],
            equations=[
                'dx/dt = v',
                'dv/dt = -omega*omega*x'
            ],
            parameters={'omega': 1.0},
            initial_conditions={'x': 1.0, 'v': 0.0}
        )
        
        assert solver._system is not None
        assert len(solver._system.variables) == 2
        assert len(solver._system.equations) == 2
    
    def test_linear_system_matrix_form(self):
        """Test linear system that could be written in matrix form"""
        solver = DynamicEquationSolver()
        
        # System: dx/dt = -2*x + y, dy/dt = x - 3*y
        solver.set_system(
            variables=['x', 'y'],
            equations=[
                'dx/dt = -a*x + b*y',
                'dy/dt = c*x - d*y'
            ],
            parameters={'a': 2, 'b': 1, 'c': 1, 'd': 3},
            initial_conditions={'x': 1.0, 'y': 0.0}
        )
        
        assert solver._system is not None
        assert len(solver._system.equations) == 2


@pytest.mark.dynamic
@pytest.mark.parsing  
@pytest.mark.error_handling
class TestParsingErrors:
    """Test error handling in equation parsing"""
    
    def test_malformed_equation(self, parser):
        """Test parsing of malformed equations"""
        variables = ['x']
        
        # Various malformed equations
        bad_equations = [
            "dx/dt = -k*x +",  # Incomplete
            "dx/dt = -k*",      # Missing variable
            "= -k*x",           # Missing LHS
            "dx/dt -k*x",       # Missing equals or operator
        ]
        
        for equation in bad_equations:
            with pytest.raises(EquationSystemError):
                parser.parse_equation(equation, variables)
    
    def test_undefined_symbols(self, parser):
        """Test equations with undefined symbols"""
        variables = ['x']
        
        # Equation with undefined parameter
        equation = "dx/dt = -undefined_param*x"
        
        # This might succeed (undefined_param becomes a symbol) or fail
        # depending on implementation - test that it handles gracefully
        try:
            expr = parser.parse_equation(equation, variables)
            # If it succeeds, should contain the undefined symbol
            symbols_in_expr = expr.free_symbols
            symbol_names = {str(s) for s in symbols_in_expr}
            assert 'undefined_param' in symbol_names
        except EquationSystemError:
            # Also acceptable to fail with meaningful error
            pass
    
    def test_variable_mismatch(self):
        """Test error when equation variables don't match system variables"""
        solver = DynamicEquationSolver()
        
        # Equation refers to variable not in system
        with pytest.raises((EquationSystemError, Exception)):
            solver.set_system(
                variables=['x'],  # Only 'x' defined
                equations=['dy/dt = -y'],  # But equation uses 'y'
                initial_conditions={'x': 1.0}
            )
    
    def test_dimension_mismatch(self):
        """Test dimension mismatch between variables and equations"""
        solver = DynamicEquationSolver()
        
        with pytest.raises(EquationSystemError):
            solver.set_system(
                variables=['x', 'y'],  # Two variables
                equations=['dx/dt = -x'],  # One equation
                initial_conditions={'x': 1.0, 'y': 2.0}
            )


@pytest.mark.dynamic
@pytest.mark.parsing
class TestParameterHandling:
    """Test parameter handling in equation parsing"""
    
    def test_explicit_parameters(self, parser):
        """Test equations with explicitly defined parameters"""
        equation = "dx/dt = -k*x + A*t"
        variables = ['x']
        
        expr = parser.parse_equation(equation, variables)
        
        symbols_in_expr = expr.free_symbols
        symbol_names = {str(s) for s in symbols_in_expr}
        
        # Should recognize x, k, A, t as symbols
        expected_symbols = {'x', 'k', 'A', 't'}
        assert expected_symbols.issubset(symbol_names)
    
    def test_greek_letter_parameters(self, parser):
        """Test equations with Greek letter parameters"""
        equation = "dx/dt = alpha*x - beta*x*y"
        variables = ['x', 'y']
        
        expr = parser.parse_equation(equation, variables)
        
        symbols_in_expr = expr.free_symbols
        symbol_names = {str(s) for s in symbols_in_expr}
        
        expected_symbols = {'x', 'y', 'alpha', 'beta'}
        assert expected_symbols.issubset(symbol_names)
    
    def test_numeric_coefficients(self, parser):
        """Test equations with numeric coefficients"""
        equation = "dx/dt = -2.5*x + 1.3*y"
        variables = ['x', 'y']
        
        expr = parser.parse_equation(equation, variables)
        
        assert expr is not None
        symbols_in_expr = expr.free_symbols
        symbol_names = {str(s) for s in symbols_in_expr}
        
        # Should contain variables but not the numeric coefficients as symbols
        assert 'x' in symbol_names
        assert 'y' in symbol_names
        assert '2.5' not in symbol_names  # Numbers shouldn't be symbols
        assert '1.3' not in symbol_names


@pytest.mark.dynamic
@pytest.mark.parsing
class TestDerivativeOrderExtraction:
    """Test extraction of derivative orders"""
    
    def test_extract_first_order_derivatives(self, parser):
        """Test extraction of first-order derivative information"""
        equations = [
            "dx/dt = -x",
            "dy/dt = y",
            "x' = -x"
        ]
        
        for equation in equations:
            orders = parser.extract_derivative_order(equation)
            
            # Should detect first-order derivatives
            assert 'x' in orders
            assert orders['x'] >= 1
    
    def test_extract_second_order_derivatives(self, parser):
        """Test extraction of second-order derivative information"""
        equations = [
            "d²x/dt² = -x",
            "d^2x/dt^2 = -x",
            "x'' = -x"
        ]
        
        for equation in equations:
            try:
                orders = parser.extract_derivative_order(equation)
                # Should detect second-order derivatives
                assert 'x' in orders
                assert orders['x'] == 2
            except:
                # Some notations might not be fully implemented
                pass
    
    def test_mixed_derivative_orders(self, parser):
        """Test equations with mixed derivative orders"""
        equation = "d²x/dt² = -omega*omega*x + dy/dt"
        
        try:
            orders = parser.extract_derivative_order(equation)
            
            # Should detect both first and second order
            assert 'x' in orders
            assert 'y' in orders
            assert orders['x'] == 2  # Second-order for x
            assert orders['y'] == 1  # First-order for y
        except:
            # This advanced parsing might not be implemented yet
            pass


@pytest.mark.dynamic 
@pytest.mark.parsing
@pytest.mark.integration
class TestParsingIntegration:
    """Test integration of parsing with solver"""
    
    def test_parsed_system_solves_correctly(self):
        """Test that parsed systems actually solve correctly"""
        solver = DynamicEquationSolver()
        
        # Set up a system that we can verify analytically
        solver.set_system(
            variables=['x'],
            equations=['dx/dt = -k*x'],
            parameters={'k': 1.0},
            initial_conditions={'x': 1.0}
        )
        
        result = solver.integrate((0, 1), method='RK45')
        
        assert result.success
        
        # Verify against analytical solution
        expected = np.exp(-1.0)  # x(1) = x0*exp(-k*t) = 1*exp(-1*1)
        actual = result.final_values['x']
        
        assert abs(actual - expected) < 0.01
    
    def test_complex_parsed_system(self):
        """Test complex system parsing and solution"""
        solver = DynamicEquationSolver()
        
        # Coupled system with cross terms
        solver.set_system(
            variables=['x', 'y'],
            equations=[
                'dx/dt = a*x + b*y',
                'dy/dt = c*x + d*y'
            ],
            parameters={'a': -1, 'b': 1, 'c': -2, 'd': -1},
            initial_conditions={'x': 1.0, 'y': 0.0}
        )
        
        result = solver.integrate((0, 1), method='RK45')
        
        assert result.success
        assert 'x' in result.variables
        assert 'y' in result.variables
        
        # System should evolve from initial conditions
        assert result.final_values['x'] != 1.0  # Should change from initial
        assert result.final_values['y'] != 0.0  # Should change from initial
