# TextToSolver Web API Integration Guide

This guide shows how to integrate TextToSolver into web applications with robust APIs, session management, and real-time capabilities.

## 🌐 Web-Ready Architecture

TextToSolver provides a complete web integration layer with:

- **Stateless Service Layer**: RESTful API compatible with any web framework
- **Session Management**: Concurrent user support with state persistence  
- **Real-time Updates**: WebSocket-compatible progress monitoring
- **Visualization Data**: Ready-to-use data for Chart.js, D3.js, Plotly
- **JSON Serialization**: Complete data exchange format
- **Error Handling**: Structured error responses with HTTP status codes

## 🚀 Quick Start

### Basic Web API Usage

```python
from text_to_solver.web_api import WebAPIService, SolverRequest

# Create service instance
service = WebAPIService()

# Create solve request
request = SolverRequest(
    equations=['x**2 + y**2 - 4', 'x - y'],
    variables=['x', 'y'], 
    initial_guess={'x': 1.5, 'y': 1.5},
    constraints={'x': (0, 3), 'y': (0, 3)}
)

# Solve system
response = service.solve_algebraic_system(request)

if response.success:
    print(f"Solution: {response.solution}")
else:
    print(f"Error: {response.error}")
```

### Session Management

```python
from text_to_solver.session_manager import SessionManager, SessionConfig

# Create session manager
manager = SessionManager(max_concurrent_sessions=100)

# Create session for user
session_id = manager.create_session(SessionConfig(
    max_iterations=50,
    timeout_seconds=300,
    enable_progress_tracking=True
))

# Track progress
def on_progress(progress):
    print(f"Iteration {progress.iteration}: {progress.residual_norm}")

manager.register_progress_callback(session_id, on_progress)
```

### Visualization Data Generation

```python
from text_to_solver.visualization_utils import VisualizationUtils

viz = VisualizationUtils()

# Generate Chart.js compatible convergence plot
chart_data = viz.generate_convergence_plot(iteration_history)

# Generate constraint visualization  
constraint_viz = viz.generate_constraint_visualization(
    variables, constraints, solution, iteration_history
)

# Generate dynamic system plots
time_series = viz.generate_dynamic_solution_plot(time, solution)
phase_portrait = viz.generate_phase_portrait(solution, 'x', 'y')
```

## 🏗️ Web Framework Integration

### Flask Integration Example

```python
from flask import Flask, request, jsonify
from text_to_solver.web_api import WebAPIService, create_solver_request_from_json

app = Flask(__name__)
api_service = WebAPIService()

@app.route('/solve/algebraic', methods=['POST'])
def solve_algebraic():
    try:
        # Parse JSON request
        solver_request = create_solver_request_from_json(request.get_data())
        
        # Solve system
        response = api_service.solve_algebraic_system(solver_request)
        
        # Return JSON response
        return jsonify(response.__dict__), 200 if response.success else 400
        
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/progress/<session_id>')
def get_progress(session_id):
    progress = api_service.get_iteration_progress(session_id)
    if progress:
        return jsonify(progress)
    else:
        return jsonify({'error': 'Session not found'}), 404
```

### FastAPI Integration Example

```python
from fastapi import FastAPI, HTTPException
from text_to_solver.web_api import WebAPIService, SolverRequest, SolverResponse

app = FastAPI()
api_service = WebAPIService()

@app.post("/solve/algebraic", response_model=SolverResponse)
async def solve_algebraic(request: SolverRequest):
    response = api_service.solve_algebraic_system(request)
    
    if not response.success:
        raise HTTPException(status_code=400, detail=response.error)
    
    return response

@app.websocket("/ws/progress/{session_id}")
async def websocket_progress(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    def send_progress(progress):
        asyncio.create_task(websocket.send_json(progress.__dict__))
    
    manager.register_progress_callback(session_id, send_progress)
    
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        manager.unregister_progress_callbacks(session_id)
```

## 📊 Frontend Integration

### JavaScript/React Example

```javascript
// Solve equation system
async function solveSystem(equations, variables, initialGuess, constraints) {
    const request = {
        equations: equations,
        variables: variables,
        initial_guess: initialGuess,
        constraints: constraints,
        solver_options: { constraint_handling: 'project' }
    };
    
    const response = await fetch('/solve/algebraic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
    });
    
    return await response.json();
}

// Real-time progress monitoring
function monitorProgress(sessionId) {
    const ws = new WebSocket(`ws://localhost:8000/ws/progress/${sessionId}`);
    
    ws.onmessage = (event) => {
        const progress = JSON.parse(event.data);
        updateProgressChart(progress);
    };
}

// Visualization with Chart.js
function createConvergencePlot(chartData) {
    const ctx = document.getElementById('convergenceChart').getContext('2d');
    
    new Chart(ctx, {
        type: 'line',
        data: chartData.data,
        options: chartData.options
    });
}
```

### Vue.js Component Example

```vue
<template>
  <div class="solver-component">
    <form @submit.prevent="solvSystem">
      <textarea v-model="equations" placeholder="Enter equations..."></textarea>
      <input v-model="variables" placeholder="Variables (comma separated)">
      <input v-model="initialGuess" placeholder='Initial guess {"x": 1, "y": 1}'>
      <button type="submit" :disabled="solving">Solve</button>
    </form>
    
    <div v-if="solution">
      <h3>Solution:</h3>
      <pre>{{ solution }}</pre>
    </div>
    
    <canvas ref="chart" v-if="chartData"></canvas>
  </div>
