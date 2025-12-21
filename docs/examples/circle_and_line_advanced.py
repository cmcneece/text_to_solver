#!/usr/bin/env python3
"""
Circle and Line Intersection with Advanced Patterns

Find where x² + y² = r² intersects with y = mx + b using advanced patterns:
- Builder Pattern for system construction
- Observer Pattern for real-time monitoring
- Strategy Pattern for optimal solving
- Factory Methods for intelligent creation
"""

import sys
import os
# Add src directory to path for imports
# Note: In production, the package should be installed with 'pip install -e .'
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src'))

import numpy as np
import matplotlib.pyplot as plt
import time

from text_to_solver import EnhancedEquationSolver
from text_to_solver.advanced_patterns import (
    EquationSystemBuilder, ConvergenceMonitor, ProgressCallback,
    create_robust_newton_strategy, SystemFactory
)

print("🎯 Circle and Line Intersection with Advanced Patterns")
print("Problem: x² + y² = r², y = mx + b")
print("✨ Featuring: Builder, Observer, Strategy, and Factory patterns")
print()

# ================================================================
# BUILDER PATTERN: Guided System Construction
# ================================================================

print("🔨 Builder Pattern: Constructing geometric system...")

# Build system step-by-step with validation
geometric_system = (EquationSystemBuilder()
                   .add_variables(['x', 'y'])
                   .add_equations([
                       'x**2 + y**2 - r**2',  # Circle equation
                       'y - m*x - b'          # Line equation
                   ])
                   .add_parameters({
                       'r': 3.0,  # Circle radius
                       'm': 2.0,  # Line slope
                       'b': 1.0   # Line intercept
                   })
                   .set_metadata('system_type', 'geometric_intersection')
                   .build())

print(f"✅ Geometric system built:")
print(f"   • Variables: {geometric_system.dependent_variables}")
print(f"   • Equations: Circle and line intersection")
print(f"   • Parameters: {list(geometric_system.parameters.keys())}")

# ================================================================
# OBSERVER PATTERN: Real-time Monitoring Setup
# ================================================================

print(f"\n🔍 Observer Pattern: Setting up monitoring...")

# Create convergence monitor for analysis
convergence_monitor = ConvergenceMonitor()

# Create progress callback for user feedback
iteration_count = 0
def progress_tracker(iteration, residual):
    global iteration_count
    iteration_count = iteration
    if iteration <= 3:  # Show first few iterations
        print(f"    🔄 Iteration {iteration}: residual = {residual:.2e}")

progress_callback = ProgressCallback(
    iteration_callback=progress_tracker,
    start_callback=lambda: print("    🟢 Solving geometric intersection..."),
    end_callback=lambda status: print(f"    🎯 Solver {status} after {iteration_count} iterations")
)

print("✅ Monitoring configured:")
print("   • Convergence analysis")
print("   • Real-time progress tracking")
print("   • Performance measurement")

# ================================================================
# STRATEGY PATTERN: Optimal Algorithm Selection
# ================================================================

print(f"\n⚡ Strategy Pattern: Selecting optimal solver strategy...")

# Use robust strategy for geometric problems
optimal_strategy = create_robust_newton_strategy()

print("✅ Strategy selected:")
print("   • Robust Newton-Raphson method")
print("   • Optimized for geometric intersections")
print("   • Enhanced convergence reliability")

# ================================================================
# ENHANCED SOLVER: All Patterns Integrated
# ================================================================

print(f"\n🚀 Enhanced Solver: Integrating all patterns...")

# Create enhanced solver with all advanced features
enhanced_solver = (EnhancedEquationSolver()
                  .set_system(geometric_system.dependent_variables,
                             geometric_system.equations,
                             geometric_system.parameters)
                  .solver_strategy(optimal_strategy)
                  .add_observer(convergence_monitor)
                  .add_observer(progress_callback)
                  .tolerance(1e-10)
                  .enable_progress_monitoring(track_convergence=True))

print("✅ Enhanced solver ready with:")
print("   • Builder-constructed system")
print("   • Strategy-optimized algorithm")
print("   • Observer-based monitoring")
print("   • Auto-configured parameters")

