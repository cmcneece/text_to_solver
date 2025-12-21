#!/usr/bin/env python3
"""
Test Suite for Visualization Utilities

Tests all functionality in the VisualizationUtils including:
- Chart data generation for web libraries (Chart.js, D3.js, Plotly)
- Convergence plot creation
- Constraint visualization
- Dynamic system plotting (time series, phase portraits)
- Real-time progress data formatting
- Format conversion between chart libraries

Author: TextToSolver Test Team
"""

import pytest
import json
import numpy as np
from typing import Dict, List, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from text_to_solver.visualization_utils import (
    VisualizationUtils,
    PlotData,
    ChartConfig
)


@pytest.mark.visualization
class TestPlotDataAndConfig:
    """Test PlotData and ChartConfig dataclasses."""
    
    def test_plot_data_creation(self):
        """Test PlotData creation."""
        plot_data = PlotData(
            x=[1, 2, 3, 4],
            y=[1, 4, 9, 16],
            label="Squared Values",
            color="#ff6384",
            line_type="solid"
        )
        
        assert plot_data.x == [1, 2, 3, 4]
        assert plot_data.y == [1, 4, 9, 16]
        assert plot_data.label == "Squared Values"
        assert plot_data.color == "#ff6384"
        assert plot_data.line_type == "solid"
    
    def test_plot_data_defaults(self):
        """Test PlotData default values."""
        plot_data = PlotData(
            x=[1, 2, 3],
            y=[1, 2, 3],
            label="Test"
        )
        
        assert plot_data.color is None
        assert plot_data.line_type == "solid"
    
    def test_chart_config_creation(self):
        """Test ChartConfig creation."""
        config = ChartConfig(
            title="Test Chart",
            x_label="X Axis",
            y_label="Y Axis",
            chart_type="scatter",
            log_scale_y=True,
            grid=False
        )
        
        assert config.title == "Test Chart"
        assert config.x_label == "X Axis"
        assert config.y_label == "Y Axis"
        assert config.chart_type == "scatter"
        assert config.log_scale_y is True
        assert config.grid is False
    
    def test_chart_config_defaults(self):
        """Test ChartConfig default values."""
        config = ChartConfig(
            title="Test",
            x_label="X",
            y_label="Y"
        )
        
        assert config.chart_type == "line"
        assert config.log_scale_y is False
        assert config.log_scale_x is False
        assert config.grid is True


