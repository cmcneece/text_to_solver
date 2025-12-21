#!/usr/bin/env python3
"""
Comprehensive flake8 fixer for text_to_solver codebase.
Fixes ALL common flake8 issues to achieve "no red" policy.
"""

import re
import os
from typing import List, Tuple


def fix_line_length(line: str, max_length: int = 79) -> List[str]:
    """Fix long lines by intelligent wrapping."""
    if len(line) <= max_length:
        return [line]
    
    # Get indentation
    stripped = line.lstrip()
    indent = line[:len(line) - len(stripped)]
    
    # Special cases for different line types
    
    # 1. Long imports
    if 'from ' in stripped and 'import' in stripped and '(' not in stripped:
        if ', ' in stripped:
            parts = stripped.split('import ')
            if len(parts) == 2:
                from_part = parts[0] + 'import ('
                imports = [imp.strip() for imp in parts[1].split(',')]
                result = [indent + from_part]
                for i, imp in enumerate(imports):
                    comma = ',' if i < len(imports) - 1 else ''
                    result.append(indent + '    ' + imp + comma)
                result.append(indent + ')')
                return result
    
    # 2. Long strings/f-strings with ValidationError
    if 'ValidationError(' in stripped and 'f"' in stripped:
        match = re.match(r'(\s*raise ValidationError\()(.*)', line)
        if match:
            prefix, rest = match.groups()
            return [
                indent + 'raise ValidationError(',
                indent + '    ' + rest
            ]
    
    # 3. Long function definitions
    if 'def ' in stripped and '(' in stripped and ')' in stripped:
        # Break after function name
        func_match = re.match(r'(\s*def\s+\w+\()(.*)', line)
        if func_match and ', ' in func_match.group(2):
            prefix, params = func_match.groups()
            param_list = [p.strip() for p in params.rstrip('):').split(',')]
            result = [indent + prefix.replace('(', '(')]
            for i, param in enumerate(param_list):
                if param:
                    comma = ',' if i < len(param_list) - 1 else ''
                    result.append(indent + '    ' + param + comma)
            if line.rstrip().endswith('):'):
                result.append(indent + ') -> None:')
            elif line.rstrip().endswith(':'):
                result.append(indent + '):')
            return result
    
    # 4. Long conditional statements 
    if ' and ' in stripped or ' or ' in stripped:
        # Break on logical operators
        for op in [' and ', ' or ']:
            if op in stripped:
                parts = stripped.split(op)
                if len(parts) > 1:
                    result = [indent + parts[0] + op.strip()]
                    for part in parts[1:]:
                        result.append(indent + '    ' + part)
                    return result
    
    # 5. Long list/dict comprehensions
    if '[' in stripped and 'for' in stripped and 'in' in stripped:
        # Break list comprehensions
        match = re.match(r'(.+\[)(.+for.+in.+)(\].*)', stripped)
        if match:
            start, middle, end = match.groups()
            return [
                indent + start,
                indent + '    ' + middle,
                indent + end
            ]
    
    # 6. Generic long lines - break at logical points
    # Look for break points: commas, operators
    break_points = [', ', ' + ', ' - ', ' * ', ' / ', ' == ', ' != ', ' and ', ' or ']
    for bp in break_points:
        if bp in stripped:
            pos = stripped.rfind(bp, 0, max_length - len(indent))
            if pos > 0:
                first_part = stripped[:pos + len(bp)]
                second_part = stripped[pos + len(bp):].lstrip()
                return [
                    indent + first_part,
                    indent + '    ' + second_part
                ]
    
    # 7. Last resort: break at space
    space_pos = stripped.rfind(' ', 0, max_length - len(indent))
    if space_pos > 0:
        first_part = stripped[:space_pos]
        second_part = stripped[space_pos:].lstrip()
        return [
            indent + first_part,
            indent + '    ' + second_part
        ]
    
    # Can't break - return original
    return [line]


def fix_flake8_issues(file_path: str) -> None:
    """Fix all flake8 issues in a Python file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    
    for line in lines:
        # Remove trailing whitespace
        line = line.rstrip() + '\n'
        
        # Skip empty lines that had whitespace
        if line.strip() == '':
            fixed_lines.append('\n')
            continue
        
        # Fix long lines
        line_fixes = fix_line_length(line.rstrip(), 79)
        for fixed_line in line_fixes:
            fixed_lines.append(fixed_line + '\n')
    
    # Ensure file ends with newline
    if fixed_lines and not fixed_lines[-1].endswith('\n'):
        fixed_lines[-1] += '\n'
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)


def fix_continuation_indentation(file_path: str) -> None:
    """Fix continuation line indentation issues."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a continuation line issue
        if (i > 0 and 
            line.strip() and 
            (line.startswith('    ') or line.startswith('\t')) and
            not lines[i-1].strip().endswith(':')):
            
            # This might be a continuation line
            prev_line = lines[i-1]
            if ('(' in prev_line and ')' not in prev_line) or prev_line.rstrip().endswith((',', '+', '-', '*', '/', '=', 'and', 'or')):
                # Ensure proper indentation for continuation
                stripped = line.lstrip()
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                # Continuation lines should be indented 4 spaces from the base
                new_line = ' ' * (prev_indent + 4) + stripped
                fixed_lines.append(new_line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
        i += 1
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))


def main():
    """Fix flake8 issues in the codebase."""
    files_to_fix = [
        'text_to_solver/TextToSolver.py',
        'examples/predator_prey_dynamics.py', 
        'examples/comprehensive_advanced_showcase.py'
    ]
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            print(f"🔧 Fixing {file_path}...")
            fix_flake8_issues(file_path)
            fix_continuation_indentation(file_path)
            print(f"✅ Fixed {file_path}")
        else:
            print(f"⚠️  File not found: {file_path}")


if __name__ == "__main__":
    main()
