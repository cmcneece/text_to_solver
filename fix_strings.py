#!/usr/bin/env python3
"""
Fix all broken strings in Python files.
"""

import re

def fix_broken_strings(file_path: str) -> None:
    """Fix broken strings across lines."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line has an unclosed string
        if ('print(' in line and 
            (('"' in line and line.count('"') % 2 != 0) or
             ("'" in line and line.count("'") % 2 != 0))):
            
            # Look for the continuation on the next line
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                
                # If next line looks like a continuation, merge them
                if (next_line.strip() and 
                    not next_line.strip().startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'except', 'else:', 'elif '))):
                    
                    # Extract the indentation
                    indent = len(line) - len(line.lstrip())
                    next_indent = len(next_line) - len(next_line.lstrip())
                    
                    if next_indent > indent:  # It's indented more, likely a continuation
                        # Merge the lines properly
                        if line.rstrip().endswith(','):
                            # Already has comma
                            fixed_line = line.rstrip() + ' '
                        elif '"' in line and '"' not in line[-10:]:
                            # String needs to be closed and reopened
                            fixed_line = line.rstrip() + ' " '
                        else:
                            fixed_line = line.rstrip() + ' '
                        
                        # Add f-string continuation
                        continuation = next_line.strip()
                        if continuation.startswith('"') or continuation.startswith("'"):
                            fixed_line += 'f' + continuation
                        else:
                            fixed_line += '"' + continuation + '"'
                        
                        fixed_lines.append(fixed_line)
                        i += 2  # Skip the next line since we merged it
                        continue
        
        fixed_lines.append(line)
        i += 1
    
    # Join and write back
    content = '\n'.join(fixed_lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    """Fix broken strings in the showcase file."""
    file_path = 'examples/comprehensive_advanced_showcase.py'
    print(f"🔧 Fixing broken strings in {file_path}...")
    
    # Simple approach - just fix the most common pattern
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern: print("text\n    more_text")  ->  print("text " "more_text") 
    patterns = [
        (r'print\("([^"]*)\n\s+([^"]*)"', r'print("\1 \2"'),
        (r'print\(f"([^"]*)\n\s+([^"]*)"', r'print(f"\1 \2"'),
        (r'print\("([^"]*):\n\s+\{', r'print(f"\1: {'),  # Fix f-string patterns
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed broken strings in {file_path}")

if __name__ == "__main__":
    main()