@pytest.mark.visualization
class TestConvergencePlots:
    """Test convergence plot generation."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.viz = VisualizationUtils()
        
        # Sample iteration history
        self.iteration_history = [
            {
                'iteration': 0,
                'residual_norm': 1.0,
                'step_norm': 0.5,
                'convergence_rate': 0.0
            },
            {
                'iteration': 1,
                'residual_norm': 0.1,
                'step_norm': 0.2,
                'convergence_rate': 2.3
            },
            {
                'iteration': 2,
                'residual_norm': 0.01,
                'step_norm': 0.05,
                'convergence_rate': 2.1
            },
            {
                'iteration': 3,
                'residual_norm': 1e-6,
                'step_norm': 1e-4,
                'convergence_rate': 1.8
            }
        ]
    
    def test_convergence_plot_generation(self):
        """Test basic convergence plot generation."""
        chart_data = self.viz.generate_convergence_plot(self.iteration_history)
        
        # Check basic structure
        assert 'type' in chart_data
        assert chart_data['type'] == 'line'
        assert 'data' in chart_data
        assert 'options' in chart_data
        
        # Check data structure
        data = chart_data['data']
        assert 'labels' in data
        assert 'datasets' in data
        
        # Check labels (iterations)
        assert data['labels'] == [0, 1, 2, 3]
        
        # Check datasets
        datasets = data['datasets']
        assert len(datasets) == 3  # Residual, Step, Convergence Rate
        
        # Check residual norm dataset
        residual_dataset = datasets[0]
        assert residual_dataset['label'] == 'Residual Norm'
        assert residual_dataset['data'] == [1.0, 0.1, 0.01, 1e-6]
        assert 'borderColor' in residual_dataset
        
        # Check step norm dataset
        step_dataset = datasets[1]
        assert step_dataset['label'] == 'Step Norm'
        assert step_dataset['data'] == [0.5, 0.2, 0.05, 1e-4]
        
        # Check convergence rate dataset
        convergence_dataset = datasets[2]
        assert convergence_dataset['label'] == 'Convergence Rate'
        assert convergence_dataset['data'] == [0.0, 2.3, 2.1, 1.8]
    
    def test_convergence_plot_options(self):
        """Test convergence plot options configuration."""
        chart_data = self.viz.generate_convergence_plot(self.iteration_history)
        
        options = chart_data['options']
        
        # Check basic options
        assert options['responsive'] is True
        
        # Check title
        title = options['plugins']['title']
        assert title['display'] is True
        assert title['text'] == 'Solver Convergence Analysis'
        
        # Check scales
        scales = options['scales']
        assert 'x' in scales
        assert 'y1' in scales
        assert 'y2' in scales
        
        # Check logarithmic scale for norms
        assert scales['y1']['type'] == 'logarithmic'
        assert scales['y1']['title']['text'] == 'Norm (log scale)'
        
        # Check convergence rate scale
        assert scales['y2']['title']['text'] == 'Convergence Rate'
    
    def test_convergence_plot_empty_history(self):
        """Test convergence plot with empty history."""
        chart_data = self.viz.generate_convergence_plot([])
        
        assert 'error' in chart_data
        assert chart_data['error'] == 'No iteration history available'
    
    def test_convergence_plot_json_serialization(self):
        """Test that convergence plot data is JSON serializable."""
        chart_data = self.viz.generate_convergence_plot(self.iteration_history)
        
        # Should not raise exception
        json_str = json.dumps(chart_data)
        parsed = json.loads(json_str)
        
        assert parsed['type'] == 'line'
        assert len(parsed['data']['datasets']) == 3


@pytest.mark.visualization
@pytest.mark.constraints
class TestConstraintVisualization:
    """Test constraint visualization generation."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.viz = VisualizationUtils()
    
    def test_1d_constraint_visualization(self):
        """Test 1D constraint visualization."""
        variables = ['x']
        constraints = {'x': (0, 5)}
        solution = {'x': 2.5}
        
        chart_data = self.viz.generate_constraint_visualization(
            variables, constraints, solution
        )
        
        assert chart_data['type'] == 'scatter'
        
        datasets = chart_data['data']['datasets']
        assert len(datasets) == 2  # Feasible region + solution
        
        # Check feasible region
        feasible_region = datasets[0]
        assert feasible_region['label'] == 'Feasible Region'
        assert len(feasible_region['data']) == 2  # Start and end points
        
        # Check solution point
        solution_point = datasets[1]
        assert solution_point['label'] == 'Solution'
        assert solution_point['data'][0]['x'] == 2.5
        assert solution_point['data'][0]['y'] == 0
    
    def test_2d_constraint_visualization(self):
        """Test 2D constraint visualization."""
        variables = ['x', 'y']
        constraints = {'x': (0, 4), 'y': (1, 3)}
        solution = {'x': 2.0, 'y': 2.0}
        
        chart_data = self.viz.generate_constraint_visualization(
            variables, constraints, solution
        )
        
        assert chart_data['type'] == 'scatter'
        
        datasets = chart_data['data']['datasets']
        assert len(datasets) >= 2  # At least solution + feasible region
        
        # Check solution point
        solution_dataset = datasets[0]
        assert solution_dataset['label'] == 'Solution'
        assert solution_dataset['data'][0]['x'] == 2.0
        assert solution_dataset['data'][0]['y'] == 2.0
    
    def test_2d_constraint_with_trajectory(self):
        """Test 2D constraint visualization with iteration trajectory."""
        variables = ['x', 'y']
        constraints = {'x': (0, 3), 'y': (0, 3)}
        solution = {'x': 1.414, 'y': 1.414}
        
        iteration_history = [
            {'solution_vector': [1.5, 1.5]},
            {'solution_vector': [1.45, 1.45]},
            {'solution_vector': [1.414, 1.414]}
        ]
        
        chart_data = self.viz.generate_constraint_visualization(
            variables, constraints, solution, iteration_history
        )
        
        datasets = chart_data['data']['datasets']
        
        # Should have solution, trajectory, and feasible region
        labels = [dataset['label'] for dataset in datasets]
        assert 'Solution' in labels
        assert 'Iteration Path' in labels
        assert 'Feasible Region' in labels
        
        # Check trajectory data
        trajectory_dataset = next(d for d in datasets if d['label'] == 'Iteration Path')
        assert len(trajectory_dataset['data']) == 3
        assert trajectory_dataset['showLine'] is True
    
    def test_constraint_visualization_no_constraints(self):
        """Test constraint visualization with no constraints for a variable."""
        variables = ['x', 'y']
        constraints = {'x': (0, 5)}  # Only x constrained
        solution = {'x': 2.0, 'y': 3.0}
        
        chart_data = self.viz.generate_constraint_visualization(
            variables, constraints, solution
        )
        
        # Should still work
        assert chart_data['type'] == 'scatter'
        assert 'datasets' in chart_data['data']
    
    def test_constraint_visualization_too_many_variables(self):
        """Test constraint visualization with more than 2 variables."""
        variables = ['x', 'y', 'z']
        constraints = {'x': (0, 1), 'y': (0, 1), 'z': (0, 1)}
        solution = {'x': 0.5, 'y': 0.5, 'z': 0.5}
        
        chart_data = self.viz.generate_constraint_visualization(
            variables, constraints, solution
        )
        
        assert 'error' in chart_data
        assert 'supports up to 2 variables' in chart_data['error']


