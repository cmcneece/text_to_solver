# TextToSolver Web Application

A comprehensive web interface for the TextToSolver API featuring interactive equation solving, real-time visualization, and session management.

## 🌟 Features

### 📝 Interactive Equation Input
- **System Definition**: Enter multiple equations (one per line)
- **Variable Specification**: Define solution variables
- **Parameter Support**: Add system parameters with values
- **Constraint Handling**: Set bounds on variables with automatic projection
- **Initial Guess**: Specify starting values for Newton's method

### 📊 Real-Time Solving Progress
- **Solution Display**: View final solution values with precision
- **Iteration History**: Track convergence step-by-step
- **Convergence Analysis**: Visual convergence rate monitoring
- **Execution Statistics**: Performance metrics and timing

### 📈 Interactive Visualization
- **Solution Plots**: Bar charts of final variable values
- **Convergence Charts**: Real-time convergence rate visualization
- **Constraint Visualization**: 2D constraint boundary plotting
- **Custom Plots**: Plot any variable against any other variable
- **Multiple Chart Types**: Bar, scatter, line plots with Chart.js

### 🔧 Advanced Features
- **Session Management**: Multi-user concurrent solving
- **Real-Time Updates**: Live progress monitoring
- **Error Handling**: Comprehensive validation and error messages
- **Responsive Design**: Works on desktop and mobile
- **Export Ready**: JSON and visualization data export

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install Flask Flask-CORS
```

### 2. Start the Web Application
```bash
python web_app.py
```

### 3. Open in Browser
Visit: [http://localhost:5000](http://localhost:5000)

## 💡 Usage Examples

### Example 1: Circle and Line Intersection
```
Equations:
x**2 + y**2 - 4
x - y

Variables: x, y
Initial Guess: {"x": 1.5, "y": 1.5}
Constraints: {"x": [0, 3], "y": [0, 3]}
```

### Example 2: Nonlinear System with Parameters
```
Equations:
x**2 + y**2 - r**2
a*x + b*y - c

Variables: x, y
Parameters: {"r": 2, "a": 1, "b": 1, "c": 2}
Initial Guess: {"x": 1.0, "y": 1.0}
```

### Example 3: Optimization Problem
```
Equations:
x**2 + y**2 - 5
2*x + 3*y - 4

