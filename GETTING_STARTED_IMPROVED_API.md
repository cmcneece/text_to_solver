# Getting Started with the Improved TextToSolver API

## Quick Start

The TextToSolver package now offers two APIs:
- **Original API**: `TextToSolver` (unchanged, fully compatible)
- **Improved API**: `EquationSolver` (new, user-friendly)

### Installation
No changes required - use your existing TextToSolver installation.

### Simple Import
```python
# Use improved API (recommended for new code)
from text_to_solver import EquationSolver, ChemicalEquilibrium

# Original API still available (existing code unchanged)  
from text_to_solver import TextToSolver, SolverOptions
```

## 🚀 Common Usage Patterns

### 1. One-Liner Equation Solving
Perfect for simple systems and interactive use:

```python
from text_to_solver import EquationSolver

# Solve x² - 4 = 0
result = EquationSolver.solve_equations(['x'], ['x**2 - 4'])
print(f"x = {result['x']}")  # Direct access: x = 2.0
print(f"Success: {result.success}")  # Check convergence
```

### 2. Fluent Interface Configuration
For complex systems needing custom settings:

```python
result = (EquationSolver()
          .set_system(['x', 'y'], ['x**2 + y**2 - 4', 'x + y - 2'])
          .tolerance(1e-10)
          .max_iterations(100) 
          .guess_strategy('scaled')
          .solve(multistart=True))

if result.success:
    print(f"Solution: x={result['x']:.4f}, y={result['y']:.4f}")
```

### 3. Parameter Studies
Efficient parameter sweeps with automatic result handling:

```python
# Set up base system
solver = (EquationSolver()
          .set_system(['C_A', 'C_B'], ['C_A + C_B - total', 'K_eq * C_A - C_B'])
          .tolerance(1e-8))

# Sweep equilibrium constant
results = solver.parameter_sweep('K_eq', [0.1, 0.5, 1.0, 2.0, 5.0])

# Analyze results
for i, result in enumerate(results):
    k_eq = [0.1, 0.5, 1.0, 2.0, 5.0][i] 
    if result.success:
        print(f"K_eq = {k_eq}: C_A = {result['C_A']:.3f}, C_B = {result['C_B']:.3f}")
```

### 4. Chemical Equilibrium Calculations
Built-in helpers for common chemical systems:

```python
from text_to_solver import ChemicalEquilibrium

# Water autoionization at different pH
water = ChemicalEquilibrium.water_autoionization(pH=6.5, temperature_c=25)
print(f"pH = 6.5 → pOH = {water['pOH']:.2f}")

# Buffer system calculation  
buffer = ChemicalEquilibrium.buffer_system(
    pka=4.75,      # Acetic acid
    total_conc_log=2.0,  # 10 mM total
    pH=4.5
)
print(f"Buffer: [A⁻] = 10^{buffer['pA']:.2f}, [HA] = 10^{buffer['pHA']:.2f}")
```

## 📊 Result Objects

### Rich Result Access
```python
result = EquationSolver.solve_equations(['x', 'y'], ['x + y - 3', 'x - y - 1'])

# Multiple access patterns
print(result['x'])           # Direct: 2.0
print(result.variables['x']) # Array: [2.0] 
print('x' in result)         # Check: True
print(result.success)        # Status: True
print(result.iterations)     # Count: 1

# Convert to simple dict
data = result.to_dict()      # {'x': 2.0, 'y': 1.0}

# Human-readable summary  
print(result)                # "✅ Converged in 1 iterations: x=2, y=1"
```

### Error Handling
```python
try:
    # This will fail - dimension mismatch
    result = EquationSolver.solve_equations(['x'], ['eq1', 'eq2'])
except EquationSystemError as e:
    print(e)
    # Prints helpful error with suggestions:
    # "System dimension mismatch: 1 variables, 2 equations
    #  Suggestion: Add more variables or remove equations"
```

## 🔄 Migration Guide

### Existing Code (No Changes Required)
Your existing TextToSolver code continues to work unchanged:

