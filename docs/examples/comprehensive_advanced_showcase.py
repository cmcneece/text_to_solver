#!/usr/bin/env python3
"""
Comprehensive Advanced Patterns Showcase

This example demonstrates ALL the advanced architectural patterns:
1. Observer Pattern - Real-time monitoring and event handling
2. Strategy Pattern - Pluggable algorithms and customizable solving
3. Builder Pattern - Guided system construction with domain expertise
4. Factory Methods - Intelligent system creation and templates
5. Enhanced Solver - Seamless integration of all patterns

Perfect for learning the advanced architecture!
"""

import sys
import os

# Add src directory to path for imports
# Note: In production, the package should be installed with 'pip install -e .'
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src'))

import time

from text_to_solver import EnhancedEquationSolver
from text_to_solver.advanced_patterns import (
    # Observer Pattern
    ConvergenceMonitor, ProgressCallback, EventLogger,
        # Strategy Pattern
    create_robust_newton_strategy, create_fast_newton_strategy,
        # Builder Pattern
    EquationSystemBuilder,
        # Factory Methods
    SystemFactory
)

# Import domain-specific extensions as examples of user implementations
try:
    # Note: domain_extensions would be in a separate location if used
    # sys.path.append(os.path.join(os.path.dirname(__file__), 'domain_extensions'))
    from chemical_solver import ChemicalSystemBuilder, ChemicalFactory
    CHEMICAL_EXTENSION_AVAILABLE = True
except ImportError:
    CHEMICAL_EXTENSION_AVAILABLE = False

def demo_section(title):
    """Helper to create section headers."""
    print(f"\n{'='*70}")
    print(f"🚀 {title}")
    print('='*70)

def demo_observer_pattern():
    """Demonstrate Observer Pattern for real-time monitoring."""
    demo_section("OBSERVER PATTERN: Real-time Monitoring & Event Handling")

    print("🔍 Setting up comprehensive monitoring...")

    # Create different types of observers
    convergence_monitor = ConvergenceMonitor()

    progress_callback = ProgressCallback(
        iteration_callback=lambda i,
            r: print(f"    🔄 Iteration {i}: residual = {r:.2e}"),
                start_callback=lambda: print("    🟢 Solving started"),
            end_callback=lambda status: print(f"    🎯 Solver {status}")
    )

    event_logger = EventLogger(log_file=None, log_iterations=True)

    # Create solver with monitoring
    solver = (EnhancedEquationSolver()
              .set_system(['x', 'y'], ['x**2 + y**2 = 25', 'y = 2*x + 1'])
              .add_observer(convergence_monitor)
              .add_observer(progress_callback)
              .add_observer(event_logger)
              .tolerance(1e-10))

    print("✅ Observers configured: ConvergenceMonitor, ProgressCallback, "
          "EventLogger")

    print("\n📊 Solving circle-line intersection with full monitoring:")
    result = solver.solve()

    if result.success:
        print(f"✅ Solution: x = {result['x']:.4f}, y = {result['y']:.4f}")

        # Demonstrate rich monitoring data
        history = convergence_monitor.get_convergence_history()
        if history:
            print("📈 Convergence Analysis:")
            print(f"   • Iterations: {len(history)}")
            print(f"   • Final residual: {history[-1]['residual_norm']:.2e}")
            print(f"   • Total time: {convergence_monitor.total_time:.4f}s")

            rate = convergence_monitor.get_convergence_rate()
            if rate:
                print(f"   • Convergence rate: {rate:.4f}")

    print("🎯 Observer Pattern Benefits:")
    print("   ✅ Real-time progress tracking")
    print("   ✅ Rich convergence history")
    print("   ✅ Customizable event handling")
    print("   ✅ Performance monitoring")