</template>

<script>
import Chart from 'chart.js/auto';

export default {
  data() {
    return {
      equations: 'x**2 + y**2 - 4\nx - y',
      variables: 'x,y',
      initialGuess: '{"x": 1.5, "y": 1.5}',
      solving: false,
      solution: null,
      chartData: null
    };
  },
  
  methods: {
    async solveSystem() {
      this.solving = true;
      
      try {
        const request = {
          equations: this.equations.split('\n'),
          variables: this.variables.split(','),
          initial_guess: JSON.parse(this.initialGuess)
        };
        
        const response = await fetch('/solve/algebraic', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(request)
        });
        
        const result = await response.json();
        
        if (result.success) {
          this.solution = result.solution;
          this.createChart(result.report.iteration_history);
        }
      } finally {
        this.solving = false;
      }
    },
    
    createChart(iterationHistory) {
      // Chart creation logic
    }
  }
};
</script>
```

## 🔧 Advanced Features

### Concurrent Session Management

```python
from text_to_solver.session_manager import SessionManager
import threading

# Handle multiple users simultaneously
def handle_user_request(user_id, request_data):
    session_id = manager.create_session(SessionConfig(
        timeout_seconds=600,
        enable_progress_tracking=True
    ))
    
    # Process request in background
    def solve_async():
        response = api_service.solve_algebraic_system(request_data)
        manager.update_session_status(session_id, 
                                    'completed' if response.success else 'failed',
                                    response)
    
    thread = threading.Thread(target=solve_async)
    thread.start()
    
    return session_id
```

### Custom Progress Callbacks

```python
def create_progress_websocket(session_id, websocket):
    """Create WebSocket progress updates."""
    
    def websocket_callback(progress):
        try:
            websocket.send(json.dumps({
                'type': 'progress',
                'data': progress.__dict__
            }))
        except:
            # Connection closed
            manager.unregister_progress_callbacks(session_id)
    
    manager.register_progress_callback(session_id, websocket_callback)
```

### Data Export and Caching

```python
# Export results in multiple formats
def export_session_results(session_id, format_type='json'):
    if format_type == 'json':
        return api_service.export_results(session_id, 'json')
    elif format_type == 'csv':
        return api_service.export_results(session_id, 'csv') 
    elif format_type == 'xlsx':
        # Custom Excel export
        session_data = manager.export_session_data(session_id)
        return create_excel_export(session_data)
```

## 📈 Performance Considerations

### Optimization Tips

1. **Session Cleanup**: Configure automatic cleanup for expired sessions
2. **Concurrent Limits**: Set appropriate limits for concurrent users
3. **Progress Throttling**: Limit progress update frequency for real-time features
4. **Caching**: Cache visualization data for repeated requests
5. **Resource Management**: Monitor memory usage for long-running sessions

```python
# Optimized configuration
manager = SessionManager(
    max_concurrent_sessions=50,  # Adjust based on server capacity
    cleanup_interval=300         # Clean up every 5 minutes
)

# Configure session timeouts appropriately
config = SessionConfig(
    timeout_seconds=1800,        # 30 minutes for complex problems
    enable_progress_tracking=True,
    auto_cleanup=True
)
```

## 🛡️ Security Considerations

### Input Validation

```python
def validate_equation_input(equations):
    """Validate user equation input for security."""
    
    # Check for dangerous operations
    dangerous_patterns = ['import ', 'exec(', 'eval(', '__']
    
    for eq in equations:
        for pattern in dangerous_patterns:
            if pattern in eq.lower():
                raise ValueError(f"Dangerous pattern detected: {pattern}")
    
    # Limit equation complexity
    if len(eq) > 1000:
        raise ValueError("Equation too long")
    
    return True
```

### Rate Limiting

```python
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self, max_requests=10, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id):
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Remove old requests
        user_requests[:] = [req for req in user_requests if now - req < self.time_window]
        
        if len(user_requests) < self.max_requests:
            user_requests.append(now)
            return True
        
        return False
```

## 🌟 Complete Example Applications

See the example files for complete implementations:

- `examples/web_server_demo.py` - Simple HTTP server with HTML interface
- `examples/web_integration_example.py` - Complete architecture demonstration
- `examples/flask_app_example.py` - Flask application with WebSocket support
- `examples/fastapi_app_example.py` - FastAPI application with async support

## 📚 API Reference

### Core Classes

- **WebAPIService**: Stateless service layer for solving
- **SessionManager**: Session state and lifecycle management
- **VisualizationUtils**: Chart data generation utilities
- **SolverRequest/Response**: Data transfer objects

### Key Methods

- `solve_algebraic_system()`: Solve algebraic equations
- `solve_dynamic_system()`: Solve differential equations
- `create_session()`: Create new user session
- `get_iteration_progress()`: Get real-time progress
- `generate_convergence_plot()`: Create convergence visualization
- `export_results()`: Export in multiple formats

This architecture provides a complete foundation for building sophisticated web applications with TextToSolver integration! 🚀
