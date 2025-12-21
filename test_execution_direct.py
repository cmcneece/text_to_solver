#!/usr/bin/env python3
"""
Direct test execution using Python subprocess to bypass terminal issues
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Execute tests directly"""
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print("🧪 TextToSolver Test Suite Execution")
    print("=" * 50)
    
    # First, test basic imports
    print("Testing imports...")
    try:
        sys.path.insert(0, str(project_dir))
        from text_to_solver import EquationSolver, TextToSolver
        print("✅ Core imports successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Execute pytest directly
    print("\nRunning pytest...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=short'
        ], capture_output=True, text=True, timeout=300)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")  
            print(result.stderr)
        
        print(f"\nExit code: {result.returncode}")
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
            return True
        else:
            print("\n❌ Some tests failed")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Test execution timed out")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\nFinal result: {'SUCCESS' if success else 'FAILURE'}")
    sys.exit(0 if success else 1)


