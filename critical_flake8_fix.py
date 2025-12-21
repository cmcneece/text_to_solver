#!/usr/bin/env python3
"""
Critical flake8 fixer - targets the most impactful issues safely.
Focuses on errors that cause "red" without breaking syntax.
"""

import re
import os

def fix_critical_flake8_issues(file_path: str) -> None:
    """Fix the most critical flake8 issues safely."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    
    for i, line in enumerate(lines):
        original_line = line
        
        # 1. Remove trailing whitespace (always safe)
        line = line.rstrip() + '\n'
        
        # 2. Fix f-strings without placeholders (safe when no braces)
        if 'f"' in line and '{' not in line and '}' not in line:
            line = line.replace('f"', '"')
        if "f'" in line and '{' not in line and '}' not in line:
            line = line.replace("f'", "'")
        
        # 3. Fix module level import positioning (move to top)
        # Skip this for now to avoid breaking things
        
        # 4. Fix continuation line indentation for simple cases
        if (i > 0 and 
            line.strip() and 
            lines[i-1].strip().endswith((',', '(', '[')) and
            not line.lstrip().startswith((')', ']', '}'))):
            
            # Ensure continuation lines are properly indented
            stripped = line.lstrip()
            if len(line) - len(stripped) < 4:  # Under-indented
                prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
                line = ' ' * (prev_indent + 4) + stripped
        
        # 5. Fix overly long lines (only very safe cases)
        if len(line) > 100:  # Only fix extremely long lines
            # Safe patterns to break on
            if ', ' in line and line.count('"') % 2 == 0:
                # Find good break point (after comma, before 80 chars)
                for pos in range(75, min(85, len(line))):
                    if line[pos:pos+2] == ', ':
                        indent = len(line) - len(line.lstrip())
                        first_part = line[:pos+1].rstrip() + '\n'
                        second_part = ' ' * (indent + 4) + line[pos+2:].lstrip()
                        fixed_lines.append(first_part)
                        fixed_lines.append(second_part)
                        continue
        
        # If we get here, use the processed line
        if line.strip() == '':
            fixed_lines.append('\n')  # Clean blank lines
        else:
            fixed_lines.append(line)
    
    # Ensure file ends with newline
    if fixed_lines and not fixed_lines[-1].endswith('\n'):
        fixed_lines[-1] += '\n'
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)

def fix_imports_positioning(file_path: str) -> None:
    """Move module level imports to the top (safe version)."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Find imports that are not at module level
    module_imports = []
    other_lines = []
    imports_moved = False
    
    # Look for obvious module level imports in wrong places
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip if inside function/class (rough heuristic)
        if any(lines[j].strip().startswith(('def ', 'class ')) 
               for j in range(max(0, i-10), i)):
            other_lines.append(line)
            continue
        
        # Check if this is a misplaced import
        if (stripped.startswith(('from text_to_solver', 'import numpy', 'import matplotlib')) and
            i > 10):  # Not near the top
            module_imports.append(stripped)
            imports_moved = True
            # Replace with comment
            other_lines.append('# Import moved to top')
        else:
            other_lines.append(line)
    
    if imports_moved:
        # Find where to insert imports (after existing imports)
        insert_pos = 0
        for i, line in enumerate(other_lines):
            if line.strip().startswith(('import ', 'from ')) and i < 50:
                insert_pos = i + 1
        
        # Insert the moved imports
        for imp in module_imports:
            other_lines.insert(insert_pos, imp)
            insert_pos += 1
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(other_lines))

def main():
    """Apply critical flake8 fixes."""
    files_to_fix = [
        'text_to_solver/TextToSolver.py',
        'examples/predator_prey_dynamics.py',
        'examples/comprehensive_advanced_showcase.py'
    ]
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            print(f"🎯 Critical fixes for {file_path}...")
            fix_critical_flake8_issues(file_path)
            # Skip import positioning for now to avoid breaking things
            # fix_imports_positioning(file_path)
            print(f"✅ Applied critical fixes to {file_path}")
            
            # Verify it still compiles
            result = os.system(f'python3 -m py_compile {file_path} 2>/dev/null')
            if result == 0:
                print(f"✅ {file_path} still compiles correctly")
            else:
                print(f"⚠️ {file_path} may have compilation issues")

if __name__ == "__main__":
    main()
