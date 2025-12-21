# Manual Execution Guide

Since the terminal execution through the AI interface is experiencing issues, here's how to run everything manually:

## 1. Environment Diagnosis

First, run the diagnostic script to verify your environment:

```bash
cd /Users/colin.mcneece@cognitedata.com/personal/text_to_solver
python3 diagnose_environment.py
```

This will check:
- Python environment
- TextToSolver import
- File system access
- pytest availability

## 2. Run the Test Suite

### Option A: Using the test runner script
```bash
python run_tests.py
```

### Option B: Using pytest directly
```bash
python -m pytest tests/ -v
```

### Option C: With coverage reporting
```bash
python run_tests.py --coverage
```

### Option D: Run specific test categories
```bash
# Basic functionality tests
python -m pytest tests/test_basic_functionality.py -v

# Enhanced features tests
python -m pytest tests/test_enhanced_functionality.py -v

# Validation and error handling tests
python -m pytest tests/test_validation_and_errors.py -v

# Integration tests
python -m pytest tests/test_integration.py -v
```

## 3. Test Individual Features

### Quick functionality test:
```bash
python simple_test_run.py
```

### Test specific solver features:
```python
# In a Python REPL or script:
from text_to_solver.TextToSolver import TextToSolver, SolverOptions

# Test basic solving
solver = TextToSolver(['x', 'y'], ['x + y - 3', 'x - y - 1'])
solution, report = solver.solve_auto()
print(f"Solution: x={solution['x'][0]:.3f}, y={solution['y'][0]:.3f}")

# Test initial guess generation
guess = solver.generate_initial_guess(strategy='heuristic')
print(f"Generated guess: {guess}")

# Test multistart solving
solution2, report2 = solver.solve_auto(multistart=True)
print(f"Multistart result: exit_flag={report2['exit_flag']}")
```

## 4. Run Examples

All examples work in Jupyter notebooks:

```bash
# Start Jupyter (if not already running)
jupyter notebook

# Then open and run:
# - examples/carbonate_speciation.ipynb
# - examples/circle_and_line.ipynb
# - examples/predator_prey_dynamics.ipynb
```

## Expected Results

If everything is working correctly, you should see:
- ✅ All imports successful
- ✅ Basic solver functionality working
- ✅ Enhanced features (auto-guess, multistart) working
- ✅ Test suite passing (if pytest is available)

## Troubleshooting

If you encounter issues:

1. **Import errors**: Check that you're in the correct directory
2. **Missing dependencies**: Install required packages:
   ```bash
   pip install numpy pandas sympy scipy
   pip install pytest pytest-cov pytest-mock pytest-benchmark  # For testing
   ```
3. **Path issues**: Make sure you're running from the project root directory

## What This Tells Us

Running these manual tests will help determine:
- Whether the enhanced TextToSolver functionality works correctly
- If the comprehensive test suite we created is functional
- Whether there are any remaining issues with the restored code
- The overall health of the project after all our enhancements