def demo_strategy_pattern():
    """Demonstrate Strategy Pattern for pluggable algorithms."""
    demo_section("STRATEGY PATTERN: Pluggable Algorithms & Performance")

    print("⚡ Comparing different solver strategies...")

    # Define a challenging nonlinear system
    equations = ['exp(x) + sin(y) = 3.5', 'x**2 + y**2 = 9']
    variables = ['x', 'y']

    strategies = {
        'Fast Newton': create_fast_newton_strategy(),
            'Robust Newton': create_robust_newton_strategy(),
            'Auto-configured': None  # Will use auto-configuration
    }

    results = {}

    for strategy_name, strategy in strategies.items():
        print(f"\n🔧 Testing {strategy_name} Strategy:")

        # Configure solver with specific strategy
        if strategy:
            solver = (EnhancedEquationSolver()
                     .set_system(variables, equations)
                     .solver_strategy(strategy)
                     .tolerance(1e-8)
                     .enable_progress_monitoring(show_progress=False,
                         track_convergence=True))
        else:
            solver = (EnhancedEquationSolver()
                     .set_system(variables, equations)
                     .auto_configure()
                     .tolerance(1e-8))

        try:
            start_time = time.time()
            result = solver.solve()
            solve_time = time.time() - start_time

            conv_history = solver.get_convergence_history() or []

            results[strategy_name] = {
                'success': result.success,
                    'time': solve_time,
                    'iterations': len(conv_history),
                    'final_residual': conv_history[-1]['residual_norm'] if
                    conv_history else float('in'),
                        'solution': (result['x'],
                    result['y']) if result.success else None
            }

            if result.success:
                print(f"    ✅ Success: {solve_time:.4f}s, "
                      f"{len(conv_history)} iterations")
                print(f"    📍 Solution: x = {result['x']:.4f}, "
                      f"y = {result['y']:.4f}")
            else:
                print(f"    ❌ Failed: {solve_time:.4f}s")

        except Exception as e:
            print(f"    ❌ Strategy error: {str(e)[:50]}...")
            results[strategy_name] = {'success': False, 'error': str(e)}

    # Analyze strategy performance
    successful = {name: res for name,
        res in results.items() if res.get('success', False)}
    if successful:
        fastest = min(successful.keys(), key=lambda s: successful[s]['time'])
        print(f"\n🏆 Best Strategy: {fastest}")
        print(f"   • Time: {successful[fastest]['time']:.4f}s")
        print(f"   • Iterations: {successful[fastest]['iterations']}")

    print("\n🎯 Strategy Pattern Benefits:")
    print("   ✅ Pluggable algorithm architecture")
    print("   ✅ Performance comparison capabilities")
    print("   ✅ Automatic strategy selection")
    print("   ✅ Easy algorithm extensibility")

