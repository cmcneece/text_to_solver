"""
Factory Method Enhancement for TextToSolver

Provides intelligent system creation, template-based factories, and domain-specific
knowledge for rapid equation system setup.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any, Tuple
import re
import json
from pathlib import Path

# Import from parent modules
from ..user_api import EquationSystem, EquationSystemError
from .builders import ChemicalSystemBuilder, EquationSystemBuilder


class SystemFactory:
    """Main factory for creating equation systems with pattern detection."""
    
    @staticmethod
    def from_equations(equations: List[str], 
                      variables: Optional[List[str]] = None,
                      auto_detect: bool = True,
                      optimize_for: Optional[str] = None,
                      **kwargs) -> EquationSystem:
        """Create system from equations with automatic pattern detection.
        
        Args:
            equations: List of equation strings
            variables: Optional variable list (auto-detected if None)
            auto_detect: Enable automatic pattern detection
            optimize_for: Optimization hint ('speed', 'accuracy', 'robustness')
            **kwargs: Additional parameters
            
        Returns:
            Configured EquationSystem
        """
        # Auto-detect variables if not provided
        if variables is None:
            variables = SystemFactory._extract_variables(equations)
        
        # Detect system patterns if enabled
        patterns = {}
        if auto_detect:
            patterns = SystemFactory._detect_patterns(equations)
        
        # Create basic system
        system = EquationSystem(
            dependent_variables=variables,
            equations=equations,
            parameters=kwargs.get('parameters', {}),
            independent_variables=kwargs.get('independent_variables', [])
        )
        
        # Apply optimizations based on patterns and hints
        if optimize_for:
            system = SystemFactory._apply_optimizations(system, optimize_for, patterns)
        
        # Always store detected patterns if auto_detect was enabled
        if auto_detect and patterns:
            system._detected_patterns = patterns
        
        return system
    
    @staticmethod
    def from_pattern(pattern_name: str, **parameters) -> EquationSystem:
        """Create system from known pattern.
        
        Args:
            pattern_name: Name of the pattern ('linear', 'circle_line', 'chemical', etc.)
            **parameters: Pattern-specific parameters
            
        Returns:
            Configured EquationSystem
        """
        pattern_factories = {
            'linear': SystemFactory._create_linear_pattern,
            'circle_line': SystemFactory._create_circle_line_pattern,
            'chemical_equilibrium': SystemFactory._create_chemical_pattern,
            'predator_prey': SystemFactory._create_predator_prey_pattern,
            'optimization': SystemFactory._create_optimization_pattern
        }
        
        if pattern_name not in pattern_factories:
            available = ', '.join(pattern_factories.keys())
            raise ValueError(f"Unknown pattern '{pattern_name}'. Available: {available}")
        
        return pattern_factories[pattern_name](**parameters)
    
    @staticmethod
    def _extract_variables(equations: List[str]) -> List[str]:
        """Extract variable names from equations."""
        variables = set()
        
        for equation in equations:
            # Find potential variable names (letters followed by optional digits/underscores)
            matches = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_]*\b', equation)
            
            for match in matches:
                # Filter out common mathematical functions and constants
                if match not in ['sin', 'cos', 'tan', 'exp', 'log', 'sqrt', 'pi', 'e',
                               'log10', 'abs', 'max', 'min', 'sum', 'np']:
                    variables.add(match)
        
        return sorted(list(variables))
    
    @staticmethod
    def _detect_patterns(equations: List[str]) -> Dict[str, Any]:
        """Detect patterns in equation systems."""
        patterns = {
            'linear': SystemFactory._is_linear_system(equations),
            'polynomial': SystemFactory._is_polynomial_system(equations),
            'chemical': SystemFactory._is_chemical_system(equations),
            'geometric': SystemFactory._is_geometric_system(equations),
            'dynamic': SystemFactory._is_dynamic_system(equations)
        }
        
        return {k: v for k, v in patterns.items() if v}
    
    @staticmethod
    def _is_linear_system(equations: List[str]) -> bool:
        """Check if system is linear."""
        for equation in equations:
            # Check for nonlinear operations
            if any(op in equation for op in ['**', '^', '*', 'sin', 'cos', 'exp', 'log']):
                # More sophisticated check needed - this is simplified
                if '**2' in equation or '^2' in equation:
                    return False
        return True
    
    @staticmethod
    def _is_polynomial_system(equations: List[str]) -> bool:
        """Check if system is polynomial."""
        for equation in equations:
            if any(func in equation for func in ['sin', 'cos', 'tan', 'exp', 'log']):
                return False
        return True
    
    @staticmethod
    def _is_chemical_system(equations: List[str]) -> bool:
        """Check if system represents chemical equilibrium."""
        chemical_indicators = ['pH', 'pK', 'log10', 'equilibrium', 'concentration']
        equation_text = ' '.join(equations).lower()
        
        return any(indicator in equation_text for indicator in chemical_indicators)
    
    @staticmethod
    def _is_geometric_system(equations: List[str]) -> bool:
        """Check if system represents geometric relationships."""
        geometric_indicators = ['**2', '^2', 'circle', 'radius', 'x**2', 'y**2']
        equation_text = ' '.join(equations)
        
        return any(indicator in equation_text for indicator in geometric_indicators)
    
    @staticmethod
    def _is_dynamic_system(equations: List[str]) -> bool:
        """Check if system represents dynamic/time-dependent relationships."""
        dynamic_indicators = ['dt', 'time', 'rate', 'derivative']
        equation_text = ' '.join(equations).lower()
        
        return any(indicator in equation_text for indicator in dynamic_indicators)
    
    @staticmethod
    def _apply_optimizations(system: EquationSystem, optimize_for: str, 
                           patterns: Dict[str, Any]) -> EquationSystem:
        """Apply optimizations based on patterns and hints."""
        # This would contain optimization logic based on detected patterns
        # For now, just add metadata
        system._optimization_hint = optimize_for
        system._detected_patterns = patterns
        return system
    
    @staticmethod
    def _create_linear_pattern(**params) -> EquationSystem:
        """Create linear system pattern."""
        n = params.get('size', 2)
        variables = [f'x{i}' for i in range(n)]
        
        # Create simple linear system: Ax = b
        equations = []
        for i in range(n):
            terms = []
            for j in range(n):
                coeff = params.get(f'a_{i}_{j}', 1.0 if i == j else 0.0)
                if coeff != 0:
                    terms.append(f"{coeff}*{variables[j]}")
            
            rhs = params.get(f'b_{i}', i + 1)
            equation = ' + '.join(terms) + f' - {rhs}'
            equations.append(equation)
        
        return EquationSystem(variables, equations)
    
    @staticmethod
    def _create_circle_line_pattern(**params) -> EquationSystem:
        """Create circle-line intersection pattern."""
        radius = params.get('radius', 'r')
        slope = params.get('slope', 'm')
        intercept = params.get('intercept', 'b')
        
        variables = ['x', 'y']
        equations = [
            f'x**2 + y**2 - {radius}**2',
            f'y - {slope}*x - {intercept}'
        ]
        
        parameters = {}
        if isinstance(radius, (int, float)):
            parameters['r'] = radius
        if isinstance(slope, (int, float)):
            parameters['m'] = slope
        if isinstance(intercept, (int, float)):
            parameters['b'] = intercept
        
        return EquationSystem(variables, equations, parameters=parameters)
    
    @staticmethod
    def _create_chemical_pattern(**params) -> EquationSystem:
        """Create chemical equilibrium pattern."""
        system_type = params.get('type', 'simple_acid_base')
        
        if system_type == 'carbonate':
            builder = ChemicalSystemBuilder()
            return builder.build_carbonate_system(
                pH=params.get('pH', 8.0),
                total_co2=params.get('total_co2', 1e-3),
                pK1=params.get('pK1', 6.35),
                pK2=params.get('pK2', 10.33)
            )
        else:
            # Simple acid-base system
            variables = ['pHA', 'pA', 'pH', 'pOH']
            equations = [
                f"pKa - pA - pH + pHA",
                f"pKw - pH - pOH",
                f"pHA + pA - pTotal"
            ]
            
            parameters = {
                'pKa': params.get('pKa', 4.75),
                'pKw': params.get('pKw', 14.0),
                'pTotal': params.get('pTotal', 3.0),
                'pH': params.get('pH', 7.0)
            }
            
            return EquationSystem(variables, equations, parameters=parameters)
    
    @staticmethod
    def _create_predator_prey_pattern(**params) -> EquationSystem:
        """Create predator-prey (Lotka-Volterra) pattern."""
        variables = ['prey', 'predator']
        equations = [
            f"alpha*prey - beta*prey*predator",
            f"delta*prey*predator - gamma*predator"
        ]
        
        parameters = {
            'alpha': params.get('alpha', 1.0),   # prey growth rate
            'beta': params.get('beta', 0.1),     # predation rate
            'delta': params.get('delta', 0.075), # predator efficiency
            'gamma': params.get('gamma', 1.5)    # predator death rate
        }
        
        return EquationSystem(variables, equations, parameters=parameters)
    
    @staticmethod
    def _create_optimization_pattern(**params) -> EquationSystem:
        """Create optimization problem as equation system."""
        # Convert optimization to KKT conditions
        # This is a simplified placeholder
        objective = params.get('objective', 'x**2 + y**2')
        constraints = params.get('constraints', [])
        
        variables = SystemFactory._extract_variables([objective] + constraints)
        
        # Add Lagrange multipliers
        for i in range(len(constraints)):
            variables.append(f'lambda_{i}')
        
        # Create KKT equations (simplified)
        equations = []
        for var in variables:
            if not var.startswith('lambda_'):
                equations.append(f'd_{objective}_d_{var}')  # Gradient condition
        
        return EquationSystem(variables, equations, parameters=params.get('parameters', {}))


class TemplateFactory:
    """Factory for creating systems from predefined templates."""
    
    def __init__(self, template_directory: Optional[str] = None):
        """Initialize template factory.
        
        Args:
            template_directory: Directory containing template files
        """
        self.template_directory = template_directory or self._get_default_templates_dir()
        self._templates_cache: Dict[str, Dict[str, Any]] = {}
    
    def _get_default_templates_dir(self) -> str:
        """Get default templates directory."""
        # In a real implementation, this would point to package templates
        return str(Path(__file__).parent / "templates")
    
    def list_templates(self) -> List[str]:
        """List available templates."""
        template_dir = Path(self.template_directory)
        if not template_dir.exists():
            return []
        
        templates = []
        for file_path in template_dir.glob("*.json"):
            templates.append(file_path.stem)
        
        return templates
    
    def load_template(self, template_name: str) -> Dict[str, Any]:
        """Load template from file."""
        if template_name in self._templates_cache:
            return self._templates_cache[template_name]
        
        template_path = Path(self.template_directory) / f"{template_name}.json"
        if not template_path.exists():
            raise FileNotFoundError(f"Template '{template_name}' not found")
        
        with open(template_path, 'r') as f:
            template = json.load(f)
        
        self._templates_cache[template_name] = template
        return template
    
    def create_from_template(self, template_name: str, **parameters) -> EquationSystem:
        """Create system from template with parameter substitution.
        
        Args:
            template_name: Name of template to use
            **parameters: Parameters to substitute in template
            
        Returns:
            Configured EquationSystem
        """
        template = self.load_template(template_name)
        
        # Substitute parameters in template
        variables = template['variables']
        equations = template['equations']
        default_params = template.get('default_parameters', {})
        
        # Merge default parameters with provided parameters
        final_params = {**default_params, **parameters}
        
        # Substitute parameters in equations
        substituted_equations = []
        for equation in equations:
            substituted_eq = equation
            for param_name, param_value in final_params.items():
                substituted_eq = substituted_eq.replace(f"{{{param_name}}}", str(param_value))
            substituted_equations.append(substituted_eq)
        
        return EquationSystem(
            dependent_variables=variables,
            equations=substituted_equations,
            parameters=final_params,
            independent_variables=template.get('independent_variables', [])
        )
    
    def save_template(self, template_name: str, system: EquationSystem, 
                     description: str = "", **metadata) -> None:
        """Save system as template.
        
        Args:
            template_name: Name for the template
            system: EquationSystem to save as template
            description: Template description
            **metadata: Additional template metadata
        """
        template_dir = Path(self.template_directory)
        template_dir.mkdir(parents=True, exist_ok=True)
        
        template = {
            'name': template_name,
            'description': description,
            'variables': system.dependent_variables,
            'equations': system.equations,
            'independent_variables': system.independent_variables,
            'default_parameters': system.parameters,
            'metadata': metadata
        }
        
        template_path = template_dir / f"{template_name}.json"
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)


class ChemicalFactory:
    """Specialized factory for chemical equilibrium systems."""
    
    @staticmethod
    def create_acid_base_system(pKa: float, pH: float = 7.0, 
                               total_concentration: float = 1e-3) -> EquationSystem:
        """Create simple acid-base equilibrium system."""
        builder = ChemicalSystemBuilder()
        return (builder
                .add_species(['HA', 'A-', 'H+', 'OH-'])
                .add_equilibrium('HA <-> A- + H+', 10**(-pKa))
                .add_water_autoionization()
                .add_mass_balance('acid', ['HA', 'A-'], total_concentration)
                .set_conditions(pH=pH)
                .build())
    
    @staticmethod
    def create_buffer_system(pKa: float, pH: float, 
                           total_concentration: float = 1e-3) -> EquationSystem:
        """Create buffer system."""
        return ChemicalFactory.create_acid_base_system(pKa, pH, total_concentration)
    
    @staticmethod
    def create_carbonate_system(pH: float = 8.1, total_co2: float = 1e-3,
                               temperature: float = 25.0) -> EquationSystem:
        """Create carbonate equilibrium system."""
        # Temperature-dependent pK values (simplified)
        pK1 = 6.35 + (temperature - 25) * 0.01  # Simplified temperature dependence
        pK2 = 10.33 + (temperature - 25) * 0.01
        
        builder = ChemicalSystemBuilder()
        return builder.build_carbonate_system(pH, total_co2, pK1, pK2)
    
    @staticmethod
    def create_polyprotic_acid(pKa_values: List[float], pH: float = 7.0,
                              total_concentration: float = 1e-3) -> EquationSystem:
        """Create polyprotic acid system."""
        n_protons = len(pKa_values)
        builder = ChemicalSystemBuilder()
        
        # Add species (H_nA, H_{n-1}A-, ..., A^{n-})
        species = []
        for i in range(n_protons + 1):
            if i == 0:
                species.append(f'H{n_protons}A')
            elif i == n_protons:
                species.append(f'A{n_protons}-')
            else:
                species.append(f'H{n_protons-i}A{i-1}-')
        
        species.extend(['H+', 'OH-'])
        builder.add_species(species)
        
        # Add equilibria
        for i, pKa in enumerate(pKa_values):
            builder.add_equilibrium(f'{species[i]} <-> {species[i+1]} + H+', 10**(-pKa))
        
        builder.add_water_autoionization()
        builder.add_mass_balance('acid', species[:-2], total_concentration)  # Exclude H+, OH-
        builder.set_conditions(pH=pH)
        
        return builder.build()


class ConfigurationFactory:
    """Factory for creating systems from configuration files."""
    
    @staticmethod
    def from_json(config_path: str) -> EquationSystem:
        """Create system from JSON configuration."""
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return EquationSystem(
            dependent_variables=config['variables'],
            equations=config['equations'],
            parameters=config.get('parameters', {}),
            independent_variables=config.get('independent_variables', [])
        )
    
    @staticmethod
    def from_yaml(config_path: str) -> EquationSystem:
        """Create system from YAML configuration."""
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML is required for YAML configuration support")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        return EquationSystem(
            dependent_variables=config['variables'],
            equations=config['equations'],
            parameters=config.get('parameters', {}),
            independent_variables=config.get('independent_variables', [])
        )
    
    @staticmethod
    def to_json(system: EquationSystem, output_path: str) -> None:
        """Save system to JSON configuration."""
        config = {
            'variables': system.dependent_variables,
            'equations': system.equations,
            'parameters': system.parameters,
            'independent_variables': system.independent_variables
        }
        
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)


# Convenience functions for common patterns
def create_simple_system(equations: List[str], variables: Optional[List[str]] = None, 
                        **kwargs) -> EquationSystem:
    """Quick system creation with minimal configuration."""
    return SystemFactory.from_equations(equations, variables, **kwargs)


def create_chemical_system(system_type: str = 'acid_base', **params) -> EquationSystem:
    """Quick chemical system creation."""
    if system_type == 'acid_base':
        return ChemicalFactory.create_acid_base_system(**params)
    elif system_type == 'carbonate':
        return ChemicalFactory.create_carbonate_system(**params)
    elif system_type == 'buffer':
        return ChemicalFactory.create_buffer_system(**params)
    else:
        return SystemFactory.from_pattern('chemical_equilibrium', type=system_type, **params)


def create_from_pattern(pattern: str, **params) -> EquationSystem:
    """Quick pattern-based system creation."""
    return SystemFactory.from_pattern(pattern, **params)
