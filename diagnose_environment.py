#!/usr/bin/env python3
"""
Environment Diagnostic Script
"""
import os
import sys
import subprocess
import platform

print("=== Environment Diagnostic ===")
print(f"Platform: {platform.platform()}")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current working directory: {os.getcwd()}")
print(f"PATH: {os.environ.get('PATH', 'Not set')}")
print(f"SHELL: {os.environ.get('SHELL', 'Not set')}")
print(f"USER: {os.environ.get('USER', 'Not set')}")

print("\n=== Python Path ===")
for path in sys.path:
    print(f"  {path}")

print("\n=== Environment Variables ===")
for key in sorted(os.environ.keys()):
    if key in ['PATH', 'PYTHONPATH', 'SHELL', 'TERM', 'USER', 'HOME', 'PWD']:
        print(f"  {key}: {os.environ[key]}")

print("\n=== Testing subprocess ===")
try:
    result = subprocess.run(['echo', 'test'], capture_output=True, text=True, timeout=5)
    print(f"  Echo test: {result.stdout.strip()}")
    print(f"  Return code: {result.returncode}")
except Exception as e:
    print(f"  Subprocess error: {e}")

print("\n=== Testing TextToSolver Import ===")
try:
    sys.path.insert(0, '/Users/colin.mcneece@cognitedata.com/personal/text_to_solver')
    from text_to_solver.TextToSolver import TextToSolver, SolverOptions
    print("  ✅ TextToSolver import successful")
    
    # Test basic functionality
    solver = TextToSolver(['x'], ['x - 1'])
    print("  ✅ TextToSolver instantiation successful")
    
    solution, report = solver.solve_auto()
    print(f"  ✅ solve_auto successful: x = {solution['x'][0]:.6f}")
    
except Exception as e:
    print(f"  ❌ TextToSolver error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Testing pytest availability ===")
try:
    import pytest
    print(f"  ✅ pytest version: {pytest.__version__}")
except ImportError as e:
    print(f"  ❌ pytest not available: {e}")

print("\n=== File system check ===")
test_paths = [
    '/Users/colin.mcneece@cognitedata.com/personal/text_to_solver',
    '/Users/colin.mcneece@cognitedata.com/personal/text_to_solver/text_to_solver',
    '/Users/colin.mcneece@cognitedata.com/personal/text_to_solver/tests',
    '/Users/colin.mcneece@cognitedata.com/personal/text_to_solver/examples'
]

for path in test_paths:
    if os.path.exists(path):
        print(f"  ✅ {path} exists")
        if os.path.isdir(path):
            try:
                files = os.listdir(path)[:5]  # First 5 files
                print(f"     Contents: {files}")
            except PermissionError:
                print(f"     Permission denied to list contents")
    else:
        print(f"  ❌ {path} does not exist")
