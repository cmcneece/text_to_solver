#!/usr/bin/env python3
"""
TextToSolver Web Application

A comprehensive web interface for the TextToSolver API featuring:
- Interactive equation input and solving
- Real-time iteration tracking
- Dynamic visualization with Chart.js
- Session management and progress monitoring
- Constraint handling and validation

Usage:
    python web_app.py
    
Then visit: http://localhost:5000

Author: TextToSolver Development Team
"""

import os
import sys
import json
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import uuid
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from text_to_solver.web_api import (
    WebAPIService, 
    SolverRequest,
    ParameterRange, 
    DynamicSolverRequest,
    solver_response_to_json
)
from text_to_solver.session_manager import SessionManager, SessionConfig
from text_to_solver.visualization_utils import VisualizationUtils

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'texttosolver-demo-key-change-in-production'
CORS(app)

# Initialize services
api_service = WebAPIService()
session_manager = SessionManager(max_concurrent_sessions=50)
viz_utils = VisualizationUtils()

# Store active solving sessions
active_sessions = {}


@app.route('/')
def index():
    """Main application page."""
    return render_template('index.html')


@app.route('/api/detect-symbols', methods=['POST'])
def detect_symbols():
    """Detect symbols in equations."""
    try:
        data = request.get_json()
        equations = data.get('equations', [])
        
        if not equations:
            return jsonify({
                'success': False,
                'error': 'No equations provided'
            }), 400
        
        # Detect symbols using the web API service
        symbols = api_service.detect_symbols(equations)
        
        return jsonify({
            'success': True,
            'symbols': symbols
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Symbol detection error: {str(e)}'
        }), 500


@app.route('/api/solve', methods=['POST'])
def solve_system():
    """Solve an equation system."""
    try:
        data = request.get_json()
        
        # Create session for this solve request
        solve_session_id = session_manager.create_session(
            SessionConfig(
                enable_progress_tracking=True,
                max_iterations=data.get('max_iterations', 50)
            )
        )
        
        # Create solver request
        # Handle parameter ranges if provided
        parameter_ranges = None
        if 'parameter_ranges' in data and data['parameter_ranges']:
            from text_to_solver.web_api import ParameterRange
            parameter_ranges = {}
            for param_name, range_data in data['parameter_ranges'].items():
                parameter_ranges[param_name] = ParameterRange(
                    lower=float(range_data['lower']),
                    upper=float(range_data['upper']),
                    increment=float(range_data['increment'])
                )
        
        solver_request = SolverRequest(
            equations=data['equations'],
            variables=data['variables'],
            initial_guess=data['initial_guess'],
            parameters=data.get('parameters', {}),
            parameter_ranges=parameter_ranges,
            constraints=data.get('constraints', {}),
            solver_options={
                'display': False,
                'store_history': True,
                'max_iter': data.get('max_iterations', 50),
                'tol_fun': data.get('tolerance', 1e-6),
                'constraint_handling': data.get('constraint_handling', 'project')
            },
            session_id=solve_session_id
        )
        
        # Solve the system
        response = api_service.solve_algebraic_system(solver_request)
        
        # Update session
        session_manager.update_session_status(
            solve_session_id,
            'completed' if response.success else 'failed',
            response
        )
        
        # Store session for progress tracking
        active_sessions[solve_session_id] = {
            'response': response,
            'timestamp': datetime.now()
        }
        
        # Generate visualization data if successful
        viz_data = {}
        if response.success and response.report and 'iteration_history' in response.report:
            iteration_history = response.report['iteration_history']
            
            # Convergence plot
            viz_data['convergence_plot'] = viz_utils.generate_convergence_plot(iteration_history)
            
            # Constraint visualization if constraints exist
            if solver_request.constraints:
                viz_data['constraint_plot'] = viz_utils.generate_constraint_visualization(
                    solver_request.variables,
                    solver_request.constraints,
                    response.solution,
                    iteration_history
                )
            
            # Parameter vs variable plots
            viz_data['solution_plot'] = generate_solution_plot(
                solver_request.parameters,
                response.solution,
                solver_request.variables
            )
        
        return jsonify({
            'success': response.success,
            'session_id': solve_session_id,
            'solution': response.solution,
            'report': response.report,
            'error': response.error,
            'warnings': response.warnings,
            'execution_time': response.execution_time,
            'visualization': viz_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/progress/<session_id>')
def get_progress(session_id):
    """Get solving progress for a session."""
    try:
        progress = session_manager.get_latest_progress(session_id)
        if progress:
            # Generate real-time visualization data
            real_time_data = viz_utils.generate_real_time_progress(progress.__dict__)
            
            return jsonify({
                'success': True,
                'progress': real_time_data,
                'iteration_count': len(session_manager.get_progress_history(session_id))
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Session not found or no progress available'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error retrieving progress: {str(e)}'
        }), 500


@app.route('/api/iteration_history/<session_id>')
def get_iteration_history(session_id):
    """Get complete iteration history for a session."""
    try:
        if session_id in active_sessions:
            response = active_sessions[session_id]['response']
            
            if response.success and response.report and 'iteration_history' in response.report:
                iteration_history = response.report['iteration_history']
                
                return jsonify({
                    'success': True,
                    'iteration_history': iteration_history,
                    'convergence_plot': viz_utils.generate_convergence_plot(iteration_history)
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No iteration history available'
                })
        else:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error retrieving history: {str(e)}'
        }), 500


