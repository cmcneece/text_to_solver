"""
Tests for Advanced Patterns in TextToSolver

Tests the Observer, Strategy, Builder, and Factory patterns implemented in Phase 2.
"""

import unittest
import numpy as np
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Import the patterns to test
from text_to_solver.advanced_patterns.observers import (
    ConvergenceMonitor, ProgressCallback, EventLogger, CallbackManager,
    SolverEvent, create_progress_monitor
)
from text_to_solver.advanced_patterns.strategies import (
    NewtonRaphsonStrategy, BroydenStrategy, BacktrackingLineSearch,
    ResidualConvergence, StepSizeConvergence, CombinedConvergence,
    create_robust_newton_strategy
)
from text_to_solver.advanced_patterns.builders import (
    EquationSystemBuilder
)  # NOTE: ChemicalSystemBuilder moved to extensions
from text_to_solver.advanced_patterns.factories import (
    SystemFactory, TemplateFactory, ConfigurationFactory
)  # NOTE: ChemicalFactory moved to extensions
from text_to_solver.enhanced_solver import EnhancedEquationSolver, create_monitored_solver
from text_to_solver.user_api import EquationSystem


class TestObserverPattern(unittest.TestCase):
    """Test Observer pattern implementations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = ConvergenceMonitor()
        self.callback_manager = CallbackManager()
    
    def test_convergence_monitor_basic(self):
        """Test basic convergence monitoring."""
        # Simulate solver events
        start_event = SolverEvent('start', 0, 0.0, float('inf'))
        self.monitor.on_start(start_event)
        
        # Simulate iterations
        for i in range(1, 4):
            residual = 1.0 / (10 ** i)  # Decreasing residual
            event = SolverEvent('iteration', i, float(i), residual, step_norm=0.1)
            self.monitor.on_iteration(event)
        
        # Simulate convergence
        final_event = SolverEvent('convergence', 3, 3.0, 1e-3)
        self.monitor.on_convergence(final_event)
        
        # Check history
        history = self.monitor.get_convergence_history()
        self.assertEqual(len(history), 3)
        self.assertEqual(self.monitor.final_status, 'converged')
        
        # Check residual history
        residuals = self.monitor.get_residual_history()
        self.assertEqual(len(residuals), 3)
        self.assertTrue(all(residuals[i] > residuals[i+1] for i in range(len(residuals)-1)))
    
    def test_progress_callback(self):
        """Test progress callback functionality."""
        iterations = []
        residuals = []
        
        def iteration_callback(iter_num, residual):
            iterations.append(iter_num)
            residuals.append(residual)
        
        callback = ProgressCallback(iteration_callback=iteration_callback)
        
        # Simulate events
        callback.on_start(SolverEvent('start', 0, 0.0, float('inf')))
        callback.on_iteration(SolverEvent('iteration', 1, 1.0, 0.1))
        callback.on_iteration(SolverEvent('iteration', 2, 2.0, 0.01))
        callback.on_convergence(SolverEvent('convergence', 2, 2.0, 0.01))
        
        self.assertEqual(iterations, [1, 2])
        self.assertEqual(residuals, [0.1, 0.01])
    
    def test_callback_manager(self):
        """Test callback manager with multiple observers."""
        monitor = ConvergenceMonitor()
        callback_called = {'value': False}
        
        def test_callback(iter_num, residual):
            callback_called['value'] = True
        
        progress = ProgressCallback(iteration_callback=test_callback)
        
        self.callback_manager.add_observer(monitor)
        self.callback_manager.add_observer(progress)
        
        # Notify all observers
        event = SolverEvent('iteration', 1, 1.0, 0.1)
        self.callback_manager.notify_iteration(event)
        
        # Check that both observers were notified
        self.assertEqual(len(monitor.get_convergence_history()), 1)
        self.assertTrue(callback_called['value'])
    
    def test_event_logger(self):
        """Test event logging functionality."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            log_file = f.name
        
        try:
            logger = EventLogger(log_file=log_file, log_iterations=True)
            
            # Simulate events
            logger.on_start(SolverEvent('start', 0, 0.0, float('inf')))
            logger.on_iteration(SolverEvent('iteration', 1, 1.0, 0.1))
            logger.on_convergence(SolverEvent('convergence', 1, 1.0, 0.01))
            
            # Check log file was created and has content
            log_path = Path(log_file)
            self.assertTrue(log_path.exists())
            
            content = log_path.read_text()
            self.assertIn('Solver started', content)
            self.assertIn('Iteration 1', content)
            self.assertIn('converged', content)
            
        finally:
            # Cleanup
            Path(log_file).unlink(missing_ok=True)