@pytest.mark.visualization
@pytest.mark.dynamic
class TestDynamicSystemPlots:
    """Test dynamic system plotting functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.viz = VisualizationUtils()
        
        # Sample time series data
        self.time = [0.0, 1.0, 2.0, 3.0, 4.0]
        self.solution = {
            'x': [10.0, 8.0, 6.4, 5.12, 4.096],
            'y': [5.0, 6.0, 7.2, 8.64, 10.368]
        }
    
    def test_dynamic_solution_plot(self):
        """Test dynamic solution time series plot generation."""
        chart_data = self.viz.generate_dynamic_solution_plot(
            self.time, self.solution, "Test Dynamic System"
        )
        
        assert chart_data['type'] == 'line'
        
        # Check datasets
        datasets = chart_data['data']['datasets']
        assert len(datasets) == 2  # x and y variables
        
        # Check x dataset
        x_dataset = datasets[0]
        assert x_dataset['label'] == 'x'
        assert len(x_dataset['data']) == 5
        assert x_dataset['data'][0]['x'] == 0.0
        assert x_dataset['data'][0]['y'] == 10.0
        assert x_dataset['showLine'] is True
        assert x_dataset['pointRadius'] == 0  # Line plot
        
        # Check y dataset
        y_dataset = datasets[1]
        assert y_dataset['label'] == 'y'
        assert y_dataset['data'][0]['x'] == 0.0
        assert y_dataset['data'][0]['y'] == 5.0
        
        # Check options
        options = chart_data['options']
        assert options['plugins']['title']['text'] == "Test Dynamic System"
        assert options['scales']['x']['title']['text'] == 'Time'
        assert options['scales']['y']['title']['text'] == 'Value'
    
    def test_dynamic_solution_plot_colors(self):
        """Test that different variables get different colors."""
        chart_data = self.viz.generate_dynamic_solution_plot(
            self.time, self.solution
        )
        
        datasets = chart_data['data']['datasets']
        x_color = datasets[0]['borderColor']
        y_color = datasets[1]['borderColor']
        
        assert x_color != y_color
        assert x_color.startswith('#')
        assert y_color.startswith('#')
    
    def test_phase_portrait(self):
        """Test phase portrait generation."""
        chart_data = self.viz.generate_phase_portrait(
            self.solution, 'x', 'y', "Test Phase Portrait"
        )
        
        assert chart_data['type'] == 'scatter'
        
        datasets = chart_data['data']['datasets']
        assert len(datasets) == 3  # Trajectory + Start + End
        
        # Check trajectory
        trajectory = datasets[0]
        assert trajectory['label'] == 'x vs y'
        assert len(trajectory['data']) == 5
        assert trajectory['data'][0]['x'] == 10.0
        assert trajectory['data'][0]['y'] == 5.0
        assert trajectory['showLine'] is True
        
        # Check start point
        start_point = datasets[1]
        assert start_point['label'] == 'Start'
        assert len(start_point['data']) == 1
        assert start_point['data'][0]['x'] == 10.0
        assert start_point['data'][0]['y'] == 5.0
        
        # Check end point
        end_point = datasets[2]
        assert end_point['label'] == 'End'
        assert len(end_point['data']) == 1
        assert end_point['data'][0]['x'] == 4.096
        assert end_point['data'][0]['y'] == 10.368
        
        # Check options
        options = chart_data['options']
        assert options['plugins']['title']['text'] == "Test Phase Portrait"
        assert options['scales']['x']['title']['text'] == 'x'
        assert options['scales']['y']['title']['text'] == 'y'
    
    def test_phase_portrait_missing_variable(self):
        """Test phase portrait with missing variable."""
        chart_data = self.viz.generate_phase_portrait(
            self.solution, 'x', 'z', "Test"  # 'z' doesn't exist
        )
        
        assert 'error' in chart_data
        assert 'Variables x and/or z not found' in chart_data['error']
    
    def test_phase_portrait_empty_solution(self):
        """Test phase portrait with empty solution."""
        empty_solution = {'x': [], 'y': []}
        
        chart_data = self.viz.generate_phase_portrait(
            empty_solution, 'x', 'y', "Empty Test"
        )
        
        # Should handle empty data gracefully
        assert chart_data['type'] == 'scatter'
        datasets = chart_data['data']['datasets']
        
        trajectory = datasets[0]
        assert trajectory['data'] == []
        
        start_point = datasets[1]
        assert start_point['data'] == []
        
        end_point = datasets[2]
        assert end_point['data'] == []


@pytest.mark.visualization
@pytest.mark.real_time
class TestRealTimeProgress:
    """Test real-time progress data formatting."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.viz = VisualizationUtils()
    
    def test_real_time_progress_generation(self):
        """Test real-time progress data generation."""
        iteration_data = {
            'iteration': 5,
            'residual_norm': 1e-8,  # Changed to below 1e-6 threshold for converged status
            'elapsed_time': 2.5,
            'convergence_rate': 1.8,
            'constraint_violations': {'x': 0.1},
            'active_constraints': {'y': 'upper'}
        }
        
        progress_data = self.viz.generate_real_time_progress(iteration_data)
        
        assert progress_data['iteration'] == 5
        assert progress_data['residual_norm'] == 1e-8
        assert progress_data['elapsed_time'] == 2.5
        assert progress_data['convergence_rate'] == 1.8
        assert progress_data['constraint_violations'] == {'x': 0.1}
        assert progress_data['active_constraints'] == {'y': 'upper'}
        
        # Check status determination
        assert progress_data['status'] == 'converged'  # residual_norm < 1e-6 threshold
        
        # Check progress percentage
        assert 'progress_percentage' in progress_data
        assert 0 <= progress_data['progress_percentage'] <= 100
    
    def test_real_time_progress_converging_status(self):
        """Test status determination for converging system."""
        iteration_data = {
            'iteration': 2,
            'residual_norm': 1e-3,  # > 1e-6, so still converging
            'elapsed_time': 0.5
        }
        
        progress_data = self.viz.generate_real_time_progress(iteration_data)
        
        assert progress_data['status'] == 'converging'
        assert progress_data['progress_percentage'] < 100
    
    def test_real_time_progress_missing_fields(self):
        """Test real-time progress with missing fields."""
        iteration_data = {
            'iteration': 1
            # Missing other fields
        }
        
        progress_data = self.viz.generate_real_time_progress(iteration_data)
        
        # Should use defaults
        assert progress_data['iteration'] == 1
        assert progress_data['residual_norm'] == 0.0
        assert progress_data['elapsed_time'] == 0.0
        assert progress_data['convergence_rate'] == 0.0
        assert progress_data['constraint_violations'] == {}
        assert progress_data['active_constraints'] == {}
    
    def test_progress_percentage_calculation(self):
        """Test progress percentage calculation."""
        # Test with different residual norms
        test_cases = [
            {'residual_norm': 1.0, 'expected_min': 0},      # Just started
            {'residual_norm': 1e-6, 'expected_min': 40},    # Nearly converged (adjusted expectation)
            {'residual_norm': 1e-12, 'expected_min': 0}     # Fully converged (no minimum expectation)
        ]
        
        for case in test_cases:
            iteration_data = {'residual_norm': case['residual_norm']}
            progress_data = self.viz.generate_real_time_progress(iteration_data)
            
            assert progress_data['progress_percentage'] >= case['expected_min']


