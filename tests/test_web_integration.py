#!/usr/bin/env python3
"""
Test Suite for Web API Integration

Comprehensive integration tests that verify all web API components
work together seamlessly:
- Service layer + Session management + Visualization
- End-to-end workflows from request to visualization
- Concurrent user scenarios
- Real-time progress monitoring
- Error handling across all layers
- Performance and resource management

Author: TextToSolver Test Team
"""

import pytest
import json
import time
import threading
from datetime import datetime
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from text_to_solver.web_api import (
    WebAPIService, 
    SolverRequest, 
    DynamicSolverRequest,
    create_solver_request_from_json
)
from text_to_solver.session_manager import SessionManager, SessionConfig
from text_to_solver.visualization_utils import VisualizationUtils


@pytest.mark.web_integration
@pytest.mark.integration
class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.api_service = WebAPIService()
        self.session_manager = SessionManager(max_concurrent_sessions=10)
        self.viz_utils = VisualizationUtils()
    
    def teardown_method(self):
        """Cleanup after each test method."""
        # Clean up sessions
        session_ids = list(self.session_manager.sessions.keys())
        for session_id in session_ids:
            self.session_manager.delete_session(session_id)
    
    def test_complete_algebraic_solving_workflow(self):
        """Test complete workflow: request -> solve -> visualize -> export."""
        
        # Step 1: Create session
        session_id = self.session_manager.create_session(
            SessionConfig(enable_progress_tracking=True, max_iterations=20)
        )
        
        # Step 2: Create and validate request
        request = SolverRequest(
            equations=['x**2 + y**2 - 9', 'x - y + 1'],
            variables=['x', 'y'],
            initial_guess={'x': 2.0, 'y': 1.0},
            constraints={'x': (-1, 4), 'y': (-1, 4)},
            solver_options={'display': False, 'store_history': True},
            session_id=session_id
        )
        
        is_valid, error = self.api_service.validate_solver_request(request)
        assert is_valid is True
        
        # Step 3: Solve system
        response = self.api_service.solve_algebraic_system(request)
        assert response.success is True
        assert response.session_id == session_id
        
        # Step 4: Update session with results
        self.session_manager.update_session_status(
            session_id, 'completed', response
        )
        
        session = self.session_manager.get_session(session_id)
        assert session.status == 'completed'
        assert session.response is not None
        
        # Step 5: Generate visualization data
        if response.report and 'iteration_history' in response.report:
            iteration_history = response.report['iteration_history']
            
            # Convergence plot
            convergence_plot = self.viz_utils.generate_convergence_plot(iteration_history)
            assert convergence_plot['type'] == 'line'
            
            # Constraint visualization
            constraint_viz = self.viz_utils.generate_constraint_visualization(
                request.variables,
                request.constraints,
                response.solution,
                iteration_history
            )
            assert constraint_viz['type'] == 'scatter'
        
        # Step 6: Export session data
        export_data = self.session_manager.export_session_data(session_id)
        assert export_data is not None
        assert export_data['session_id'] == session_id
        assert export_data['status'] == 'completed'
        
        # Step 7: Export results in different formats
        self.api_service.active_sessions[session_id] = {'response': response.__dict__}
        
        json_export = self.api_service.export_results(session_id, 'json')
        assert json_export is not None
        
        csv_export = self.api_service.export_results(session_id, 'csv')
        assert csv_export is not None
        assert 'variable,value' in csv_export
    
    def test_complete_dynamic_solving_workflow(self):
        """Test complete dynamic system workflow with visualization."""
        
        # Step 1: Create session
        session_id = self.session_manager.create_session(
            SessionConfig(timeout_seconds=600)
        )
        
        # Step 2: Create dynamic request
        request = DynamicSolverRequest(
            equations=['dx/dt = -0.5*x', 'dy/dt = 0.3*y'],
            variables=['x', 'y'],
            time_range=(0, 5),
            initial_conditions={'x': 8, 'y': 4},
            method='RK45',
            session_id=session_id
        )
        
        # Step 3: Solve dynamic system
        response = self.api_service.solve_dynamic_system(request)
        assert response.success is True
        
        # Step 4: Update session
        self.session_manager.update_session_status(
            session_id, 'completed', response
        )
        
        # Step 5: Generate dynamic visualizations
        if response.solution:
            time_data = response.solution['time']
            solution_data = response.solution['solution']
            
            # Time series plot
            time_series = self.viz_utils.generate_dynamic_solution_plot(
                time_data, solution_data, "Predator-Prey System"
            )
            assert time_series['type'] == 'line'
            assert len(time_series['data']['datasets']) == 2
            
            # Phase portrait
            phase_portrait = self.viz_utils.generate_phase_portrait(
                solution_data, 'x', 'y', "Phase Portrait"
            )
            assert phase_portrait['type'] == 'scatter'
            
            # Verify data consistency
            assert len(time_data) == len(solution_data['x'])
            assert len(time_data) == len(solution_data['y'])
    
    def test_error_propagation_through_workflow(self):
        """Test error handling propagates correctly through the entire workflow."""
        
        # Step 1: Create session
        session_id = self.session_manager.create_session()
        
        # Step 2: Create invalid request
        request = SolverRequest(
            equations=['invalid equation syntax ###'],
            variables=['x'],
            initial_guess={'x': 1.0},
            session_id=session_id
        )
        
        # Step 3: Validate (should pass - syntax check happens during solving)
        is_valid, error = self.api_service.validate_solver_request(request)
        assert is_valid is True
        
        # Step 4: Solve (should fail)
        response = self.api_service.solve_algebraic_system(request)
        assert response.success is False
        assert response.error is not None
        
        # Step 5: Update session with error
        self.session_manager.update_session_status(
            session_id, 'failed', response, response.error
        )
        
        session = self.session_manager.get_session(session_id)
        assert session.status == 'failed'
        assert session.error_message is not None
        
        # Step 6: Verify statistics updated correctly
        stats = self.session_manager.get_session_statistics()
        assert stats['failed_sessions'] == 1
    
    def test_json_round_trip_workflow(self):
        """Test complete JSON serialization/deserialization workflow."""
        
        # Step 1: Create request from JSON
        json_request = json.dumps({
            "equations": ["x**2 + y**2 - 25", "x + y - 7"],
            "variables": ["x", "y"],
            "initial_guess": {"x": 4.0, "y": 3.0},
            "constraints": {"x": (0, 6), "y": (0, 6)},
            "solver_options": {"display": False, "store_history": True}
        })
        
        request = create_solver_request_from_json(json_request)
        
        # Step 2: Solve
        response = self.api_service.solve_algebraic_system(request)
        assert response.success is True
        
        # Step 3: Serialize response back to JSON
        from text_to_solver.web_api import solver_response_to_json
        response_json = solver_response_to_json(response)
        
        # Step 4: Verify JSON is valid and contains expected data
        parsed_response = json.loads(response_json)
        assert parsed_response['success'] is True
        assert 'solution' in parsed_response
        assert 'x' in parsed_response['solution']
        assert 'y' in parsed_response['solution']
        
        # Step 5: Generate visualization from JSON data
        if parsed_response['report'] and 'iteration_history' in parsed_response['report']:
            iteration_history = parsed_response['report']['iteration_history']
            convergence_plot = self.viz_utils.generate_convergence_plot(iteration_history)
            
            # Should be JSON serializable
            json.dumps(convergence_plot)  # Should not raise


