#!/usr/bin/env python3
"""
Session Management for TextToSolver Web Applications

This module provides session management capabilities for web applications,
including state persistence, progress tracking, and configuration management.
It enables stateful interactions while maintaining clean separation between
the solver core and web interface.

Key Features:
- Session state management
- Progress tracking and real-time updates
- Configuration persistence
- Result caching and export
- Concurrent session handling
- Session cleanup and resource management

Author: TextToSolver Development Team
"""

import uuid
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import weakref
from collections import defaultdict

from .web_api import SolverRequest, SolverResponse, DynamicSolverRequest, ProgressUpdate


@dataclass
class SessionConfig:
    """Configuration for solver sessions."""
    max_iterations: int = 50
    tolerance: float = 1e-6
    timeout_seconds: int = 300
    enable_progress_tracking: bool = True
    auto_cleanup: bool = True
    constraint_handling: str = 'project'


@dataclass
class SessionState:
    """State information for an active solver session."""
    session_id: str
    status: str  # 'created', 'running', 'completed', 'failed', 'timeout'
    created_at: datetime
    updated_at: datetime
    request: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    progress_history: List[ProgressUpdate] = None
    config: Optional[SessionConfig] = None
    solver_instance: Optional[Any] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.progress_history is None:
            self.progress_history = []


