"""
Scheme Variant Optimiser - What-If Engine for Development Schemes
Generates multiple scheme variants and ranks them by Planning Score × Profit
"""

from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import math
import random
from itertools import product
from datetime import datetime

from modules.development_calculator import (
    DevelopmentCalculator, ViabilityInputs, ViabilityResults,
    UnitType, LandCosts, BuildCosts, PlanningCosts, FinanceCosts, SalesCosts
)

logger = logging.getLogger(__name__)

class OptimisationStrategy(Enum):
    """Different optimisation strategies"""
    PROFIT_MAXIMISE = "profit_maximise"
    PLANNING_SAFE = "planning_safe"
    BALANCED = "balanced"
    QUICK_WIN = "quick_win"
    RISK_AVERSE = "risk_averse"

class ConstraintType(Enum):
    """Types of development constraints"""
    SITE_AREA = "site_area"
    HEIGHT_LIMIT = "height_limit"
    UNIT_COUNT_MAX = "unit_count_max"
    DENSITY_MAX = "density_max"
    PARKING_RATIO = "parking_ratio"
    AFFORDABLE_HOUSING = "affordable_housing"
    OPEN_SPACE = "open_space"
    FLOOD_ZONE = "flood_zone"

@dataclass
class SiteConstraints:
    """Physical and planning constraints on the site"""
    site_area_sqm: float
    site_area_acres: float
    max_height_stories: int = 3
    max_density_dph: float = 35  # Dwellings per hectare
    max_coverage_percent: float = 40  # Site coverage %
    required_parking_spaces: float = 1.5  # Per unit
    affordable_housing_percent: float = 0  # % required
    open_space_percent: float = 20  # % of site
    flood_zone: str = "1"  # 1, 2, 3a, 3b
    conservation_area: bool = False
    listed_building: bool = False
    green_belt: bool = False
    
    def __post_init__(self):
        if self.site_area_acres == 0 and self.site_area_sqm > 0:
            self.site_area_acres = self.site_area_sqm / 4047  # Convert sqm to acres
        elif self.site_area_sqm == 0 and self.site_area_acres > 0:
            self.site_area_sqm = self.site_area_acres * 4047  # Convert acres to sqm

@dataclass
class PlanningScoreFactors:
    """Factors that contribute to planning score"""
    policy_compliance: float = 0  # 0-100
    community_benefit: float = 0  # 0-100
    design_quality: float = 0  # 0-100
    sustainability: float = 0  # 0-100
    local_need_met: float = 0  # 0-100
    infrastructure_impact: float = 0  # 0-100 (negative impact = lower score)
    heritage_impact: float = 0  # 0-100
    environmental_impact: float = 0  # 0-100
    
    @property
    def overall_score(self) -> float:
        """Calculate weighted overall planning score"""
        weights = {
            "policy_compliance": 0.25,
            "community_benefit": 0.15,
            "design_quality": 0.15,
            "sustainability": 0.15,
            "local_need_met": 0.10,
            "infrastructure_impact": 0.10,
            "heritage_impact": 0.05,
            "environmental_impact": 0.05
        }
        
        total_score = 0
        for factor, weight in weights.items():
            total_score += getattr(self, factor) * weight
        
        return min(100, max(0, total_score))

@dataclass
class SchemeVariant:
    """A specific development scheme variant"""
    variant_id: str
    name: str
    description: str
    unit_types: List[UnitType]
    site_constraints: SiteConstraints
    planning_score_factors: PlanningScoreFactors
    viability_inputs: ViabilityInputs
    viability_results: Optional[ViabilityResults] = None
    planning_score: float = 0
    combined_score: float = 0  # Planning Score × Profit Score
    risk_factors: List[str] = None
    
    def __post_init__(self):
        if self.risk_factors is None:
            self.risk_factors = []
        self.planning_score = self.planning_score_factors.overall_score
    
    @property
    def total_units(self) -> int:
        return sum(unit.count for unit in self.unit_types)
    
    @property
    def density_dph(self) -> float:
        """Calculate density in dwellings per hectare"""
        hectares = self.site_constraints.site_area_sqm / 10000
        return self.total_units / hectares if hectares > 0 else 0
    
    @property
    def is_feasible(self) -> bool:
        """Check if variant meets basic constraints"""
        if self.total_units > self.site_constraints.max_density_dph * (self.site_constraints.site_area_sqm / 10000):
            return False
        if self.viability_results and not self.viability_results.is_viable:
            return False
        return True

@dataclass
class OptimisationParameters:
    """Parameters for scheme optimisation"""
    strategy: OptimisationStrategy
    max_variants: int = 50
    profit_weight: float = 0.6  # Weight for profit vs planning score
    planning_weight: float = 0.4
    min_planning_score: float = 60  # Minimum acceptable planning score
    min_profit_margin: float = 15  # Minimum profit margin %
    include_affordable: bool = True
    explore_heights: bool = True
    explore_densities: bool = True
    explore_unit_mix: bool = True