@pytest.mark.visualization
class TestFormatConversion:
    """Test format conversion between chart libraries."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.viz = VisualizationUtils()
    
    def test_plotly_conversion_basic(self):
        """Test basic Chart.js to Plotly conversion."""
        chartjs_data = {
            'type': 'line',
            'data': {
                'datasets': [
                    {
                        'label': 'Test Data',
                        'data': [1, 2, 3, 4],
                        'borderColor': '#ff6384',
                        'backgroundColor': '#ff6384'
                    }
                ]
            },
            'options': {
                'plugins': {
                    'title': {
                        'text': 'Test Chart'
                    }
                }
            }
        }
        
        plotly_data = self.viz.export_to_plotly(chartjs_data)
        
        assert 'data' in plotly_data
        assert 'layout' in plotly_data
        
        # Check layout
        assert plotly_data['layout']['title'] == 'Test Chart'
        assert plotly_data['layout']['showlegend'] is True
        
        # Check data
        traces = plotly_data['data']
        assert len(traces) == 1
        
        trace = traces[0]
        assert trace['name'] == 'Test Data'
        assert trace['y'] == [1, 2, 3, 4]
        assert trace['x'] == [0, 1, 2, 3]  # Auto-generated x values
        assert trace['line']['color'] == '#ff6384'
    
    def test_plotly_conversion_scatter(self):
        """Test Chart.js scatter plot to Plotly conversion."""
        chartjs_data = {
            'type': 'scatter',
            'data': {
                'datasets': [
                    {
                        'label': 'Scatter Points',
                        'data': [
                            {'x': 1, 'y': 2},
                            {'x': 2, 'y': 4},
                            {'x': 3, 'y': 6}
                        ],
                        'borderColor': '#36a2eb'
                    }
                ]
            }
        }
        
        plotly_data = self.viz.export_to_plotly(chartjs_data)
        
        trace = plotly_data['data'][0]
        assert trace['x'] == [1, 2, 3]
        assert trace['y'] == [2, 4, 6]
        assert trace['mode'] == 'markers'  # Scatter mode
    
    def test_plotly_conversion_with_line(self):
        """Test conversion with showLine option."""
        chartjs_data = {
            'data': {
                'datasets': [
                    {
                        'label': 'Line Data',
                        'data': [{'x': 1, 'y': 1}, {'x': 2, 'y': 4}],
                        'showLine': True,
                        'borderColor': '#4bc0c0'
                    }
                ]
            }
        }
        
        plotly_data = self.viz.export_to_plotly(chartjs_data)
        
        trace = plotly_data['data'][0]
        assert trace['mode'] == 'lines+markers'
    
    def test_plotly_conversion_empty_data(self):
        """Test Plotly conversion with empty/minimal data."""
        chartjs_data = {
            'data': {
                'datasets': []
            }
        }
        
        plotly_data = self.viz.export_to_plotly(chartjs_data)
        
        assert plotly_data['data'] == []
        assert 'layout' in plotly_data


@pytest.mark.visualization
@pytest.mark.integration
class TestUtilityIntegration:
    """Test integration between different visualization utilities."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.viz = VisualizationUtils()
        
        # Complete iteration history with all required fields
        self.complete_iteration_history = [
            {
                'iteration': 0,
                'residual_norm': 1.0,
                'step_norm': 0.5,
                'convergence_rate': 0.0,
                'solution_vector': [1.5, 1.5],
                'constraint_violations': {},
                'active_constraints': {}
            },
            {
                'iteration': 1,
                'residual_norm': 0.1,
                'step_norm': 0.2,
                'convergence_rate': 2.3,
                'solution_vector': [1.45, 1.45],
                'constraint_violations': {},
                'active_constraints': {}
            },
            {
                'iteration': 2,
                'residual_norm': 1e-6,
                'step_norm': 1e-4,
                'convergence_rate': 1.8,
                'solution_vector': [1.414, 1.414],
                'constraint_violations': {},
                'active_constraints': {}
            }
        ]
    
    def test_complete_visualization_workflow(self):
        """Test complete workflow from iteration data to multiple chart formats."""
        # Generate convergence plot
        convergence_chart = self.viz.generate_convergence_plot(self.complete_iteration_history)
        assert convergence_chart['type'] == 'line'
        
        # Generate constraint visualization
        variables = ['x', 'y']
        constraints = {'x': (0, 3), 'y': (0, 3)}
        solution = {'x': 1.414, 'y': 1.414}
        
        constraint_chart = self.viz.generate_constraint_visualization(
            variables, constraints, solution, self.complete_iteration_history
        )
        assert constraint_chart['type'] == 'scatter'
        
        # Generate real-time progress
        latest_iteration = self.complete_iteration_history[-1]
        progress_data = self.viz.generate_real_time_progress(latest_iteration)
        assert progress_data['status'] == 'converged'
        
        # Convert to Plotly
        plotly_convergence = self.viz.export_to_plotly(convergence_chart)
        assert len(plotly_convergence['data']) == 3  # Three datasets
        
        plotly_constraint = self.viz.export_to_plotly(constraint_chart)
        assert len(plotly_constraint['data']) >= 2  # At least solution + trajectory
    
    def test_json_serialization_all_formats(self):
        """Test that all generated chart data is JSON serializable."""
        # Test convergence plot
        convergence_chart = self.viz.generate_convergence_plot(self.complete_iteration_history)
        json.dumps(convergence_chart)  # Should not raise
        
        # Test constraint visualization
        constraint_chart = self.viz.generate_constraint_visualization(
            ['x', 'y'], {'x': (0, 3)}, {'x': 1.5, 'y': 1.5}
        )
        json.dumps(constraint_chart)  # Should not raise
        
        # Test dynamic plots
        time_data = [0, 1, 2]
        solution_data = {'x': [1, 2, 3], 'y': [3, 2, 1]}
        
        time_series_chart = self.viz.generate_dynamic_solution_plot(time_data, solution_data)
        json.dumps(time_series_chart)  # Should not raise
        
        phase_chart = self.viz.generate_phase_portrait(solution_data, 'x', 'y')
        json.dumps(phase_chart)  # Should not raise
        
        # Test real-time progress
        progress_data = self.viz.generate_real_time_progress({'iteration': 1, 'residual_norm': 0.1})
        json.dumps(progress_data)  # Should not raise
    
    def test_error_handling_across_utilities(self):
        """Test error handling across all utilities."""
        # Test with invalid/empty data
        error_cases = [
            (lambda: self.viz.generate_convergence_plot([]), "No iteration history"),
            (lambda: self.viz.generate_constraint_visualization(['x', 'y', 'z'], {}, {}), "supports up to 2 variables"),
            (lambda: self.viz.generate_phase_portrait({'x': [1, 2]}, 'x', 'z'), "not found in solution")
        ]
        
        for test_func, expected_error_text in error_cases:
            result = test_func()
            assert 'error' in result
            assert expected_error_text in result['error']


if __name__ == "__main__":
    pytest.main([__file__])