class TestStrategyPattern(unittest.TestCase):
    """Test Strategy pattern implementations."""
    
    def test_backtracking_line_search(self):
        """Test backtracking line search strategy."""
        line_search = BacktrackingLineSearch(alpha=1e-4, rho=0.5)
        
        # Mock function that evaluates residual
        def mock_func(x):
            return x**2  # Simple quadratic
        
        x = np.array([2.0])
        direction = np.array([-1.0])  # Descent direction
        f_val = mock_func(x)
        f_norm = np.linalg.norm(f_val)
        
        step_size = line_search.compute_step_size(x, direction, mock_func, f_val, f_norm)
        
        self.assertGreater(step_size, 0)
        self.assertLessEqual(step_size, 1.0)
        self.assertEqual(line_search.get_name(), "Backtracking")
    
    def test_convergence_strategies(self):
        """Test convergence strategies."""
        # Test residual convergence
        residual_conv = ResidualConvergence()
        from text_to_solver.TextToSolver import SolverOptions
        
        options = SolverOptions(tol_fun=1e-6)
        
        # Should not converge with large residual
        large_residual = np.array([1.0, 1.0])
        self.assertFalse(residual_conv.check_convergence(large_residual, np.zeros(2), 1, options))
        
        # Should converge with small residual
        small_residual = np.array([1e-8, 1e-8])
        self.assertTrue(residual_conv.check_convergence(small_residual, np.zeros(2), 1, options))
        
        # Test step size convergence
        step_conv = StepSizeConvergence(step_tolerance=1e-5)  # Set explicit tolerance
        x1 = np.array([1.0, 2.0])
        x2 = np.array([1.000001, 2.000001])  # Small step
        
        # First call (no previous x)
        self.assertFalse(step_conv.check_convergence(np.zeros(2), x1, 1, options))
        # Second call with small step
        self.assertTrue(step_conv.check_convergence(np.zeros(2), x2, 2, options))
    
    def test_combined_convergence(self):
        """Test combined convergence strategy."""
        residual_conv = ResidualConvergence()
        step_conv = StepSizeConvergence()
        
        # Test OR combination (any criterion)
        combined_or = CombinedConvergence([residual_conv, step_conv], require_all=False)
        self.assertEqual(combined_or.get_name(), "Residual OR StepSize")
        
        # Test AND combination (all criteria)
        combined_and = CombinedConvergence([residual_conv, step_conv], require_all=True)
        self.assertEqual(combined_and.get_name(), "Residual AND StepSize")
    
    def test_strategy_creation(self):
        """Test strategy factory functions."""
        robust_strategy = create_robust_newton_strategy()
        self.assertIsInstance(robust_strategy, NewtonRaphsonStrategy)
        self.assertEqual(robust_strategy.get_name(), "Newton-Raphson")
        self.assertIn("Backtracking", robust_strategy.get_description())


class TestBuilderPattern(unittest.TestCase):
    """Test Builder pattern implementations."""
    
    def test_equation_system_builder(self):
        """Test basic equation system builder."""
        builder = EquationSystemBuilder()
        
        system = (builder
                  .add_variable('x', 'First variable')
                  .add_variable('y', 'Second variable')
                  .add_equation('x + y - 3', 'Sum equation')
                  .add_equation('x - y - 1', 'Difference equation')
                  .add_parameter('a', 1.0, 'Parameter a')
                  .build())
        
        self.assertEqual(system.dependent_variables, ['x', 'y'])
        self.assertEqual(len(system.equations), 2)
        self.assertEqual(system.parameters['a'], 1.0)
        self.assertIn('x_description', system._metadata)
    
    def test_builder_validation(self):
        """Test builder validation."""
        builder = EquationSystemBuilder()
        
        # Should fail with no variables
        with self.assertRaises(Exception):
            builder.build()
        
        # Should fail with mismatched dimensions
        with self.assertRaises(Exception):
            (builder
             .add_variable('x')
             .add_equation('x - 1')
             .add_equation('x - 2')  # Too many equations
             .build())
    
    # NOTE: test_chemical_system_builder removed - ChemicalSystemBuilder moved to extensions
    
    # NOTE: test_chemical_builder_carbonate removed - ChemicalSystemBuilder moved to extensions


