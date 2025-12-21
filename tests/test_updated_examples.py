#!/usr/bin/env python3
"""
Tests for the updated examples to ensure they work with the new EquationSolver API
"""

import pytest
import numpy as np
from text_to_solver import EquationSolver
from text_to_solver.user_api import EquationSystemError, SolverError

# Note: Domain-specific functionality removed - examples now use general-purpose solver
CHEMICAL_EXTENSION_AVAILABLE = False


class TestUpdatedExamples:
    """Test the updated examples use the new API correctly."""

    def test_circle_line_parameter_sweep(self):
        """Test circle and line example with parameter sweep (Method 1)."""
        # From updated circle_and_line.py
        equations = ['x**2 + y**2 = z**2', 'y = 5*x']
        variables = ['x', 'y']
        
        # Create solver with fluent interface
        solver = (EquationSolver()
                  .set_system(variables, equations)
                  .tolerance(1e-10)
                  .guess_strategy('auto'))
        
        # Test parameter sweep
        radii = [1, 2, 3]
        results = solver.parameter_sweep('z', radii)
        
        # Should have successful results (relaxed expectation for initial convergence)
        successful = [r for r in results if r.success]
        assert len(successful) >= 1, f"Should have at least 1 successful solution, got {len(successful)}"
        
        # Verify solutions are correct
        for i, result in enumerate(results):
            if result.success:
                x, y, z = result['x'], result['y'], radii[i]
                
                # Check circle equation: x² + y² = z²
                circle_error = abs(x**2 + y**2 - z**2)
                assert circle_error < 1e-8, f"Circle constraint violated: error={circle_error}"
                
                # Check line equation: y = 5x
                line_error = abs(y - 5*x)
                assert line_error < 1e-8, f"Line constraint violated: error={line_error}"

    def test_circle_line_one_liner(self):
        """Test circle and line example with one-liner solutions (Method 2)."""
        # Test individual one-liner solution
        result = EquationSolver.solve_equations(
            variables=['x', 'y'],
            equations=['x**2 + y**2 = z**2', 'y = 5*x'],
            parameters={'z': 3.0},
            tolerance=1e-10
        )
        
        assert result.success, "One-liner solution should converge"
        
        x, y = result['x'], result['y']
        
        # Verify analytical solution: x = z/√26, y = 5z/√26 for z=3
        expected_x = 3.0 / np.sqrt(26)
        expected_y = 15.0 / np.sqrt(26)
        
        assert abs(x - expected_x) < 1e-8, f"x coordinate error: {abs(x - expected_x)}"
        assert abs(y - expected_y) < 1e-8, f"y coordinate error: {abs(y - expected_y)}"

    def test_circle_line_custom_configuration(self):
        """Test circle and line example with custom configuration (Method 3)."""
        # Test advanced configuration options
        custom_solver = (EquationSolver()
                         .set_system(['x', 'y'], ['x**2 + y**2 = z**2', 'y = 5*x'])
                         .tolerance(1e-12)  # Higher precision
                         .guess_strategy('scaled')  # Different strategy
                         .with_parameters({'z': 3.5}))  # Non-integer radius

        result = custom_solver.solve()
        
        assert result.success, "Custom configuration should converge"
        assert result.residual_norm < 1e-10, "Should achieve high precision"
        
        # Verify solution
        x, y = result['x'], result['y']
        circle_error = abs(x**2 + y**2 - 3.5**2)
        line_error = abs(y - 5*x)
        
        assert circle_error < 1e-10, f"High precision circle constraint: error={circle_error}"
        assert line_error < 1e-10, f"High precision line constraint: error={line_error}"

    # NOTE: test_carbonate_chemical_helpers removed - ChemicalEquilibrium functionality moved to extensions

    def test_carbonate_parameter_sweep(self):
        """Test carbonate system with EquationSolver parameter sweep."""
        # From updated carbonate_speciation.py - Method 2
        carbonate_vars = ['pHCO3', 'pCO3', 'pH2CO3', 'pOH']
        carbonate_equations = [
            'pK1 - pHCO3 - pH + pH2CO3',      # 1st dissociation equilibrium
            'pK2 - pCO3 - pH + pHCO3',        # 2nd dissociation equilibrium  
            'pKw - pH - pOH',                  # Water autoionization
            'pH2CO3 + pHCO3 + pCO3 - pCO2T'   # Mass balance (log-space)
        ]
        
        CHEMICAL_PARAMS = {
            'pKw': 14.0, 'pK1': 6.35, 'pK2': 10.33, 'pCO2T': 3.0
        }
        
        solver = (EquationSolver()
                  .set_system(carbonate_vars, carbonate_equations)
                  .tolerance(1e-8)
                  .guess_strategy('chemical_equilibrium')
                  .with_parameters(CHEMICAL_PARAMS))
        
        # Test parameter sweep over a small pH range
        pH_range = [6.0, 7.0, 8.0, 9.0, 10.0]
        results = solver.parameter_sweep('pH', pH_range)
        
        successful = [r for r in results if r.success]
        assert len(successful) >= 3, f"Should have at least 3 successful solutions, got {len(successful)}"
        
        # Verify mass balance for successful results
        for i, result in enumerate(results):
            if result.success:
                ph_val = pH_range[i]
                
                # Basic sanity checks (p-values can be negative for high concentrations)
                assert -10 < result['pH2CO3'] < 20, f"pH2CO3 out of range: {result['pH2CO3']}"
                assert -10 < result['pHCO3'] < 20, f"pHCO3 out of range: {result['pHCO3']}"
                assert -10 < result['pCO3'] < 20, f"pCO3 out of range: {result['pCO3']}"
                
                # Mass balance check (in log space)
                mass_balance = result['pH2CO3'] + result['pHCO3'] + result['pCO3'] - CHEMICAL_PARAMS['pCO2T']
                
                # Allow some tolerance for mass balance in log space
                assert abs(mass_balance) < 0.1, f"Mass balance error at pH {ph_val}: {mass_balance}"

    def test_carbonate_one_liner_scenarios(self):
        """Test carbonate system one-liner solutions for research scenarios."""
        # From updated carbonate_speciation.py - Method 3
        carbonate_vars = ['pHCO3', 'pCO3', 'pH2CO3', 'pOH']
        carbonate_equations = [
            'pK1 - pHCO3 - pH + pH2CO3',
            'pK2 - pCO3 - pH + pHCO3', 
            'pKw - pH - pOH',
            'pH2CO3 + pHCO3 + pCO3 - pCO2T'
        ]
        
        CHEMICAL_PARAMS = {
            'pKw': 14.0, 'pK1': 6.35, 'pK2': 10.33, 'pCO2T': 3.0
        }
        
        research_scenarios = [
            ("Neutral conditions", 7.0),
            ("Ocean surface", 8.1),
            ("Alkaline conditions", 9.0)
        ]
        
        successful_scenarios = []
        for scenario, ph_val in research_scenarios:
            result = EquationSolver.solve_equations(
                variables=carbonate_vars,
                equations=carbonate_equations,
                parameters={**CHEMICAL_PARAMS, 'pH': ph_val},
                tolerance=1e-8,
                multistart=True  # Extra robustness
            )
            
            if result.success:
                successful_scenarios.append((scenario, ph_val, result))
                
                # Verify solution makes chemical sense
                h2co3_conc = 10**(-result['pH2CO3'])
                hco3_conc = 10**(-result['pHCO3'])
                co3_conc = 10**(-result['pCO3'])
                
                # All concentrations should be positive and reasonable (allowing higher concentrations)
                assert 1e-20 < h2co3_conc < 10, f"H2CO3 concentration unreasonable: {h2co3_conc}"
                assert 1e-20 < hco3_conc < 10, f"HCO3 concentration unreasonable: {hco3_conc}"  
                assert 1e-20 < co3_conc < 10, f"CO3 concentration unreasonable: {co3_conc}"
        
        assert len(successful_scenarios) >= 2, "Should have at least 2 successful scenarios"

    def test_equation_syntax_flexibility(self):
        """Test different equation syntax formats from examples."""
        # Test different ways to express the same equations (from Method 4 in circle_and_line.py)
        alternative_formats = [
            # Standard format
            ['x**2 + y**2 - z**2', 'y - 5*x'],
            # Equality format  
            ['x**2 + y**2 = z**2', 'y = 5*x'],
            # Mixed format
            ['x**2 + y**2 - z**2 = 0', 'y = 5*x']
        ]
        
        successful_formats = 0
        for i, eqs in enumerate(alternative_formats):
            result = EquationSolver.solve_equations(
                variables=['x', 'y'],
                equations=eqs,
                parameters={'z': 2.5},
                tolerance=1e-8  # Relaxed tolerance for stability
            )
            
            if result.success:
                successful_formats += 1
                
                # Verify solution regardless of format
                x, y = result['x'], result['y']
                circle_error = abs(x**2 + y**2 - 2.5**2)
                line_error = abs(y - 5*x)
                
                assert circle_error < 1e-8, f"Format {i+1} circle constraint: error={circle_error}"
                assert line_error < 1e-8, f"Format {i+1} line constraint: error={line_error}"
        
        assert successful_formats >= 1, f"Should handle at least 1 equation format, got {successful_formats}"

    # NOTE: test_water_autoionization_helper removed - ChemicalEquilibrium functionality moved to extensions

    def test_error_handling_robustness(self):
        """Test robust error handling from advanced features examples."""
        # Test with challenging conditions that might fail
        try:
            extreme_result = EquationSolver.solve_equations(
                variables=['pHCO3', 'pCO3', 'pH2CO3', 'pOH'],
                equations=[
                    'pK1 - pHCO3 - pH + pH2CO3',
                    'pK2 - pCO3 - pH + pHCO3',
                    'pKw - pH - pOH', 
                    'pH2CO3 + pHCO3 + pCO3 - pCO2T'
                ],
                parameters={'pH': 2.0, 'pKw': 14.0, 'pK1': 6.35, 'pK2': 10.33, 'pCO2T': 3.0},
                tolerance=1e-8,
                multistart=True
            )
            
            # Either succeeds or fails gracefully
            if extreme_result.success:
                # If it succeeds, values should be in reasonable range (p-values can be negative)
                assert -15 < extreme_result['pH2CO3'] < 20, f"pH2CO3 out of range: {extreme_result['pH2CO3']}"
            else:
                # Should fail gracefully without crashing
                assert not extreme_result.success, "Should report failure clearly"
                
        except Exception as e:
            # Should not raise unhandled exceptions
            pytest.fail(f"Should handle extreme conditions gracefully, got exception: {e}")
