#!/usr/bin/env python3
"""
Carbonate Speciation Example

This example demonstrates solving the carbonate system equilibrium to predict
the distribution of CO2 species (H2CO3, HCO3-, CO3²-) as a function of pH
using the EquationSolver and ChemicalEquilibrium APIs.

Key chemical equilibria:
1. H2CO3 ⇌ H+ + HCO3-       (1st dissociation, pK1 = 6.35)
2. HCO3- ⇌ H+ + CO3²-       (2nd dissociation, pK2 = 10.33)
3. H2O ⇌ H+ + OH-           (Water autoionization, pKw = 14.0)
4. Mass balance: CT = [H2CO3] + [HCO3-] + [CO3²-]
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
import time
from text_to_solver import EquationSolver

print("🧪 Carbonate Speciation System")
print("=" * 32)
print("Analyzing CO2 chemistry: H2CO3 ⇌ HCO3- ⇌ CO3²-")
print("Using general-purpose EquationSolver for chemical equilibrium")

# System parameters (25°C, 1 atm)
CHEMICAL_PARAMS = {
    'pKw': 14.0,     # Water ionization constant
    'pK1': 6.35,     # 1st dissociation constant
    'pK2': 10.33,    # 2nd dissociation constant  
    'pCO2T': 3.0     # Total CO2 = 1 mM (negative log)
}

# ================================================================
# METHOD 1: General-Purpose Solver for Chemical Equilibrium
# ================================================================

print(f"\n🧪 Method 1: General-Purpose Solver for Key Conditions")
print("-" * 54)

print("Solving carbonate equilibrium using general EquationSolver:")

# Define the carbonate system equations (same chemistry, general solver)
carbonate_equations = [
    'pK1 - pHCO3 - pH + pH2CO3',      # 1st dissociation equilibrium
    'pK2 - pCO3 - pH + pHCO3',        # 2nd dissociation equilibrium  
    'pKw - pH - pOH',                  # Water autoionization
    'pH2CO3 + pHCO3 + pCO3 - pCO2T'   # Mass balance (log-space)
]

carbonate_variables = ['pH2CO3', 'pHCO3', 'pCO3', 'pOH']

key_conditions = [
    ("Ocean surface (pH 8.1)", 8.1),
    ("Neutral water (pH 7.0)", 7.0),
    ("Acid rain (pH 5.0)", 5.0),
    ("Alkaline water (pH 10.0)", 10.0),
    ("Highly alkaline (pH 11.5)", 11.5)
]

carbonate_helper_results = []
start_time = time.time()

for condition_name, ph_val in key_conditions:
    result = EquationSolver.solve_equations(
        variables=carbonate_variables,
        equations=carbonate_equations,
        parameters={
            'pK1': 6.35,
            'pK2': 10.33, 
            'pKw': 14.0,
            'pH': ph_val,
            'pCO2T': 3.0  # 1 mM total CO2 (negative log)
        }
    )
    
    carbonate_helper_results.append((condition_name, ph_val, result))
    
    if result.success:
        # Calculate molar concentrations from p-values
        h2co3_conc = 10**(-result['pH2CO3'])
        hco3_conc = 10**(-result['pHCO3'])
        co3_conc = 10**(-result['pCO3'])
        total = h2co3_conc + hco3_conc + co3_conc
        
        # Calculate fractions
        alpha0 = h2co3_conc / total
        alpha1 = hco3_conc / total
        alpha2 = co3_conc / total
        
        print(f"  {condition_name}:")
        print(f"    • Fractions: H2CO3={alpha0:.2f}, HCO3-={alpha1:.2f}, CO3²-={alpha2:.2f}")
        print(f"    • Dominant species: {['H2CO3', 'HCO3-', 'CO3²-'][np.argmax([alpha0, alpha1, alpha2])]}")
    else:
        print(f"  {condition_name}: ❌ Failed to converge")

helper_time = time.time() - start_time
print(f"General solver: {len(key_conditions)} conditions solved in {helper_time:.3f}s")

# ================================================================
# METHOD 2: Parameter Sweep with EquationSolver
# ================================================================

print(f"\n📊 Method 2: pH Range Analysis with Parameter Sweep")
print("-" * 50)

# Define the carbonate system equations (pH as parameter, species as variables)
carbonate_vars = ['pHCO3', 'pCO3', 'pH2CO3', 'pOH']
carbonate_equations = [
    'pK1 - pHCO3 - pH + pH2CO3',      # 1st dissociation equilibrium
    'pK2 - pCO3 - pH + pHCO3',        # 2nd dissociation equilibrium  
    'pKw - pH - pOH',                  # Water autoionization
    'pH2CO3 + pHCO3 + pCO3 - pCO2T'   # Mass balance (log-space)
]

# Create solver with chemical-specific configuration
solver = (EquationSolver()
          .set_system(carbonate_vars, carbonate_equations)
          .tolerance(1e-8)
          .guess_strategy('chemical_equilibrium')
          .with_parameters(CHEMICAL_PARAMS))

# Analyze pH range from acidic to basic
pH_range = np.linspace(4, 12, 40)
print(f"Analyzing pH range: {pH_range[0]:.1f} to {pH_range[-1]:.1f} ({len(pH_range)} points)")

start_time = time.time()
results = solver.parameter_sweep('pH', pH_range.tolist())
sweep_time = time.time() - start_time

successful = sum(1 for r in results if r.success)
print(f"✅ Parameter sweep: {successful}/{len(pH_range)} successful in {sweep_time:.3f}s")

# Extract successful results
success_mask = [r.success for r in results]
ph_success = pH_range[success_mask]
results_success = [r for r in results if r.success]

if len(results_success) > 0:
    print(f"   pH range with solutions: {ph_success[0]:.1f} to {ph_success[-1]:.1f}")
    
    # Find crossover points where species become dominant
    h2co3_vals = np.array([r['pH2CO3'] for r in results_success])
    hco3_vals = np.array([r['pHCO3'] for r in results_success])
    co3_vals = np.array([r['pCO3'] for r in results_success])
    
    # Convert to concentrations and find crossovers
    h2co3_conc = 10**(-h2co3_vals)
    hco3_conc = 10**(-hco3_vals)
    co3_conc = 10**(-co3_vals)
    
    # Find pH where HCO3- = H2CO3 (should be near pK1)
    diff1 = np.abs(h2co3_conc - hco3_conc)
    idx1 = np.argmin(diff1)
    
    # Find pH where CO3²- = HCO3- (should be near pK2)  
    diff2 = np.abs(hco3_conc - co3_conc)
    idx2 = np.argmin(diff2)
    
    print(f"   Crossover points:")
    print(f"     • H2CO3 = HCO3- at pH ≈ {ph_success[idx1]:.2f} (theory: pK1 = {CHEMICAL_PARAMS['pK1']:.2f})")
    print(f"     • HCO3- = CO3²- at pH ≈ {ph_success[idx2]:.2f} (theory: pK2 = {CHEMICAL_PARAMS['pK2']:.2f})")

# ================================================================
# METHOD 3: One-liner Solutions for Specific Cases
# ================================================================

print(f"\n🎯 Method 3: One-liner Solutions for Specific Studies")
print("-" * 52)

print("Demonstrating different temperature and ionic strength conditions:")

# Temperature effects (approximate)
temperature_studies = [
    ("Cold water (10°C)", {'pH': 8.0, 'pK1': 6.42, 'pK2': 10.40}),  # Higher pK values
    ("Room temp (25°C)", {'pH': 8.0, 'pK1': 6.35, 'pK2': 10.33}),   # Standard
    ("Warm water (40°C)", {'pH': 8.0, 'pK1': 6.28, 'pK2': 10.26})   # Lower pK values
]

print("Temperature effect on carbonate speciation at pH 8.0:")
start_time = time.time()

for study_name, params in temperature_studies:
    result = EquationSolver.solve_equations(
        variables=carbonate_vars,
        equations=carbonate_equations, 
        parameters={**CHEMICAL_PARAMS, **params, 'pCO2T': 3.0},
        tolerance=1e-10
    )
    
    if result.success:
        # Calculate dominant species
        concentrations = {
            'H2CO3': 10**(-result['pH2CO3']),
            'HCO3-': 10**(-result['pHCO3']),
            'CO3²-': 10**(-result['pCO3'])
        }
        total = sum(concentrations.values())
        fractions = {k: v/total for k, v in concentrations.items()}
        dominant = max(fractions, key=fractions.get)
        
        print(f"  {study_name}: Dominant species = {dominant} ({fractions[dominant]:.1%})")
    else:
        print(f"  {study_name}: ❌ Failed to converge")

oneliner_time = time.time() - start_time
print(f"Temperature studies: {len(temperature_studies)} conditions in {oneliner_time:.3f}s")

# ================================================================
# METHOD 4: Advanced Configuration and Analysis  
# ================================================================

print(f"\n⚙️ Method 4: Advanced Analysis with Custom Configuration")
print("-" * 56)

# High-precision analysis for publication-quality results
precision_solver = (EquationSolver()
                   .set_system(carbonate_vars, carbonate_equations)
                   .tolerance(1e-12)  # Higher precision
                   .guess_strategy('scaled')
                   .with_parameters(CHEMICAL_PARAMS))

# Analyze critical pH region around pK1
critical_ph = np.linspace(5.5, 7.5, 21)  # Around pK1 = 6.35
print(f"High-precision analysis around pK1 ({len(critical_ph)} points):")

start_time = time.time()
critical_results = precision_solver.parameter_sweep('pH', critical_ph.tolist())
precision_time = time.time() - start_time

successful_critical = sum(1 for r in critical_results if r.success)
print(f"✅ High-precision: {successful_critical}/{len(critical_ph)} successful in {precision_time:.3f}s")

if successful_critical > 0:
    # Find exact pK1 from equal concentrations
    critical_success = [r for r in critical_results if r.success]
    ph_critical = [critical_ph[i] for i, r in enumerate(critical_results) if r.success]
    
    h2co3_crit = np.array([10**(-r['pH2CO3']) for r in critical_success])
    hco3_crit = np.array([10**(-r['pHCO3']) for r in critical_success])
    
    # Find minimum difference
    diff_crit = np.abs(h2co3_crit - hco3_crit)
    min_idx = np.argmin(diff_crit)
    
    print(f"   Precise pK1 determination: pH = {ph_critical[min_idx]:.3f}")
    print(f"   Concentration difference: {diff_crit[min_idx]:.2e} M")
    print(f"   Residual norm: {critical_success[min_idx].residual_norm:.2e}")

# ================================================================
# COMPREHENSIVE VISUALIZATION
# ================================================================

print(f"\n📊 Creating comprehensive carbonate speciation visualization...")

if len(results_success) > 5:
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # Plot 1: Species distribution (log concentrations)
    ax1.plot(ph_success, h2co3_vals, 'b-', linewidth=2, label='H₂CO₃', marker='o', markersize=3)
    ax1.plot(ph_success, hco3_vals, 'g-', linewidth=2, label='HCO₃⁻', marker='s', markersize=3)
    ax1.plot(ph_success, co3_vals, 'r-', linewidth=2, label='CO₃²⁻', marker='^', markersize=3)
    
    # Add pK lines
    ax1.axvline(CHEMICAL_PARAMS['pK1'], color='gray', linestyle='--', alpha=0.7, label='pK₁')
    ax1.axvline(CHEMICAL_PARAMS['pK2'], color='gray', linestyle=':', alpha=0.7, label='pK₂')
    
    ax1.set_xlabel('pH')
    ax1.set_ylabel('p[Species] = -log₁₀[Species] (M)')
    ax1.set_title('Carbonate Species Distribution (Log Scale)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Species fractions with dominant regions
    total_conc = 10**(-CHEMICAL_PARAMS['pCO2T'])
    alpha0 = 10**(-h2co3_vals) / total_conc
    alpha1 = 10**(-hco3_vals) / total_conc
    alpha2 = 10**(-co3_vals) / total_conc
    
    ax2.fill_between(ph_success, 0, alpha0, alpha=0.3, color='blue', label='H₂CO₃ region')
    ax2.fill_between(ph_success, 0, alpha1, alpha=0.3, color='green', label='HCO₃⁻ region')  
    ax2.fill_between(ph_success, 0, alpha2, alpha=0.3, color='red', label='CO₃²⁻ region')
    
    ax2.plot(ph_success, alpha0, 'b-', linewidth=2, label='α₀ (H₂CO₃)')
    ax2.plot(ph_success, alpha1, 'g-', linewidth=2, label='α₁ (HCO₃⁻)')
    ax2.plot(ph_success, alpha2, 'r-', linewidth=2, label='α₂ (CO₃²⁻)')
    
    ax2.axvline(CHEMICAL_PARAMS['pK1'], color='gray', linestyle='--', alpha=0.7)
    ax2.axvline(CHEMICAL_PARAMS['pK2'], color='gray', linestyle=':', alpha=0.7)
    
    ax2.set_xlabel('pH')
    ax2.set_ylabel('Species Fraction')
    ax2.set_title('Carbonate Species Fractions')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 1)
    
    # Plot 3: Buffer capacity (derivative of fraction vs pH)
    if len(ph_success) > 3:
        dpH = ph_success[1] - ph_success[0]
        buffer_capacity = np.gradient(alpha1, dpH)  # HCO3- buffering
        
        ax3.plot(ph_success, buffer_capacity, 'purple', linewidth=2)
        ax3.axvline(CHEMICAL_PARAMS['pK1'], color='gray', linestyle='--', alpha=0.7, label='pK₁')
        ax3.axvline(CHEMICAL_PARAMS['pK2'], color='gray', linestyle=':', alpha=0.7, label='pK₂')
        
        ax3.set_xlabel('pH')
        ax3.set_ylabel('Buffer Capacity (dα₁/dpH)')
        ax3.set_title('Carbonate Buffer Capacity')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
    
    # Plot 4: Environmental conditions overlay
    ax4.scatter([result[1] for result in carbonate_helper_results if result[2].success],
               [0.5] * len([r for r in carbonate_helper_results if r[2].success]),
               s=100, c=['blue', 'green', 'orange', 'red', 'purple'][:len(carbonate_helper_results)],
               alpha=0.7, zorder=5)
    
    for i, (name, ph, result) in enumerate(carbonate_helper_results):
        if result.success:
            ax4.annotate(name.split('(')[0], (ph, 0.5), 
                        xytext=(0, 20), textcoords='offset points',
                        ha='center', fontsize=8, rotation=45)
    
    ax4.plot(ph_success, alpha0, 'b-', alpha=0.3, label='H₂CO₃')
    ax4.plot(ph_success, alpha1, 'g-', alpha=0.3, label='HCO₃⁻')
    ax4.plot(ph_success, alpha2, 'r-', alpha=0.3, label='CO₃²⁻')
    
    ax4.set_xlabel('pH')
    ax4.set_ylabel('Species Fraction')
    ax4.set_title('Environmental pH Conditions')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(0, 1)
    
    plt.tight_layout()
    plt.show()
    
    print("✅ Comprehensive visualization complete!")

# ================================================================
# SUMMARY AND INSIGHTS
# ================================================================

print(f"\n📋 CARBONATE SYSTEM ANALYSIS SUMMARY:")
print("=" * 38)

print(f"\n🧪 Chemical Insights:")
print(f"   • Acidic (pH < {CHEMICAL_PARAMS['pK1']:.1f}): H₂CO₃ dominates")
print(f"   • Neutral ({CHEMICAL_PARAMS['pK1']:.1f} < pH < {CHEMICAL_PARAMS['pK2']:.1f}): HCO₃⁻ dominates")
print(f"   • Basic (pH > {CHEMICAL_PARAMS['pK2']:.1f}): CO₃²⁻ dominates")
print(f"   • Ocean pH (~8.1): ~90% HCO₃⁻, ~10% CO₃²⁻")

print(f"\n⚡ Computational Performance:")
print(f"   • Chemical helpers: {helper_time:.3f}s for {len(key_conditions)} conditions")
print(f"   • Parameter sweep: {sweep_time:.3f}s for {len(pH_range)} pH points") 
print(f"   • Temperature studies: {oneliner_time:.3f}s for {len(temperature_studies)} cases")
print(f"   • High-precision: {precision_time:.3f}s for {len(critical_ph)} points")

print(f"\n🎯 General-Purpose EquationSolver Capabilities Demonstrated:")
print("   ✅ Chemical equilibrium solving with mathematical equations")
print("   ✅ Parameter sweeps for pH/temperature studies")  
print("   ✅ One-liner solutions for specific conditions")
print("   ✅ Custom high-precision configurations")
print("   ✅ Natural equation syntax for any domain")
print("   ✅ Automatic guess generation for nonlinear systems")

print(f"\n🌊 Applications:")
print("   • Ocean acidification studies")
print("   • Water treatment system design") 
print("   • Geochemical modeling")
print("   • Environmental pH monitoring")
print("   • Educational chemical equilibrium")

print(f"\n✨ General-Purpose Solver + Mathematical Modeling = Powerful Analysis! ✨")