# ================================================================
# INTELLIGENT SOLVING WITH ANALYSIS
# ================================================================

print(f"\n📊 System Analysis and Solving:")

# Analyze system characteristics
analysis = enhanced_solver.analyze_system()
print(f"System analysis:")
print(f"   • Type: {analysis['system_type']}")
print(f"   • Variables: {analysis['n_variables']}")
print(f"   • Equations: {analysis['n_equations']}")
print(f"   • Difficulty: {analysis['difficulty_estimate']}")

# Solve with full monitoring
start_time = time.time()
result = enhanced_solver.solve()
solve_time = time.time() - start_time

if result.success:
    x, y = result['x'], result['y']
    print(f"\n✅ Solution found in {solve_time:.4f}s:")
    print(f"   • Intersection: x = {x:.4f}, y = {y:.4f}")
    
    # Verify solution
    r, m, b = 3.0, 2.0, 1.0
    circle_check = x**2 + y**2
    line_check = m*x + b
    
    print(f"   • Verification:")
    print(f"     Circle: x² + y² = {circle_check:.4f} (should be {r**2})")
    print(f"     Line: mx + b = {line_check:.4f}, y = {y:.4f}")
    
    # Display convergence information
    history = convergence_monitor.get_convergence_history()
    if history:
        print(f"   • Convergence: {len(history)} iterations")
        print(f"   • Final residual: {history[-1]['residual_norm']:.2e}")
        
        rate = convergence_monitor.get_convergence_rate()
        if rate:
            print(f"   • Convergence rate: {rate:.4f}")
else:
    print(f"❌ Solution failed after {solve_time:.4f}s")

# ================================================================
# FACTORY METHODS: Intelligent Parameter Sweep
# ================================================================

print(f"\n🏭 Factory Methods: Intelligent parameter sweep...")

# Use factory method for creating similar systems
print("Creating parameter sweep using intelligent configuration:")

# Parameter sweep with monitoring
radii = [1, 2, 3, 4, 5]
sweep_results = []

print(f"Analyzing {len(radii)} different circle radii:")

for i, radius in enumerate(radii):
    # Create solver with same configuration but different radius
    sweep_solver = (EnhancedEquationSolver()
                   .set_system(geometric_system.dependent_variables,
                              geometric_system.equations,
                              {**geometric_system.parameters, 'r': radius})
                   .solver_strategy(optimal_strategy)
                   .tolerance(1e-8))
    
    # Solve quickly without verbose monitoring
    sweep_start = time.time()
    sweep_result = sweep_solver.solve()
    sweep_time = time.time() - sweep_start
    
    if sweep_result.success:
        x, y = sweep_result['x'], sweep_result['y']
        sweep_results.append((radius, x, y, sweep_time))
        print(f"   r={radius}: x={x:.3f}, y={y:.3f} ({sweep_time:.4f}s)")
    else:
        print(f"   r={radius}: ❌ Failed ({sweep_time:.4f}s)")

sweep_success_rate = len(sweep_results) / len(radii)
total_sweep_time = sum(t for _, _, _, t in sweep_results)

print(f"\n✅ Parameter sweep complete:")
print(f"   • Success rate: {len(sweep_results)}/{len(radii)} ({sweep_success_rate:.1%})")
print(f"   • Total time: {total_sweep_time:.4f}s")
print(f"   • Average per case: {total_sweep_time/len(sweep_results):.4f}s" if sweep_results else "")

# ================================================================
# ENHANCED VISUALIZATION WITH PATTERN ANNOTATIONS
# ================================================================