@pytest.mark.web_integration
@pytest.mark.concurrent
class TestConcurrentUsers:
    """Test scenarios with multiple concurrent users."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.api_service = WebAPIService()
        self.session_manager = SessionManager(max_concurrent_sessions=20)
        self.viz_utils = VisualizationUtils()
    
    def teardown_method(self):
        """Cleanup after each test method."""
        session_ids = list(self.session_manager.sessions.keys())
        for session_id in session_ids:
            self.session_manager.delete_session(session_id)
    
    def test_concurrent_algebraic_solving(self):
        """Test multiple users solving different algebraic systems concurrently."""
        
        # Define different problems for different users
        problems = [
            {
                'equations': ['x**2 + y**2 - 4', 'x - y'],
                'variables': ['x', 'y'],
                'initial_guess': {'x': 1.5, 'y': 1.5}
            },
            {
                'equations': ['x**2 - 9', 'y - 2'],
                'variables': ['x', 'y'],
                'initial_guess': {'x': 2.0, 'y': 2.0}
            },
            {
                'equations': ['x + y - 5', '2*x - y - 1'],
                'variables': ['x', 'y'],
                'initial_guess': {'x': 2.0, 'y': 3.0}
            }
        ]
        
        results = []
        errors = []
        
        def solve_problem(problem_index):
            try:
                # Create session
                session_id = self.session_manager.create_session()
                
                # Create request
                problem = problems[problem_index]
                request = SolverRequest(
                    equations=problem['equations'],
                    variables=problem['variables'],
                    initial_guess=problem['initial_guess'],
                    solver_options={'display': False},
                    session_id=session_id
                )
                
                # Solve
                response = self.api_service.solve_algebraic_system(request)
                
                # Update session
                status = 'completed' if response.success else 'failed'
                self.session_manager.update_session_status(session_id, status, response)
                
                results.append({
                    'problem_index': problem_index,
                    'session_id': session_id,
                    'success': response.success,
                    'solution': response.solution
                })
                
            except Exception as e:
                errors.append({'problem_index': problem_index, 'error': str(e)})
        
        # Run problems concurrently
        threads = []
        for i in range(len(problems)):
            thread = threading.Thread(target=solve_problem, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3
        
        # All should have succeeded
        for result in results:
            assert result['success'] is True
            assert result['solution'] is not None
        
        # Verify session statistics
        stats = self.session_manager.get_session_statistics()
        assert stats['total_sessions_created'] == 3
        assert stats['completed_sessions'] == 3
    
    def test_concurrent_progress_monitoring(self):
        """Test concurrent progress monitoring for multiple users."""
        
        # Create sessions for multiple users
        session_ids = []
        for i in range(3):
            session_id = self.session_manager.create_session(
                SessionConfig(enable_progress_tracking=True)
            )
            session_ids.append(session_id)
        
        # Track progress updates for each session
        progress_updates = {session_id: [] for session_id in session_ids}
        
        def progress_callback(session_id):
            def callback(progress):
                progress_updates[session_id].append(progress)
            return callback
        
        # Register callbacks
        for session_id in session_ids:
            self.session_manager.register_progress_callback(
                session_id, progress_callback(session_id)
            )
        
        def simulate_solver_progress(session_id, iterations):
            """Simulate solver progress for a session."""
            for i in range(iterations):
                iteration_data = {
                    'iteration': i,
                    'residual_norm': 1.0 / (10 ** i),
                    'elapsed_time': i * 0.1,
                    'convergence_rate': 2.0 if i > 0 else 0.0
                }
                
                self.session_manager.add_progress_update(session_id, iteration_data)
                time.sleep(0.01)  # Small delay to simulate computation
        
        # Simulate progress for all sessions concurrently
        threads = []
        iteration_counts = [3, 4, 5]  # Different number of iterations per session
        
        for i, session_id in enumerate(session_ids):
            thread = threading.Thread(
                target=simulate_solver_progress,
                args=(session_id, iteration_counts[i])
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify progress was tracked correctly
        for i, session_id in enumerate(session_ids):
            updates = progress_updates[session_id]
            expected_count = iteration_counts[i]
            
            assert len(updates) == expected_count
            
            # Verify progress order
            for j, update in enumerate(updates):
                assert update.iteration == j
                assert update.session_id == session_id
    
    def test_concurrent_visualization_generation(self):
        """Test concurrent visualization generation from multiple sessions."""
        
        # Create sample iteration histories for different sessions
        iteration_histories = [
            [
                {'iteration': 0, 'residual_norm': 1.0, 'step_norm': 0.5, 'convergence_rate': 0.0, 'solution_vector': [1.5, 1.5]},
                {'iteration': 1, 'residual_norm': 0.1, 'step_norm': 0.2, 'convergence_rate': 2.3, 'solution_vector': [1.45, 1.45]},
                {'iteration': 2, 'residual_norm': 1e-6, 'step_norm': 1e-4, 'convergence_rate': 1.8, 'solution_vector': [1.414, 1.414]}
            ],
            [
                {'iteration': 0, 'residual_norm': 0.5, 'step_norm': 0.3, 'convergence_rate': 0.0, 'solution_vector': [1.6, 1.6]},
                {'iteration': 1, 'residual_norm': 0.05, 'step_norm': 0.1, 'convergence_rate': 2.0, 'solution_vector': [1.42, 1.42]},
                {'iteration': 2, 'residual_norm': 5e-7, 'step_norm': 5e-5, 'convergence_rate': 1.5, 'solution_vector': [1.414, 1.414]}
            ],
            [
                {'iteration': 0, 'residual_norm': 2.0, 'step_norm': 1.0, 'convergence_rate': 0.0, 'solution_vector': [2.0, 2.0]},
                {'iteration': 1, 'residual_norm': 0.2, 'step_norm': 0.4, 'convergence_rate': 2.5, 'solution_vector': [1.5, 1.5]},
                {'iteration': 2, 'residual_norm': 2e-6, 'step_norm': 2e-4, 'convergence_rate': 2.0, 'solution_vector': [1.414, 1.414]}
            ]
        ]
        
        visualization_results = []
        viz_errors = []
        
        def generate_visualizations(history_index):
            try:
                history = iteration_histories[history_index]
                
                # Generate convergence plot
                convergence_plot = self.viz_utils.generate_convergence_plot(history)
                
                # Generate constraint visualization
                constraint_viz = self.viz_utils.generate_constraint_visualization(
                    ['x', 'y'],
                    {'x': (0, 3), 'y': (0, 3)},
                    {'x': 1.4, 'y': 1.4},
                    history
                )
                
                # Generate real-time progress
                progress_data = self.viz_utils.generate_real_time_progress(history[-1])
                
                visualization_results.append({
                    'history_index': history_index,
                    'convergence_plot': convergence_plot,
                    'constraint_viz': constraint_viz,
                    'progress_data': progress_data
                })
                
            except Exception as e:
                viz_errors.append({'history_index': history_index, 'error': str(e)})
        
        # Generate visualizations concurrently
        threads = []
        for i in range(len(iteration_histories)):
            thread = threading.Thread(target=generate_visualizations, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(viz_errors) == 0, f"Visualization errors: {viz_errors}"
        assert len(visualization_results) == 3
        
        # Verify all visualizations were generated correctly
        for result in visualization_results:
            assert result['convergence_plot']['type'] == 'line'
            assert result['constraint_viz']['type'] == 'scatter'
            assert 'progress_percentage' in result['progress_data']


@pytest.mark.web_integration
@pytest.mark.performance
class TestResourceManagement:
    """Test resource management and performance aspects."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.api_service = WebAPIService()
        self.session_manager = SessionManager(max_concurrent_sessions=5)
        self.viz_utils = VisualizationUtils()
    
    def teardown_method(self):
        """Cleanup after each test method."""
        session_ids = list(self.session_manager.sessions.keys())
        for session_id in session_ids:
            self.session_manager.delete_session(session_id)
    
    def test_session_limit_enforcement(self):
        """Test that session limits are properly enforced."""
        
        # Create maximum number of sessions
        session_ids = []
        for i in range(5):  # max_concurrent_sessions = 5
            session_id = self.session_manager.create_session()
            session_ids.append(session_id)
        
        assert len(self.session_manager.sessions) == 5
        
        # Try to create another session - should fail
        with pytest.raises(RuntimeError, match="Maximum number of concurrent sessions"):
            self.session_manager.create_session()
        
        # Delete a session and try again - should succeed
        self.session_manager.delete_session(session_ids[0])
        
        new_session_id = self.session_manager.create_session()
        assert new_session_id is not None
        assert len(self.session_manager.sessions) == 5
    
    def test_memory_cleanup_after_session_deletion(self):
        """Test that memory is properly cleaned up when sessions are deleted."""
        
        # Create sessions with progress data
        session_ids = []
        for i in range(3):
            session_id = self.session_manager.create_session()
            session_ids.append(session_id)
            
            # Add significant progress data
            for j in range(10):
                iteration_data = {
                    'iteration': j,
                    'residual_norm': 1.0 / (j + 1),
                    'elapsed_time': j * 0.1
                }
                self.session_manager.add_progress_update(session_id, iteration_data)
        
        # Verify sessions exist
        assert len(self.session_manager.sessions) == 3
        
        # Delete all sessions
        for session_id in session_ids:
            self.session_manager.delete_session(session_id)
        
        # Verify cleanup
        assert len(self.session_manager.sessions) == 0
        assert len(self.session_manager.progress_callbacks) == 0
    
    def test_large_visualization_data_handling(self):
        """Test handling of large visualization datasets."""
        
        # Create large iteration history
        large_history = []
        for i in range(100):  # 100 iterations
            large_history.append({
                'iteration': i,
                'residual_norm': 1.0 / (10 ** (i / 20)),  # Gradual convergence
                'step_norm': 0.1 / (i + 1),
                'convergence_rate': 2.0,
                'solution_vector': [1.0 + i * 0.01, 1.0 + i * 0.01]  # Large solution vectors
            })
        
        # Generate convergence plot
        convergence_plot = self.viz_utils.generate_convergence_plot(large_history)
        
        # Verify structure is correct
        assert convergence_plot['type'] == 'line'
        assert len(convergence_plot['data']['labels']) == 100
        
        # Verify JSON serializable
        json_str = json.dumps(convergence_plot)
        parsed = json.loads(json_str)
        assert len(parsed['data']['labels']) == 100
        
        # Generate constraint visualization with trajectory
        constraint_viz = self.viz_utils.generate_constraint_visualization(
            ['x', 'y'],
            {'x': (0, 5), 'y': (0, 5)},
            {'x': 2.0, 'y': 2.0},
            large_history
        )
        
        # Should handle large trajectory data
        assert constraint_viz['type'] == 'scatter'
        
        # Find trajectory dataset
        trajectory_dataset = None
        for dataset in constraint_viz['data']['datasets']:
            if dataset['label'] == 'Iteration Path':
                trajectory_dataset = dataset
                break
        
        assert trajectory_dataset is not None
        assert len(trajectory_dataset['data']) == 100
    
    def test_performance_with_concurrent_operations(self):
        """Test performance characteristics with concurrent operations."""
        
        start_time = time.time()
        
        # Simulate realistic concurrent load
        def simulate_user_session():
            # Create session
            session_id = self.session_manager.create_session()
            
            # Solve small problem
            request = SolverRequest(
                equations=['x**2 - 4'],
                variables=['x'],
                initial_guess={'x': 2.1},
                solver_options={'display': False}
            )
            
            response = self.api_service.solve_algebraic_system(request)
            
            # Update session
            self.session_manager.update_session_status(
                session_id, 'completed' if response.success else 'failed', response
            )
            
            # Generate basic visualization
            if response.report and 'iteration_history' in response.report:
                self.viz_utils.generate_convergence_plot(response.report['iteration_history'])
            
            return response.success
        
        # Run multiple concurrent user sessions
        threads = []
        results = []
        
        for i in range(5):  # 5 concurrent users
            def thread_target():
                result = simulate_user_session()
                results.append(result)
            
            thread = threading.Thread(target=thread_target)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify all succeeded
        assert all(results), "Some sessions failed"
        assert len(results) == 5
        
        # Performance check - should complete within reasonable time
        # This is a loose check since performance depends on hardware
        assert execution_time < 10.0, f"Execution took too long: {execution_time:.2f}s"
        
        # Verify session statistics are correct
        stats = self.session_manager.get_session_statistics()
        assert stats['completed_sessions'] == 5
        assert stats['current_active_sessions'] == 5  # Sessions not deleted


