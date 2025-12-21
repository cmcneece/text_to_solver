==========================================
text_to_solver: easy to set-up non-linear solver
==========================================

text_to_solver is a Python package that makes it easy to solve systems of
non-linear equations. Simply define your equations as strings, and the package
will automatically generate the Jacobian and solve the system using a
Newton-Raphson method with backtracking line search.

Features
--------

- Define equations as strings - no need to manually compute derivatives
- Automatic Jacobian computation using SymPy
- Supports dependent and independent variables
- Parameter substitution
- Efficient sparse matrix operations
- Configurable solver options

Installation
------------

Install from source::

    pip install .

Or install in development mode::

    pip install -e .

Requirements
------------

- Python 3.6+
- numpy
- scipy
- sympy
- pandas

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

License
-------

BSD License
