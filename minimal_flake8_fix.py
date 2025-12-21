#!/usr/bin/env python3
"""
Ultra-safe flake8 fixer - only the most conservative changes.
"""

import re
import os

def minimal_flake8_fix(file_path: str) -> None:
    """Apply only the absolute safest flake8 fixes."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    
    for line in lines:
        # 1. Remove trailing whitespace (100% safe)
        cleaned_line = line.rstrip()
        
        # 2. Fix f-strings without placeholders (safe when no braces)
        if 'f"' in cleaned_line and '{' not in cleaned_line and '}' not in cleaned_line:
            cleaned_line = cleaned_line.replace('f"', '"')
        if "f'" in cleaned_line and '{' not in cleaned_line and '}' not in cleaned_line:
            cleaned_line = cleaned_line.replace("f'", "'")
        
        # 3. Clean blank lines (safe)
        if cleaned_line == '':
            fixed_lines.append('\n')
        else:
            fixed_lines.append(cleaned_line + '\n')
    
    # 4. Ensure file ends with newline
    if fixed_lines and not fixed_lines[-1].endswith('\n'):
        fixed_lines[-1] += '\n'
    elif not fixed_lines:
        fixed_lines = ['\n']
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)

def main():
    """Apply minimal safe fixes."""
    files = [
        'text_to_solver/TextToSolver.py',
        'examples/predator_prey_dynamics.py', 
        'examples/comprehensive_advanced_showcase.py'
    ]
    
    for file_path in files:
        if os.path.exists(file_path):
            print(f"🔧 Minimal fix: {file_path}")
            minimal_flake8_fix(file_path)
            
            # Test compilation
            result = os.system(f'python3 -m py_compile {file_path} 2>/dev/null')
            if result == 0:
                print(f"✅ {file_path} - safe fixes applied, still compiles")
            else:
                print(f"❌ {file_path} - compilation issue!")

if __name__ == "__main__":
    main()