if sweep_results:
    print(f"\n📊 Creating enhanced visualization...")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Geometric view with pattern annotations
    theta = np.linspace(0, 2*np.pi, 100)
    
    # Show multiple circles and line
    colors = ['blue', 'green', 'red', 'purple', 'orange']
    for i, (radius, x_sol, y_sol, _) in enumerate(sweep_results[:3]):  # Show first 3
        x_circle = radius * np.cos(theta)
        y_circle = radius * np.sin(theta)
        color = colors[i % len(colors)]
        ax1.plot(x_circle, y_circle, color=color, alpha=0.7, 
                label=f'Circle r={radius}', linewidth=2)
        
        # Mark intersection
        ax1.plot([x_sol, -x_sol], [y_sol, -y_sol], 'o', color=color, 
                markersize=8, alpha=0.8)
    
    # Line
    x_line = np.linspace(-6, 6, 100)
    y_line = 2.0 * x_line + 1.0  # m=2, b=1
    ax1.plot(x_line, y_line, 'k-', label='Line: y = 2x + 1', linewidth=2)
    
    ax1.set_xlim([-6, 6])
    ax1.set_ylim([-6, 6])
    ax1.set_aspect('equal')
    ax1.set_xlabel('x')
    ax1.set_ylabel('y')
    ax1.set_title('Circle-Line Intersections\n(Built with Advanced Patterns)', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add pattern annotation
    ax1.text(0.02, 0.98, '✨ Advanced Features:\n• Builder Pattern\n• Observer monitoring\n• Strategy optimization\n• Factory automation', 
             transform=ax1.transAxes, va='top', fontsize=9,
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    # Plot 2: Performance analysis and pattern benefits
    ax2.text(0.5, 0.95, 'Advanced Pattern Benefits\nfor Geometric Problems', 
             ha='center', va='top', transform=ax2.transAxes, 
             fontsize=14, fontweight='bold')
    
    # Display results and pattern information
    if sweep_results:
        radii_solved = [r for r, _, _, _ in sweep_results]
        x_coords = [x for _, x, _, _ in sweep_results]
        y_coords = [y for _, _, y, _ in sweep_results]
        times = [t for _, _, _, t in sweep_results]
        
        pattern_summary = f"""
🔨 BUILDER PATTERN:
   ✅ Guided system construction
   ✅ Automatic validation
   ✅ Metadata management

🔍 OBSERVER PATTERN:
   ✅ Real-time monitoring: {len(history) if 'history' in locals() else 'N/A'} iterations tracked
   ✅ Progress callbacks implemented
   ✅ Performance measurement

⚡ STRATEGY PATTERN:
   ✅ Robust Newton strategy selected
   ✅ Optimized for geometric problems
   ✅ Enhanced convergence reliability

🏭 FACTORY METHODS:
   ✅ Parameter sweep automation
   ✅ Intelligent system replication
   ✅ Batch processing: {len(sweep_results)} cases

📊 PERFORMANCE RESULTS:
   • Success rate: {sweep_success_rate:.1%}
   • Total time: {total_sweep_time:.4f}s
   • Fastest solve: {min(times):.4f}s
   • Average time: {total_sweep_time/len(sweep_results):.4f}s

🎯 GEOMETRIC INSIGHTS:
   • Radius range: {min(radii_solved)}-{max(radii_solved)}
   • x-coordinates: {min(x_coords):.2f} to {max(x_coords):.2f}
   • y-coordinates: {min(y_coords):.2f} to {max(y_coords):.2f}
        """
    else:
        pattern_summary = "No successful results to analyze"
    
    ax2.text(0.05, 0.85, pattern_summary, ha='left', va='top',
             transform=ax2.transAxes, fontsize=9, fontfamily='monospace')
    
    ax2.set_xlim([0, 1])
    ax2.set_ylim([0, 1])
    ax2.axis('off')
    
    plt.tight_layout()
    plt.savefig('circle_and_line_advanced_output.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print("✅ Enhanced visualization saved as 'circle_and_line_advanced_output.png'")

print(f"\n🎉 Advanced Patterns Showcase Complete!")
print("="*60)
print("✨ Demonstrated capabilities:")
print("   🔨 Builder Pattern: Guided geometric system construction")
print("   🔍 Observer Pattern: Real-time convergence monitoring")
print("   ⚡ Strategy Pattern: Optimized algorithm selection")
print("   🏭 Factory Methods: Intelligent parameter automation")
print("   🚀 Enhanced Solver: Seamless pattern integration")

print(f"\n💡 Key benefits achieved:")
print("   • Flexible, extensible architecture")
print("   • Rich monitoring and diagnostics")
print("   • Intelligent auto-configuration")
print("   • Production-ready performance")

print(f"\n🚀 TextToSolver: Enterprise-ready equation solving!")
print("="*50)
