#!/usr/bin/env python3
"""
Minimal Circle and Line Intersection Example

Find where x² + y² = z² intersects with y = 5x for different circle radii.
"""

import sys
import os
# Add src directory to path for imports
# Note: In production, the package should be installed with 'pip install -e .'
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src'))

import numpy as np
import matplotlib.pyplot as plt
from text_to_solver import EquationSolver

print("🎯 Circle and Line Intersection")
print("Problem: x² + y² = z², y = 5x")
print()

# ================================================================
# Basic Single Solution
# ================================================================

print("📍 Single Solution (z=3):")
result = EquationSolver.solve_equations(
    variables=['x', 'y'],
    equations=['x**2 + y**2 = z**2', 'y = 5*x'],
    parameters={'z': 3}
)

if result.success:
    x, y = result['x'], result['y']
    print(f"   x = {x:.3f}, y = {y:.3f}")
    print(f"   Verification: x²+y² = {x**2 + y**2:.3f}, z² = 9")
    print(f"   Constraint: y/x = {y/x:.3f} (should be 5)")
else:
    print("   ❌ Failed to converge")

# ================================================================
# Parameter Sweep
# ================================================================

print("\n📊 Parameter Sweep (multiple radii):")
solver = (EquationSolver()
          .set_system(['x', 'y'], ['x**2 + y**2 = z**2', 'y = 5*x'])
          .tolerance(1e-8))

radii = [1, 2, 3, 4, 5]
results = solver.parameter_sweep('z', radii)

successful = [r for r in results if r.success]
print(f"   Solved {len(successful)}/{len(radii)} cases successfully")

for i, result in enumerate(results):
    if result.success:
        x, y = result['x'], result['y']
        print(f"   z={radii[i]}: x={x:.3f}, y={y:.3f}")

# ================================================================
# Simple Visualization
# ================================================================

if len(successful) > 0:
    print("\n📊 Creating plot...")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot 1: Geometric view for z=3
    theta = np.linspace(0, 2*np.pi, 100)
    z_val = 3
    
    # Circle
    x_circle = z_val * np.cos(theta)
    y_circle = z_val * np.sin(theta)
    ax1.plot(x_circle, y_circle, 'b-', label=f'Circle: x² + y² = {z_val}²', linewidth=2)
    
    # Line
    x_line = np.linspace(-4, 4, 100)
    y_line = 5 * x_line
    ax1.plot(x_line, y_line, 'g-', label='Line: y = 5x', linewidth=2)
    
    # Intersection points
    if results[2].success:  # z=3 case
        x_int, y_int = results[2]['x'], results[2]['y']
        ax1.plot([x_int, -x_int], [y_int, -y_int], 'ro', markersize=8, label='Intersections')
    
    ax1.set_xlim([-4, 4])
    ax1.set_ylim([-4, 4])
    ax1.set_aspect('equal')
    ax1.set_xlabel('x')
    ax1.set_ylabel('y')
    ax1.set_title('Circle-Line Intersection')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Solution coordinates vs radius
    z_success = [radii[i] for i, r in enumerate(results) if r.success]
    x_coords = [r['x'] for r in results if r.success]
    y_coords = [r['y'] for r in results if r.success]
    
    ax2.plot(z_success, x_coords, 'bo-', label='x-coordinate', linewidth=2, markersize=6)
    ax2.plot(z_success, y_coords, 'ro-', label='y-coordinate', linewidth=2, markersize=6)
    ax2.set_xlabel('Circle Radius (z)')
    ax2.set_ylabel('Intersection Coordinates')
    ax2.set_title('Solution vs Radius')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('circle_and_line_output.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print("✅ Plot saved as 'circle_and_line_output.png'")

print("\n✨ Example complete!")
print("This demonstrates basic EquationSolver functionality:")
print("• Natural equation syntax with '=' signs")
print("• Single solution and parameter sweeps")
print("• Automatic convergence and verification")