class VariantGenerator:
    """Generates scheme variants based on parameters"""
    
    def __init__(self, base_constraints: SiteConstraints):
        self.base_constraints = base_constraints
        self.calculator = DevelopmentCalculator()
        
        # Predefined unit type templates
        self.unit_templates = {
            "studio": {"size_sqft": 400, "value_per_sqft": 520},
            "1bed_flat": {"size_sqft": 550, "value_per_sqft": 480},
            "2bed_flat": {"size_sqft": 750, "value_per_sqft": 450},
            "2bed_house": {"size_sqft": 900, "value_per_sqft": 420},
            "3bed_house": {"size_sqft": 1200, "value_per_sqft": 400},
            "4bed_house": {"size_sqft": 1500, "value_per_sqft": 390},
            "affordable_rent": {"size_sqft": 850, "value_per_sqft": 200},
            "shared_ownership": {"size_sqft": 800, "value_per_sqft": 300}
        }
    
    def generate_unit_mix_variants(self, total_units_range: Tuple[int, int]) -> List[List[UnitType]]:
        """Generate different unit mix combinations"""
        variants = []
        min_units, max_units = total_units_range
        
        # Define mix strategies
        mix_strategies = [
            # All houses
            {"2bed_house": 0.4, "3bed_house": 0.6},
            # All flats
            {"1bed_flat": 0.3, "2bed_flat": 0.7},
            # Mixed development
            {"1bed_flat": 0.2, "2bed_flat": 0.3, "2bed_house": 0.3, "3bed_house": 0.2},
            # Family focused
            {"2bed_house": 0.3, "3bed_house": 0.5, "4bed_house": 0.2},
            # Starter homes
            {"studio": 0.2, "1bed_flat": 0.4, "2bed_flat": 0.4},
            # Premium mix
            {"2bed_flat": 0.4, "3bed_house": 0.4, "4bed_house": 0.2}
        ]
        
        # Add affordable housing variants if required
        if self.base_constraints.affordable_housing_percent > 0:
            for strategy in mix_strategies:
                affordable_strategy = strategy.copy()
                affordable_percent = self.base_constraints.affordable_housing_percent / 100
                
                # Reduce market housing proportionally
                for unit_type in affordable_strategy:
                    affordable_strategy[unit_type] *= (1 - affordable_percent)
                
                # Add affordable units
                affordable_strategy["affordable_rent"] = affordable_percent * 0.7
                affordable_strategy["shared_ownership"] = affordable_percent * 0.3
                
                mix_strategies.append(affordable_strategy)
        
        # Generate unit mixes for different total unit counts
        for total_units in range(min_units, max_units + 1, 2):
            for strategy in mix_strategies:
                unit_types = []
                
                for unit_name, proportion in strategy.items():
                    count = max(1, round(total_units * proportion))
                    template = self.unit_templates[unit_name]
                    
                    unit_types.append(UnitType(
                        name=unit_name,
                        count=count,
                        size_sqft=template["size_sqft"],
                        size_sqm=0,
                        value_per_sqft=template["value_per_sqft"],
                        total_value=0
                    ))
                
                # Adjust to exact total if needed
                actual_total = sum(unit.count for unit in unit_types)
                if actual_total != total_units and unit_types:
                    difference = total_units - actual_total
                    unit_types[0].count += difference
                    if unit_types[0].count < 1:
                        unit_types[0].count = 1
                
                variants.append(unit_types)
        
        return variants
    
    def calculate_planning_score(self, variant: SchemeVariant) -> PlanningScoreFactors:
        """Calculate planning score factors for a variant"""
        factors = PlanningScoreFactors()
        
        # Policy compliance - based on density and constraints
        density = variant.density_dph
        max_density = self.base_constraints.max_density_dph
        
        if density <= max_density * 0.8:
            factors.policy_compliance = 90
        elif density <= max_density:
            factors.policy_compliance = 75
        else:
            factors.policy_compliance = 40  # Over density
        
        # Community benefit - based on unit mix diversity and affordable housing
        unit_type_diversity = len(variant.unit_types)
        affordable_units = sum(unit.count for unit in variant.unit_types 
                              if "affordable" in unit.name or "shared" in unit.name)
        affordable_percent = (affordable_units / variant.total_units * 100) if variant.total_units > 0 else 0
        
        factors.community_benefit = min(100, unit_type_diversity * 15 + affordable_percent)
        
        # Design quality - based on unit sizes and site coverage
        avg_unit_size = sum(unit.size_sqft * unit.count for unit in variant.unit_types) / variant.total_units
        if avg_unit_size >= 1000:
            factors.design_quality = 85
        elif avg_unit_size >= 800:
            factors.design_quality = 70
        else:
            factors.design_quality = 55
        
        # Sustainability - bonus for higher density (within limits)
        if 25 <= density <= 40:
            factors.sustainability = 80
        elif 20 <= density <= 50:
            factors.sustainability = 65
        else:
            factors.sustainability = 50
        
        # Local need - favour family housing
        family_units = sum(unit.count for unit in variant.unit_types 
                          if "3bed" in unit.name or "4bed" in unit.name)
        family_percent = (family_units / variant.total_units * 100) if variant.total_units > 0 else 0
        factors.local_need_met = min(100, family_percent * 2 + 40)
        
        # Infrastructure impact - lower for fewer units
        if variant.total_units <= 10:
            factors.infrastructure_impact = 85
        elif variant.total_units <= 20:
            factors.infrastructure_impact = 70
        else:
            factors.infrastructure_impact = 55
        
        # Heritage impact - penalty for conservation areas
        if self.base_constraints.conservation_area:
            factors.heritage_impact = 60
        else:
            factors.heritage_impact = 80
        
        # Environmental impact - based on density and green space
        if density <= 30:
            factors.environmental_impact = 80
        else:
            factors.environmental_impact = 65
        
        return factors

