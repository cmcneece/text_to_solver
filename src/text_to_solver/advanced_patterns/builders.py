"""
Builder Pattern Implementation for TextToSolver

Provides guided construction of complex equation systems with validation,
templates, and domain-specific knowledge built-in.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
import numpy as np

# Import from parent modules
from ..user_api import EquationSystem, EquationSystemError


class SystemBuilder(ABC):
    """Abstract base class for system builders."""
    
    @abstractmethod
    def build(self) -> EquationSystem:
        """Build and return the equation system."""
        pass
    
    @abstractmethod
    def reset(self) -> 'SystemBuilder':
        """Reset the builder to initial state."""
        pass


class EquationSystemBuilder(SystemBuilder):
    """Builder for general equation systems with step-by-step construction."""
    
    def __init__(self):
        """Initialize equation system builder."""
        self.reset()
    
    def reset(self) -> 'EquationSystemBuilder':
        """Reset builder to initial state."""
        self._variables: List[str] = []
        self._equations: List[str] = []
        self._parameters: Dict[str, Union[int, float]] = {}
        self._independent_variables: List[str] = []
        self._constraints: List[str] = []
        self._metadata: Dict[str, Any] = {}
        return self
    
    def add_variable(self, name: str, description: Optional[str] = None) -> 'EquationSystemBuilder':
        """Add a dependent variable to the system.
        
        Args:
            name: Variable name
            description: Optional description
            
        Returns:
            Self for method chaining
        """
        if name in self._variables:
            raise EquationSystemError.duplicate_variables([name])
        
        self._variables.append(name)
        if description:
            self._metadata[f"{name}_description"] = description
        return self
    
    def add_variables(self, names: List[str]) -> 'EquationSystemBuilder':
        """Add multiple dependent variables.
        
        Args:
            names: List of variable names
            
        Returns:
            Self for method chaining
        """
        for name in names:
            self.add_variable(name)
        return self
    
    def add_equation(self, equation: str, description: Optional[str] = None) -> 'EquationSystemBuilder':
        """Add an equation to the system.
        
        Args:
            equation: Equation string
            description: Optional description
            
        Returns:
            Self for method chaining
        """
        self._equations.append(equation)
        if description:
            eq_idx = len(self._equations) - 1
            self._metadata[f"equation_{eq_idx}_description"] = description
        return self
    
    def add_equations(self, equations: List[str]) -> 'EquationSystemBuilder':
        """Add multiple equations.
        
        Args:
            equations: List of equation strings
            
        Returns:
            Self for method chaining
        """
        for equation in equations:
            self.add_equation(equation)
        return self
    
    def add_parameter(self, name: str, value: Union[int, float], 
                     description: Optional[str] = None) -> 'EquationSystemBuilder':
        """Add a parameter to the system.
        
        Args:
            name: Parameter name
            value: Parameter value
            description: Optional description
            
        Returns:
            Self for method chaining
        """
        self._parameters[name] = value
        if description:
            self._metadata[f"{name}_description"] = description
        return self
    
    def add_parameters(self, parameters: Dict[str, Union[int, float]]) -> 'EquationSystemBuilder':
        """Add multiple parameters.
        
        Args:
            parameters: Dictionary of parameter names and values
            
        Returns:
            Self for method chaining
        """
        self._parameters.update(parameters)
        return self
    
    def add_independent_variable(self, name: str) -> 'EquationSystemBuilder':
        """Add an independent variable.
        
        Args:
            name: Independent variable name
            
        Returns:
            Self for method chaining
        """
        if name not in self._independent_variables:
            self._independent_variables.append(name)
        return self
    
    def add_constraint(self, constraint: str) -> 'EquationSystemBuilder':
        """Add a constraint to validate the system.
        
        Args:
            constraint: Constraint description
            
        Returns:
            Self for method chaining
        """
        self._constraints.append(constraint)
        return self
    
    def set_metadata(self, key: str, value: Any) -> 'EquationSystemBuilder':
        """Set metadata for the system.
        
        Args:
            key: Metadata key
            value: Metadata value
            
        Returns:
            Self for method chaining
        """
        self._metadata[key] = value
        return self
    
    def validate_system(self) -> None:
        """Validate the system before building."""
        if not self._variables:
            raise EquationSystemError.validation_failed("No variables specified")
        
        if not self._equations:
            raise EquationSystemError.validation_failed("No equations specified")
        
        if len(self._variables) != len(self._equations):
            raise EquationSystemError.dimension_mismatch(
                len(self._variables), len(self._equations)
            )
    
    def build(self) -> EquationSystem:
        """Build and return the equation system."""
        self.validate_system()
        
        system = EquationSystem(
            dependent_variables=self._variables.copy(),
            equations=self._equations.copy(),
            independent_variables=self._independent_variables.copy(),
            parameters=self._parameters.copy()
        )
        
        # Add metadata if any
        if self._metadata:
            system._metadata = self._metadata.copy()
        
        return system


class ChemicalSystemBuilder(EquationSystemBuilder):
    """Specialized builder for chemical equilibrium systems."""
    
    def __init__(self):
        """Initialize chemical system builder."""
        super().__init__()
        self._init_chemical_attributes()
    
    def _init_chemical_attributes(self):
        """Initialize chemical-specific attributes."""
        self._species: List[str] = []
        self._equilibria: List[Dict[str, Any]] = []
        self._mass_balances: List[Dict[str, Any]] = []
        self._conditions: Dict[str, float] = {}
    
    def reset(self) -> 'ChemicalSystemBuilder':
        """Reset builder to initial state."""
        super().reset()
        self._init_chemical_attributes()
        return self
    
    def add_species(self, species: Union[str, List[str]], 
                   concentration_variable: Optional[str] = None) -> 'ChemicalSystemBuilder':
        """Add chemical species to the system.
        
        Args:
            species: Species name or list of species names
            concentration_variable: Optional custom concentration variable name
            
        Returns:
            Self for method chaining
        """
        if isinstance(species, str):
            species = [species]
        
        for spec in species:
            if spec not in self._species:
                self._species.append(spec)
                
                # Create concentration variable (default: p + species name for log concentration)
                var_name = concentration_variable or f"p{spec.replace('-', '').replace('+', '')}"
                self.add_variable(var_name, f"Negative log concentration of {spec}")
        
        return self
    
    def add_equilibrium(self, reaction: str, K: float, 
                       temperature_dependent: bool = False) -> 'ChemicalSystemBuilder':
        """Add chemical equilibrium reaction.
        
        Args:
            reaction: Reaction string (e.g., 'H2CO3 <-> HCO3- + H+')
            K: Equilibrium constant
            temperature_dependent: Whether K depends on temperature
            
        Returns:
            Self for method chaining
        """
        equilibrium = {
            'reaction': reaction,
            'K': K,
            'pK': -np.log10(K),
            'temperature_dependent': temperature_dependent
        }
        self._equilibria.append(equilibrium)
        
        # Parse reaction and create equilibrium equation
        equation = self._create_equilibrium_equation(reaction, K)
        self.add_equation(equation, f"Equilibrium: {reaction}")
        
        return self
    
    def add_mass_balance(self, name: str, species: List[str], 
                        total_concentration: Optional[float] = None) -> 'ChemicalSystemBuilder':
        """Add mass balance constraint.
        
        Args:
            name: Mass balance name
            species: List of species involved
            total_concentration: Total concentration (if known)
            
        Returns:
            Self for method chaining
        """
        mass_balance = {
            'name': name,
            'species': species,
            'total_concentration': total_concentration
        }
        self._mass_balances.append(mass_balance)
        
        # Create mass balance equation
        equation = self._create_mass_balance_equation(name, species, total_concentration)
        self.add_equation(equation, f"Mass balance: {name}")
        
        return self
    
    def set_conditions(self, **conditions) -> 'ChemicalSystemBuilder':
        """Set experimental conditions.
        
        Args:
            **conditions: Conditions like pH, temperature, ionic_strength, etc.
            
        Returns:
            Self for method chaining
        """
        self._conditions.update(conditions)
        
        # Add conditions as parameters or constraints
        for condition, value in conditions.items():
            if condition.lower() == 'ph':
                self.add_parameter('pH', value, 'Solution pH')
            elif condition.lower() == 'temperature':
                self.add_parameter('T', value, 'Temperature in Celsius')
            elif condition.lower() == 'ionic_strength':
                self.add_parameter('I', value, 'Ionic strength')
            else:
                self.add_parameter(condition, value)
        
        return self
    
    def add_water_autoionization(self, pKw: float = 14.0) -> 'ChemicalSystemBuilder':
        """Add water autoionization equilibrium.
        
        Args:
            pKw: Negative log of water autoionization constant
            
        Returns:
            Self for method chaining
        """
        self.add_species(['H+', 'OH-'])
        self.add_equilibrium('H2O <-> H+ + OH-', 10**(-pKw))
        self.add_parameter('pKw', pKw, 'Water autoionization constant')
        
        # Add the actual equilibrium equation
        self.add_equation('pKw - pH - pOH', 'Water autoionization')
        
        return self
    
    def _create_equilibrium_equation(self, reaction: str, K: float) -> str:
        """Create equilibrium equation from reaction string."""
        # Simplified parsing - would need more sophisticated parsing in practice
        pK = -np.log10(K)
        
        # For now, return a template equation
        # In practice, would parse reaction and create proper equation
        return f"{pK} - (products) + (reactants)"  # Placeholder
    
    def _create_mass_balance_equation(self, name: str, species: List[str], 
                                     total_conc: Optional[float]) -> str:
        """Create mass balance equation."""
        # Create equation in log space
        species_terms = []
        for spec in species:
            var_name = f"p{spec.replace('-', '').replace('+', '')}"
            species_terms.append(f"10**(-{var_name})")
        
        if total_conc is not None:
            total_term = str(total_conc)
        else:
            total_term = f"total_{name}"
            self.add_parameter(f"total_{name}", 1e-3, f"Total {name} concentration")
        
        equation = " + ".join(species_terms) + f" - {total_term}"
        return equation
    
    def build_carbonate_system(self, pH: float = 8.0, total_co2: float = 1e-3,
                              pK1: float = 6.35, pK2: float = 10.33) -> EquationSystem:
        """Build a complete carbonate system.
        
        Args:
            pH: Solution pH
            total_co2: Total CO2 concentration
            pK1: First dissociation constant
            pK2: Second dissociation constant
            
        Returns:
            Complete carbonate system
        """
        return (self.reset()
                .add_species(['H2CO3', 'HCO3-', 'CO3-2', 'H+', 'OH-'])
                .add_equilibrium('H2CO3 <-> HCO3- + H+', 10**(-pK1))
                .add_equilibrium('HCO3- <-> CO3-2 + H+', 10**(-pK2))
                .add_water_autoionization()
                .add_mass_balance('carbon', ['H2CO3', 'HCO3-', 'CO3-2'], total_co2)
                .set_conditions(pH=pH)
                .build())


class OptimizationProblemBuilder(EquationSystemBuilder):
    """Builder for optimization problems converted to equation systems."""
    
    def __init__(self):
        """Initialize optimization problem builder."""
        super().__init__()
        self._objective_function: Optional[str] = None
        self._constraints: List[str] = []
        self._bounds: Dict[str, Tuple[float, float]] = {}
    
    def set_objective(self, objective: str, minimize: bool = True) -> 'OptimizationProblemBuilder':
        """Set objective function.
        
        Args:
            objective: Objective function string
            minimize: Whether to minimize (True) or maximize (False)
            
        Returns:
            Self for method chaining
        """
        if not minimize:
            objective = f"-({objective})"
        self._objective_function = objective
        return self
    
    def add_inequality_constraint(self, constraint: str) -> 'OptimizationProblemBuilder':
        """Add inequality constraint (g(x) <= 0).
        
        Args:
            constraint: Constraint string
            
        Returns:
            Self for method chaining
        """
        self._constraints.append(constraint)
        return self
    
    def add_bounds(self, variable: str, lower: float, upper: float) -> 'OptimizationProblemBuilder':
        """Add variable bounds.
        
        Args:
            variable: Variable name
            lower: Lower bound
            upper: Upper bound
            
        Returns:
            Self for method chaining
        """
        self._bounds[variable] = (lower, upper)
        return self
    
    def build(self) -> EquationSystem:
        """Build optimization problem as equation system using KKT conditions."""
        if not self._objective_function:
            raise EquationSystemError.validation_failed("No objective function specified")
        
        # Convert optimization to equation system using KKT conditions
        # This is a simplified version - full implementation would be more complex
        
        # Add Lagrange multipliers
        for i, constraint in enumerate(self._constraints):
            self.add_variable(f"lambda_{i}", f"Lagrange multiplier for constraint {i}")
        
        # Add gradient of Lagrangian = 0 equations
        # Simplified - would need symbolic differentiation
        for var in self._variables:
            if not var.startswith('lambda_'):
                equation = f"d_L_d_{var}"  # Placeholder for gradient
                self.add_equation(equation, f"Gradient condition for {var}")
        
        # Add complementary slackness conditions
        for i, constraint in enumerate(self._constraints):
            self.add_equation(f"lambda_{i} * ({constraint})", 
                            f"Complementary slackness {i}")
        
        return super().build()


# Factory functions for common system types
def create_linear_system_builder() -> EquationSystemBuilder:
    """Create builder configured for linear systems."""
    return EquationSystemBuilder().set_metadata('system_type', 'linear')


def create_nonlinear_system_builder() -> EquationSystemBuilder:
    """Create builder configured for nonlinear systems."""
    return (EquationSystemBuilder()
            .set_metadata('system_type', 'nonlinear')
            .set_metadata('requires_good_initial_guess', True))


def create_chemical_equilibrium_builder() -> ChemicalSystemBuilder:
    """Create builder for chemical equilibrium systems."""
    return ChemicalSystemBuilder().set_metadata('domain', 'chemistry')