class TestFactoryPattern(unittest.TestCase):
    """Test Factory pattern implementations."""
    
    def test_system_factory_from_equations(self):
        """Test system creation from equations."""
        equations = ['x + y - 3', 'x - y - 1']
        
        system = SystemFactory.from_equations(equations)
        
        self.assertEqual(set(system.dependent_variables), {'x', 'y'})
        self.assertEqual(system.equations, equations)
    
    def test_system_factory_pattern_detection(self):
        """Test pattern detection in factory."""
        # Linear system
        linear_eqs = ['2*x + 3*y - 5', 'x - y - 1']
        system = SystemFactory.from_equations(linear_eqs, auto_detect=True)
        self.assertTrue(hasattr(system, '_detected_patterns'))
        
        # Geometric system
        geometric_eqs = ['x**2 + y**2 - 4', 'y - 2*x']
        system = SystemFactory.from_equations(geometric_eqs, auto_detect=True)
        self.assertIsInstance(system, EquationSystem)
    
    def test_system_factory_patterns(self):
        """Test creating systems from patterns."""
        # Linear pattern
        linear_system = SystemFactory.from_pattern('linear', size=2, a_0_0=2, a_0_1=1, b_0=3)
        self.assertEqual(len(linear_system.dependent_variables), 2)
        
        # Circle-line pattern
        circle_system = SystemFactory.from_pattern('circle_line', radius=3, slope=2, intercept=1)
        self.assertIn('x', circle_system.dependent_variables)
        self.assertIn('y', circle_system.dependent_variables)
    
    # NOTE: test_chemical_factory removed - ChemicalFactory moved to extensions
    
    def test_template_factory(self):
        """Test template factory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            factory = TemplateFactory(temp_dir)
            
            # Create a test template
            template_data = {
                'name': 'test_template',
                'description': 'Test template',
                'variables': ['x', 'y'],
                'equations': ['{a}*x + {b}*y - {c}', 'x - y - {d}'],
                'default_parameters': {'a': 1, 'b': 1, 'c': 3, 'd': 1}
            }
            
            template_path = Path(temp_dir) / 'test_template.json'
            with open(template_path, 'w') as f:
                json.dump(template_data, f)
            
            # Test template loading and usage
            system = factory.create_from_template('test_template', a=2, c=5)
            
            self.assertEqual(system.dependent_variables, ['x', 'y'])
            self.assertIn('2*x + 1*y - 5', system.equations[0])
    
    def test_configuration_factory(self):
        """Test configuration-based system creation."""
        config_data = {
            'variables': ['x', 'y'],
            'equations': ['x + y - 3', 'x - y - 1'],
            'parameters': {'a': 1.0}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            system = ConfigurationFactory.from_json(config_path)
            self.assertEqual(system.dependent_variables, ['x', 'y'])
            self.assertEqual(system.parameters['a'], 1.0)
        finally:
            Path(config_path).unlink(missing_ok=True)


class TestEnhancedSolver(unittest.TestCase):
    """Test Enhanced Equation Solver with pattern integration."""
    
    def test_enhanced_solver_basic(self):
        """Test basic enhanced solver functionality."""
        solver = EnhancedEquationSolver()
        
        # Test method chaining
        result = (solver
                  .set_system(['x', 'y'], ['x + y - 3', 'x - y - 1'])
                  .tolerance(1e-8)
                  .enable_progress_monitoring(show_progress=False))
        
        self.assertIs(result, solver)  # Should return self for chaining
        self.assertTrue(solver._progress_enabled)
    
    def test_enhanced_solver_monitoring(self):
        """Test solver with monitoring enabled."""
        solver = (EnhancedEquationSolver()
                  .set_system(['x', 'y'], ['x + y - 3', 'x - y - 1'])
                  .enable_progress_monitoring(show_progress=False, track_convergence=True))
        
        # Should have convergence monitor
        self.assertIsNotNone(solver._convergence_monitor)
        
        # Solve and check monitoring
        result = solver.solve()
        self.assertTrue(result.success)
        
        # Should have history (even if empty due to quick convergence)
        history = solver.get_convergence_history()
        self.assertIsInstance(history, list)
    
    def test_enhanced_solver_from_pattern(self):
        """Test creating solver from pattern."""
        solver = EnhancedEquationSolver.from_pattern(
            'circle_line', 
            radius=3, 
            slope=2, 
            intercept=1
        )
        
        self.assertIsNotNone(solver._system)
        self.assertIn('x', solver._system.dependent_variables)
        self.assertIn('y', solver._system.dependent_variables)
    
    # NOTE: test_enhanced_solver_chemical removed - chemical system creation moved to extensions
    
    def test_system_analysis(self):
        """Test system analysis functionality."""
        solver = (EnhancedEquationSolver()
                  .set_system(['x', 'y'], ['x + y - 3', 'x - y - 1']))
        
        analysis = solver.analyze_system()
        
        self.assertIn('n_variables', analysis)
        self.assertIn('n_equations', analysis)
        self.assertIn('system_type', analysis)
        self.assertIn('detected_patterns', analysis)
        self.assertEqual(analysis['n_variables'], 2)
        self.assertEqual(analysis['n_equations'], 2)
    
    def test_auto_configuration(self):
        """Test automatic configuration."""
        solver = (EnhancedEquationSolver()
                  .set_system(['x', 'y'], ['x + y - 3', 'x - y - 1'])
                  .auto_configure())
        
        # Should have configured solver based on analysis
        self.assertIsNotNone(solver._solver_strategy)
        
        # Test solving with auto-configuration
        result = solver.solve()
        self.assertTrue(result.success)
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        # Test monitored solver creation
        solver = create_monitored_solver(['x + y - 3', 'x - y - 1'])
        self.assertIsInstance(solver, EnhancedEquationSolver)
        self.assertTrue(solver._progress_enabled)
        
        # Test solving
        result = solver.solve()
        self.assertTrue(result.success)
        
        expected_x, expected_y = 2.0, 1.0
        self.assertAlmostEqual(result['x'], expected_x, places=6)
        self.assertAlmostEqual(result['y'], expected_y, places=6)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
