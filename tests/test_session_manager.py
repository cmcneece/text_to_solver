#!/usr/bin/env python3
"""
Test Suite for Session Management

Tests all functionality in the SessionManager including:
- Session creation and lifecycle management
- Progress tracking and real-time updates
- Concurrent session handling
- Resource cleanup and memory management
- Session statistics and monitoring
- WebSocket integration support

Author: TextToSolver Test Team
"""

import pytest
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from text_to_solver.session_manager import (
    SessionManager,
    SessionConfig,
    SessionState,
    ProgressUpdate,
    WebSocketProgressManager
)
from text_to_solver.web_api import SolverResponse


@pytest.mark.session_management
class TestSessionConfig:
    """Test SessionConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SessionConfig()
        
        assert config.max_iterations == 50
        assert config.tolerance == 1e-6
        assert config.timeout_seconds == 300
        assert config.enable_progress_tracking is True
        assert config.auto_cleanup is True
        assert config.constraint_handling == 'project'
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = SessionConfig(
            max_iterations=100,
            tolerance=1e-8,
            timeout_seconds=600,
            enable_progress_tracking=False,
            constraint_handling='error'
        )
        
        assert config.max_iterations == 100
        assert config.tolerance == 1e-8
        assert config.timeout_seconds == 600
        assert config.enable_progress_tracking is False
        assert config.constraint_handling == 'error'


@pytest.mark.session_management
class TestSessionState:
    """Test SessionState dataclass."""
    
    def test_session_state_creation(self):
        """Test SessionState creation with post_init."""
        now = datetime.now()
        state = SessionState(
            session_id="test-session",
            status="created",
            created_at=now,
            updated_at=now
        )
        
        assert state.session_id == "test-session"
        assert state.status == "created"
        assert state.progress_history == []  # Should be initialized
        assert state.config is None
        assert state.error_message is None


@pytest.mark.session_management
class TestSessionManager:
    """Test core SessionManager functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.manager = SessionManager(max_concurrent_sessions=5, cleanup_interval=1)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        # Clean up any remaining sessions
        session_ids = list(self.manager.sessions.keys())
        for session_id in session_ids:
            self.manager.delete_session(session_id)
    
    def test_manager_creation(self):
        """Test SessionManager creation."""
        manager = SessionManager(max_concurrent_sessions=10)
        
        assert manager.max_concurrent_sessions == 10
        assert manager.cleanup_interval == 300  # Default
        assert isinstance(manager.sessions, dict)
        assert len(manager.sessions) == 0
        assert manager.stats['total_sessions'] == 0
    
    def test_create_session(self):
        """Test session creation."""
        session_id = self.manager.create_session()
        
        assert session_id is not None
        assert session_id in self.manager.sessions
        
        session = self.manager.sessions[session_id]
        assert session.session_id == session_id
        assert session.status == 'created'
        assert session.config is not None
        assert self.manager.stats['total_sessions'] == 1
        assert self.manager.stats['active_sessions'] == 1
    
    def test_create_session_with_config(self):
        """Test session creation with custom config."""
        config = SessionConfig(max_iterations=100, timeout_seconds=600)
        session_id = self.manager.create_session(config)
        
        session = self.manager.sessions[session_id]
        assert session.config.max_iterations == 100
        assert session.config.timeout_seconds == 600
    
    def test_session_limit_enforcement(self):
        """Test that session limits are enforced."""
        # Create maximum sessions
        session_ids = []
        for i in range(5):  # max_concurrent_sessions = 5
            session_id = self.manager.create_session()
            session_ids.append(session_id)
        
        # Should have 5 sessions
        assert len(self.manager.sessions) == 5
        
        # Try to create another - should raise error
        with pytest.raises(RuntimeError, match="Maximum number of concurrent sessions"):
            self.manager.create_session()
    
    def test_get_session(self):
        """Test retrieving sessions."""
        session_id = self.manager.create_session()
        
        # Existing session
        session = self.manager.get_session(session_id)
        assert session is not None
        assert session.session_id == session_id
        
        # Non-existent session
        non_existent = self.manager.get_session("invalid-session-id")
        assert non_existent is None
    
    def test_update_session_status(self):
        """Test updating session status."""
        session_id = self.manager.create_session()
        
        # Update to running
        self.manager.update_session_status(session_id, 'running')
        
        session = self.manager.get_session(session_id)
        assert session.status == 'running'
        
        # Update to completed with response
        response = SolverResponse(
            success=True,
            session_id=session_id,
            solution={'x': 1.414}
        )
        
        self.manager.update_session_status(session_id, 'completed', response)
        
        session = self.manager.get_session(session_id)
        assert session.status == 'completed'
        assert session.response is not None
        assert session.response['success'] is True
        
        # Check statistics update
        assert self.manager.stats['completed_sessions'] == 1
        assert self.manager.stats['active_sessions'] == 0
    
    def test_update_session_with_error(self):
        """Test updating session with error message."""
        session_id = self.manager.create_session()
        
        self.manager.update_session_status(
            session_id, 
            'failed', 
            error_message="Test error message"
        )
        
        session = self.manager.get_session(session_id)
        assert session.status == 'failed'
        assert session.error_message == "Test error message"
        assert self.manager.stats['failed_sessions'] == 1
    
    def test_delete_session(self):
        """Test session deletion."""
        session_id = self.manager.create_session()
        
        # Session exists
        assert session_id in self.manager.sessions
        assert self.manager.stats['active_sessions'] == 1
        
        # Delete session
        result = self.manager.delete_session(session_id)
        
        assert result is True
        assert session_id not in self.manager.sessions
        assert self.manager.stats['active_sessions'] == 0
        
        # Try to delete non-existent session
        result = self.manager.delete_session("invalid-session")
        assert result is False