class SchemeOptimiser:
    """Main scheme optimisation engine"""
    
    def __init__(self):
        self.calculator = DevelopmentCalculator()
        self.generator = None
    
    def optimise_scheme(self, 
                       site_constraints: SiteConstraints,
                       base_viability: ViabilityInputs,
                       parameters: OptimisationParameters) -> List[SchemeVariant]:
        """Run complete scheme optimisation"""
        
        logger.info(f"Starting scheme optimisation with strategy: {parameters.strategy.value}")
        
        self.generator = VariantGenerator(site_constraints)
        variants = []
        
        # Calculate feasible unit count range
        max_units_by_density = int(site_constraints.max_density_dph * (site_constraints.site_area_sqm / 10000))
        min_units = max(1, int(max_units_by_density * 0.3))
        max_units = min(max_units_by_density, 50)  # Practical limit
        
        logger.info(f"Unit range: {min_units} - {max_units} units")
        
        # Generate unit mix variants
        unit_mix_variants = self.generator.generate_unit_mix_variants((min_units, max_units))
        
        # Create scheme variants
        for i, unit_mix in enumerate(unit_mix_variants[:parameters.max_variants]):
            variant_id = f"VAR_{i+1:03d}"
            
            # Create variant inputs
            variant_inputs = self._create_variant_inputs(base_viability, unit_mix)
            
            # Create variant
            variant = SchemeVariant(
                variant_id=variant_id,
                name=f"Variant {i+1}",
                description=self._generate_variant_description(unit_mix),
                unit_types=unit_mix,
                site_constraints=site_constraints,
                planning_score_factors=PlanningScoreFactors(),
                viability_inputs=variant_inputs
            )
            
            # Calculate planning score
            variant.planning_score_factors = self.generator.calculate_planning_score(variant)
            variant.planning_score = variant.planning_score_factors.overall_score
            
            # Calculate viability
            try:
                variant.viability_results = self.calculator.calculate_viability(variant_inputs)
            except Exception as e:
                logger.warning(f"Viability calculation failed for {variant_id}: {e}")
                continue
            
            # Check feasibility
            if not variant.is_feasible:
                continue
            
            # Check minimum thresholds
            if variant.planning_score < parameters.min_planning_score:
                variant.risk_factors.append("Below minimum planning score")
            
            if variant.viability_results.profit_margin_percent < parameters.min_profit_margin:
                variant.risk_factors.append("Below minimum profit margin")
            
            # Calculate combined score
            profit_score = min(100, variant.viability_results.profit_margin_percent * 2)  # Scale to 0-100
            variant.combined_score = (
                variant.planning_score * parameters.planning_weight +
                profit_score * parameters.profit_weight
            )
            
            variants.append(variant)
        
        # Sort by combined score (descending)
        variants.sort(key=lambda v: v.combined_score, reverse=True)
        
        # Apply strategy-specific filtering
        variants = self._apply_strategy_filter(variants, parameters)
        
        logger.info(f"Generated {len(variants)} feasible variants")
        
        return variants[:20]  # Return top 20
    
    def _create_variant_inputs(self, base_inputs: ViabilityInputs, unit_mix: List[UnitType]) -> ViabilityInputs:
        """Create viability inputs for a variant"""
        # Copy base inputs and update unit mix
        import copy
        variant_inputs = copy.deepcopy(base_inputs)
        variant_inputs.unit_types = unit_mix
        
        # Update build costs based on total sqft
        total_sqft = sum(unit.count * unit.size_sqft for unit in unit_mix)
        variant_inputs.build_costs.total_sqft = total_sqft
        
        return variant_inputs
    
    def _generate_variant_description(self, unit_mix: List[UnitType]) -> str:
        """Generate human-readable description of variant"""
        total_units = sum(unit.count for unit in unit_mix)
        
        descriptions = []
        for unit in unit_mix:
            if unit.count > 0:
                descriptions.append(f"{unit.count}×{unit.name}")
        
        return f"{total_units} units: {', '.join(descriptions)}"
    
    def _apply_strategy_filter(self, variants: List[SchemeVariant], parameters: OptimisationParameters) -> List[SchemeVariant]:
        """Apply strategy-specific filtering"""
        if parameters.strategy == OptimisationStrategy.PROFIT_MAXIMISE:
            # Prioritise highest profit margins
            return sorted(variants, key=lambda v: v.viability_results.profit_margin_percent, reverse=True)
        
        elif parameters.strategy == OptimisationStrategy.PLANNING_SAFE:
            # Prioritise highest planning scores
            safe_variants = [v for v in variants if v.planning_score >= 75]
            return sorted(safe_variants, key=lambda v: v.planning_score, reverse=True)
        
        elif parameters.strategy == OptimisationStrategy.QUICK_WIN:
            # Prioritise smaller schemes with good returns
            quick_wins = [v for v in variants if v.total_units <= 15 and v.viability_results.profit_margin_percent >= 20]
            return sorted(quick_wins, key=lambda v: v.combined_score, reverse=True)
        
        elif parameters.strategy == OptimisationStrategy.RISK_AVERSE:
            # Prioritise variants with fewer risk factors
            low_risk = [v for v in variants if len(v.risk_factors) <= 1 and v.planning_score >= 70]
            return sorted(low_risk, key=lambda v: v.combined_score, reverse=True)
        
        else:  # BALANCED
            return variants

    def compare_variants(self, variants: List[SchemeVariant]) -> Dict[str, Any]:
        """Generate comparison analysis of top variants"""
        if not variants:
            return {"error": "No variants to compare"}
        
        top_5 = variants[:5]
        
        comparison = {
            "summary": {
                "total_variants": len(variants),
                "top_variant": top_5[0].name,
                "best_planning_score": max(v.planning_score for v in top_5),
                "best_profit_margin": max(v.viability_results.profit_margin_percent for v in top_5),
                "unit_range": f"{min(v.total_units for v in top_5)}-{max(v.total_units for v in top_5)} units"
            },
            "variants": []
        }
        
        for variant in top_5:
            variant_data = {
                "id": variant.variant_id,
                "name": variant.name,
                "description": variant.description,
                "total_units": variant.total_units,
                "density_dph": round(variant.density_dph, 1),
                "planning_score": round(variant.planning_score, 1),
                "profit_margin": round(variant.viability_results.profit_margin_percent, 1),
                "combined_score": round(variant.combined_score, 1),
                "gdv": variant.viability_results.gdv,
                "net_profit": variant.viability_results.net_profit,
                "risk_factors": variant.risk_factors,
                "unit_breakdown": [
                    {
                        "type": unit.name,
                        "count": unit.count,
                        "size_sqft": unit.size_sqft,
                        "value_per_sqft": unit.value_per_sqft
                    }
                    for unit in variant.unit_types
                ]
            }
            comparison["variants"].append(variant_data)
        
        return comparison
    
    def export_comparison(self, variants: List[SchemeVariant]) -> bytes:
        """Export variant comparison to Excel"""
        # This would generate detailed Excel comparison
        return b"Excel comparison would be generated here"

# Helper functions
def create_sample_optimisation() -> Tuple[SiteConstraints, ViabilityInputs, OptimisationParameters]:
    """Create sample optimisation for testing"""
    
    # Sample site constraints
    site_constraints = SiteConstraints(
        site_area_sqm=5000,  # 0.5 hectares
        site_area_acres=1.24,
        max_height_stories=3,
        max_density_dph=35,
        affordable_housing_percent=20
    )
    
    # Base viability inputs
    from modules.development_calculator import create_sample_viability
    base_viability = create_sample_viability()
    
    # Optimisation parameters
    parameters = OptimisationParameters(
        strategy=OptimisationStrategy.BALANCED,
        max_variants=30,
        profit_weight=0.6,
        planning_weight=0.4
    )
    
    return site_constraints, base_viability, parameters

# Global optimiser instance
scheme_optimiser = SchemeOptimiser()

# Export classes and functions
__all__ = [
    "OptimisationStrategy",
    "ConstraintType", 
    "SiteConstraints",
    "PlanningScoreFactors",
    "SchemeVariant",
    "OptimisationParameters",
    "VariantGenerator",
    "SchemeOptimiser",
    "scheme_optimiser",
    "create_sample_optimisation"
]