#!/usr/bin/env python3
"""
Test Suite for Web App Endpoints

Tests Flask web application endpoints including:
- Symbol detection endpoint
- Enhanced solver endpoint with parameter ranges
- Request/response validation
- Error handling

Author: TextToSolver Test Team
"""

import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Flask app for testing
from web_app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.mark.web_api
class TestSymbolDetectionEndpoint:
    """Test the /api/detect-symbols endpoint."""
    
    def test_detect_symbols_success(self, client):
        """Test successful symbol detection."""
        data = {
            'equations': ['a*x + b*y - c', 'x - y + d']
        }
        
        response = client.post(
            '/api/detect-symbols',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['success'] is True
        assert 'symbols' in result
        
        symbols = result['symbols']['detected_symbols']
        expected_symbols = ['a', 'b', 'c', 'd', 'x', 'y']
        
        assert len(symbols) == len(expected_symbols)
        assert all(sym in symbols for sym in expected_symbols)
    
    def test_detect_symbols_empty_equations(self, client):
        """Test symbol detection with empty equations."""
        data = {'equations': []}
        
        response = client.post(
            '/api/detect-symbols',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        
        result = json.loads(response.data)
        assert result['success'] is False
        assert 'No equations provided' in result['error']
    
    def test_detect_symbols_missing_equations(self, client):
        """Test symbol detection with missing equations field."""
        data = {}
        
        response = client.post(
            '/api/detect-symbols',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        
        result = json.loads(response.data)
        assert result['success'] is False
    
    def test_detect_symbols_invalid_json(self, client):
        """Test symbol detection with invalid JSON."""
        response = client.post(
            '/api/detect-symbols',
            data='invalid json',
            content_type='application/json'
        )
        
        # Flask should return 400 for invalid JSON
        assert response.status_code in [400, 500]
    
    def test_detect_symbols_complex_equations(self, client):
        """Test symbol detection with complex mathematical expressions."""
        data = {
            'equations': [
                'alpha*sin(omega*t) + beta*cos(phi)',
                'gamma*exp(lambda_val*x) - delta*log(y)'
            ]
        }
        
        response = client.post(
            '/api/detect-symbols',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['success'] is True
        
        symbols = result['symbols']['detected_symbols']
        
        # Should detect variables and parameters
        expected_variables = ['alpha', 'beta', 'gamma', 'delta', 'lambda_val', 'omega', 'phi', 't', 'x', 'y']
        detected_variables = [sym for sym in expected_variables if sym in symbols]
        
        # Should have detected most/all variables (depending on parsing)
        assert len(detected_variables) >= 8  # Allow some flexibility in parsing


@pytest.mark.web_api 
class TestEnhancedSolverEndpoint:
    """Test the enhanced /api/solve endpoint with parameter ranges."""
    
    def test_solve_with_parameter_ranges_success(self, client):
        """Test solving with parameter ranges."""
        data = {
            'equations': ['a*x - 1'],
            'variables': ['x'],
            'initial_guess': {'x': 1.0},
            'parameter_ranges': {
                'a': {'lower': 0.5, 'upper': 1.5, 'increment': 0.5}
            }
        }
        
        response = client.post(
            '/api/solve',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['success'] is True
        assert 'sweep_summary' in result['solution']
        
        sweep_data = result['report']
        assert sweep_data['total_combinations'] == 3
        assert len(sweep_data['sweep_results']) == 3
    
    def test_solve_without_parameter_ranges(self, client):
        """Test regular solving without parameter ranges."""
        data = {
            'equations': ['x + y - 3', 'x - y - 1'],
            'variables': ['x', 'y'],
            'initial_guess': {'x': 1.0, 'y': 1.0}
        }
        
        response = client.post(
            '/api/solve',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['success'] is True
        assert 'x' in result['solution']
        assert 'y' in result['solution']
        
        # Should not be a sweep result
        assert 'sweep_summary' not in result['solution']
    
    def test_solve_with_multiple_parameter_ranges(self, client):
        """Test solving with multiple parameter ranges."""
        data = {
            'equations': ['a*x + b*y - 1', 'x + y - 2'],
            'variables': ['x', 'y'],
            'initial_guess': {'x': 1.0, 'y': 1.0},
            'parameter_ranges': {
                'a': {'lower': 1.0, 'upper': 2.0, 'increment': 1.0},
                'b': {'lower': 0.5, 'upper': 1.0, 'increment': 0.5}
            }
        }
        
        response = client.post(
            '/api/solve',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['success'] is True
        
        sweep_data = result['report']
        assert sweep_data['total_combinations'] == 4  # 2 * 2 combinations
    
    def test_solve_parameter_ranges_invalid_format(self, client):
        """Test solving with invalid parameter range format."""
        data = {
            'equations': ['a*x - 1'],
            'variables': ['x'],
            'initial_guess': {'x': 1.0},
            'parameter_ranges': {
                'a': {'lower': 'invalid', 'upper': 1.0, 'increment': 0.1}
            }
        }
        
        response = client.post(
            '/api/solve',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should return error for invalid parameter range format
        assert response.status_code == 200  # Flask returns 200 but with error in response
        
        result = json.loads(response.data)
        assert result['success'] is False
        assert 'error' in result
    
    def test_solve_parameter_ranges_too_large(self, client):
        """Test parameter sweep size limitations."""
        data = {
            'equations': ['a*x + b*y - 1'],
            'variables': ['x'],
            'initial_guess': {'x': 1.0},
            'parameter_ranges': {
                'a': {'lower': 0, 'upper': 100, 'increment': 1},
                'b': {'lower': 0, 'upper': 100, 'increment': 1}
                # This creates 101 * 101 = 10201 combinations > 10000 limit
            }
        }
        
        response = client.post(
            '/api/solve',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        result = json.loads(response.data)
        # Should either fail with error or succeed with warnings
        if not result['success']:
            assert 'too large' in result['error'].lower()
        else:
            assert result['warnings'] is not None


@pytest.mark.web_api
class TestWebAppIntegration:
    """Test integration scenarios for the web app."""
    
    def test_home_page_accessibility(self, client):
        """Test that the home page loads successfully."""
        response = client.get('/')
        
        assert response.status_code == 200
        # Should contain HTML content
        assert b'html' in response.data.lower()
        assert b'texttosolver' in response.data.lower()
    
    def test_symbol_detection_workflow(self, client):
        """Test complete symbol detection workflow."""
        # Step 1: Detect symbols
        detect_data = {
            'equations': ['k*x**2 + m*y - g', 'x + y - L']
        }
        
        detect_response = client.post(
            '/api/detect-symbols',
            data=json.dumps(detect_data),
            content_type='application/json'
        )
        
        assert detect_response.status_code == 200
        detect_result = json.loads(detect_response.data)
        assert detect_result['success'] is True
        
        symbols = detect_result['symbols']['detected_symbols']
        assert 'x' in symbols
        assert 'y' in symbols
        assert 'k' in symbols
        assert 'm' in symbols
        assert 'g' in symbols
        assert 'L' in symbols
        
        # Step 2: Use detected symbols in solve request
        # Classify x, y as variables and k, m, g, L as parameters
        solve_data = {
            'equations': ['k*x**2 + m*y - g', 'x + y - L'],
            'variables': ['x', 'y'],
            'initial_guess': {'x': 1.0, 'y': 1.0},
            'parameters': {'g': 9.81, 'L': 10.0},
            'parameter_ranges': {
                'k': {'lower': 1.0, 'upper': 3.0, 'increment': 1.0},
                'm': {'lower': 0.5, 'upper': 1.5, 'increment': 0.5}
            }
        }
        
        solve_response = client.post(
            '/api/solve',
            data=json.dumps(solve_data),
            content_type='application/json'
        )
        
        assert solve_response.status_code == 200
        solve_result = json.loads(solve_response.data)
        
        # Should successfully perform parameter sweep
        if solve_result['success']:
            assert 'sweep_summary' in solve_result['solution']
            sweep_data = solve_result['report']
            expected_combinations = 3 * 3  # k has 3 values, m has 3 values
            assert sweep_data['total_combinations'] == expected_combinations
    
    def test_error_handling_chain(self, client):
        """Test error handling through the request chain."""
        # Test with invalid equation structure
        data = {
            'equations': [],  # Empty equations should trigger error
            'variables': ['x']
        }
        
        # First try symbol detection
        detect_response = client.post(
            '/api/detect-symbols',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert detect_response.status_code == 400
        
        # Then try solve (should also fail appropriately)
        solve_response = client.post(
            '/api/solve',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should return appropriate error response
        assert solve_response.status_code == 200  # Flask app returns 200 with error in JSON
        result = json.loads(solve_response.data)
        assert result['success'] is False


@pytest.mark.web_api
class TestRequestValidation:
    """Test request validation for new endpoints."""
    
    def test_detect_symbols_content_type_validation(self, client):
        """Test that symbol detection requires correct content type."""
        response = client.post(
            '/api/detect-symbols',
            data='equations=x+y',  # Form data instead of JSON
            content_type='application/x-www-form-urlencoded'
        )
        
        # Should handle gracefully (either reject or process appropriately)
        # The exact behavior depends on Flask configuration
        assert response.status_code in [200, 400, 415]
    
    def test_solve_backward_compatibility(self, client):
        """Test that enhanced solve endpoint maintains backward compatibility."""
        # Test old-style request without parameter_ranges
        old_format_data = {
            'equations': ['x + y - 3'],
            'variables': ['x'],
            'initial_guess': {'x': 1.5}
        }
        
        response = client.post(
            '/api/solve',
            data=json.dumps(old_format_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['success'] is True
        assert 'x' in result['solution']
        
        # Should be regular solve, not sweep
        assert 'sweep_summary' not in result['solution']
    
    def test_parameter_range_edge_cases(self, client):
        """Test parameter range edge cases and validation."""
        edge_cases = [
            # Single point range
            {
                'parameter_ranges': {
                    'a': {'lower': 1.0, 'upper': 1.0, 'increment': 0.1}
                }
            },
            # Very small increment
            {
                'parameter_ranges': {
                    'a': {'lower': 0.0, 'upper': 0.001, 'increment': 0.0001}
                }
            },
            # Negative range
            {
                'parameter_ranges': {
                    'a': {'lower': -2.0, 'upper': 2.0, 'increment': 1.0}
                }
            }
        ]
        
        base_data = {
            'equations': ['a*x - 1'],
            'variables': ['x'],
            'initial_guess': {'x': 1.0}
        }
        
        for i, case in enumerate(edge_cases):
            test_data = {**base_data, **case}
            
            response = client.post(
                '/api/solve',
                data=json.dumps(test_data),
                content_type='application/json'
            )
            
            assert response.status_code == 200, f"Edge case {i} failed with status {response.status_code}"
            
            result = json.loads(response.data)
            # Each case should either succeed or fail gracefully
            assert 'success' in result
            
            if result['success']:
                # If successful, should have appropriate sweep data
                assert 'sweep_summary' in result['solution']


if __name__ == "__main__":
    pytest.main([__file__])
