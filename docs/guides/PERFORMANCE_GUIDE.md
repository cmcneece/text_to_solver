# TextToSolver Performance Optimization Guide

## 🎯 **Quick Wins (Immediate Impact)**

### 1. **Use Appropriate Tolerances**
```python
# For speed over precision
fast_options = SolverOptions(
    tol_fun=1e-6,    # Relaxed function tolerance
    tol_x=1e-8,      # Relaxed step tolerance  
    max_iter=15,     # Fewer iterations
    display=False    # Skip printing overhead
)

# For high-precision applications
precise_options = SolverOptions(
    tol_fun=1e-12,
    tol_x=1e-14,
    max_iter=50
)
```

### 2. **Choose the Right Initial Guess Strategy**
```python
# Fastest: Use heuristic for simple systems
solver.solve_auto(guess_strategy='heuristic')

# Best convergence: Use auto for complex systems
solver.solve_auto(guess_strategy='auto')

# For repeated similar problems: Use scaled
solver.solve_auto(guess_strategy='scaled')
```

### 3. **Optimize System Size**
```python
# ✅ Good: Minimize system size by substitution
solver = TextToSolver(['x', 'y'], [
    'x + y - 3',           # 2 variables, 2 equations
    'x**2 + y**2 - 5'
])

# ❌ Avoid: Unnecessarily large systems  
solver = TextToSolver(['x', 'y', 'z', 'w'], [
    'x + y - 3',
    'x**2 + y**2 - 5', 
    'z - (x + y)',        # z can be eliminated
    'w - z**2'            # w can be eliminated
])
```

## ⚡ **Algorithm-Level Optimizations**

### 4. **Use Multistart Strategically**
```python
# For well-conditioned problems: Skip multistart
solution, report = solver.solve_auto(multistart=False)

# For ill-conditioned problems: Use multistart
solution, report = solver.solve_auto(multistart=True)

# Check condition before deciding
if solver.estimate_condition_number() > 1e10:
    solution, report = solver.solve_auto(multistart=True)
```

### 5. **Leverage Pattern Detection**
```python
# Let the solver detect patterns automatically
pattern = solver._detect_equation_patterns()
print(f"Detected pattern: {pattern}")

# Use specialized methods for known patterns
if pattern == 'linear':
    # Linear systems converge faster
    solution, report = solver.solve_auto(
        options=SolverOptions(max_iter=5)  # Fewer iterations needed
    )
```

### 6. **Batch Similar Problems**
```python
# ✅ Efficient: Reuse solver for parameter sweeps
solver = TextToSolver(['x', 'y'], ['a*x + b*y - c', 'x**2 + y**2 - r'])

solutions = []
for a, b, c, r in parameter_sets:
    solver.parameters = {'a': a, 'b': b, 'c': c, 'r': r}
    solver.generate_symbolic()  # Only regenerate symbols
    solver.functionalize()      # Only recompile functions
    
    solution, _ = solver.solve_auto()
    solutions.append(solution)
```

## 🔧 **Implementation Optimizations**

### 7. **Symbolic Expression Simplification**
```python
# Before creating solver, simplify expressions
import sympy as sp

# Original complex expression
original = "exp(log(x)) + sin(arcsin(y)) + x**2 + x**2"

# Simplified version
x, y = sp.symbols('x y')
expr = sp.sympify(original)
simplified = sp.simplify(expr)
print(simplified)  # 2*x**2 + x + y

# Use simplified version in solver
solver = TextToSolver(['x', 'y'], [str(simplified) + ' - target'])
```

### 8. **Efficient Variable Ordering**
```python
# ✅ Order variables by coupling strength
# Put strongly coupled variables adjacent
solver = TextToSolver(
    ['x', 'y', 'z'],  # x and y are strongly coupled
    [
        'x**2 + x*y - 1',      # Equation involving x, y
        'y**2 + x*y - 2',      # Equation involving x, y  
        'z - x - y'            # Weakly coupled z
    ]
)
```

### 9. **Memory-Efficient Evaluation**
```python
# For large parameter sweeps, use generators
def parameter_generator():
    for i in range(1000):
        yield {'a': i, 'b': i**2, 'c': i**3}

# Memory-efficient processing
for params in parameter_generator():
    solver.parameters = params
    solution, _ = solver.solve_auto()
    # Process solution immediately, don't store all
    process_solution(solution)
```

## 📊 **Performance Monitoring**

### 10. **Profile Your Solver Usage**
```python
import time
import cProfile

def profile_solver():
    start_time = time.time()
    
    solver = TextToSolver(['x', 'y'], ['x**2 + y**2 - 4', 'x + y - 2'])
    
    # Time symbolic generation
    symb_start = time.time()
    solver.generate_symbolic() 
    symb_time = time.time() - symb_start
    
    # Time function compilation
    func_start = time.time()
    solver.functionalize()
    func_time = time.time() - func_start
    
    # Time solving
    solve_start = time.time()
    solution, report = solver.solve_auto()
    solve_time = time.time() - solve_start
    
    print(f"Symbolic generation: {symb_time:.4f}s")
    print(f"Function compilation: {func_time:.4f}s") 
    print(f"Solving: {solve_time:.4f}s")
    print(f"Total: {time.time() - start_time:.4f}s")
    
    return report

# Detailed profiling
cProfile.run('profile_solver()', 'solver_profile.prof')
```

## 🎯 **Problem-Specific Tips**