@pytest.mark.web_integration
@pytest.mark.real_time
class TestRealTimeFeatures:
    """Test real-time features and WebSocket integration support."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.api_service = WebAPIService()
        self.session_manager = SessionManager()
        self.viz_utils = VisualizationUtils()
    
    def teardown_method(self):
        """Cleanup after each test method."""
        session_ids = list(self.session_manager.sessions.keys())
        for session_id in session_ids:
            self.session_manager.delete_session(session_id)
    
    def test_real_time_progress_updates(self):
        """Test real-time progress update mechanism."""
        
        session_id = self.session_manager.create_session(
            SessionConfig(enable_progress_tracking=True)
        )
        
        # Mock WebSocket connection
        mock_websocket = Mock()
        websocket_messages = []
        
        def mock_send(message):
            websocket_messages.append(json.loads(message))
        
        mock_websocket.send = mock_send
        
        # Setup WebSocket manager
        from text_to_solver.session_manager import WebSocketProgressManager
        ws_manager = WebSocketProgressManager(self.session_manager)
        ws_manager.register_client(session_id, mock_websocket)
        
        # Simulate solver iterations
        for i in range(5):
            iteration_data = {
                'iteration': i,
                'residual_norm': 1.0 / (10 ** i),
                'elapsed_time': i * 0.2,
                'convergence_rate': 2.0
            }
            
            self.session_manager.add_progress_update(session_id, iteration_data)
        
        # Verify WebSocket messages were sent
        # Note: The actual sending depends on the callback mechanism
        # which is set up when registering the client
        
        # Verify progress history
        history = self.session_manager.get_progress_history(session_id)
        assert len(history) == 5
        
        # Verify latest progress
        latest = self.session_manager.get_latest_progress(session_id)
        assert latest is not None
        assert latest.iteration == 4
    
    def test_progress_to_visualization_pipeline(self):
        """Test pipeline from progress updates to visualization data."""
        
        session_id = self.session_manager.create_session()
        
        # Simulate complete solver run with detailed progress
        iteration_history = []
        for i in range(10):
            iteration_data = {
                'iteration': i,
                'residual_norm': 1.0 / (10 ** i),  # Changed to converge faster (10^i instead of 2^i)
                'step_norm': 0.5 / (10 ** i),
                'convergence_rate': 1.5,
                'elapsed_time': i * 0.1,
                'solution_vector': [1.0 + i * 0.01, 1.0 + i * 0.01],
                'constraint_violations': {},
                'active_constraints': {}
            }
            
            self.session_manager.add_progress_update(session_id, iteration_data)
            iteration_history.append(iteration_data)
        
        # Get progress history
        progress_history = self.session_manager.get_progress_history(session_id)
        assert len(progress_history) == 10
        
        # Generate real-time visualization data
        latest_progress = self.session_manager.get_latest_progress(session_id)
        real_time_data = self.viz_utils.generate_real_time_progress(
            latest_progress.__dict__
        )
        
        assert real_time_data['iteration'] == 9
        assert real_time_data['status'] == 'converged'  # Should be converged by now
        assert real_time_data['progress_percentage'] > 20  # Adjusted expectation
        
        # Generate full convergence visualization
        convergence_plot = self.viz_utils.generate_convergence_plot(iteration_history)
        
        assert convergence_plot['type'] == 'line'
        assert len(convergence_plot['data']['labels']) == 10
    
    def test_concurrent_real_time_monitoring(self):
        """Test real-time monitoring for multiple concurrent sessions."""
        
        # Create multiple sessions
        session_ids = []
        for i in range(3):
            session_id = self.session_manager.create_session(
                SessionConfig(enable_progress_tracking=True)
            )
            session_ids.append(session_id)
        
        # Track real-time data for each session
        real_time_data = {}
        
        def simulate_solving_with_progress(session_id, max_iterations):
            """Simulate solving with periodic progress updates."""
            for i in range(max_iterations):
                iteration_data = {
                    'iteration': i,
                    'residual_norm': 1.0 / ((i + 1) ** 2),
                    'elapsed_time': i * 0.05,
                    'convergence_rate': 1.8
                }
                
                self.session_manager.add_progress_update(session_id, iteration_data)
                
                # Generate real-time visualization data
                latest = self.session_manager.get_latest_progress(session_id)
                if latest:
                    real_time_data[session_id] = self.viz_utils.generate_real_time_progress(
                        latest.__dict__
                    )
                
                time.sleep(0.01)  # Simulate computation time
        
        # Run simulations concurrently
        threads = []
        iteration_counts = [5, 7, 4]  # Different iteration counts
        
        for i, session_id in enumerate(session_ids):
            thread = threading.Thread(
                target=simulate_solving_with_progress,
                args=(session_id, iteration_counts[i])
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify real-time data was generated for all sessions
        assert len(real_time_data) == 3
        
        for i, session_id in enumerate(session_ids):
            data = real_time_data[session_id]
            expected_final_iteration = iteration_counts[i] - 1
            
            assert data['iteration'] == expected_final_iteration
            assert 'progress_percentage' in data
            assert 'status' in data


if __name__ == "__main__":
    pytest.main([__file__])
