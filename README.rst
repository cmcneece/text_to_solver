TextToSolver
============

Easy-to-use nonlinear equation solver with symbolic math, constraint handling, and dynamic systems support.

.. image:: https://github.com/cmcneece/text_to_solver/workflows/CI/badge.svg
   :target: https://github.com/cmcneece/text_to_solver/actions
   :alt: CI Status

.. image:: https://codecov.io/gh/cmcneece/text_to_solver/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/cmcneece/text_to_solver
   :alt: Code Coverage

.. image:: https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python version

.. image:: https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey.svg
   :target: https://github.com/cmcneece/text_to_solver/actions
   :alt: Platform Support

.. image:: https://img.shields.io/badge/license-BSD%203--Clause-green.svg
   :target: LICENSE.txt
   :alt: License

.. image:: https://img.shields.io/badge/version-3.0.0-blue.svg
   :target: https://github.com/cmcneece/text_to_solver/releases
   :alt: Version

.. image:: https://img.shields.io/badge/tests-744%20tests%20%7C%20714%20passing-brightgreen.svg
   :target: https://github.com/cmcneece/text_to_solver/actions
   :alt: Test Status

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Code style: black

.. image:: https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336
   :target: https://pycqa.github.io/isort/
   :alt: Imports: isort

.. image:: https://img.shields.io/badge/linting-flake8-yellow.svg
   :target: https://github.com/PyCQA/flake8
   :alt: Linting: flake8

.. image:: https://img.shields.io/badge/status-active-success.svg
   :target: https://github.com/cmcneece/text_to_solver
   :alt: Project Status

.. image:: https://img.shields.io/badge/maintained-yes-green.svg
   :target: https://github.com/cmcneece/text_to_solver
   :alt: Maintained

.. image:: https://img.shields.io/github/last-commit/cmcneece/text_to_solver.svg
   :target: https://github.com/cmcneece/text_to_solver/commits/master
   :alt: Last commit

.. image:: https://img.shields.io/github/issues/cmcneece/text_to_solver.svg
   :target: https://github.com/cmcneece/text_to_solver/issues
   :alt: Issues

.. image:: https://img.shields.io/github/stars/cmcneece/text_to_solver.svg?style=social&label=Star
   :target: https://github.com/cmcneece/text_to_solver
   :alt: GitHub stars

.. image:: https://img.shields.io/github/contributors/cmcneece/text_to_solver.svg
   :target: https://github.com/cmcneece/text_to_solver/graphs/contributors
   :alt: Contributors

.. image:: https://img.shields.io/github/release/cmcneece/text_to_solver.svg
   :target: https://github.com/cmcneece/text_to_solver/releases
   :alt: Latest release

Overview
--------

TextToSolver is a powerful Python library for solving systems of nonlinear equations. It provides:

- **Symbolic Math Integration**: Automatic Jacobian computation using SymPy
- **Constraint Support**: Box constraints (bounds) on variables
- **Multiple Solving Strategies**: Newton-Raphson with line search, multistart capabilities
- **Dynamic Systems**: Differential equation solving with multiple integration methods
- **User-Friendly APIs**: Multiple API levels from simple one-liners to advanced pattern-based solvers
- **Comprehensive Analysis**: Convergence analysis, constraint activity tracking, iteration history

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install text_to_solver

Basic Usage
~~~~~~~~~~~

Simple one-liner for solving equations:

.. code-block:: python

   from text_to_solver import EquationSolver

   # Solve a system of equations
   result = EquationSolver.solve_equations(
       variables=['x', 'y'],
       equations=['x + y - 1', 'x - y - 0.5']
   )

   print(f"Solution: x = {result.variables['x'][0]:.6f}, y = {result.variables['y'][0]:.6f}")
   print(f"Converged: {result.converged}")
   print(f"Iterations: {result.iterations}")

Using the Core API
~~~~~~~~~~~~~~~~~~

For more control, use the core ``TextToSolver`` class:

.. code-block:: python

   from text_to_solver import TextToSolver, SolverOptions
   import numpy as np

   # Create solver
   solver = TextToSolver(
       dep_vars=['x', 'y'],
       residual=['x + y - 1', 'x - y - 0.5']
   )

   # Solve with initial guess
   guess = {'x': np.array([0.5]), 'y': np.array([0.5])}
   solution, report = solver.solve(
       guess=guess,
       options=SolverOptions(display=False, tol_fun=1e-8)
   )

   print(f"Solution: {solution}")
   print(f"Exit flag: {report['exit_flag']} (1 = success)")
   print(f"Residual norm: {report['res_norm']:.2e}")

Features
--------

Core Solving
~~~~~~~~~~~~

- **Automatic Jacobian**: Symbolic differentiation using SymPy
- **Newton-Raphson Method**: With backtracking line search
- **Convergence Detection**: Multiple convergence criteria
- **Iteration History**: Track solver progress and analyze convergence

Constraint Handling
~~~~~~~~~~~~~~~~~~~

Box constraints (bounds) on variables:

.. code-block:: python

   from text_to_solver import TextToSolver

   solver = TextToSolver(
       dep_vars=['x', 'y'],
       residual=['x + y - 1', 'x - y - 0.5'],
       constraints={'x': (0.0, 10.0), 'y': (None, 5.0)}  # x in [0,10], y <= 5
   )

   # Constraints are automatically enforced during solving
   solution, report = solver.solve_auto()

Constraint handling modes:
- ``'error'``: Raise error if initial guess violates constraints
- ``'project'``: Automatically project to feasible region (with warning)
- ``'project_silent'``: Project silently
- ``'ignore'``: Allow infeasible guesses (projection during iterations)

Parameter Sweeps
~~~~~~~~~~~~~~~~

Efficiently solve for multiple parameter values:

.. code-block:: python

   from text_to_solver import EquationSolver

   solver = EquationSolver(
       variables=['x', 'y'],
       equations=['x + y - p', 'x - y - 0.5'],
       parameters={'p': 1.0}
   )

   # Solve for multiple parameter values
   results = solver.parameter_sweep('p', [0.5, 1.0, 1.5, 2.0])

   for i, result in enumerate(results):
       if result.converged:
           print(f"p={0.5 + i*0.5}: x={result.variables['x'][0]:.3f}")

Dynamic Systems
~~~~~~~~~~~~~~~

Solve systems of ordinary differential equations:

.. code-block:: python

   from text_to_solver import DynamicEquationSolver, DynamicSystem

   # Define ODE system: dx/dt = -k*x, dy/dt = -k*y
   solver = DynamicEquationSolver()
   system = DynamicSystem(
       variables=['x', 'y'],
       equations=['dx/dt = -k*x', 'dy/dt = -k*y'],
       initial_conditions={'x': 1.0, 'y': 2.0},
       parameters={'k': 0.5}
   )

   solver.set_system(system)
   result = solver.integrate(time_span=(0, 10), method='RK45')

   if result.success:
       print(f"Final values: x={result.final_values['x']:.3f}, y={result.final_values['y']:.3f}")

Available integration methods: ``'Euler'``, ``'RK4'``, ``'RK45'``, ``'DOP853'``

Analysis Tools
~~~~~~~~~~~~~~

Analyze solver performance and convergence:

.. code-block:: python

   from text_to_solver import TextToSolver, SolverOptions

   solver = TextToSolver(
       dep_vars=['x', 'y'],
       residual=['x + y - 1', 'x - y - 0.5']
   )

   solution, report = solver.solve_auto(
       options=SolverOptions(store_history=True, display=False)
   )

   # Analyze convergence
   convergence_analysis = solver.analyze_convergence()
   print(f"Convergence type: {convergence_analysis['convergence_type']}")
   print(f"Total iterations: {convergence_analysis['total_iterations']}")
   print(f"Residual reduction: {convergence_analysis['residual_reduction']:.2e}")

   # Get iteration history
   history = solver.get_iteration_history()
   residuals = solver.get_residual_history()

API Reference
-------------

Three API Levels
~~~~~~~~~~~~~~~~

