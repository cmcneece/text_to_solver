==========================================
text_to_solver: easy to set-up non-linear solver
==========================================

text_to_solver is a comprehensive Python package for solving systems of
non-linear equations. Define your equations as strings, and the package
will automatically generate the Jacobian and solve the system using a
Newton-Raphson method with backtracking line search.

Features
--------

- **Multiple APIs**: Original, User-friendly, Enhanced, and Dynamic system APIs
- **Define equations as strings** - no need to manually compute derivatives
- **Automatic Jacobian computation** using SymPy
- **Supports dependent and independent variables**
- **Parameter substitution**
- **Efficient sparse matrix operations**
- **Configurable solver options**
- **Dynamic systems support** - solve differential equations
- **Web API** - RESTful API for solver integration
- **Advanced patterns** - Observer, Strategy, Builder, Factory patterns
- **Session management** - track and manage solver sessions

Installation
------------

Install from source::

    pip install .

Or install in development mode::

    pip install -e .

For web API support::

    pip install -e ".[web]"

For visualization support::

    pip install -e ".[visualization]"

For all optional features::

    pip install -e ".[all]"

Requirements
------------

- Python 3.6+
- numpy
- scipy
- sympy
- pandas

Optional dependencies:
- Flask, Flask-CORS, Werkzeug (for web API)
- matplotlib (for visualization)

Usage
-----

Basic example::

    from text_to_solver import TextToSolver
    import numpy as np

    # Define equations as strings
    residual = ['x ** 2 + y ** 2 - z ** 2', 'y - 5 * x']
    dep_vars = ['x', 'y']  # Variables to solve for
    ind_vars = ['z']        # Independent variables

    # Create solver
    sys = TextToSolver(dep_vars, residual, indep_vars=ind_vars)

    # Solve with initial guess
    guess = {'x': -np.ones(5), 'y': np.ones(5)}
    ind_var = {'z': np.array([1, 2, 3, 4, 5])}
    solution, report = sys.solve(guess, indep_var_val=ind_var)

User-friendly API example::

    from text_to_solver import EquationSolver

    solver = EquationSolver()
    solver.add_equation('x**2 + y**2 = 1')
    solver.add_equation('y = 2*x')
    result = solver.solve({'x': 0.5, 'y': 1.0})

License
-------

BSD License