@pytest.mark.session_management
@pytest.mark.real_time
class TestProgressTracking:
    """Test progress tracking functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.manager = SessionManager(max_concurrent_sessions=5)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        session_ids = list(self.manager.sessions.keys())
        for session_id in session_ids:
            self.manager.delete_session(session_id)
    
    def test_add_progress_update(self):
        """Test adding progress updates."""
        session_id = self.manager.create_session()
        
        iteration_data = {
            'iteration': 1,
            'residual_norm': 0.1,
            'elapsed_time': 0.5
        }
        
        self.manager.add_progress_update(session_id, iteration_data)
        
        progress_history = self.manager.get_progress_history(session_id)
        assert len(progress_history) == 1
        
        progress = progress_history[0]
        assert progress.session_id == session_id
        assert progress.iteration == 1
        assert progress.residual_norm == 0.1
        assert progress.elapsed_time == 0.5
        assert progress.status == 'running'
    
    def test_multiple_progress_updates(self):
        """Test multiple progress updates in sequence."""
        session_id = self.manager.create_session()
        
        # Add multiple updates
        for i in range(5):
            iteration_data = {
                'iteration': i,
                'residual_norm': 1.0 / (10 ** i),
                'elapsed_time': i * 0.1
            }
            self.manager.add_progress_update(session_id, iteration_data)
        
        progress_history = self.manager.get_progress_history(session_id)
        assert len(progress_history) == 5
        
        # Check ordering and values
        for i, progress in enumerate(progress_history):
            assert progress.iteration == i
            assert progress.residual_norm == 1.0 / (10 ** i)
    
    def test_get_latest_progress(self):
        """Test getting latest progress update."""
        session_id = self.manager.create_session()
        
        # No progress initially
        latest = self.manager.get_latest_progress(session_id)
        assert latest is None
        
        # Add some progress
        for i in range(3):
            iteration_data = {
                'iteration': i,
                'residual_norm': 0.1,
                'elapsed_time': i * 0.1
            }
            self.manager.add_progress_update(session_id, iteration_data)
        
        # Get latest
        latest = self.manager.get_latest_progress(session_id)
        assert latest is not None
        assert latest.iteration == 2  # Last iteration
    
    def test_progress_callbacks(self):
        """Test progress callback registration and notification."""
        session_id = self.manager.create_session()
        
        # Setup callback
        callback_called = []
        
        def test_callback(progress):
            callback_called.append(progress)
        
        self.manager.register_progress_callback(session_id, test_callback)
        
        # Add progress update
        iteration_data = {
            'iteration': 1,
            'residual_norm': 0.1,
            'elapsed_time': 0.5
        }
        
        self.manager.add_progress_update(session_id, iteration_data)
        
        # Callback should have been called
        assert len(callback_called) == 1
        assert callback_called[0].iteration == 1
    
    def test_unregister_progress_callbacks(self):
        """Test unregistering progress callbacks."""
        session_id = self.manager.create_session()
        
        callback_called = []
        
        def test_callback(progress):
            callback_called.append(progress)
        
        self.manager.register_progress_callback(session_id, test_callback)
        
        # Add progress - should trigger callback
        iteration_data = {'iteration': 1, 'residual_norm': 0.1, 'elapsed_time': 0.5}
        self.manager.add_progress_update(session_id, iteration_data)
        
        assert len(callback_called) == 1
        
        # Unregister callbacks
        self.manager.unregister_progress_callbacks(session_id)
        
        # Add more progress - should not trigger callback
        iteration_data = {'iteration': 2, 'residual_norm': 0.01, 'elapsed_time': 1.0}
        self.manager.add_progress_update(session_id, iteration_data)
        
        assert len(callback_called) == 1  # Still only 1
    
    def test_progress_with_nonexistent_session(self):
        """Test progress updates with non-existent session."""
        iteration_data = {'iteration': 1, 'residual_norm': 0.1, 'elapsed_time': 0.5}
        
        # Should not raise error
        self.manager.add_progress_update("nonexistent-session", iteration_data)
        
        # Should return empty list
        history = self.manager.get_progress_history("nonexistent-session")
        assert history == []
        
        # Should return None
        latest = self.manager.get_latest_progress("nonexistent-session")
        assert latest is None


@pytest.mark.session_management
@pytest.mark.concurrent
class TestConcurrentSessions:
    """Test concurrent session handling."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.manager = SessionManager(max_concurrent_sessions=10)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        session_ids = list(self.manager.sessions.keys())
        for session_id in session_ids:
            self.manager.delete_session(session_id)
    
    def test_concurrent_session_creation(self):
        """Test creating sessions concurrently."""
        session_ids = []
        errors = []
        
        def create_session():
            try:
                session_id = self.manager.create_session()
                session_ids.append(session_id)
            except Exception as e:
                errors.append(e)
        
        # Create multiple sessions concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_session)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should have created all sessions without errors
        assert len(errors) == 0
        assert len(session_ids) == 5
        assert len(set(session_ids)) == 5  # All unique
        assert len(self.manager.sessions) == 5
    
    def test_concurrent_progress_updates(self):
        """Test concurrent progress updates to different sessions."""
        # Create sessions
        session_ids = []
        for i in range(3):
            session_id = self.manager.create_session()
            session_ids.append(session_id)
        
        def add_progress_to_session(session_id, iteration_count):
            for i in range(iteration_count):
                iteration_data = {
                    'iteration': i,
                    'residual_norm': 1.0 / (i + 1),
                    'elapsed_time': i * 0.1
                }
                self.manager.add_progress_update(session_id, iteration_data)
        
        # Add progress concurrently
        threads = []
        for i, session_id in enumerate(session_ids):
            thread = threading.Thread(
                target=add_progress_to_session,
                args=(session_id, (i + 1) * 3)  # Different number of iterations
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        for i, session_id in enumerate(session_ids):
            history = self.manager.get_progress_history(session_id)
            expected_length = (i + 1) * 3
            assert len(history) == expected_length
    
    def test_concurrent_session_operations(self):
        """Test various concurrent operations on sessions."""
        session_ids = []
        
        # Create sessions
        for i in range(3):
            session_id = self.manager.create_session()
            session_ids.append(session_id)
        
        results = {'status_updates': 0, 'progress_updates': 0, 'deletions': 0}
        
        def update_status(session_id):
            self.manager.update_session_status(session_id, 'running')
            results['status_updates'] += 1
        
        def add_progress(session_id):
            iteration_data = {'iteration': 1, 'residual_norm': 0.1, 'elapsed_time': 0.5}
            self.manager.add_progress_update(session_id, iteration_data)
            results['progress_updates'] += 1
        
        def delete_session(session_id):
            if self.manager.delete_session(session_id):
                results['deletions'] += 1
        
        # Perform operations concurrently
        threads = []
        
        # Status updates
        for session_id in session_ids:
            thread = threading.Thread(target=update_status, args=(session_id,))
            threads.append(thread)
        
        # Progress updates
        for session_id in session_ids[:2]:  # Only first 2
            thread = threading.Thread(target=add_progress, args=(session_id,))
            threads.append(thread)
        
        # Delete one session
        thread = threading.Thread(target=delete_session, args=(session_ids[-1],))
        threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert results['status_updates'] == 3
        assert results['progress_updates'] == 2
        assert results['deletions'] == 1
        assert len(self.manager.sessions) == 2  # 3 created - 1 deleted


@pytest.mark.session_management
class TestSessionStatistics:
    """Test session statistics and monitoring."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.manager = SessionManager(max_concurrent_sessions=10)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        session_ids = list(self.manager.sessions.keys())
        for session_id in session_ids:
            self.manager.delete_session(session_id)
    
    def test_initial_statistics(self):
        """Test initial statistics state."""
        stats = self.manager.get_session_statistics()
        
        assert stats['total_sessions_created'] == 0
        assert stats['current_active_sessions'] == 0
        assert stats['completed_sessions'] == 0
        assert stats['failed_sessions'] == 0
        assert stats['status_breakdown'] == {}
        assert stats['max_concurrent_limit'] == 10
    
    def test_statistics_after_session_creation(self):
        """Test statistics after creating sessions."""
        # Create sessions
        session_ids = []
        for i in range(3):
            session_id = self.manager.create_session()
            session_ids.append(session_id)
        
        stats = self.manager.get_session_statistics()
        
        assert stats['total_sessions_created'] == 3
        assert stats['current_active_sessions'] == 3
        assert stats['status_breakdown']['created'] == 3
    
    def test_statistics_with_status_updates(self):
        """Test statistics with various status updates."""
        # Create sessions
        session_ids = []
        for i in range(4):
            session_id = self.manager.create_session()
            session_ids.append(session_id)
        
        # Update statuses
        self.manager.update_session_status(session_ids[0], 'running')
        self.manager.update_session_status(session_ids[1], 'completed')
        self.manager.update_session_status(session_ids[2], 'failed')
        # session_ids[3] remains 'created'
        
        stats = self.manager.get_session_statistics()
        
        assert stats['total_sessions_created'] == 4
        assert stats['current_active_sessions'] == 4
        assert stats['completed_sessions'] == 1
        assert stats['failed_sessions'] == 1
        assert stats['status_breakdown']['created'] == 1
        assert stats['status_breakdown']['running'] == 1
        assert stats['status_breakdown']['completed'] == 1
        assert stats['status_breakdown']['failed'] == 1
    
    def test_list_sessions(self):
        """Test listing sessions with filters."""
        # Create sessions with different statuses
        session_ids = []
        for i in range(3):
            session_id = self.manager.create_session()
            session_ids.append(session_id)
        
        self.manager.update_session_status(session_ids[0], 'running')
        self.manager.update_session_status(session_ids[1], 'completed')
        # session_ids[2] remains 'created'
        
        # List all sessions
        all_sessions = self.manager.list_sessions()
        assert len(all_sessions) == 3
        
        # List completed sessions
        completed_sessions = self.manager.list_sessions('completed')
        assert len(completed_sessions) == 1
        assert completed_sessions[0]['session_id'] == session_ids[1]
        assert completed_sessions[0]['status'] == 'completed'
        
        # List running sessions
        running_sessions = self.manager.list_sessions('running')
        assert len(running_sessions) == 1
        assert running_sessions[0]['session_id'] == session_ids[0]


@pytest.mark.session_management
class TestDataExport:
    """Test data export functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.manager = SessionManager()
    
    def teardown_method(self):
        """Cleanup after each test method."""
        session_ids = list(self.manager.sessions.keys())
        for session_id in session_ids:
            self.manager.delete_session(session_id)
    
    def test_export_session_data(self):
        """Test exporting complete session data."""
        config = SessionConfig(max_iterations=100, timeout_seconds=600)
        session_id = self.manager.create_session(config)
        
        # Add some progress
        iteration_data = {'iteration': 1, 'residual_norm': 0.1, 'elapsed_time': 0.5}
        self.manager.add_progress_update(session_id, iteration_data)
        
        # Update status
        self.manager.update_session_status(session_id, 'running')
        
        # Export data
        export_data = self.manager.export_session_data(session_id, include_progress=True)
        
        assert export_data is not None
        assert export_data['session_id'] == session_id
        assert export_data['status'] == 'running'
        assert 'created_at' in export_data
        assert 'updated_at' in export_data
        assert export_data['config']['max_iterations'] == 100
        assert len(export_data['progress_history']) == 1
        assert export_data['progress_history'][0]['iteration'] == 1
    
    def test_export_without_progress(self):
        """Test exporting session data without progress history."""
        session_id = self.manager.create_session()
        
        export_data = self.manager.export_session_data(session_id, include_progress=False)
        
        assert export_data is not None
        assert 'progress_history' not in export_data
    
    def test_export_nonexistent_session(self):
        """Test exporting data for non-existent session."""
        export_data = self.manager.export_session_data("nonexistent-session")
        
        assert export_data is None


@pytest.mark.session_management
@pytest.mark.performance
class TestResourceCleanup:
    """Test resource cleanup and memory management."""
    
    def test_session_timeout_cleanup(self):
        """Test automatic cleanup of timed-out sessions."""
        manager = SessionManager(max_concurrent_sessions=10, cleanup_interval=0.1)
        
        # Create session with short timeout
        config = SessionConfig(timeout_seconds=0.1)  # Very short timeout
        session_id = manager.create_session(config)
        
        assert session_id in manager.sessions
        
        # Wait for cleanup
        time.sleep(0.2)
        
        # Trigger cleanup manually (since cleanup interval might not have fired)
        with manager._lock:
            manager._cleanup_expired_sessions()
        
        # Session should be cleaned up
        assert session_id not in manager.sessions
    
    def test_manual_cleanup_call(self):
        """Test manual cleanup of expired sessions."""
        manager = SessionManager()
        
        # Create session
        session_id = manager.create_session()
        
        # Manually expire the session by modifying its timestamp
        session = manager.sessions[session_id]
        session.updated_at = datetime.now() - timedelta(seconds=400)  # Older than default timeout
        
        # Call cleanup
        with manager._lock:
            manager._cleanup_expired_sessions()
        
        # Session should be removed
        assert session_id not in manager.sessions


@pytest.mark.session_management
@pytest.mark.real_time
class TestWebSocketProgressManager:
    """Test WebSocket progress manager functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.session_manager = SessionManager()
        self.ws_manager = WebSocketProgressManager(self.session_manager)
    
    def test_websocket_manager_creation(self):
        """Test WebSocket manager creation."""
        assert self.ws_manager.session_manager is self.session_manager
        assert isinstance(self.ws_manager.connected_clients, dict)
    
    def test_client_registration(self):
        """Test WebSocket client registration."""
        session_id = self.session_manager.create_session()
        mock_websocket = Mock()
        
        self.ws_manager.register_client(session_id, mock_websocket)
        
        assert session_id in self.ws_manager.connected_clients
        assert mock_websocket in self.ws_manager.connected_clients[session_id]
    
    def test_client_unregistration(self):
        """Test WebSocket client unregistration."""
        session_id = self.session_manager.create_session()
        mock_websocket = Mock()
        
        # Register then unregister
        self.ws_manager.register_client(session_id, mock_websocket)
        self.ws_manager.unregister_client(session_id, mock_websocket)
        
        assert session_id not in self.ws_manager.connected_clients
    
    def test_progress_broadcast(self):
        """Test progress update broadcasting."""
        session_id = self.session_manager.create_session()
        mock_websocket = Mock()
        
        self.ws_manager.register_client(session_id, mock_websocket)
        
        # Create progress update
        progress = ProgressUpdate(
            session_id=session_id,
            iteration=1,
            residual_norm=0.1,
            elapsed_time=0.5,
            status='running',
            timestamp=datetime.now().isoformat()
        )
        
        # Broadcast should be called when progress is added
        # (This is tested indirectly through the callback mechanism)
        self.session_manager.add_progress_update(session_id, {
            'iteration': 1,
            'residual_norm': 0.1,
            'elapsed_time': 0.5
        })
        
        # Verify callback was registered
        assert session_id in self.session_manager.progress_callbacks


if __name__ == "__main__":
    pytest.main([__file__])