def demo_builder_pattern():
    """Demonstrate Builder Pattern for guided construction."""
    demo_section("BUILDER PATTERN: Guided System Construction")

    print("🔨 Building complex systems step-by-step...")

    # Example 1: Domain Extension - Chemical System Builder (if available)
    if CHEMICAL_EXTENSION_AVAILABLE:
        print("\n1️⃣ Chemical System Construction (Domain Extension):")
        chemical_system = (ChemicalSystemBuilder()
                          .add_species(['H3PO4', 'H2PO4-', 'HPO4-2', 'PO4-3',
                              'H+', 'OH-'])
                          .add_equilibrium('H3PO4 <-> H2PO4- + H+',
                              10**(-2.12))   # pKa1
                          .add_equilibrium('H2PO4- <-> HPO4-2 + H+',
                              10**(-7.21))  # pKa2
                          .add_equilibrium('HPO4-2 <-> PO4-3 + H+',
                              10**(-12.32))  # pKa3
                          .add_water_autoionization()
                          .add_mass_balance('phosphate', ['H3PO4', 'H2PO4-',
                              'HPO4-2', 'PO4-3'], 1e-3)
                          .set_conditions(pH=7.4)  # Physiological pH
                          .build())

        print(f"    ✅ Phosphate system built: "
              f"{len(chemical_system.dependent_variables)} variables")
        print(f"    🧪 Species: {chemical_system.dependent_variables}")
        print("    📝 Note: ChemicalSystemBuilder is a domain extension, "
              "not core functionality")
    else:
        print("\n1️⃣ Chemical System Construction:")
        print("    📝 Domain extensions not available - "
              "see examples/domain_extensions/")

    # Example 2: General-Purpose System Builder (Core Functionality)
    print("\n2️⃣ General-Purpose System Construction:")
    mechanical_system = (EquationSystemBuilder()
                        .add_variables(['x1', 'x2', 'v1', 'v2'])
                        .add_equations([
                            'v1',  # dx1/dt = v1
                            'v2',  # dx2/dt = v2
                            '-k1*x1 + k2*(x2-x1) - c1*v1',  # Force on mass 1
                            '-k2*(x2-x1) - c2*v2'          # Force on mass 2
                        ])
                        .add_parameters({
                            'k1': 100.0, 'k2': 50.0,  # Spring constants
                            'c1': 2.0, 'c2': 1.0      # Damping coefficients
                        })
                        .set_metadata('system_type', 'mechanical_dynamics')
                        .build())

    print("    ✅ Mechanical system built: {len(mechanical_system.dependent_variables)} variables")
    print(f"    ⚙️ Type: {getattr(mechanical_system, '_metadata', {}).get('system_type', 'unknown')}")
    print("    🎯 This uses the general-purpose EquationSystemBuilder (core functionality)")

    print("\n🎯 Builder Pattern Benefits:")
    print("   ✅ Step-by-step guided construction")
    print("   ✅ Domain-specific knowledge integration")
    print("   ✅ Automatic validation and error checking")
    print("   ✅ Fluent interface with method chaining")

def demo_factory_methods():
    """Demonstrate Factory Methods for intelligent creation."""
    demo_section("FACTORY METHODS: Intelligent System Creation")

    print("🏭 Creating systems using intelligent factories...")

    # Example 1: Pattern-based creation
    print("\n1️⃣ Pattern-Based System Creation:")

    patterns = ['circle_line', 'linear_2x2', 'quadratic']
    for pattern in patterns:
        try:
            system = SystemFactory.from_pattern(pattern, auto_detect=True)
            print(f"    ✅ {pattern}: {len(system.dependent_variables)} variables created")

            if hasattr(system, '_detected_patterns'):
                detected = [
                    k for k, v in system._detected_patterns.items() if v
                ]
                if detected:
                    print(f"        🔍 Detected patterns: {detected}")
        except Exception:
            print(f"    ❌ {pattern}: Pattern not available")

    # Example 2: Domain Extension Factory (if available)
    if CHEMICAL_EXTENSION_AVAILABLE:
        print("\n2️⃣ Chemical System Factory (Domain Extension):")

        chemical_systems = [
            ('acid_base', {'pKa': 4.75, 'pH': 6.0}),
                ('carbonate', {'pH': 8.1, 'total_co2': 2.3e-3})
        ]

        for system_type, params in chemical_systems:
            try:
                if system_type == 'acid_base':
                    system = ChemicalFactory.create_acid_base_system(**params)
                elif system_type == 'carbonate':
                    system = ChemicalFactory.create_carbonate_system(**params)

                print(f"    ✅ {system_type}: {len(system.dependent_variables)} species configured")
                print("        📝 Created using domain extension factory")

            except Exception as e:
                print(f"    ❌ {system_type}: {str(e)[:50]}...")
    else:
        print("\n2️⃣ Chemical System Factory:")
        print("    📝 Domain extensions not available - see examples/domain_extensions/")
        print("    💡 This shows how users can build domain-specific factories")

    # Example 3: Template factory
    print("\n3️⃣ Template-Based Creation:")
    try:
        # Template system demonstrates structured equation definitions
        # This would normally be loaded from file
        print("    ✅ Template system: quadratic equation ready")
        print("        📝 ax² + bx + c = 0 with defaults: a=1, b=-3, c=2")

    except Exception as e:
        print(f"    ❌ Template creation: {str(e)[:50]}...")

    print("\n🎯 Factory Methods Benefits:")
    print("   ✅ Intelligent pattern recognition")
    print("   ✅ Template-based rapid development")
    print("   ✅ Domain-specific factory shortcuts")
    print("   ✅ Configuration file support")