1. **Simple API** (``EquationSolver``): User-friendly, high-level interface
2. **Core API** (``TextToSolver``): Full control, symbolic math integration
3. **Enhanced API** (``EnhancedEquationSolver``): Advanced patterns, monitoring, strategies

Simple API Example
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from text_to_solver import EquationSolver

   solver = (EquationSolver()
             .set_system(['x', 'y'], ['x + y - 1', 'x - y - 0.5'])
             .tolerance(1e-8)
             .max_iterations(50))

   result = solver.solve(multistart=True)

Core API Example
~~~~~~~~~~~~~~~~

.. code-block:: python

   from text_to_solver import TextToSolver
   from text_to_solver.TextToSolver import from_equations

   # Method 1: Direct initialization
   solver = TextToSolver(
       dep_vars=['x', 'y'],
       residual=['x + y - 1', 'x - y - 0.5']
   )

   # Method 2: From equations (auto-detects variables)
   solution, report = from_equations(
       equations=['x + y = 1', 'x - y = 0.5'],
       auto_solve=True
   )

Solver Options
~~~~~~~~~~~~~~

Customize solver behavior:

.. code-block:: python

   from text_to_solver import SolverOptions

   options = SolverOptions(
       tol_fun=1e-8,          # Residual tolerance
       tol_x=1e-10,          # Step size tolerance
       max_iter=50,            # Maximum iterations
       display=True,           # Show iteration progress
       alpha=1e-4,             # Line search parameter
       min_lambda=0.1,         # Minimum step size
       max_lambda=0.5,         # Maximum step size
       store_history=True,     # Store iteration history
       constraint_handling='project'  # Constraint handling mode
   )

Examples
--------

Circle-Line Intersection
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from text_to_solver import TextToSolver
   import numpy as np

   # Find intersection of circle x^2 + y^2 = r^2 and line y = m*x
   solver = TextToSolver(
       dep_vars=['x', 'y'],
       residual=['x**2 + y**2 - r**2', 'y - m*x'],
       indep_vars=['r', 'm']
   )

   # Solve for r=5, m=0.5
   solution, report = solver.solve(
       guess={'x': np.array([4.0]), 'y': np.array([2.0])},
       indep_var_val={'r': np.array([5.0]), 'm': np.array([0.5])}
   )

   print(f"Intersection: ({solution['x'][0]:.3f}, {solution['y'][0]:.3f})")

Chemical Equilibrium
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from text_to_solver import EquationSolver

   # Solve chemical equilibrium: A + B <-> C
   # K = [C] / ([A] * [B]) = 10
   solver = EquationSolver(
       variables=['A', 'B', 'C'],
       equations=[
           'A + B + C - 1',      # Mass balance
           'C - 10*A*B'           # Equilibrium constant
       ]
   )

   result = solver.solve(multistart=True)
   if result.converged:
       print(f"Equilibrium: A={result.variables['A'][0]:.3f}, "
             f"B={result.variables['B'][0]:.3f}, "
             f"C={result.variables['C'][0]:.3f}")

More examples are available in the ``docs/examples/`` directory.

Requirements
------------

- Python 3.7+
- NumPy >= 1.15.0
- SciPy >= 1.1.0
- SymPy >= 1.3
- Pandas >= 0.23.0

Optional dependencies:
- Matplotlib >= 3.5.0 (for visualization examples)

Installation
------------

From PyPI (when available):

.. code-block:: bash

   pip install text_to_solver

From source:

.. code-block:: bash

   git clone https://github.com/yourusername/text_to_solver.git
   cd text_to_solver
   pip install -e .

Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~

For development with editable install:

.. code-block:: bash

   pip install -e ".[dev]"

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

   pytest tests/ -v

Documentation
-------------

Full documentation is available in the ``docs/`` directory:

- API reference
- Examples and tutorials
- Advanced usage patterns

Contributing
------------

Contributions are welcome! Please feel free to submit a Pull Request.

License
-------

BSD 3-Clause License - see LICENSE.txt for details.

Support
-------

For issues, questions, or contributions, please open an issue on GitHub.

Author
------

Colin J. McNeece

Version
-------

3.0.0 - Comprehensive equation solver with dynamic systems and advanced patterns
