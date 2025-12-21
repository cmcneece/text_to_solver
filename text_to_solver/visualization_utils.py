#!/usr/bin/env python3
"""
Visualization Utilities for TextToSolver Web Applications

This module provides utilities for preparing solver data for visualization
in web applications. It generates plotting data, convergence charts, and
constraint visualization data that can be easily consumed by JavaScript
charting libraries.

Key Features:
- Convergence plot data generation
- Constraint visualization data
- Solution trajectory plotting
- Real-time progress data formatting
- Export to popular chart formats (Chart.js, D3.js, Plotly)

Author: TextToSolver Development Team
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
import json


@dataclass
class PlotData:
    """Container for plot data in web-friendly format."""
    x: List[float]
    y: List[float]
    label: str
    color: Optional[str] = None
    line_type: str = 'solid'


@dataclass
class ChartConfig:
    """Configuration for chart generation."""
    title: str
    x_label: str
    y_label: str
    chart_type: str = 'line'  # 'line', 'scatter', 'bar'
    log_scale_y: bool = False
    log_scale_x: bool = False
    grid: bool = True


class VisualizationUtils:
    """Utility class for generating visualization data."""
    
    @staticmethod
    def generate_convergence_plot(iteration_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate convergence plot data from iteration history.
        
        Args:
            iteration_history: List of iteration data dictionaries
            
        Returns:
            Chart data in Chart.js format
        """
        if not iteration_history:
            return {"error": "No iteration history available"}
        
        iterations = []
        residuals = []
        step_norms = []
        convergence_rates = []
        
        for iter_data in iteration_history:
            iterations.append(iter_data['iteration'])
            residuals.append(iter_data['residual_norm'])
            step_norms.append(iter_data['step_norm'])
            convergence_rates.append(iter_data['convergence_rate'])
        
        chart_data = {
            "type": "line",
            "data": {
                "labels": iterations,
                "datasets": [
                    {
                        "label": "Residual Norm",
                        "data": residuals,
                        "borderColor": "#ff6384",
                        "backgroundColor": "rgba(255, 99, 132, 0.1)",
                        "yAxisID": "y1"
                    },
                    {
                        "label": "Step Norm",
                        "data": step_norms,
                        "borderColor": "#36a2eb",
                        "backgroundColor": "rgba(54, 162, 235, 0.1)",
                        "yAxisID": "y1"
                    },
                    {
                        "label": "Convergence Rate",
                        "data": convergence_rates,
                        "borderColor": "#4bc0c0",
                        "backgroundColor": "rgba(75, 192, 192, 0.1)",
                        "yAxisID": "y2"
                    }
                ]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "Solver Convergence Analysis"
                    },
                    "legend": {
                        "display": True
                    }
                },
                "scales": {
                    "x": {
                        "display": True,
                        "title": {
                            "display": True,
                            "text": "Iteration"
                        }
                    },
                    "y1": {
                        "type": "logarithmic",
                        "display": True,
                        "position": "left",
                        "title": {
                            "display": True,
                            "text": "Norm (log scale)"
                        }
                    },
                    "y2": {
                        "display": True,
                        "position": "right",
                        "title": {
                            "display": True,
                            "text": "Convergence Rate"
                        },
                        "grid": {
                            "drawOnChartArea": False
                        }
                    }
                }
            }
        }
        
        return chart_data
    
    @staticmethod
    def generate_constraint_visualization(variables: List[str], 
                                        constraints: Dict[str, Tuple[Optional[float], Optional[float]]],
                                        solution: Dict[str, float],
                                        iteration_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generate constraint visualization data.
        
        Args:
            variables: List of variable names
            constraints: Constraint definitions
            solution: Final solution values
            iteration_history: Optional iteration history for trajectory
            
        Returns:
            Visualization data showing constraints and solution path
        """
        if len(variables) > 2:
            return {"error": "Constraint visualization currently supports up to 2 variables"}
        
        if len(variables) == 1:
            # 1D constraint visualization
            var = variables[0]
            if var not in constraints:
                return {"error": f"No constraints defined for variable {var}"}
            
            lower, upper = constraints[var]
            sol_val = solution[var]
            
            chart_data = {
                "type": "scatter",
                "data": {
                    "datasets": [
                        {
                            "label": "Feasible Region",
                            "data": [],
                            "backgroundColor": "rgba(75, 192, 192, 0.3)",
                            "borderColor": "#4bc0c0",
                            "showLine": True
                        },
                        {
                            "label": "Solution",
                            "data": [{"x": sol_val, "y": 0}],
                            "backgroundColor": "#ff6384",
                            "borderColor": "#ff6384",
                            "pointRadius": 8
                        }
                    ]
                }
            }
            
            # Add feasible region
            x_min = lower if lower is not None else sol_val - 5
            x_max = upper if upper is not None else sol_val + 5
            chart_data["data"]["datasets"][0]["data"] = [
                {"x": x_min, "y": 0},
                {"x": x_max, "y": 0}
            ]
            
            return chart_data
        
        elif len(variables) == 2:
            # 2D constraint visualization
            var1, var2 = variables
            sol1, sol2 = solution[var1], solution[var2]
            
            datasets = []
            
            # Add solution point
            datasets.append({
                "label": "Solution",
                "data": [{"x": sol1, "y": sol2}],
                "backgroundColor": "#ff6384",
                "borderColor": "#ff6384",
                "pointRadius": 8
            })
            
            # Add iteration trajectory if available
            if iteration_history:
                trajectory_data = []
                for iter_data in iteration_history:
                    if len(iter_data['solution_vector']) >= 2:
                        trajectory_data.append({
                            "x": iter_data['solution_vector'][0],
                            "y": iter_data['solution_vector'][1]
                        })
                
                if trajectory_data:
                    datasets.append({
                        "label": "Iteration Path",
                        "data": trajectory_data,
                        "backgroundColor": "rgba(54, 162, 235, 0.5)",
                        "borderColor": "#36a2eb",
                        "showLine": True,
                        "pointRadius": 3
                    })
            
            # Add constraint boundaries
            if var1 in constraints or var2 in constraints:
                # Create constraint boundary lines
                x_bounds = constraints.get(var1, (None, None))
                y_bounds = constraints.get(var2, (None, None))
                
                # Determine plot range
                x_min = x_bounds[0] if x_bounds[0] is not None else sol1 - 5
                x_max = x_bounds[1] if x_bounds[1] is not None else sol1 + 5
                y_min = y_bounds[0] if y_bounds[0] is not None else sol2 - 5
                y_max = y_bounds[1] if y_bounds[1] is not None else sol2 + 5
                
                # Add feasible region rectangle
                if x_bounds[0] is not None or x_bounds[1] is not None or y_bounds[0] is not None or y_bounds[1] is not None:
                    feasible_region = [
                        {"x": x_min, "y": y_min},
                        {"x": x_max, "y": y_min},
                        {"x": x_max, "y": y_max},
                        {"x": x_min, "y": y_max},
                        {"x": x_min, "y": y_min}
                    ]
                    
                    datasets.append({
                        "label": "Feasible Region",
                        "data": feasible_region,
                        "backgroundColor": "rgba(75, 192, 192, 0.1)",
                        "borderColor": "#4bc0c0",
                        "showLine": True,
                        "pointRadius": 0,
                        "fill": True
                    })
            
            chart_data = {
                "type": "scatter",
                "data": {"datasets": datasets},
                "options": {
                    "responsive": True,
                    "plugins": {
                        "title": {
                            "display": True,
                            "text": f"Solution Path and Constraints ({var1} vs {var2})"
                        }
                    },
                    "scales": {
                        "x": {
                            "title": {
                                "display": True,
                                "text": var1
                            }
                        },
                        "y": {
                            "title": {
                                "display": True,
                                "text": var2
                            }
                        }
                    }
                }
            }
            
            return chart_data
    
    @staticmethod
    def generate_dynamic_solution_plot(time: List[float], 
                                     solution: Dict[str, List[float]],
                                     title: str = "Dynamic System Solution") -> Dict[str, Any]:
        """
        Generate plot data for dynamic system solutions.
        
        Args:
            time: Time points
            solution: Solution data for each variable
            title: Plot title
            
        Returns:
            Chart data for time series plot
        """
        datasets = []
        colors = ['#ff6384', '#36a2eb', '#4bc0c0', '#ff9f40', '#9966ff', '#ffcd56']
        
        for i, (var, values) in enumerate(solution.items()):
            datasets.append({
                "label": var,
                "data": [{"x": t, "y": v} for t, v in zip(time, values)],
                "borderColor": colors[i % len(colors)],
                "backgroundColor": colors[i % len(colors)] + "20",  # Add transparency
                "showLine": True,
                "pointRadius": 0
            })
        
        chart_data = {
            "type": "line",
            "data": {"datasets": datasets},
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": title
                    }
                },
                "scales": {
                    "x": {
                        "title": {
                            "display": True,
                            "text": "Time"
                        }
                    },
                    "y": {
                        "title": {
                            "display": True,
                            "text": "Value"
                        }
                    }
                }
            }
        }
        
        return chart_data
    
    @staticmethod
    def generate_phase_portrait(solution: Dict[str, List[float]], 
                              var1: str, var2: str,
                              title: str = "Phase Portrait") -> Dict[str, Any]:
        """
        Generate phase portrait for 2D dynamic systems.
        
        Args:
            solution: Solution data
            var1: First variable name
            var2: Second variable name
            title: Plot title
            
        Returns:
            Chart data for phase portrait
        """
        if var1 not in solution or var2 not in solution:
            return {"error": f"Variables {var1} and/or {var2} not found in solution"}
        
        trajectory_data = [
            {"x": x, "y": y} 
            for x, y in zip(solution[var1], solution[var2])
        ]
        
        chart_data = {
            "type": "scatter",
            "data": {
                "datasets": [
                    {
                        "label": f"{var1} vs {var2}",
                        "data": trajectory_data,
                        "borderColor": "#ff6384",
                        "backgroundColor": "rgba(255, 99, 132, 0.1)",
                        "showLine": True,
                        "pointRadius": 1
                    },
                    {
                        "label": "Start",
                        "data": [trajectory_data[0]] if trajectory_data else [],
                        "backgroundColor": "#4bc0c0",
                        "pointRadius": 8
                    },
                    {
                        "label": "End",
                        "data": [trajectory_data[-1]] if trajectory_data else [],
                        "backgroundColor": "#ff9f40",
                        "pointRadius": 8
                    }
                ]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": title
                    }
                },
                "scales": {
                    "x": {
                        "title": {
                            "display": True,
                            "text": var1
                        }
                    },
                    "y": {
                        "title": {
                            "display": True,
                            "text": var2
                        }
                    }
                }
            }
        }
        
        return chart_data
    
    @staticmethod
    def generate_real_time_progress(iteration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate real-time progress data for live updates.
        
        Args:
            iteration_data: Current iteration data
            
        Returns:
            Progress data formatted for real-time display
        """
        return {
            "iteration": iteration_data.get("iteration", 0),
            "residual_norm": float(iteration_data.get("residual_norm", 0)),
            "elapsed_time": float(iteration_data.get("elapsed_time", 0)),
            "convergence_rate": float(iteration_data.get("convergence_rate", 0)),
            "constraint_violations": iteration_data.get("constraint_violations", {}),
            "active_constraints": iteration_data.get("active_constraints", {}),
            "status": "converging" if iteration_data.get("residual_norm", 1) > 1e-6 else "converged",
            "progress_percentage": min(100, max(0, 100 * (1 - np.log10(max(iteration_data.get("residual_norm", 1), 1e-12)) / -12)))
        }
    
    @staticmethod
    def export_to_plotly(chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Chart.js format to Plotly format.
        
        Args:
            chart_data: Chart data in Chart.js format
            
        Returns:
            Chart data in Plotly format
        """
        # This is a basic conversion - could be expanded based on needs
        plotly_data = {
            "data": [],
            "layout": {
                "title": chart_data.get("options", {}).get("plugins", {}).get("title", {}).get("text", ""),
                "showlegend": True
            }
        }
        
        if "datasets" in chart_data.get("data", {}):
            for dataset in chart_data["data"]["datasets"]:
                trace = {
                    "name": dataset.get("label", ""),
                    "mode": "lines+markers" if dataset.get("showLine") else "markers",
                    "line": {"color": dataset.get("borderColor", "#1f77b4")},
                    "marker": {"color": dataset.get("backgroundColor", "#1f77b4")}
                }
                
                # Handle different data formats
                if dataset["data"] and isinstance(dataset["data"][0], dict):
                    trace["x"] = [point["x"] for point in dataset["data"]]
                    trace["y"] = [point["y"] for point in dataset["data"]]
                else:
                    trace["y"] = dataset["data"]
                    trace["x"] = list(range(len(dataset["data"])))
                
                plotly_data["data"].append(trace)
        
        return plotly_data


# Example usage and testing
if __name__ == "__main__":
    # Example iteration history
    iteration_history = [
        {"iteration": 0, "residual_norm": 1.0, "step_norm": 0.5, "convergence_rate": 0.0, "solution_vector": [1.5, 1.5]},
        {"iteration": 1, "residual_norm": 0.1, "step_norm": 0.2, "convergence_rate": 2.3, "solution_vector": [1.4, 1.4]},
        {"iteration": 2, "residual_norm": 0.01, "step_norm": 0.05, "convergence_rate": 2.1, "solution_vector": [1.41, 1.41]},
        {"iteration": 3, "residual_norm": 1e-6, "step_norm": 1e-4, "convergence_rate": 1.8, "solution_vector": [1.414, 1.414]}
    ]
    
    # Test convergence plot
    viz = VisualizationUtils()
    convergence_plot = viz.generate_convergence_plot(iteration_history)
    print("Convergence Plot Data:")
    print(json.dumps(convergence_plot, indent=2))
    
    # Test constraint visualization
    constraints = {"x": (0, 3), "y": (0, 3)}
    solution = {"x": 1.414, "y": 1.414}
    constraint_viz = viz.generate_constraint_visualization(["x", "y"], constraints, solution, iteration_history)
    print("\nConstraint Visualization Data:")
    print(json.dumps(constraint_viz, indent=2))
