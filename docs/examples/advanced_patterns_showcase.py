#!/usr/bin/env python3
"""
Advanced Patterns Showcase

This example demonstrates advanced OOP design patterns in TextToSolver:
- Observer Pattern: Real-time monitoring and event handling
- Strategy Pattern: Pluggable algorithms and customizable solving
- Builder Pattern: Guided system construction with domain expertise
- Factory Methods: Intelligent system creation and templates

The example shows how these patterns make TextToSolver flexible, extensible,
and powerful while maintaining ease of use.
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add src directory to path for imports
# Note: In production, the package should be installed with 'pip install -e .'
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src'))

# Import the enhanced solver and patterns
from text_to_solver.enhanced_solver import EnhancedEquationSolver, create_monitored_solver, create_chemical_solver
from text_to_solver.advanced_patterns.observers import ConvergenceMonitor, ProgressCallback, EventLogger
from text_to_solver.advanced_patterns.strategies import create_robust_newton_strategy, create_fast_newton_strategy
from text_to_solver.advanced_patterns.builders import ChemicalSystemBuilder, EquationSystemBuilder
from text_to_solver.advanced_patterns.factories import SystemFactory, ChemicalFactory

print("🚀 Advanced Patterns Showcase")
print("=" * 45)

# ================================================================
# 1. Observer Pattern: Real-time Monitoring
# ================================================================
print("\n🔍 OBSERVER PATTERN: Real-time Monitoring")
print("-" * 40)

print("Creating solver with comprehensive monitoring...")

# Create convergence monitor and progress callback
convergence_monitor = ConvergenceMonitor()
progress_callback = ProgressCallback(
    iteration_callback=lambda i, r: print(f"    Iteration {i}: residual = {r:.2e}"),
    start_callback=lambda: print("    🟢 Solver started"),
    end_callback=lambda status: print(f"    🎯 Solver {status}")
)

# Create enhanced solver with monitoring
solver = (EnhancedEquationSolver()
          .set_system(['x', 'y'], ['x**2 + y**2 - 25', 'y - 2*x + 1'])
          .add_observer(convergence_monitor)
          .add_observer(progress_callback)
          .tolerance(1e-10))

print("\nSolving circle-line intersection with monitoring:")
result = solver.solve()

if result.success:
    print(f"✅ Solution: x = {result['x']:.6f}, y = {result['y']:.6f}")
    
    # Display convergence analysis
    history = convergence_monitor.get_convergence_history()
    if history:
        print(f"📊 Convergence Summary:")
        print(f"    Iterations: {len(history)}")
        print(f"    Final residual: {history[-1]['residual_norm']:.2e}")
        print(f"    Total time: {convergence_monitor.total_time:.4f}s")
        
        rate = convergence_monitor.get_convergence_rate()
        if rate:
            print(f"    Convergence rate: {rate:.4f}")
else:
    print("❌ Solver failed to converge")

# ================================================================
# 2. Strategy Pattern: Pluggable Algorithms
# ================================================================
print("\n⚡ STRATEGY PATTERN: Pluggable Algorithms")
print("-" * 40)

print("Comparing different solver strategies on the same problem...")

# Define a challenging nonlinear system
equations = [
    'exp(x) + sin(y) - 2.5',
    'x**2 + y**2 - 4'
]
variables = ['x', 'y']

strategies = {
    'Fast Newton': create_fast_newton_strategy(),
    'Robust Newton': create_robust_newton_strategy(),
}

results = {}
for strategy_name, strategy in strategies.items():
    print(f"\n🔧 Testing {strategy_name} Strategy:")
    
    solver = (EnhancedEquationSolver()
              .set_system(variables, equations)
              .solver_strategy(strategy)
              .tolerance(1e-8)
              .enable_progress_monitoring(show_progress=False, track_convergence=True))
    
    try:
        result = solver.solve()
        conv_history = solver.get_convergence_history() or []
        
        results[strategy_name] = {
            'success': result.success,
            'iterations': len(conv_history),
            'final_residual': conv_history[-1]['residual_norm'] if conv_history else float('inf'),
            'solution': (result['x'], result['y']) if result.success else None
        }
        
        if result.success:
            print(f"    ✅ Converged in {len(conv_history)} iterations")
            print(f"    📍 Solution: x = {result['x']:.6f}, y = {result['y']:.6f}")
        else:
            print(f"    ❌ Failed to converge")
            
    except Exception as e:
        print(f"    ❌ Strategy failed: {e}")
        results[strategy_name] = {'success': False, 'error': str(e)}

# ================================================================
# 3. Builder Pattern: Guided System Construction
# ================================================================
print("\n🔨 BUILDER PATTERN: Guided System Construction")
print("-" * 40)

print("Building a complex chemical equilibrium system step-by-step...")

# Build carbonate system using the builder pattern
chemical_builder = ChemicalSystemBuilder()

carbonate_system = (chemical_builder
                    .reset()
                    .add_species(['H2CO3', 'HCO3-', 'CO3-2', 'H+', 'OH-'])
                    .add_equilibrium('H2CO3 <-> HCO3- + H+', 10**(-6.35))
                    .add_equilibrium('HCO3- <-> CO3-2 + H+', 10**(-10.33))  
                    .add_water_autoionization()
                    .add_mass_balance('carbon', ['H2CO3', 'HCO3-', 'CO3-2'], 1e-3)
                    .set_conditions(pH=8.1, temperature=25.0)
                    .build())

print(f"🧪 Chemical System Built:")
print(f"    Variables: {len(carbonate_system.dependent_variables)}")
print(f"    Equations: {len(carbonate_system.equations)}")
print(f"    Parameters: {len(carbonate_system.parameters)}")

# Build a mechanical system using general builder
print("\nBuilding a mechanical system (spring-mass dynamics)...")

mechanical_builder = EquationSystemBuilder()

spring_system = (mechanical_builder
                 .reset()
                 .add_variables(['x1', 'x2', 'v1', 'v2'])
                 .add_equation('v1', 'Velocity of mass 1')
                 .add_equation('v2', 'Velocity of mass 2')  
                 .add_equation('-k1*x1 + k2*(x2-x1) - c1*v1', 'Force on mass 1')
                 .add_equation('-k2*(x2-x1) - c2*v2', 'Force on mass 2')
                 .add_parameters({
                     'k1': 100.0,  # Spring constant 1
                     'k2': 50.0,   # Spring constant 2
                     'c1': 2.0,    # Damping coefficient 1
                     'c2': 1.0     # Damping coefficient 2
                 })
                 .set_metadata('system_type', 'mechanical_dynamics')
                 .build())

print(f"🔧 Mechanical System Built:")
print(f"    Variables: {spring_system.dependent_variables}")
print(f"    System type: {getattr(spring_system, '_metadata', {}).get('system_type', 'unknown')}")

# ================================================================
# 4. Factory Methods: Intelligent System Creation
# ================================================================
print("\n🏭 FACTORY METHODS: Intelligent System Creation")
print("-" * 40)

print("Creating systems using intelligent factories...")

# Pattern-based creation
print("\n📐 Creating geometric system from pattern:")
circle_line_system = SystemFactory.from_pattern(
    'circle_line',
    radius=5,
    slope=1.5,
    intercept=2
)

solver = EnhancedEquationSolver().set_system(
    circle_line_system.dependent_variables,
    circle_line_system.equations,
    circle_line_system.parameters
)

result = solver.solve()
if result.success:
    print(f"    ✅ Circle-line intersection: x = {result['x']:.4f}, y = {result['y']:.4f}")

# Smart equation detection
print("\n🤖 Auto-detecting system patterns:")
equations_to_analyze = [
    ['2*x + 3*y - 7', 'x - y - 1'],  # Linear
    ['x**2 + y**2 - 9', 'y - x + 2'],  # Geometric
    ['pH2CO3 + log10(alpha) - pCO2', 'pH2CO3 - pH - pHCO3 + pK1']  # Chemical
]

for i, equations in enumerate(equations_to_analyze):
    system = SystemFactory.from_equations(equations, auto_detect=True)
    
    if hasattr(system, '_detected_patterns'):
        patterns = [k for k, v in system._detected_patterns.items() if v]
        print(f"    System {i+1}: Detected patterns: {patterns}")
    else:
        print(f"    System {i+1}: Pattern detection not available")

# Chemical factory shortcuts
print("\n🧪 Chemical system factory shortcuts:")

# Acid-base system
acid_system_solver = EnhancedEquationSolver.create_acid_base_system(
    pKa=4.75,  # Acetic acid
    pH=5.0,
    total_concentration=0.01
)

print(f"    🟢 Acid-base system created with {len(acid_system_solver._system.dependent_variables)} variables")

# Carbonate system
carbonate_solver = EnhancedEquationSolver.create_carbonate_system(
    pH=8.1,
    total_co2=2.3e-3,  # Typical seawater
    temperature=25.0
)

print(f"    🌊 Carbonate system created for seawater conditions")

# ================================================================
# 5. Integration Showcase: All Patterns Working Together
# ================================================================
print("\n🎯 INTEGRATION SHOWCASE: All Patterns Together")
print("-" * 40)

print("Demonstrating all patterns working together for optimal solving...")

# Create a challenging chemical system using the builder
complex_builder = ChemicalSystemBuilder()

# Build a complex phosphate system (triprotic acid)
phosphate_system = (complex_builder
                    .reset()
                    .add_species(['H3PO4', 'H2PO4-', 'HPO4-2', 'PO4-3', 'H+', 'OH-'])
                    .add_equilibrium('H3PO4 <-> H2PO4- + H+', 10**(-2.12))   # pKa1
                    .add_equilibrium('H2PO4- <-> HPO4-2 + H+', 10**(-7.21))  # pKa2
                    .add_equilibrium('HPO4-2 <-> PO4-3 + H+', 10**(-12.32))  # pKa3
                    .add_water_autoionization()
                    .add_mass_balance('phosphate', ['H3PO4', 'H2PO4-', 'HPO4-2', 'PO4-3'], 1e-3)
                    .set_conditions(pH=7.4)  # Physiological pH
                    .build())

# Create enhanced solver with full monitoring and auto-configuration
enhanced_solver = (EnhancedEquationSolver()
                   .set_system(
                       phosphate_system.dependent_variables,
                       phosphate_system.equations,
                       phosphate_system.parameters
                   )
                   .enable_progress_monitoring(show_progress=True, track_convergence=True)
                   .auto_configure())

print(f"\n🧬 Solving complex phosphate system (pH 7.4):")
print(f"    System complexity: {len(phosphate_system.dependent_variables)} variables, {len(phosphate_system.equations)} equations")

# Get system analysis
analysis = enhanced_solver.analyze_system()
print(f"    Detected type: {analysis['system_type']}")
print(f"    Difficulty: {analysis['difficulty_estimate']}")
print(f"    Recommended strategy: {analysis['recommended_strategy']}")

# Solve with full pattern integration
result = enhanced_solver.solve()

if result.success:
    print(f"    ✅ Solution converged successfully!")
    
    # Display key chemical concentrations
    print(f"    📊 Key Results:")
    for var in ['pH3PO4', 'pH2PO4', 'pHPO4', 'pPO4']:
        if var in result.variables:
            p_value = result[var]
            concentration = 10**(-p_value)
            print(f"        {var}: {p_value:.3f} (concentration: {concentration:.2e} M)")
    
    # Show convergence analysis
    history = enhanced_solver.get_convergence_history()
    if history:
        print(f"    ⏱️  Convergence: {len(history)} iterations in {enhanced_solver._convergence_monitor.total_time:.3f}s")
        
        # Plot convergence if possible
        try:
            enhanced_solver.plot_convergence()
            print(f"    📈 Convergence plot displayed")
        except:
            print(f"    📈 Convergence plot not available (matplotlib needed)")
else:
    print(f"    ❌ Solution failed to converge")

# ================================================================
# 6. Performance and Flexibility Benefits
# ================================================================
print("\n📈 PERFORMANCE & FLEXIBILITY BENEFITS")
print("-" * 40)

print("Demonstrating the benefits of the advanced patterns:")

benefits = [
    "🔍 Real-time monitoring: Track solver progress and diagnose issues",
    "⚡ Pluggable algorithms: Choose optimal strategy for each problem",  
    "🔨 Guided construction: Build complex systems with validation",
    "🏭 Intelligent creation: Auto-detect patterns and apply best practices",
    "🎯 Seamless integration: All patterns work together harmoniously",
    "📊 Rich diagnostics: Analyze system characteristics and performance",
    "🔧 Easy customization: Extend functionality without breaking existing code"
]

for benefit in benefits:
    print(f"    {benefit}")

print("\n✨ Advanced Patterns Demonstration Complete!")
print("=" * 60)
print("TextToSolver now features advanced OOP design patterns that provide:")
print("• Maximum flexibility through pluggable components")
print("• Enhanced monitoring and diagnostics capabilities")  
print("• Domain-specific knowledge and intelligent defaults")
print("• Seamless integration with core equation solving functionality")
print("• Production-ready architecture for complex problems")

print("\n🚀 Ready for production use!")
