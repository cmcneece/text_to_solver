"""
text_to_solver: Easy to set-up non-linear solver

A Python package for solving systems of non-linear equations by defining
equations as strings. Automatically generates Jacobians and solves using
Newton-Raphson method.
"""

from .TextToSolver import TextToSolver

__version__ = '0.1.0'
__all__ = ['TextToSolver']