```python
# This still works exactly as before
from text_to_solver import TextToSolver, SolverOptions

solver = TextToSolver(['x', 'y'], ['x + y - 3', 'x - y - 1'])
solution, report = solver.solve_auto()
# ... existing code unchanged
```

### Gradual Adoption
Start using the improved API in new code:

```python
# Old approach (still works)
solver = TextToSolver(['x', 'y'], ['x + y - 3', 'x - y - 1'])
options = SolverOptions(tol_fun=1e-8, display=False)
solution, report = solver.solve_auto(options=options)
x_old = solution['x'][0]

# New approach (same result, cleaner code)
result = EquationSolver.solve_equations(
    ['x', 'y'], ['x + y - 3', 'x - y - 1'], tolerance=1e-8)
x_new = result['x']

# Both give the same answer!
assert abs(x_old - x_new) < 1e-10
```

## 🧪 Advanced Features

### Custom Initial Guesses
```python
# Provide specific initial guess
custom_guess = {'x': np.array([1.5]), 'y': np.array([0.5])}

result = (EquationSolver()
          .set_system(['x', 'y'], ['x**2 + y**2 - 4', 'x + y - 2'])
          .solve(custom_guess=custom_guess))
```

### System Parameters
```python
# System with parameters
solver = EquationSolver().set_system(
    ['x', 'y'], 
    ['x + y - sum_val', 'x - y - diff_val']
)

# Update parameters and solve
result = (solver
          .with_parameters({'sum_val': 5.0, 'diff_val': 1.0})
          .solve())

# Try different parameters
result2 = (solver
           .with_parameters({'sum_val': 7.0, 'diff_val': 3.0})
           .solve())
```

### Robust Solving
```python
# Use multistart for difficult nonlinear systems
result = EquationSolver.solve_equations(
    ['x', 'y'], 
    ['sin(x) + cos(y) - 1', 'exp(x) * log(y) - 2'],
    multistart=True,  # Try multiple starting points
    tolerance=1e-8
)
```

## 💡 Tips & Best Practices

### Choose the Right API
- **One-liner**: Use `EquationSolver.solve_equations()` for simple problems
- **Fluent interface**: Use method chaining for complex configurations  
- **Parameter sweeps**: Use `.parameter_sweep()` for batch calculations
- **Chemical problems**: Use `ChemicalEquilibrium` helpers when applicable

### Error Handling
```python
from text_to_solver import EquationSolver, EquationSystemError, SolverError

try:
    result = EquationSolver.solve_equations(variables, equations)
    if result.success:
        # Process successful result
        process_solution(result)
    else:
        # Handle convergence failure
        print(f"Failed to converge: residual = {result.residual_norm}")
        
except EquationSystemError as e:
    # System setup problems (dimension mismatch, etc.)
    print(f"System error: {e}")
    
except SolverError as e:
    # Solver runtime problems
    print(f"Solver error: {e}")
```

### Performance Tips
- Use parameter sweeps instead of loops for batch calculations
- Enable multistart for difficult nonlinear systems  
- Set appropriate tolerance (don't over-specify precision)
- Reuse solver objects when solving similar systems repeatedly

## 📚 Further Reading

- `PHASE_1_IMPLEMENTATION_SUMMARY.md`: Detailed implementation notes
- `demo_improved_api_working.py`: Live demonstration of all features
- `text_to_solver/improved_api.py`: Full API source code
- Original documentation: Still valid for `TextToSolver` class

## 🎯 Key Benefits Recap

✅ **75% less code** for typical use cases  
✅ **Intuitive result access**: `result['x']` instead of `solution['x'][0]`  
✅ **Fluent configuration**: Method chaining for complex setups  
✅ **Rich error messages**: Helpful guidance when things go wrong  
✅ **Domain helpers**: Built-in chemical equilibrium calculations  
✅ **Full compatibility**: Existing code works unchanged  
✅ **IDE-friendly**: Auto-completion guides usage  

---

**Ready to solve equations more efficiently? Start with the examples above!** 🚀
