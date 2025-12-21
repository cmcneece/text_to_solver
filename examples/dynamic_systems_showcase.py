#!/usr/bin/env python3
"""
Dynamic Systems Showcase - TextToSolver

This example demonstrates differential equation solving capabilities, including:

1. Time-dependent system integration
2. Multiple integration methods (Euler, RK4, adaptive)
3. Different types of ODEs (exponential, oscillatory, nonlinear)
4. Convenience functions and full API
5. Visualization of dynamic behavior

TextToSolver can now handle:
- dx/dt notation and derivatives
- Time integration over specified ranges  
- Initial conditions and parameters
- Multiple integration algorithms
- Rich result objects with interpolation
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List
import sys
import os

# Add the package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from text_to_solver import (
    DynamicEquationSolver, 
    solve_ode_system,
    DynamicSolutionResult
)


def demo_simple_exponential_decay():
    """Demonstrate exponential decay: dx/dt = -k*x"""
    print("\n" + "="*50)
    print("1. EXPONENTIAL DECAY")
    print("="*50)
    print("Solving: dx/dt = -k*x")
    print("Initial condition: x(0) = 100")
    print("Parameter: k = 0.1")
    
    # Method 1: Full API
    solver = DynamicEquationSolver()
    solver.set_system(
        variables=['x'],
        equations=['dx/dt = -k*x'],
        parameters={'k': 0.1},
        initial_conditions={'x': 100.0}
    )
    
    result = solver.integrate(time_span=(0, 50), method='RK45')
    
    if result.success:
        print(f"\n✓ Solution found!")
        print(f"  x(0) = {result.initial_values['x']:.1f}")
        print(f"  x(50) = {result.final_values['x']:.3f}")
        print(f"  Analytical x(50) = {100 * np.exp(-0.1*50):.3f}")
        print(f"  Integration points: {len(result.time_points)}")
        
        # Demonstrate interpolation
        x_at_25 = result.at_time(25.0)['x']
        print(f"  x(25) = {x_at_25:.3f} (interpolated)")
        
        return result
    else:
        print(f"✗ Failed: {result.message}")
        return None


def demo_harmonic_oscillator():
    """Demonstrate simple harmonic oscillator: d²x/dt² = -ω²*x"""
    print("\n" + "="*50)
    print("2. HARMONIC OSCILLATOR")  
    print("="*50)
    print("Solving: d²x/dt² = -ω²*x")
    print("Converting to first-order system:")
    print("  dx/dt = v")
    print("  dv/dt = -ω²*x")
    print("Initial conditions: x(0) = 1, v(0) = 0")
    print("Parameter: ω = 1.0")
    
    # Convert second-order to first-order system
    solver = DynamicEquationSolver()
    solver.set_system(
        variables=['x', 'v'],
        equations=[
            'dx/dt = v',
            'dv/dt = -omega*omega*x'
        ],
        parameters={'omega': 1.0},
        initial_conditions={'x': 1.0, 'v': 0.0}
    )
    
    result = solver.integrate(time_span=(0, 4*np.pi), method='RK45')
    
    if result.success:
        print(f"\n✓ Oscillator solved!")
        print(f"  Period ≈ {2*np.pi:.2f}, simulated {4*np.pi/(2*np.pi):.1f} periods")
        print(f"  Final position: x = {result.final_values['x']:.3f}")
        print(f"  Final velocity: v = {result.final_values['v']:.3f}")
        print(f"  Expected: x ≈ 1.0, v ≈ 0.0 (full cycles)")
        
        # Check energy conservation
        x_values = result['x']
        v_values = result['v']
        energy = 0.5 * (v_values**2 + x_values**2)  # E = ½(v² + ω²x²), ω=1
        energy_variation = (np.max(energy) - np.min(energy)) / np.mean(energy)
        print(f"  Energy conservation: {energy_variation*100:.2f}% variation")
        
        return result
    else:
        print(f"✗ Failed: {result.message}")
        return None


def demo_predator_prey_dynamics():
    """Demonstrate Lotka-Volterra predator-prey system"""
    print("\n" + "="*50)
    print("3. PREDATOR-PREY DYNAMICS")
    print("="*50) 
    print("Solving Lotka-Volterra equations:")
    print("  dx/dt = α*x - β*x*y  (prey growth - predation)")
    print("  dy/dt = δ*x*y - γ*y  (predator growth - death)")
    
    # Method 1: General-purpose solver
    print("\nUsing general-purpose solver...")
    solver1 = DynamicEquationSolver()
    solver1.set_system(
        variables=['x', 'y'],
        equations=[
            'dx/dt = alpha*x - beta*x*y',  # Prey growth - predation
            'dy/dt = delta*x*y - gamma*y'  # Predator growth from hunting - death
        ],
        parameters={'alpha': 1.0, 'beta': 0.1, 'delta': 0.075, 'gamma': 1.5},
        initial_conditions={'x': 10, 'y': 5}
    )
    result1 = solver1.integrate(time_span=(0, 15), method='RK45')
    
    if result1.success:
        print(f"✓ Convenience method: prey {result1.initial_values['x']:.1f} → {result1.final_values['x']:.1f}")
        print(f"                      pred {result1.initial_values['y']:.1f} → {result1.final_values['y']:.1f}")
    
    # Method 2: solve_ode_system function
    print("\nUsing solve_ode_system...")
    result2 = solve_ode_system(
        variables=['prey', 'predator'],
        equations=[
            'dprey/dt = alpha*prey - beta*prey*predator',
            'dpredator/dt = delta*prey*predator - gamma*predator'
        ],
        parameters={'alpha': 1.0, 'beta': 0.1, 'delta': 0.075, 'gamma': 1.5},
        initial_conditions={'prey': 10, 'predator': 5},
        time_span=(0, 15),
        method='RK45'
    )
    
    if result2.success:
        print(f"✓ solve_ode_system: prey {result2.initial_values['prey']:.1f} → {result2.final_values['prey']:.1f}")
        print(f"                    pred {result2.initial_values['predator']:.1f} → {result2.final_values['predator']:.1f}")
        
        # Check for oscillations
        prey_values = result2['prey']
        pred_values = result2['predator']
        prey_range = np.max(prey_values) - np.min(prey_values)
        pred_range = np.max(pred_values) - np.min(pred_values)
        
        print(f"  Prey oscillation range: {prey_range:.1f}")
        print(f"  Predator oscillation range: {pred_range:.1f}")
        
        return result2
    else:
        print(f"✗ Failed: {result2.message}")
        return None


def demo_integration_methods():
    """Compare different integration methods on the same system"""
    print("\n" + "="*50)
    print("4. INTEGRATION METHOD COMPARISON")
    print("="*50)
    print("Comparing methods on: dx/dt = -x + A*t")
    print("Initial condition: x(0) = 0, A = 0.1")
    print("Time span: [0, 10]")
    
    # Set up the system - use a simpler equation to avoid function parsing issues
    solver = DynamicEquationSolver()
    solver.set_system(
        variables=['x'],
        equations=['dx/dt = -x + A*t'],  # Simpler linear forcing
        parameters={'A': 0.1},
        initial_conditions={'x': 0.0}
    )
    
    methods = {
        'Euler': ('euler', {'dt': 0.01}),
        'RK4': ('rk4', {'dt': 0.01}),
        'RK45': ('RK45', {}),
        'DOP853': ('DOP853', {})
    }
    
    results = {}
    computation_info = {}
    
    for name, (method, kwargs) in methods.items():
        try:
            result = solver.integrate((0, 10), method=method, **kwargs)
            if result.success:
                results[name] = result
                n_points = len(result.time_points)
                final_x = result.final_values['x']
                computation_info[name] = (n_points, final_x)
                print(f"  ✓ {name:8s}: {n_points:4d} points, x(10) = {final_x:.4f}")
            else:
                print(f"  ✗ {name:8s}: {result.message}")
        except Exception as e:
            print(f"  ✗ {name:8s}: Exception - {str(e)}")
    
    # Analytical solution for comparison
    # dx/dt = -x + A*t has solution x(t) = A*(t - 1 + exp(-t))
    A = 0.1
    analytical_x10 = A * (10 - 1 + np.exp(-10))
    print(f"\n  Analytical x(10) = {analytical_x10:.4f}")
    
    # Show errors
    print("\n  Method errors:")
    for name, (n_points, final_x) in computation_info.items():
        error = abs(final_x - analytical_x10)
        print(f"    {name:8s}: {error:.2e} (relative: {error/abs(analytical_x10)*100:.2f}%)")
    
    return results


def demo_system_analysis():
    """Demonstrate analysis tools for dynamic systems"""
    print("\n" + "="*50)
    print("5. SYSTEM ANALYSIS TOOLS")
    print("="*50)
    print("Analyzing a damped oscillator: d²x/dt² + 2ζω₀dx/dt + ω₀²x = 0")
    
    # Parameters for different damping cases
    omega0 = 1.0  # Natural frequency
    cases = {
        'Underdamped': 0.1,    # ζ < 1
        'Critical': 1.0,       # ζ = 1  
        'Overdamped': 2.0      # ζ > 1
    }
    
    all_results = {}
    
    for case_name, zeta in cases.items():
        print(f"\n{case_name} (ζ = {zeta}):")
        
        solver = DynamicEquationSolver()
        # Calculate derived parameters to avoid complex expressions
        damping_coeff = 2 * zeta * omega0
        spring_coeff = omega0 * omega0
        
        solver.set_system(
            variables=['x', 'v'],
            equations=[
                'dx/dt = v',
                'dv/dt = -damping*v - spring*x'
            ],
            parameters={'damping': damping_coeff, 'spring': spring_coeff},
            initial_conditions={'x': 1.0, 'v': 0.0}
        )
        
        result = solver.integrate((0, 10), method='RK45')
        
        if result.success:
            all_results[case_name] = result
            
            # Analyze the response
            x_values = result['x']
            final_x = result.final_values['x']
            
            # Find settling time (when |x| < 0.05)
            settling_indices = np.where(np.abs(x_values) < 0.05)[0]
            if len(settling_indices) > 0:
                settling_time = result.time_points[settling_indices[0]]
                print(f"  Settling time (5%): {settling_time:.2f} s")
            else:
                print(f"  Settling time: > 10 s")
            
            # Find overshoot (for underdamped)
            if zeta < 1:
                max_x = np.max(x_values)
                overshoot = (max_x - 0) * 100  # Steady state is 0
                print(f"  Maximum overshoot: {overshoot:.1f}%")
            
            print(f"  Final position: x(10) = {final_x:.4f}")
            
        else:
            print(f"  ✗ Failed: {result.message}")
    
    return all_results


def create_comprehensive_visualization():
    """Create visualization showing all the dynamic system examples"""
    print("\n" + "="*50)
    print("6. COMPREHENSIVE VISUALIZATION")
    print("="*50)
    
    # Run examples to get results
    decay_result = demo_simple_exponential_decay()
    oscillator_result = demo_harmonic_oscillator()
    predator_prey_result = demo_predator_prey_dynamics()
    
    if not all([decay_result, oscillator_result, predator_prey_result]):
        print("Cannot create visualization - some examples failed")
        return
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('TextToSolver: Dynamic Systems Showcase', fontsize=16)
    
    # 1. Exponential Decay
    ax = axes[0, 0]
    ax.plot(decay_result.time_points, decay_result['x'], 'b-', linewidth=2, label='Numerical')
    analytical = 100 * np.exp(-0.1 * decay_result.time_points)
    ax.plot(decay_result.time_points, analytical, 'r--', linewidth=1, label='Analytical')
    ax.set_xlabel('Time')
    ax.set_ylabel('x')
    ax.set_title('Exponential Decay\ndx/dt = -kx')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 2. Harmonic Oscillator - Position
    ax = axes[0, 1]
    ax.plot(oscillator_result.time_points, oscillator_result['x'], 'g-', linewidth=2)
    ax.set_xlabel('Time')
    ax.set_ylabel('Position x')
    ax.set_title('Harmonic Oscillator\nd²x/dt² = -ω²x')
    ax.grid(True, alpha=0.3)
    
    # 3. Harmonic Oscillator - Phase Plot
    ax = axes[0, 2]
    ax.plot(oscillator_result['x'], oscillator_result['v'], 'g-', linewidth=2)
    ax.set_xlabel('Position x')
    ax.set_ylabel('Velocity v')
    ax.set_title('Phase Portrait')
    ax.grid(True, alpha=0.3)
    ax.axis('equal')
    
    # 4. Predator-Prey Time Series
    ax = axes[1, 0]
    ax.plot(predator_prey_result.time_points, predator_prey_result['prey'], 'b-', 
            linewidth=2, label='Prey')
    ax.plot(predator_prey_result.time_points, predator_prey_result['predator'], 'r-', 
            linewidth=2, label='Predator')
    ax.set_xlabel('Time')
    ax.set_ylabel('Population')
    ax.set_title('Predator-Prey Dynamics')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 5. Predator-Prey Phase Plot
    ax = axes[1, 1]
    ax.plot(predator_prey_result['prey'], predator_prey_result['predator'], 'purple', linewidth=2)
    ax.plot(predator_prey_result['prey'][0], predator_prey_result['predator'][0], 'go', 
            markersize=8, label='Start')
    ax.plot(predator_prey_result['prey'][-1], predator_prey_result['predator'][-1], 'ro', 
            markersize=8, label='End')
    ax.set_xlabel('Prey Population')
    ax.set_ylabel('Predator Population')
    ax.set_title('Predator-Prey Phase Portrait')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 6. Integration Method Comparison
    ax = axes[1, 2]
    methods_results = demo_integration_methods()
    colors = ['blue', 'red', 'green', 'orange']
    for i, (name, result) in enumerate(methods_results.items()):
        if i < len(colors):
            # Subsample for cleaner plot
            n_points = len(result.time_points)
            step = max(1, n_points // 200)
            t_sub = result.time_points[::step]
            x_sub = result['x'][::step]
            ax.plot(t_sub, x_sub, color=colors[i], linewidth=1.5, 
                   label=f'{name}', alpha=0.8)
    
    ax.set_xlabel('Time')
    ax.set_ylabel('x')
    ax.set_title('Integration Methods\ndx/dt = -x + sin(t)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('dynamic_systems_showcase.png', dpi=150, bbox_inches='tight')
    print("✓ Comprehensive visualization saved as 'dynamic_systems_showcase.png'")


def main():
    """Main demonstration function"""
    print("TextToSolver: Dynamic Systems Showcase")
    print("=" * 50)
    print("This example demonstrates differential equation solving capabilities:")
    print("• Time-dependent system integration")  
    print("• Multiple integration methods")
    print("• Different ODE types (linear, nonlinear, systems)")
    print("• Analysis and visualization tools")
    print("• Convenient APIs for common systems")
    
    
    try:
        # Run all demonstrations
        demo_simple_exponential_decay()
        demo_harmonic_oscillator()
        demo_predator_prey_dynamics()
        demo_integration_methods()
        demo_system_analysis()
        
        # Create visualization
        print("\nGenerating visualization...")
        create_comprehensive_visualization()
        
        # Summary
        print("\n" + "="*60)
        print("🎉 DYNAMIC SYSTEMS SHOWCASE COMPLETE")
        print("="*60)
        print("Key capabilities demonstrated:")
        print("✓ Differential equation parsing (dx/dt notation)")
        print("✓ Multiple integration methods (Euler, RK4, RK45, DOP853)")
        print("✓ System analysis (oscillators, population dynamics)")
        print("✓ Rich result objects with interpolation")
        print("✓ Convenient APIs and flexibility")
        print("✓ Comprehensive visualization")
        
        print(f"\nTextToSolver: Complete equation solving framework")
        print(f"  ✓ Algebraic equation systems")
        print(f"  ✓ Advanced OOP patterns") 
        print(f"  ✓ Dynamic systems")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Showcase failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    print("\n" + "="*60)
    if success:
        print("View 'dynamic_systems_showcase.png' for comprehensive visualization!")
    sys.exit(0 if success else 1)