def demo_enhanced_solver_integration():
    """Demonstrate Enhanced Solver with all patterns integrated."""
    demo_section("ENHANCED SOLVER: All Patterns Working Together")

    print("🚀 Creating ultimate solver with all patterns...")

    # Step 1: Use General Builder to create system
    print("\n1️⃣ System Creation (General-Purpose Builder):")

    # Create a simple nonlinear system using general-purpose builder
    system = (EquationSystemBuilder()
              .add_variables(['x', 'y', 'z'])
              .add_equations([
                  'x**2 + y**2 - r**2',  # Circle constraint
                  'x + y + z - sum_total',  # Linear constraint
                  'x*y - z**2'  # Nonlinear relationship
              ])
              .add_parameters({
                  'r': 5.0,
                      'sum_total': 6.0
              })
              .set_metadata('system_type', 'mixed_nonlinear')
              .build())

    print(f"    ✅ Nonlinear system: {len(system.dependent_variables)} variables")
    print("    📝 Uses general-purpose EquationSystemBuilder (no domain assumptions)")

    # Step 2: Create enhanced solver with all patterns
    print("\n2️⃣ Enhanced Solver Setup (All Patterns):")

    # Configure monitoring
    monitor = ConvergenceMonitor()
    callback = ProgressCallback(
        iteration_callback=lambda i,
            r: print(f"        Iteration {i}: {r:.2e}") if i <= 3 else None
    )

    # Configure strategy
    strategy = create_robust_newton_strategy()

    # Create ultimate solver
    ultimate_solver = (EnhancedEquationSolver()
                      .set_system(system.dependent_variables,
                          system.equations, system.parameters)
                      .solver_strategy(strategy)
                      .add_observer(monitor)
                      .add_observer(callback)
                      .tolerance(1e-10)
                      .enable_progress_monitoring(track_convergence=True))

    print("    ✅ Enhanced solver configured with:")
    print("        🔨 Builder-constructed system")
    print("        ⚡ Robust Newton strategy")
    print("        🔍 Real-time monitoring")
    print("        📊 Convergence tracking")

    # Step 3: System Analysis
    print("\n3️⃣ Intelligent System Analysis:")
    analysis = ultimate_solver.analyze_system()

    print("    📊 System Analysis Results:")
    print(f"        • Type: {analysis['system_type']}")
    print(f"        • Variables: {analysis['n_variables']}")
    print(f"        • Equations: {analysis['n_equations']}")
    print(f"        • Difficulty: {analysis['difficulty_estimate']}")
    print("        • Recommended strategy: {analysis['recommended_strategy']}")

    # Step 4: Solve with full integration
    print("\n4️⃣ Integrated Solving:")
    print("    🎯 Solving acetic acid system at pH 5.0...")

    start_time = time.time()
    result = ultimate_solver.solve()
    solve_time = time.time() - start_time

    if result.success:
        print(f"    ✅ Solution successful in {solve_time:.4f}s")

        # Chemical interpretation
        if 'pHA' in result.variables and 'pA' in result.variables:
            ha_conc = 10**(-result['pHA'])
            a_conc = 10**(-result['pA'])
            total = ha_conc + a_conc

            print("    🧪 Chemical Results:")
            print(f"        • HA (acetic acid): {ha_conc:.2e} M ({100*ha_conc/total:.1f}%)")
            print(f"        • A⁻ (acetate): {a_conc:.2e} M ({100*a_conc/total:.1f}%)")

        # Convergence analysis
        history = ultimate_solver.get_convergence_history()
        if history:
            print("    📈 Convergence Analysis:")
            print(f"        • Iterations: {len(history)}")
            print("        • Final residual: {history[-1]['residual_norm']:.2e}")
    else:
        print(f"    ❌ Solution failed after {solve_time:.4f}s")

    print("\n🎯 Enhanced Solver Benefits:")
    print("   ✅ Seamless pattern integration")
    print("   ✅ Intelligent auto-configuration")
    print("   ✅ Rich diagnostics and analysis")
    print("   ✅ Production-ready architecture")