### 11. **Chemical Equilibrium Systems**
```python
# Use appropriate scaling for chemical systems
chemical_solver = TextToSolver(
    ['pH', 'pCO2', 'pHCO3'],
    ['-pK1 + pHCO3 + pH - pCO2', ...]
)

# Chemical systems often benefit from:
# - Scaled initial guesses
# - Relaxed tolerances for log-space variables
# - Multistart for multiple equilibria
solution, report = chemical_solver.solve_auto(
    guess_strategy='scaled',
    multistart=True,
    options=SolverOptions(tol_fun=1e-8)  # Relaxed for log variables
)
```

### 12. **Lotka-Volterra (Predator-Prey) Systems**
```python
# Use analytical initial guesses for biological systems
bio_solver = TextToSolver(['prey', 'predator'], [...])

# Biological systems benefit from:
# - Analytical guesses based on equilibrium points
# - Bounded variables (populations > 0)
# - Conservative step sizes
solution, report = bio_solver.solve_auto(
    guess_strategy='analytical', 
    options=SolverOptions(alpha=1e-3)  # Conservative steps
)
```

### 13. **Large Sparse Systems**
```python
# For systems with many variables but sparse coupling
large_solver = TextToSolver(
    [f'x_{i}' for i in range(100)],  # 100 variables
    sparse_equations  # Only local coupling
)

# Use specialized options for large systems
large_options = SolverOptions(
    tol_fun=1e-8,     # Relaxed tolerance
    max_iter=100,     # More iterations allowed
    display=False     # Reduce output overhead
)
```

## ⚠️ **Common Performance Pitfalls**

### 14. **Avoid These Patterns**
```python
# ❌ DON'T: Recreate solver repeatedly
for params in parameter_list:
    solver = TextToSolver(vars, eqs)  # Expensive!
    solver.parameters = params
    solution = solver.solve_auto()

# ✅ DO: Reuse solver object  
solver = TextToSolver(vars, eqs)
for params in parameter_list:
    solver.parameters = params
    solver.generate_symbolic()  # Only regenerate when needed
    solver.functionalize()
    solution = solver.solve_auto()

# ❌ DON'T: Use overly tight tolerances by default
bad_options = SolverOptions(tol_fun=1e-15)  # Unnecessary precision

# ❌ DON'T: Use multistart for simple linear systems
linear_solver.solve_auto(multistart=True)  # Overkill

# ❌ DON'T: Keep display=True for production code
SolverOptions(display=True)  # Slows down batch processing
```

## 📈 **Expected Performance Gains**

| Optimization | Speed Improvement | When to Use |
|-------------|------------------|-------------|
| Appropriate tolerances | 2-5x | Always |
| Optimal guess strategy | 2-10x | Complex systems |
| Solver reuse | 5-50x | Parameter sweeps |
| Pattern detection | 1.5-3x | Structured systems |
| Symbolic caching | 3-20x | Repeated compilations |
| Multistart (when needed) | 1-∞x | Convergence issues |

## 🔍 **Debugging Performance Issues**

### 15. **Identify Bottlenecks**
```python
# Check convergence issues
def diagnose_convergence(solver, guess):
    solution, report = solver.solve(guess)
    
    print(f"Exit flag: {report['exit_flag']}")
    print(f"Iterations: {report['iter_count']}")
    print(f"Final residual: {report['res_norm']}")
    
    if report['exit_flag'] != 1:
        print("⚠️  Convergence issues detected")
        print("💡 Try: multistart=True or better initial guess")
    
    if report['iter_count'] > 30:
        print("⚠️  Slow convergence detected") 
        print("💡 Try: better scaling or different tolerances")

# Check system conditioning
def check_conditioning(solver, solution):
    # Evaluate Jacobian at solution
    x_list = [solution[var] for var in solver.variables_string]
    _, jac = solver.evaluate_res_jac(x_list, [])
    
    # Estimate condition number (rough)
    jac_dense = jac.toarray()
    cond_est = np.linalg.norm(jac_dense) * np.linalg.norm(np.linalg.pinv(jac_dense))
    
    print(f"Condition estimate: {cond_est:.2e}")
    if cond_est > 1e12:
        print("⚠️  Ill-conditioned system detected")
        print("💡 Try: variable scaling or regularization")
```

## 🎉 **Performance Testing Results**

Run these benchmarks to measure your improvements:

```python
def benchmark_solver():
    """Benchmark different solver configurations."""
    test_problems = [
        ('Linear', ['x', 'y'], ['2*x + 3*y - 7', 'x - y - 1']),
        ('Nonlinear', ['x', 'y'], ['x**2 + y**2 - 4', 'x*y - 1']),
        ('Chemical', ['pH', 'pOH'], ['-14 + pH + pOH', 'pH - 7'])
    ]
    
    configurations = [
        ('Default', {}),
        ('Fast', {'options': SolverOptions(tol_fun=1e-6, max_iter=15)}),
        ('Multistart', {'multistart': True}),
        ('Heuristic', {'guess_strategy': 'heuristic'})
    ]
    
    for prob_name, vars, eqs in test_problems:
        print(f"\n{prob_name} System:")
        solver = TextToSolver(vars, eqs)
        
        for conf_name, kwargs in configurations:
            start = time.time()
            solution, report = solver.solve_auto(**kwargs)
            elapsed = time.time() - start
            
            status = "✅" if report['exit_flag'] == 1 else "❌"
            print(f"  {conf_name:12} {elapsed:.4f}s {status}")

benchmark_solver()
```

This guide provides both immediate wins and advanced optimization strategies. Start with the quick wins, then implement more sophisticated optimizations based on your specific use cases!
