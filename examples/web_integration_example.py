#!/usr/bin/env python3
"""
Complete Web Integration Example for TextToSolver

This example demonstrates how to integrate TextToSolver into a web application
with full session management, real-time progress updates, and visualization
data generation. It shows the complete architecture for front-end/back-end
separation.

Features Demonstrated:
- RESTful API service layer
- Session management with state persistence
- Real-time progress tracking
- Visualization data generation for charting libraries
- Error handling and validation
- Export capabilities (JSON, CSV)
- Concurrent session handling
- Resource cleanup and management

This serves as a blueprint for web application integration.

QUICK START:
    python examples/web_integration_example.py

Author: TextToSolver Development Team
"""

import json
import sys
import os
from typing import Dict, Any
import time
import threading
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from text_to_solver.web_api import WebAPIService, SolverRequest, DynamicSolverRequest
from text_to_solver.session_manager import SessionManager, SessionConfig
from text_to_solver.visualization_utils import VisualizationUtils


class WebApplicationDemo:
    """
    Demonstration of a complete web application integration.
    
    This class shows how to combine all the web API components
    into a cohesive application architecture.
    """
    
    def __init__(self):
        """Initialize the web application components."""
        self.api_service = WebAPIService()
        self.session_manager = SessionManager(max_concurrent_sessions=10)
        self.viz_utils = VisualizationUtils()
        
        print("🚀 Web Application Demo Initialized")
        print("=" * 50)
    
    def demonstrate_algebraic_solving_workflow(self):
        """Demonstrate complete algebraic solving workflow."""
        
        print("\n1️⃣  ALGEBRAIC SOLVING WORKFLOW")
        print("-" * 40)
        
        # Create session
        session_id = self.session_manager.create_session(
            SessionConfig(max_iterations=20, enable_progress_tracking=True)
        )
        print(f"✅ Created session: {session_id}")
        
        # Create solve request
        request = SolverRequest(
            equations=['x**2 + y**2 - 9', '2*x + y - 6'],
            variables=['x', 'y'],
            initial_guess={'x': 2.0, 'y': 2.0},
            constraints={'x': (0, 4), 'y': (0, 4)},
            solver_options={
                'constraint_handling': 'project',
                'display': False,
                'store_history': True
            },
            session_id=session_id
        )
        
        print(f"📝 Request: {request.equations}")
        print(f"🎯 Initial guess: {request.initial_guess}")
        print(f"🔒 Constraints: {request.constraints}")
        
        # Solve system
        response = self.api_service.solve_algebraic_system(request)
        
        # Update session
        self.session_manager.update_session_status(
            session_id, 
            'completed' if response.success else 'failed',
            response
        )
        
        print(f"✅ Solved: {response.success}")
        if response.success:
            print(f"🎯 Solution: {response.solution}")
            print(f"⏱️  Execution time: {response.execution_time:.3f}s")
            
            # Generate visualization data
            if response.report and 'iteration_history' in response.report:
                print(f"📊 Generating visualization data...")
                
                # Convergence plot
                convergence_plot = self.viz_utils.generate_convergence_plot(
                    response.report['iteration_history']
                )
                print(f"   ✓ Convergence plot data generated")
                
                # Constraint visualization
                constraint_viz = self.viz_utils.generate_constraint_visualization(
                    request.variables,
                    request.constraints,
                    response.solution,
                    response.report['iteration_history']
                )
                print(f"   ✓ Constraint visualization data generated")
                
                # Export data
                export_data = self.session_manager.export_session_data(session_id)
                print(f"   ✓ Session data exported")
        else:
            print(f"❌ Error: {response.error}")
        
        return session_id, response
    
    def demonstrate_dynamic_solving_workflow(self):
        """Demonstrate dynamic system solving workflow."""
        
        print("\n2️⃣  DYNAMIC SOLVING WORKFLOW")
        print("-" * 40)
        
        # Create session
        session_id = self.session_manager.create_session(
            SessionConfig(timeout_seconds=600)  # Longer timeout for dynamic systems
        )
        print(f"✅ Created session: {session_id}")
        
        # Create dynamic solve request  
        request = DynamicSolverRequest(
            equations=['dx/dt = -0.1*x + 0.075*x*y', 'dy/dt = -0.05*y + 0.025*x*y'],
            variables=['x', 'y'],
            time_range=(0, 50),
            initial_conditions={'x': 10, 'y': 5},
            method='RK45',
            session_id=session_id
        )
        
        print(f"📝 Equations: {request.equations}")
        print(f"⏱️  Time range: {request.time_range}")
        print(f"🎯 Initial conditions: {request.initial_conditions}")
        
        # Solve system
        response = self.api_service.solve_dynamic_system(request)
        
        # Update session
        self.session_manager.update_session_status(
            session_id,
            'completed' if response.success else 'failed',
            response
        )
        
        print(f"✅ Solved: {response.success}")
        if response.success and response.solution:
            time_points = len(response.solution['time'])
            variables = list(response.solution['solution'].keys())
            
            print(f"📊 Time points: {time_points}")
            print(f"🔢 Variables: {variables}")
            print(f"⏱️  Execution time: {response.execution_time:.3f}s")
            
            # Generate visualization data
            print(f"📊 Generating dynamic visualization data...")
            
            # Time series plot
            time_series_plot = self.viz_utils.generate_dynamic_solution_plot(
                response.solution['time'],
                response.solution['solution'],
                "Predator-Prey Dynamics"
            )
            print(f"   ✓ Time series plot data generated")
            
            # Phase portrait
            phase_plot = self.viz_utils.generate_phase_portrait(
                response.solution['solution'],
                'x', 'y',
                "Predator-Prey Phase Portrait"
            )
            print(f"   ✓ Phase portrait data generated")
        else:
            print(f"❌ Error: {response.error}")
        
        return session_id, response
    
    def demonstrate_concurrent_sessions(self):
        """Demonstrate handling multiple concurrent sessions."""
        
        print("\n3️⃣  CONCURRENT SESSION MANAGEMENT")
        print("-" * 40)
        
        # Create multiple sessions
        session_ids = []
        for i in range(3):
            session_id = self.session_manager.create_session(
                SessionConfig(max_iterations=10)
            )
            session_ids.append(session_id)
        
        print(f"✅ Created {len(session_ids)} concurrent sessions")
        
        # Simulate concurrent solving
        def solve_in_session(session_id, problem_id):
            request = SolverRequest(
                equations=[f'x**2 + y**2 - {4 + problem_id}', 'x - y'],
                variables=['x', 'y'],
                initial_guess={'x': 1.0 + problem_id * 0.5, 'y': 1.0 + problem_id * 0.5},
                session_id=session_id,
                solver_options={'display': False}
            )
            
            response = self.api_service.solve_algebraic_system(request)
            self.session_manager.update_session_status(
                session_id,
                'completed' if response.success else 'failed',
                response
            )
            
            print(f"   Session {session_id[:8]}... solved problem {problem_id}")
            return response
        
        # Run concurrent solves
        threads = []
        for i, session_id in enumerate(session_ids):
            thread = threading.Thread(
                target=solve_in_session,
                args=(session_id, i + 1)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check session statistics
        stats = self.session_manager.get_session_statistics()
        print(f"📊 Session statistics: {stats}")
        
        # List active sessions
        active_sessions = self.session_manager.list_sessions('completed')
        print(f"✅ Completed sessions: {len(active_sessions)}")
        
        return session_ids
    
    def demonstrate_real_time_progress(self):
        """Demonstrate real-time progress monitoring."""
        
        print("\n4️⃣  REAL-TIME PROGRESS MONITORING")
        print("-" * 40)
        
        # Create session with progress tracking
        session_id = self.session_manager.create_session(
            SessionConfig(enable_progress_tracking=True)
        )
        
        progress_updates = []
        
        def progress_callback(progress_update):
            """Callback to capture progress updates."""
            progress_updates.append(progress_update)
            print(f"   📊 Iteration {progress_update.iteration}: "
                  f"residual = {progress_update.residual_norm:.2e}, "
                  f"time = {progress_update.elapsed_time:.3f}s")
        
        # Register progress callback
        self.session_manager.register_progress_callback(session_id, progress_callback)
        
        # Simulate progress updates (normally these come from the solver)
        print("📡 Simulating real-time progress updates:")
        for i in range(5):
            iteration_data = {
                'iteration': i,
                'residual_norm': 1.0 / (10 ** i),
                'elapsed_time': i * 0.1,
                'convergence_rate': 2.0 if i > 0 else 0.0
            }
            
            self.session_manager.add_progress_update(session_id, iteration_data)
            time.sleep(0.1)  # Simulate time between iterations
        
        print(f"✅ Captured {len(progress_updates)} progress updates")
        
        # Generate real-time visualization data
        if progress_updates:
            latest_progress = progress_updates[-1]
            real_time_data = self.viz_utils.generate_real_time_progress(
                latest_progress.__dict__
            )
            print(f"📊 Real-time visualization data: {real_time_data}")
        
        return session_id, progress_updates
    
    def demonstrate_export_capabilities(self, session_id: str):
        """Demonstrate data export capabilities."""
        
        print("\n5️⃣  DATA EXPORT CAPABILITIES")
        print("-" * 40)
        
        # Export as JSON
        json_export = self.api_service.export_results(session_id, 'json')
        if json_export:
            print(f"✅ JSON export: {len(json_export)} characters")
            print(f"   Preview: {json_export[:100]}...")
        
        # Export as CSV
        csv_export = self.api_service.export_results(session_id, 'csv')
        if csv_export:
            print(f"✅ CSV export: {len(csv_export)} characters")
            print(f"   Preview: {csv_export[:100]}...")
        
        # Export complete session data
        session_data = self.session_manager.export_session_data(session_id, include_progress=True)
        if session_data:
            print(f"✅ Complete session export available")
            print(f"   Keys: {list(session_data.keys())}")
    
    def demonstrate_error_handling(self):
        """Demonstrate comprehensive error handling."""
        
        print("\n6️⃣  ERROR HANDLING AND VALIDATION")
        print("-" * 40)
        
        # Test invalid request
        invalid_request = SolverRequest(
            equations=['invalid equation syntax ###'],
            variables=['x'],
            initial_guess={'x': 'not_a_number'}  # This will cause validation error
        )
        
        print("🧪 Testing invalid request...")
        response = self.api_service.solve_algebraic_system(invalid_request)
        
        if not response.success:
            print(f"✅ Error properly caught: {response.error}")
        
        # Test constraint violation
        constraint_violation = SolverRequest(
            equations=['x**2 - 4'],
            variables=['x'],
            initial_guess={'x': -5.0},  # Outside constraint
            constraints={'x': (0, 3)},
            solver_options={'constraint_handling': 'error'}
        )
        
        print("🧪 Testing constraint violation...")
        response = self.api_service.solve_algebraic_system(constraint_violation)
        
        if not response.success:
            print(f"✅ Constraint error properly caught")
        else:
            print(f"⚠️  Constraint handling prevented error")
    
    def run_complete_demo(self):
        """Run the complete web integration demonstration."""
        
        print("🌐 TEXTTOSOLVER WEB INTEGRATION DEMO")
        print("=" * 60)
        print("This demonstrates a complete web application architecture")
        print("with TextToSolver integration, session management, and")
        print("real-time visualization capabilities.")
        print()
        
        try:
            # Run demonstrations
            session1, response1 = self.demonstrate_algebraic_solving_workflow()
            session2, response2 = self.demonstrate_dynamic_solving_workflow()
            concurrent_sessions = self.demonstrate_concurrent_sessions()
            session3, progress = self.demonstrate_real_time_progress()
            
            # Use first successful session for export demo
            export_session = session1 if response1.success else (session2 if response2.success else session3)
            self.demonstrate_export_capabilities(export_session)
            
            self.demonstrate_error_handling()
            
            # Final statistics
            print("\n📊 FINAL STATISTICS")
            print("-" * 40)
            stats = self.session_manager.get_session_statistics()
            print(json.dumps(stats, indent=2))
            
            print("\n🎉 WEB INTEGRATION DEMO COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("This architecture provides:")
            print("✅ Stateless API service layer")
            print("✅ Session management for concurrent users")
            print("✅ Real-time progress monitoring") 
            print("✅ Visualization data generation")
            print("✅ Comprehensive error handling")
            print("✅ Export capabilities for multiple formats")
            print("✅ Resource management and cleanup")
            print()
            print("Ready for integration with web frameworks like:")
            print("• Flask/FastAPI + React/Vue.js")
            print("• Django + Angular")
            print("• Node.js/Express + any frontend")
            print("• WebSocket support for real-time updates")
            
        except Exception as e:
            print(f"❌ Demo error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    # Run the complete demonstration
    demo = WebApplicationDemo()
    demo.run_complete_demo()
