#!/usr/bin/env python3
"""
Web Server Demo for TextToSolver

A simple HTTP server demonstration showing how to integrate TextToSolver
with web applications. This provides RESTful endpoints for equation solving
and real-time progress monitoring.

QUICK START:
    python examples/web_server_demo.py
    
Then visit: http://localhost:8080

Endpoints:
- POST /solve/algebraic - Solve algebraic equation system
- POST /solve/dynamic - Solve dynamic equation system  
- GET /progress/{session_id} - Get real-time solving progress
- GET /export/{session_id} - Export results in JSON/CSV

Author: TextToSolver Development Team
"""

import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any
import threading
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from text_to_solver.web_api import (
    WebAPIService, 
    SolverRequest, 
    DynamicSolverRequest,
    create_solver_request_from_json,
    create_dynamic_request_from_json,
    solver_response_to_json
)


class TextToSolverHandler(BaseHTTPRequestHandler):
    """HTTP request handler for TextToSolver web API."""
    
    def __init__(self, *args, **kwargs):
        self.api_service = WebAPIService()
        super().__init__(*args, **kwargs)
    
    def _set_cors_headers(self):
        """Set CORS headers for web app integration."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def _send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        """Send JSON response with proper headers."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode('utf-8'))
    
    def _send_error_response(self, message: str, status_code: int = 400):
        """Send error response."""
        error_data = {'error': message, 'success': False}
        self._send_json_response(error_data, status_code)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.strip('/').split('/')
        
        if len(path_parts) == 0 or path_parts[0] == '':
            # Serve simple HTML demo page
            self._serve_demo_page()
        elif len(path_parts) >= 2 and path_parts[0] == 'progress':
            # Get solving progress
            session_id = path_parts[1]
            progress = self.api_service.get_iteration_progress(session_id)
            if progress:
                self._send_json_response(progress)
            else:
                self._send_error_response("Session not found", 404)
        elif len(path_parts) >= 2 and path_parts[0] == 'export':
            # Export results
            session_id = path_parts[1]
            query_params = parse_qs(parsed_path.query)
            format_type = query_params.get('format', ['json'])[0]
            
            results = self.api_service.export_results(session_id, format_type)
            if results:
                if format_type == 'csv':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/csv')
                    self.send_header('Content-Disposition', f'attachment; filename=results_{session_id}.csv')
                    self._set_cors_headers()
                    self.end_headers()
                    self.wfile.write(results.encode('utf-8'))
                else:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self._set_cors_headers()
                    self.end_headers()
                    self.wfile.write(results.encode('utf-8'))
            else:
                self._send_error_response("Session not found or no results", 404)
        else:
            self._send_error_response("Endpoint not found", 404)
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.strip('/').split('/')
        
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            if len(path_parts) >= 2 and path_parts[0] == 'solve':
                if path_parts[1] == 'algebraic':
                    # Solve algebraic system
                    request = create_solver_request_from_json(post_data)
                    response = self.api_service.solve_algebraic_system(request)
                    self._send_json_response(response.__dict__)
                    
                elif path_parts[1] == 'dynamic':
                    # Solve dynamic system
                    request = create_dynamic_request_from_json(post_data)
                    response = self.api_service.solve_dynamic_system(request)
                    self._send_json_response(response.__dict__)
                    
                else:
                    self._send_error_response("Unknown solve type", 400)
            else:
                self._send_error_response("Invalid endpoint", 400)
                
        except json.JSONDecodeError:
            self._send_error_response("Invalid JSON in request body", 400)
        except Exception as e:
            self._send_error_response(f"Server error: {str(e)}", 500)
    
    def _serve_demo_page(self):
        """Serve a simple HTML demo page."""
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>TextToSolver Web Demo</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { margin: 20px 0; }
        textarea { width: 100%; height: 100px; margin: 10px 0; }
        button { padding: 10px 20px; margin: 5px; background: #007cba; color: white; border: none; cursor: pointer; }
        button:hover { background: #005a8a; }
        .result { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .error { background: #ffebee; border: 1px solid #f44336; }
        .success { background: #e8f5e8; border: 1px solid #4caf50; }
    </style>
</head>
<body>
    <h1>🧮 TextToSolver Web Demo</h1>
    
    <div class="container">
        <h2>Algebraic Equation Solver</h2>
        <p>Solve systems like: x² + y² = 4, x - y = 0</p>
        
        <label>Equations (one per line):</label>
        <textarea id="equations">x**2 + y**2 - 4
x - y</textarea>
        
        <label>Variables (comma separated):</label>
        <input type="text" id="variables" value="x,y" style="width: 100%; padding: 5px;">
        
        <label>Initial Guess (JSON format):</label>
        <input type="text" id="guess" value='{"x": 1.5, "y": 1.5}' style="width: 100%; padding: 5px;">
        
        <label>Constraints (JSON format, optional):</label>
        <input type="text" id="constraints" value='{"x": [0, 3], "y": [0, 3]}' style="width: 100%; padding: 5px;">
        
        <button onclick="solveAlgebraic()">Solve Algebraic System</button>
        <button onclick="clearResults()">Clear Results</button>
    </div>
    
    <div class="container">
        <h2>Dynamic Equation Solver</h2>
        <p>Solve differential equations like: dx/dt = -0.1*x + 0.05*x*y</p>
        
        <label>Differential Equations (one per line):</label>
        <textarea id="ode_equations">dx/dt = -0.1*x + 0.05*x*y
dy/dt = 0.1*y - 0.05*x*y</textarea>
        
        <label>Variables:</label>
        <input type="text" id="ode_variables" value="x,y" style="width: 100%; padding: 5px;">
        
        <label>Time Range [start, end]:</label>
        <input type="text" id="time_range" value="[0, 20]" style="width: 100%; padding: 5px;">
        
        <label>Initial Conditions:</label>
        <input type="text" id="initial_conditions" value='{"x": 10, "y": 5}' style="width: 100%; padding: 5px;">
        
        <button onclick="solveDynamic()">Solve Dynamic System</button>
    </div>
    
    <div id="results"></div>
    
    <script>
        async function solveAlgebraic() {
            const equations = document.getElementById('equations').value.split('\\n').filter(eq => eq.trim());
            const variables = document.getElementById('variables').value.split(',').map(v => v.trim());
            const guess = JSON.parse(document.getElementById('guess').value);
            const constraintsText = document.getElementById('constraints').value.trim();
            
            let constraints = null;
            if (constraintsText) {
                try {
                    const parsed = JSON.parse(constraintsText);
                    constraints = {};
                    for (const [key, value] of Object.entries(parsed)) {
                        constraints[key] = Array.isArray(value) ? value : [value[0], value[1]];
                    }
                } catch (e) {
                    showResult('Invalid constraints format', true);
                    return;
                }
            }
            
            const request = {
                equations: equations,
                variables: variables,
                initial_guess: guess,
                constraints: constraints,
                solver_options: { display: false }
            };
            
            try {
                const response = await fetch('/solve/algebraic', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(request)
                });
                
                const result = await response.json();
                showResult(result, !result.success);
            } catch (error) {
                showResult('Network error: ' + error.message, true);
            }
        }
        
        async function solveDynamic() {
            const equations = document.getElementById('ode_equations').value.split('\\n').filter(eq => eq.trim());
            const variables = document.getElementById('ode_variables').value.split(',').map(v => v.trim());
            const timeRange = JSON.parse(document.getElementById('time_range').value);
            const initialConditions = JSON.parse(document.getElementById('initial_conditions').value);
            
            const request = {
                equations: equations,
                variables: variables,
                time_range: timeRange,
                initial_conditions: initialConditions,
                method: 'RK45'
            };
            
            try {
                const response = await fetch('/solve/dynamic', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(request)
                });
                
                const result = await response.json();
                showResult(result, !result.success);
            } catch (error) {
                showResult('Network error: ' + error.message, true);
            }
        }
        
        function showResult(result, isError = false) {
            const resultsDiv = document.getElementById('results');
            const resultClass = isError ? 'result error' : 'result success';
            
            let content = `<div class="${resultClass}">`;
            if (typeof result === 'string') {
                content += `<h3>Error</h3><p>${result}</p>`;
            } else {
                content += `<h3>${result.success ? 'Success' : 'Error'}</h3>`;
                content += `<pre>${JSON.stringify(result, null, 2)}</pre>`;
            }
            content += '</div>';
            
            resultsDiv.innerHTML = content + resultsDiv.innerHTML;
        }
        
        function clearResults() {
            document.getElementById('results').innerHTML = '';
        }
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[{self.date_time_string()}] {format % args}")


def run_server(port: int = 8080):
    """Run the TextToSolver web server."""
    server_address = ('', port)
    
    # Create a class that shares the WebAPIService instance
    class SharedServiceHandler(TextToSolverHandler):
        api_service = WebAPIService()  # Shared instance
    
    httpd = HTTPServer(server_address, SharedServiceHandler)
    
    print(f"🚀 TextToSolver Web Server Starting...")
    print(f"📡 Server running at http://localhost:{port}")
    print(f"🌐 Demo page: http://localhost:{port}")
    print(f"📊 API Endpoints:")
    print(f"   POST /solve/algebraic - Solve algebraic equations")
    print(f"   POST /solve/dynamic - Solve differential equations")
    print(f"   GET /progress/{{session_id}} - Get solving progress")
    print(f"   GET /export/{{session_id}} - Export results")
    print(f"🛑 Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped by user")
        httpd.server_close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='TextToSolver Web Server Demo')
    parser.add_argument('--port', type=int, default=8080, help='Server port (default: 8080)')
    
    args = parser.parse_args()
    run_server(args.port)