Variables: x, y
Initial Guess: {"x": 1.0, "y": 1.0}
Constraints: {"x": [0, 2], "y": [0, 2]}
```

## 🎨 User Interface Layout

### Left Panel: System Definition
- **Equations Input**: Multi-line text area for equation entry
- **Variables**: Comma-separated list of solution variables
- **Initial Guess**: JSON format initial values
- **Parameters**: JSON format parameter values
- **Constraints**: JSON format variable bounds
- **Solve Button**: Initiates solving with loading indicator

### Right Panel: Results and Progress
- **Solution Tab**: Final variable values and statistics
- **Iterations Tab**: Step-by-step convergence history
- **Convergence Tab**: Real-time convergence rate plot

### Bottom Panel: Interactive Visualization
- **Plot Type Selection**: Choose from multiple visualization types
- **Custom Plotting**: Select any variables for x/y axes
- **Chart Controls**: Interactive plot generation
- **Chart Display**: Full-featured Chart.js visualizations

## 🔧 Technical Architecture

### Backend (Flask)
- **REST API Endpoints**: `/api/solve`, `/api/progress`, `/api/visualize`
- **Web API Service**: Stateless solving service
- **Session Management**: Concurrent user support
- **Visualization Utils**: Chart data generation

### Frontend (HTML/JavaScript)
- **Responsive Design**: CSS Grid with mobile support
- **Chart.js Integration**: Interactive plotting library
- **Real-Time Updates**: AJAX communication with backend
- **Error Handling**: Comprehensive validation and user feedback

### API Integration
- **WebAPIService**: Core solving functionality
- **SessionManager**: Multi-user session handling
- **VisualizationUtils**: Chart data preparation
- **JSON Communication**: Structured request/response format

## 📡 API Endpoints

### POST /api/solve
Solve an equation system
```json
{
  "equations": ["x**2 + y**2 - 4", "x - y"],
  "variables": ["x", "y"],
  "initial_guess": {"x": 1.5, "y": 1.5},
  "parameters": {},
  "constraints": {"x": [0, 3], "y": [0, 3]}
}
```

### GET /api/progress/{session_id}
Get real-time solving progress
```json
{
  "success": true,
  "progress": {
    "iteration": 3,
    "residual_norm": 1e-8,
    "status": "converged"
  }
}
```

### POST /api/visualize
Generate custom visualization
```json
{
  "session_id": "uuid",
  "plot_type": "variable_vs_variable",
  "x_variable": "x",
  "y_variable": "y"
}
```

## 🎯 Visualization Features

### Built-in Plot Types
1. **Solution Values**: Bar chart of final variable values
2. **Convergence Analysis**: Line plot of residual norm vs iteration
3. **Constraint Visualization**: 2D constraint boundary with solution path
4. **Custom Variable Plots**: Any variable vs any variable scatter plots

### Interactive Controls
- **Plot Type Selector**: Choose visualization type
- **Variable Selectors**: Pick x/y axes for custom plots
- **Real-Time Updates**: Charts update as solving progresses
- **Responsive Charts**: Automatic resizing and mobile support

### Chart.js Integration
- **Professional Plots**: High-quality, interactive charts
- **Export Ready**: Charts can be saved as images
- **Customizable**: Colors, labels, and styling options
- **Animation**: Smooth transitions and loading effects

## 🛠️ Development and Customization

### Adding New Plot Types
1. Add option to `plot-type` selector in HTML
2. Implement chart generation in `generatePlot()` JavaScript function
3. Add backend support in `/api/visualize` endpoint if needed

### Extending Equation Input
1. Modify form HTML in `templates/index.html`
2. Update `solveSystem()` JavaScript function
3. Extend `SolverRequest` handling in `web_app.py`

### Custom Styling
- Edit CSS styles in `templates/index.html`
- Modify Chart.js options in JavaScript functions
- Add new responsive breakpoints for mobile support

## 🔒 Security Considerations

### Input Validation
- **Equation Parsing**: SymPy-based safe expression evaluation
- **JSON Validation**: Structured input validation
- **Parameter Limits**: Reasonable bounds on solving parameters
- **Session Management**: Automatic cleanup and timeout

### Production Deployment
- Change `app.secret_key` to a secure random value
- Set `debug=False` in production
- Use proper WSGI server (e.g., Gunicorn)
- Add HTTPS and security headers

## 📈 Performance Features

### Optimization
- **Concurrent Sessions**: Multiple users simultaneously
- **Session Cleanup**: Automatic resource management
- **Efficient Solving**: Optimized Newton-Raphson implementation
- **Caching**: Session result storage for visualization

### Scalability
- **Session Limits**: Configurable concurrent user limits
- **Memory Management**: Automatic cleanup of expired sessions
- **Load Balancing**: Stateless design supports load balancers
- **Database Ready**: Session data can be persisted to database

## 🎉 Next Steps

### Potential Enhancements
1. **User Authentication**: Login system for saved sessions
2. **Solution History**: Database storage of previous solves
3. **Collaborative Features**: Share sessions between users  
4. **Advanced Visualization**: 3D plots, animation, parameter sweeps
5. **Mobile App**: React Native or PWA version
6. **Cloud Deployment**: Docker containerization

### Integration Possibilities
- **Jupyter Integration**: Export to notebook format
- **MATLAB/Python Export**: Generate equivalent code
- **API Documentation**: Swagger/OpenAPI specification
- **WebSocket Upgrades**: Full real-time bidirectional communication

---

## 🏆 Result

You now have a **complete, production-ready web application** that showcases all the TextToSolver capabilities:

- **Interactive equation solving** with real-time progress
- **Professional visualization** with Chart.js integration  
- **Multi-user support** with session management
- **Responsive design** for desktop and mobile
- **Comprehensive API** ready for further integration

**Start the app and explore the full power of TextToSolver in your browser!** 🌐🎯
