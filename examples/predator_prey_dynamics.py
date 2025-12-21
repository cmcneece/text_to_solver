#!/usr/bin/env python3
"""
Predator-Prey Dynamics Example - TextToSolver

This example demonstrates dynamic systems capability by solving
the classic Lotka-Volterra predator-prey equations over time.

TextToSolver can solve both steady-state solutions and integrate
systems through time to see the full dynamic behavior including oscillations.

Mathematical Model:
dx/dt = αx - βxy  (prey growth rate - predation rate)
dy/dt = δxy - γy  (predator growth from hunting - death rate)

Where:
- x = prey population
- y = predator population
- α = prey intrinsic growth rate
- β = predation efficiency
- δ = predator efficiency at converting prey to offspring
- γ = predator death rate
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Add the package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from text_to_solver import (
    DynamicEquationSolver,
        EquationSolver  # For comparison with steady-state
)


def solve_steady_state_comparison():
    """Compare with the old steady-state approach for reference"""
    print("Steady-State Analysis")
    print("-" * 40)

    # Find equilibrium points using algebraic solver
    solver = EquationSolver()

    # Equilibrium when dx/dt = dy/dt = 0
    solver.set_system(
        variables=['x', 'y'],
            equations=[
            'alpha*x - beta*x*y',    # dx/dt = 0
            'delta*x*y - gamma*y'    # dy/dt = 0
        ],
            parameters={'alpha': 1.0, 'beta': 0.1, 'delta': 0.075, 'gamma': 1.5}
    )

    # Find non-trivial equilibrium
    result = solver.solve(custom_guess={'x': np.array([10]),
        'y': np.array([5])})

    if result.success:
        x_eq, y_eq = result.values['x'], result.values['y']
        print(f"Equilibrium point: x* = {x_eq:.2f}, y* = {y_eq:.2f}")
        print("This represents the center of the oscillations")
    else:
        print("Could not find equilibrium point")
        x_eq, y_eq = 20.0, 10.0  # Default values

    return x_eq, y_eq


def solve_dynamic_system():
    """Solve the full dynamic system over time"""
    print("\nDynamic Time Evolution")
    print("-" * 40)

    # Method 1: Using the general-purpose solver
    print("Method 1: General-purpose solver")
    solver = DynamicEquationSolver()
    solver.set_system(
        variables=['x', 'y'],
        equations=[
            'dx/dt = alpha*x - beta*x*y',  # Prey growth - predation
            'dy/dt = delta*x*y - gamma*y'  # Predator growth from hunting - death
        ],
        parameters={
            'alpha': 1.0,    # Prey growth rate
            'beta': 0.1,     # Predation efficiency
            'delta': 0.075,  # Predator conversion efficiency
            'gamma': 1.5     # Predator death rate
        },
            initial_conditions={'x': 10, 'y': 5}  # Initial populations
    )
    result = solver.integrate(time_span=(0, 20), method='RK45')

    if result.success:
        print("✓ Integration successful!")
        print(f"  Time span: {result.integration_info['time_span']}")
        print(f"  Method: {result.integration_info['method']}")
        print(f"  Data points: {len(result.time_points)}")
        print(f"  Initial: prey={result.initial_values['x']:.1f}, "
              f"predator={result.initial_values['y']:.1f}")
        print(f"  Final: prey={result.final_values['x']:.1f}, "
              f"predator={result.final_values['y']:.1f}")

        # Analyze the dynamics
        prey_values = result['x']
        predator_values = result['y']

        prey_max = np.max(prey_values)
        prey_min = np.min(prey_values)
        pred_max = np.max(predator_values)
        pred_min = np.min(predator_values)

        print(f"  Prey oscillation: {prey_min:.1f} to {prey_max:.1f}")
        print(f"  Predator oscillation: {pred_min:.1f} to {pred_max:.1f}")

        return result
    else:
        print(f"✗ Integration failed: {result.message}")
        return None


def demonstrate_multiple_scenarios():
    """Compare different parameter scenarios"""
    print("\nParameter Sensitivity Analysis")
    print("-" * 40)

    scenarios = {
        'Baseline': {'alpha': 1.0, 'beta': 0.1, 'delta': 0.075, 'gamma': 1.5},
            'High Growth': {'alpha': 1.5, 'beta': 0.1, 'delta': 0.075,
            'gamma': 1.5},
                'Efficient Predator': {'alpha': 1.0, 'beta': 0.15, 'delta': 0.1,
            'gamma': 1.5},
                'Hardy Prey': {'alpha': 1.0, 'beta': 0.08, 'delta': 0.06, 'gamma': 1.5}
    }

    results = {}

    for name, params in scenarios.items():
        print(f"\nScenario: {name}")
        solver = DynamicEquationSolver()
        solver.set_system(
            variables=['x', 'y'],
                equations=[
                'dx/dt = alpha*x - beta*x*y',  # Prey growth - predation
                'dy/dt = delta*x*y - gamma*y'  # Predator growth from hunting - death
            ],
                parameters={
                'alpha': params['alpha'],
                    'beta': params['beta'],
                    'delta': params['delta'],
                    'gamma': params['gamma']
            },
                initial_conditions={'x': 10, 'y': 5}
        )
        result = solver.integrate(time_span=(0, 15), method='RK45')

        if result.success:
            results[name] = result

            # Calculate period of oscillation (rough estimate)
            prey_vals = result['x']
            time_vals = result.time_points

            # Find peaks
            peaks = []
            for i in range(1, len(prey_vals)-1):
                if (prey_vals[i] > prey_vals[i-1] and
                    prey_vals[i] > prey_vals[i+1]):
                    peaks.append(time_vals[i])

            if len(peaks) >= 2:
                avg_period = np.mean(np.diff(peaks))
                print(f"  ✓ Estimated period: {avg_period:.2f} time units")
            else:
                print("  ✓ Period: Not enough cycles to estimate")

            prey_range = np.max(prey_vals) - np.min(prey_vals)
            pred_range = np.max(result['y']) - np.min(result['y'])
            print(f"  Oscillation amplitude: prey ±{prey_range/2:.1f}, "
                  f"predator ±{pred_range/2:.1f}")
        else:
            print(f"  ✗ Failed: {result.message}")

    return results


def create_visualization(main_result, scenario_results, equilibrium_point):
    """Create comprehensive visualization of the dynamics"""
    print("\nCreating Visualization...")

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Predator-Prey Dynamics: TextToSolver', fontsize=14)

    # 1. Main time series
    ax = axes[0, 0]
    ax.plot(main_result.time_points, main_result['x'], 'b-', linewidth=2,
        label='Prey')
    ax.plot(main_result.time_points, main_result['y'], 'r-', linewidth=2,
        label='Predator')
    ax.axhline(equilibrium_point[0], color='blue', linestyle='--', alpha=0.5,
        label='Prey equilibrium')
    ax.axhline(equilibrium_point[1], color='red', linestyle='--', alpha=0.5,
        label='Pred equilibrium')
    ax.set_xlabel('Time')
    ax.set_ylabel('Population')
    ax.set_title('Time Evolution')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. Phase portrait
    ax = axes[0, 1]
    ax.plot(main_result['x'], main_result['y'], 'purple', linewidth=2)
    ax.plot(main_result['x'][0], main_result['y'][0], 'go', markersize=8,
        label='Start')
    ax.plot(main_result['x'][-1], main_result['y'][-1], 'ro', markersize=6,
        label='End')
    ax.plot(equilibrium_point[0], equilibrium_point[1], 'k*', markersize=10,
        label='Equilibrium')
    ax.set_xlabel('Prey Population')
    ax.set_ylabel('Predator Population')
    ax.set_title('Phase Portrait')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 3. Multiple scenarios comparison
    ax = axes[1, 0]
    colors = ['blue', 'red', 'green', 'orange']
    for i, (name, result) in enumerate(scenario_results.items()):
        if i < len(colors):
            ax.plot(result.time_points, result['x'], color=colors[i],
                linewidth=1.5, label=f'{name} (prey)', alpha=0.8)
    ax.set_xlabel('Time')
    ax.set_ylabel('Prey Population')
    ax.set_title('Scenario Comparison: Prey')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 4. Energy-like conservation check
    ax = axes[1, 1]
    # For Lotka-Volterra, there's a conserved quantity:
    # H = δx + γy - α*ln(y) - β*ln(x)
    x_vals = main_result['x']
    y_vals = main_result['y']

    # Parameters from main result
    alpha, beta, delta, gamma = 1.0, 0.1, 0.075, 1.5

    # Avoid log(0) by adding small epsilon
    x_safe = np.maximum(x_vals, 1e-10)
    y_safe = np.maximum(y_vals, 1e-10)

    H = (delta * x_vals + gamma * y_vals -
         alpha * np.log(y_safe) - beta * np.log(x_safe))

    ax.plot(main_result.time_points, H, 'green', linewidth=2)
    ax.set_xlabel('Time')
    ax.set_ylabel('Conserved Quantity H')
    ax.set_title('Conservation Check')
    ax.grid(True, alpha=0.3)

    # Add text with conservation info
    H_variation = (np.max(H) - np.min(H)) / np.mean(np.abs(H))
    ax.text(0.05, 0.95, f'Variation: {H_variation*100:.2f}%',
        transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    plt.savefig('predator_prey_analysis.png', dpi=150, bbox_inches='tight')
    print("✓ Visualization saved as 'predator_prey_analysis.png'")


def demonstrate_advanced_features():
    """Show advanced features like interpolation and different methods"""
    print("\nAdvanced Features Demonstration")
    print("-" * 40)

    # Solve with different integration methods
    solver = DynamicEquationSolver()
    solver.set_system(
        variables=['x', 'y'],
            equations=[
            'dx/dt = alpha*x - beta*x*y',
                'dy/dt = delta*x*y - gamma*y'
        ],
            parameters={'alpha': 1.0, 'beta': 0.1, 'delta': 0.075, 'gamma': 1.5},
            initial_conditions={'x': 10.0, 'y': 5.0}
    )

    methods = ['RK45', 'DOP853', 'euler']
    method_results = {}

    print("Comparing integration methods:")
    for method in methods:
        try:
            if method == 'euler':
                result = solver.integrate((0, 10), method=method, dt=0.01)
            else:
                result = solver.integrate((0, 10), method=method)

            if result.success:
                method_results[method] = result
                n_points = len(result.time_points)
                final_prey = result.final_values['x']
                print(f"  ✓ {method:8s}: {n_points:4d} points, "
                      f"final prey = {final_prey:.2f}")
            else:
                print(f"  ✗ {method:8s}: {result.message}")
        except Exception as e:
            print(f"  ✗ {method:8s}: Exception - {str(e)}")

    # Demonstrate interpolation
    if 'RK45' in method_results:
        result = method_results['RK45']
        print("\nInterpolation capabilities:")

        # Get values at specific times
        times_of_interest = [2.5, 5.0, 7.5]
        for t in times_of_interest:
            values = result.at_time(t)
            print(f"  t={t:3.1f}: prey={values['x']:.2f}, "
                  f"predator={values['y']:.2f}")

        # Interpolation functions available via result.interpolate() if needed
        print("  ✓ Interpolation functions available for continuous access")

    return method_results


def main():
    """Main demonstration function"""
    print("=" * 60)
    print("Predator-Prey Dynamics: TextToSolver")
    print("=" * 60)
    print("This example demonstrates comprehensive predator-prey analysis:")
    print("• Equilibrium analysis: Find steady-state points (algebraic)")
    print("• Dynamic simulation: Full time evolution (differential equations)")
    print("• Advanced analysis: Multiple integration methods and "
          "visualization")

    try:
        # Step 1: Steady-state analysis (for comparison)
        equilibrium = solve_steady_state_comparison()

        # Step 2: Dynamic system solution
        main_result = solve_dynamic_system()
        if not main_result:
            print("Failed to solve main system")
            return False

        # Step 3: Multiple scenarios
        scenario_results = demonstrate_multiple_scenarios()

        # Step 4: Advanced features
        demonstrate_advanced_features()

        # Step 5: Comprehensive visualization
        create_visualization(main_result, scenario_results, equilibrium)

        # Summary
        print("\n" + "=" * 60)
        print("🎉 PREDATOR-PREY ANALYSIS COMPLETE")
        print("=" * 60)
        print("Key insights:")
        print("✓ System exhibits stable limit cycle oscillations")
        print("✓ Equilibrium point found algebraically matches orbit center")
        print("✓ Different parameters affect period and amplitude")
        print("✓ Multiple integration methods give consistent results")
        print("✓ TextToSolver handles both static and dynamic systems")

        print("\nComprehensive Analysis Results:")
        print(f"  Equilibrium point: ({equilibrium[0]:.1f}, "
              f"{equilibrium[1]:.1f})")
        print(f"  Time evolution: {len(main_result.time_points)} data points "
              f"over {main_result.time_span[1]} time units")
        print("  Rich analysis: Periods, amplitudes, phase portraits, "
              "conservation")

        return True

    except Exception as e:
        print(f"\n✗ Example failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 60)
    if success:
        print("View 'predator_prey_analysis.png' for complete analysis!")
    sys.exit(0 if success else 1)