@app.route('/api/visualize', methods=['POST'])
def generate_custom_plot():
    """Generate custom visualization plots."""
    try:
        data = request.get_json()
        session_id = data['session_id']
        plot_type = data['plot_type']
        
        if session_id not in active_sessions:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            })
        
        response = active_sessions[session_id]['response']
        
        if not response.success:
            return jsonify({
                'success': False,
                'error': 'Cannot visualize failed solution'
            })
        
        plot_data = None
        
        if plot_type == 'parameter_vs_variables':
            # Plot parameters vs variables
            plot_data = generate_parameter_variable_plot(
                data.get('parameters', {}),
                response.solution,
                data.get('x_axis', 'parameters'),
                data.get('y_axis', 'variables')
            )
            
        elif plot_type == 'variable_vs_variable':
            # Plot one variable vs another
            plot_data = generate_variable_vs_variable_plot(
                response.solution,
                data.get('x_variable'),
                data.get('y_variable')
            )
            
        elif plot_type == 'convergence':
            # Convergence analysis
            if response.report and 'iteration_history' in response.report:
                plot_data = viz_utils.generate_convergence_plot(
                    response.report['iteration_history']
                )
        
        return jsonify({
            'success': True,
            'plot_data': plot_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Visualization error: {str(e)}'
        }), 500


@app.route('/api/session_stats')
def get_session_stats():
    """Get session manager statistics."""
    try:
        stats = session_manager.get_session_statistics()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error retrieving stats: {str(e)}'
        }), 500


def generate_solution_plot(parameters, solution, variables):
    """Generate solution visualization plot."""
    if not parameters and not solution:
        return None
    
    # Create scatter plot of parameters vs variables
    datasets = []
    
    if parameters:
        # Parameters on x-axis, variables on y-axis
        param_names = list(parameters.keys())
        param_values = list(parameters.values())
        
        for i, (var_name, var_value) in enumerate(solution.items()):
            datasets.append({
                'label': f'{var_name} = {var_value:.4f}',
                'data': [{'x': j, 'y': var_value} for j in range(len(param_names))],
                'backgroundColor': f'hsl({i * 60}, 70%, 50%)',
                'borderColor': f'hsl({i * 60}, 70%, 40%)'
            })
        
        return {
            'type': 'scatter',
            'data': {'datasets': datasets},
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'Solution Values'
                    }
                },
                'scales': {
                    'x': {
                        'type': 'linear',
                        'title': {
                            'display': True,
                            'text': 'Parameter Index'
                        },
                        'ticks': {
                            'callback': f'function(value, index) {{ return {param_names}[index] || value; }}'
                        }
                    },
                    'y': {
                        'title': {
                            'display': True,
                            'text': 'Variable Value'
                        }
                    }
                }
            }
        }
    else:
        # Just show solution values as bar chart
        return {
            'type': 'bar',
            'data': {
                'labels': list(solution.keys()),
                'datasets': [{
                    'label': 'Solution Values',
                    'data': list(solution.values()),
                    'backgroundColor': 'rgba(75, 192, 192, 0.6)',
                    'borderColor': 'rgba(75, 192, 192, 1)',
                    'borderWidth': 1
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'Solution Values'
                    }
                },
                'scales': {
                    'y': {
                        'title': {
                            'display': True,
                            'text': 'Value'
                        }
                    }
                }
            }
        }


def generate_parameter_variable_plot(parameters, solution, x_axis, y_axis):
    """Generate parameter vs variable plot."""
    # Implementation for custom parameter/variable plotting
    return generate_solution_plot(parameters, solution, list(solution.keys()))


def generate_variable_vs_variable_plot(solution, x_variable, y_variable):
    """Generate variable vs variable plot."""
    if x_variable not in solution or y_variable not in solution:
        return None
    
    return {
        'type': 'scatter',
        'data': {
            'datasets': [{
                'label': f'{y_variable} vs {x_variable}',
                'data': [{
                    'x': solution[x_variable],
                    'y': solution[y_variable]
                }],
                'backgroundColor': 'rgba(255, 99, 132, 0.6)',
                'borderColor': 'rgba(255, 99, 132, 1)',
                'pointRadius': 8
            }]
        },
        'options': {
            'responsive': True,
            'plugins': {
                'title': {
                    'display': True,
                    'text': f'{y_variable} vs {x_variable}'
                }
            },
            'scales': {
                'x': {
                    'title': {
                        'display': True,
                        'text': x_variable
                    }
                },
                'y': {
                    'title': {
                        'display': True,
                        'text': y_variable
                    }
                }
            }
        }
    }


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("🌐 TextToSolver Web Application")
    print("=" * 50)
    print("Starting Flask development server...")
    print("Visit: http://localhost:5001")
    print("Press Ctrl+C to stop the server")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5001)
