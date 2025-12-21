#!/usr/bin/env python3
"""
Conservative flake8 fixer - only fixes safe issues without breaking syntax.
"""

import re
import os

def conservative_fix_file(file_path: str) -> None:
    """Apply only the safest flake8 fixes."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    
    for line in lines:
        original_line = line
        
        # 1. Remove trailing whitespace (always safe)
        line = line.rstrip() + '\n'
        
        # 2. Fix f-strings without placeholders (safe replacements)
        # f"text" -> "text" when no {} present
        if 'f"' in line and '{' not in line:
            line = line.replace('f"', '"')
        if "f'" in line and '{' not in line:
            line = line.replace("f'", "'")
            
        # 3. Only fix VERY obvious line length issues - simple cases
        if len(line) > 85:  # Only fix really long lines
            # Only fix lines with clear break points and no complex syntax
            if ', ' in line and '(' in line and ')' in line and len(line) < 120:
                # Simple parameter lists 
                if line.count('"') % 2 == 0 and line.count("'") % 2 == 0:
                    # Safe to break - even number of quotes
                    comma_pos = line.rfind(', ', 0, 75)
                    if comma_pos > 40:  # Reasonable break point
                        indent = len(line) - len(line.lstrip())
                        first_part = line[:comma_pos + 1].rstrip() + '\n'
                        second_part = ' ' * (indent + 4) + line[comma_pos + 2:].lstrip()
                        fixed_lines.append(first_part)
                        fixed_lines.append(second_part)
                        continue
        
        fixed_lines.append(line)
    
    # 4. Remove blank lines with only whitespace  
    final_lines = []
    for line in fixed_lines:
        if line.strip() == '':
            final_lines.append('\n')
        else:
            final_lines.append(line)
    
    # 5. Ensure file ends with newline
    if final_lines and not final_lines[-1].endswith('\n'):
        final_lines[-1] += '\n'
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(final_lines)

def main():
    """Apply conservative fixes."""
    files_to_fix = [
        'examples/predator_prey_dynamics.py',
        'examples/comprehensive_advanced_showcase.py'
    ]
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            print(f"🔧 Conservative fix for {file_path}...")
            conservative_fix_file(file_path)
            print(f"✅ Applied conservative fixes to {file_path}")

if __name__ == "__main__":
    main()