class SessionManager:
    """
    Manages solver sessions for web applications.
    
    Provides:
    - Session creation and lifecycle management
    - Progress tracking and real-time updates
    - Result caching and persistence
    - Resource cleanup and memory management
    """
    
    def __init__(self, max_concurrent_sessions: int = 100, cleanup_interval: int = 300):
        """
        Initialize session manager.
        
        Args:
            max_concurrent_sessions: Maximum number of concurrent sessions
            cleanup_interval: Cleanup interval in seconds
        """
        self.sessions: Dict[str, SessionState] = {}
        self.max_concurrent_sessions = max_concurrent_sessions
        self.cleanup_interval = cleanup_interval
        self.progress_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.RLock()
        
        # Start background cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        
        # Session statistics
        self.stats = {
            'total_sessions': 0,
            'active_sessions': 0,
            'completed_sessions': 0,
            'failed_sessions': 0
        }
    
    def create_session(self, config: Optional[SessionConfig] = None) -> str:
        """
        Create a new solver session.
        
        Args:
            config: Optional session configuration
            
        Returns:
            Session ID
        """
        with self._lock:
            # Check session limit
            if len(self.sessions) >= self.max_concurrent_sessions:
                self._cleanup_expired_sessions()
                if len(self.sessions) >= self.max_concurrent_sessions:
                    raise RuntimeError("Maximum number of concurrent sessions reached")
            
            session_id = str(uuid.uuid4())
            now = datetime.now()
            
            session = SessionState(
                session_id=session_id,
                status='created',
                created_at=now,
                updated_at=now,
                config=config or SessionConfig()
            )
            
            self.sessions[session_id] = session
            self.stats['total_sessions'] += 1
            self.stats['active_sessions'] += 1
            
            return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """
        Get session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionState or None if not found
        """
        with self._lock:
            return self.sessions.get(session_id)
    
    def update_session_status(self, session_id: str, status: str, 
                            response: Optional[SolverResponse] = None,
                            error_message: Optional[str] = None):
        """
        Update session status and response.
        
        Args:
            session_id: Session identifier
            status: New status
            response: Optional solver response
            error_message: Optional error message
        """
        with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                old_status = session.status
                
                session.status = status
                session.updated_at = datetime.now()
                
                if response:
                    session.response = asdict(response)
                
                if error_message:
                    session.error_message = error_message
                
                # Update statistics
                if old_status != status:
                    if status == 'completed':
                        self.stats['completed_sessions'] += 1
                        if old_status in ['created', 'running']:
                            self.stats['active_sessions'] -= 1
                    elif status == 'failed':
                        self.stats['failed_sessions'] += 1
                        if old_status in ['created', 'running']:
                            self.stats['active_sessions'] -= 1
    
    def add_progress_update(self, session_id: str, iteration_data: Dict[str, Any]):
        """
        Add progress update for a session.
        
        Args:
            session_id: Session identifier
            iteration_data: Iteration progress data
        """
        with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                
                progress_update = ProgressUpdate(
                    session_id=session_id,
                    iteration=iteration_data.get('iteration', 0),
                    residual_norm=float(iteration_data.get('residual_norm', 0)),
                    elapsed_time=float(iteration_data.get('elapsed_time', 0)),
                    status='running',
                    timestamp=datetime.now().isoformat()
                )
                
                session.progress_history.append(progress_update)
                session.updated_at = datetime.now()
                
                # Notify progress callbacks
                for callback in self.progress_callbacks.get(session_id, []):
                    try:
                        callback(progress_update)
                    except Exception as e:
                        print(f"Error in progress callback: {e}")
    
    def get_progress_history(self, session_id: str) -> List[ProgressUpdate]:
        """
        Get progress history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of progress updates
        """
        with self._lock:
            if session_id in self.sessions:
                return self.sessions[session_id].progress_history.copy()
            return []
    
    def get_latest_progress(self, session_id: str) -> Optional[ProgressUpdate]:
        """
        Get latest progress update for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Latest progress update or None
        """
        with self._lock:
            if session_id in self.sessions:
                history = self.sessions[session_id].progress_history
                return history[-1] if history else None
            return None
    
    def register_progress_callback(self, session_id: str, callback: Callable[[ProgressUpdate], None]):
        """
        Register a callback for progress updates.
        
        Args:
            session_id: Session identifier
            callback: Callback function
        """
        with self._lock:
            self.progress_callbacks[session_id].append(callback)
    
    def unregister_progress_callbacks(self, session_id: str):
        """
        Remove all progress callbacks for a session.
        
        Args:
            session_id: Session identifier
        """
        with self._lock:
            if session_id in self.progress_callbacks:
                del self.progress_callbacks[session_id]
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and clean up resources.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was deleted, False if not found
        """
        with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                
                # Update statistics
                if session.status in ['created', 'running']:
                    self.stats['active_sessions'] -= 1
                
                # Clean up callbacks
                self.unregister_progress_callbacks(session_id)
                
                # Remove session
                del self.sessions[session_id]
                return True
            return False
    
    def list_sessions(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all sessions with optional status filter.
        
        Args:
            status_filter: Optional status to filter by
            
        Returns:
            List of session summaries
        """
        with self._lock:
            sessions = []
            for session in self.sessions.values():
                if status_filter is None or session.status == status_filter:
                    sessions.append({
                        'session_id': session.session_id,
                        'status': session.status,
                        'created_at': session.created_at.isoformat(),
                        'updated_at': session.updated_at.isoformat(),
                        'progress_count': len(session.progress_history),
                        'has_result': session.response is not None
                    })
            return sessions
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get session management statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            current_sessions = len(self.sessions)
            status_counts = defaultdict(int)
            
            for session in self.sessions.values():
                status_counts[session.status] += 1
            
            return {
                'total_sessions_created': self.stats['total_sessions'],
                'current_active_sessions': current_sessions,
                'completed_sessions': self.stats['completed_sessions'],
                'failed_sessions': self.stats['failed_sessions'],
                'status_breakdown': dict(status_counts),
                'max_concurrent_limit': self.max_concurrent_sessions
            }
    
    def export_session_data(self, session_id: str, include_progress: bool = True) -> Optional[Dict[str, Any]]:
        """
        Export complete session data.
        
        Args:
            session_id: Session identifier
            include_progress: Whether to include progress history
            
        Returns:
            Complete session data or None if not found
        """
        with self._lock:
            if session_id not in self.sessions:
                return None
            
            session = self.sessions[session_id]
            
            export_data = {
                'session_id': session.session_id,
                'status': session.status,
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat(),
                'request': session.request,
                'response': session.response,
                'config': asdict(session.config) if session.config else None,
                'error_message': session.error_message
            }
            
            if include_progress:
                export_data['progress_history'] = [asdict(p) for p in session.progress_history]
            
            return export_data
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions (called with lock held)."""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            # Calculate timeout based on session config
            timeout = timedelta(seconds=session.config.timeout_seconds if session.config else 300)
            
            if now - session.updated_at > timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.delete_session(session_id)
    
    def _cleanup_loop(self):
        """Background cleanup loop."""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                with self._lock:
                    self._cleanup_expired_sessions()
            except Exception as e:
                print(f"Error in cleanup loop: {e}")


class WebSocketProgressManager:
    """
    Manages WebSocket connections for real-time progress updates.
    
    This class would integrate with web frameworks like Flask-SocketIO
    or FastAPI WebSockets to provide real-time progress updates.
    """
    
    def __init__(self, session_manager: SessionManager):
        """
        Initialize WebSocket progress manager.
        
        Args:
            session_manager: SessionManager instance
        """
        self.session_manager = session_manager
        self.connected_clients: Dict[str, List[Any]] = defaultdict(list)  # session_id -> [websockets]
    
    def register_client(self, session_id: str, websocket_connection):
        """
        Register a WebSocket client for progress updates.
        
        Args:
            session_id: Session identifier
            websocket_connection: WebSocket connection object
        """
        self.connected_clients[session_id].append(websocket_connection)
        
        # Register callback with session manager
        self.session_manager.register_progress_callback(
            session_id, 
            lambda progress: self._broadcast_progress(session_id, progress)
        )
    
    def unregister_client(self, session_id: str, websocket_connection):
        """
        Unregister a WebSocket client.
        
        Args:
            session_id: Session identifier
            websocket_connection: WebSocket connection object
        """
        if session_id in self.connected_clients:
            self.connected_clients[session_id] = [
                conn for conn in self.connected_clients[session_id] 
                if conn != websocket_connection
            ]
            
            # Clean up if no more clients
            if not self.connected_clients[session_id]:
                del self.connected_clients[session_id]
                self.session_manager.unregister_progress_callbacks(session_id)
    
    def _broadcast_progress(self, session_id: str, progress: ProgressUpdate):
        """
        Broadcast progress update to all connected clients.
        
        Args:
            session_id: Session identifier
            progress: Progress update
        """
        if session_id in self.connected_clients:
            message = json.dumps(asdict(progress))
            
            # Remove disconnected clients
            active_clients = []
            for client in self.connected_clients[session_id]:
                try:
                    # This would depend on the WebSocket library being used
                    # client.send(message)  # For websockets library
                    # socketio.emit('progress', message, room=session_id)  # For Flask-SocketIO
                    active_clients.append(client)
                except Exception:
                    # Client disconnected
                    pass
            
            self.connected_clients[session_id] = active_clients


# Example usage and testing
if __name__ == "__main__":
    # Example usage of session manager
    manager = SessionManager()
    
    # Create a session
    session_id = manager.create_session(SessionConfig(max_iterations=20))
    print(f"Created session: {session_id}")
    
    # Simulate progress updates
    for i in range(5):
        iteration_data = {
            'iteration': i,
            'residual_norm': 1.0 / (10 ** i),
            'elapsed_time': i * 0.1
        }
        manager.add_progress_update(session_id, iteration_data)
    
    # Update session status
    manager.update_session_status(session_id, 'completed')
    
    # Get session data
    session_data = manager.export_session_data(session_id)
    print(f"Session data: {json.dumps(session_data, indent=2, default=str)}")
    
    # Get statistics
    stats = manager.get_session_statistics()
    print(f"Session statistics: {json.dumps(stats, indent=2)}")
    
    # Clean up
    manager.delete_session(session_id)