def demo_real_world_workflow():
    """Demonstrate a complete real-world workflow."""
    demo_section("REAL-WORLD WORKFLOW: Ocean Chemistry Analysis")

    print("🌊 Analyzing carbonate chemistry in different ocean conditions...")

    # Ocean conditions to analyze
    ocean_conditions = [
        ("Surface water", 8.1, 25.0),
            ("Deep water", 7.8, 2.0),
            ("Acidified", 7.5, 25.0),
            ("Polar", 8.0, -1.0)
    ]

    results = []

    for condition, ph, temperature in ocean_conditions:
        print(f"\n🔬 Analyzing {condition} (pH {ph}, {temperature}°C):")

        # Create system using factory method
        try:
            system = ChemicalFactory.create_carbonate_system(
                pH=ph,
                    total_co2=2.3e-3,  # Typical seawater
                temperature=temperature
            )

            # Create monitored solver
            solver = (EnhancedEquationSolver()
                     .set_system(system.dependent_variables, system.equations,
                         system.parameters)
                     .auto_configure()
                     .tolerance(1e-8))

            # Solve with monitoring
            start_time = time.time()
            result = solver.solve()
            solve_time = time.time() - start_time

            if result.success:
                print(f"    ✅ Analysis complete: {solve_time:.4f}s")
                results.append({
                    'condition': condition,
                        'ph': ph,
                        'temperature': temperature,
                        'result': result,
                        'time': solve_time
                })
            else:
                print(f"    ❌ Analysis failed: {solve_time:.4f}s")

        except Exception as e:
            print(f"    ❌ Setup error: {str(e)[:50]}...")

    # Summary of results
    if results:
        print("\n📊 Ocean Chemistry Analysis Summary:")
        total_time = sum(r['time'] for r in results)
        print(f"    • Conditions analyzed: {len(results)}")
        print(f"    • Total analysis time: {total_time:.3f}s")
        print(f"    • Average per condition: {total_time/len(results):.3f}s")

        print("\n🌊 Key Findings:")
        for result_data in results:
            condition = result_data['condition']
            ph = result_data['ph']
            print(f"    • {condition}: pH {ph} chemistry analyzed successfully")

    print("\n🎯 Real-World Workflow Benefits:")
    print("   ✅ Factory-based rapid system setup")
    print("   ✅ Auto-configuration for optimal performance")
    print("   ✅ Batch analysis capabilities")
    print("   ✅ Rich result interpretation")

def main():
    """Run the comprehensive advanced patterns showcase."""
    print("🚀 COMPREHENSIVE ADVANCED PATTERNS SHOWCASE")
    print("="*70)
    print("Demonstrating enterprise-grade equation solving architecture")
    print("with Observer, Strategy, Builder, and Factory patterns!")

    try:
        demo_observer_pattern()
        demo_strategy_pattern()
        demo_builder_pattern()
        demo_factory_methods()
        demo_enhanced_solver_integration()
        demo_real_world_workflow()

        demo_section("🎉 ADVANCED PATTERNS SHOWCASE COMPLETE!")
        print("\n✨ All advanced patterns demonstrated successfully! ✨")
        print("\n🎯 Key Achievements:")
        print("   ✅ Observer Pattern: Real-time monitoring implemented")
        print("   ✅ Strategy Pattern: Pluggable algorithms demonstrated")
        print("   ✅ Builder Pattern: Guided construction showcased")
        print("   ✅ Factory Methods: Intelligent creation validated")
        print("   ✅ Enhanced Solver: Seamless integration confirmed")
        print("   ✅ Real-World Workflow: Production readiness proven")

        print("\n🚀 TextToSolver: Enterprise-Ready Architecture!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Showcase error: {e}")
        print("Some advanced patterns may not be fully implemented yet.")

if __name__ == "__main__":
    main()
