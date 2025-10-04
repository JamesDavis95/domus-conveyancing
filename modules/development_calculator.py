"""
Development Calculator - ROI Engine for Viability Analysis
Calculates GDV, costs, profits, IRR, and residual land values for development projects
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP
import math
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class UnitType:
    """Definition of a unit type in the scheme"""
    name: str  # e.g., "1-bed flat", "3-bed house"
    count: int
    size_sqft: float
    size_sqm: float
    value_per_sqft: float
    total_value: float
    
    def __post_init__(self):
        if self.size_sqm == 0 and self.size_sqft > 0:
            self.size_sqm = self.size_sqft * 0.092903  # Convert sqft to sqm
        elif self.size_sqft == 0 and self.size_sqm > 0:
            self.size_sqft = self.size_sqm * 10.7639  # Convert sqm to sqft
        
        if self.total_value == 0:
            self.total_value = self.count * self.size_sqft * self.value_per_sqft

@dataclass
class LandCosts:
    """Land acquisition costs"""
    purchase_price: float
    stamp_duty: float = 0
    legal_fees: float = 0
    survey_costs: float = 0
    other_costs: float = 0
    
    def __post_init__(self):
        if self.stamp_duty == 0:
            self.stamp_duty = self.calculate_stamp_duty(self.purchase_price)
        if self.legal_fees == 0:
            self.legal_fees = max(5000, self.purchase_price * 0.01)  # 1% or £5k min
        if self.survey_costs == 0:
            self.survey_costs = max(2000, self.purchase_price * 0.005)  # 0.5% or £2k min
    
    @property
    def total(self) -> float:
        return sum([
            self.purchase_price,
            self.stamp_duty,
            self.legal_fees,
            self.survey_costs,
            self.other_costs
        ])
    
    @staticmethod
    def calculate_stamp_duty(price: float) -> float:
        """Calculate stamp duty for land purchase"""
        if price <= 150000:
            return 0
        elif price <= 250000:
            return (price - 150000) * 0.02
        elif price <= 925000:
            return 2000 + (price - 250000) * 0.05
        elif price <= 1500000:
            return 35750 + (price - 925000) * 0.10
        else:
            return 93250 + (price - 1500000) * 0.12

@dataclass
class BuildCosts:
    """Construction and development costs"""
    base_build_cost_sqft: float
    total_sqft: float
    external_works_percent: float = 15  # % of build cost
    contingency_percent: float = 5  # % of build cost
    professional_fees_percent: float = 12  # % of build cost
    other_costs: float = 0
    
    @property
    def base_build_cost(self) -> float:
        return self.base_build_cost_sqft * self.total_sqft
    
    @property
    def external_works(self) -> float:
        return self.base_build_cost * (self.external_works_percent / 100)
    
    @property
    def contingency(self) -> float:
        return self.base_build_cost * (self.contingency_percent / 100)
    
    @property
    def professional_fees(self) -> float:
        return self.base_build_cost * (self.professional_fees_percent / 100)
    
    @property
    def total(self) -> float:
        return sum([
            self.base_build_cost,
            self.external_works,
            self.contingency,
            self.professional_fees,
            self.other_costs
        ])

@dataclass
class PlanningCosts:
    """Planning and regulatory costs"""
    planning_application_fee: float = 0
    cil_total: float = 0  # Community Infrastructure Levy
    s106_contributions: float = 0  # Section 106 contributions
    bng_cost: float = 0  # Biodiversity Net Gain
    other_contributions: float = 0
    
    @property
    def total(self) -> float:
        return sum([
            self.planning_application_fee,
            self.cil_total,
            self.s106_contributions,
            self.bng_cost,
            self.other_contributions
        ])

@dataclass
class FinanceCosts:
    """Finance and holding costs"""
    interest_rate_percent: float = 6.5  # Annual interest rate
    development_period_months: float = 18  # Total development period
    sales_period_months: float = 6  # Sales period
    arrangement_fee: float = 0  # Loan arrangement fee
    monitoring_fee: float = 0  # Lender monitoring fee
    exit_fee_percent: float = 1  # % of loan on exit
    
    def calculate_finance_cost(self, total_cost: float) -> float:
        """Calculate total finance cost based on development cashflow"""
        monthly_rate = self.interest_rate_percent / 100 / 12
        
        # Simplified cashflow: assume costs drawn down evenly over development period
        # and sales occur evenly over sales period
        avg_loan_months = (self.development_period_months / 2) + (self.sales_period_months / 2)
        
        interest_cost = total_cost * monthly_rate * avg_loan_months
        exit_fee = total_cost * (self.exit_fee_percent / 100)
        
        return interest_cost + exit_fee + self.arrangement_fee + self.monitoring_fee

@dataclass
class SalesCosts:
    """Sales and marketing costs"""
    agent_fee_percent: float = 1.5  # % of GDV
    legal_fees_percent: float = 0.5  # % of GDV
    marketing_cost: float = 0  # Fixed marketing cost
    show_home_cost: float = 0  # Show home costs
    other_costs: float = 0
    
    def calculate_total(self, gdv: float) -> float:
        """Calculate total sales costs"""
        agent_fees = gdv * (self.agent_fee_percent / 100)
        legal_fees = gdv * (self.legal_fees_percent / 100)
        
        return agent_fees + legal_fees + self.marketing_cost + self.show_home_cost + self.other_costs

@dataclass
class ViabilityInputs:
    """Complete viability assessment inputs"""
    project_name: str
    unit_types: List[UnitType]
    land_costs: LandCosts
    build_costs: BuildCosts
    planning_costs: PlanningCosts
    finance_costs: FinanceCosts
    sales_costs: SalesCosts
    developer_profit_percent: float = 20  # % of GDV
    
    @property
    def total_units(self) -> int:
        return sum(unit.count for unit in self.unit_types)
    
    @property
    def total_sqft(self) -> float:
        return sum(unit.count * unit.size_sqft for unit in self.unit_types)
    
    @property
    def gdv(self) -> float:
        """Gross Development Value"""
        return sum(unit.total_value for unit in self.unit_types)

@dataclass
class ViabilityResults:
    """Viability assessment results"""
    gdv: float
    total_costs: float
    developer_profit: float
    developer_profit_percent: float
    net_profit: float
    profit_margin_percent: float
    residual_land_value: float
    land_value_per_acre: float
    land_value_per_sqft: float
    irr_percent: float
    cost_breakdown: Dict[str, float]
    sensitivity_analysis: Dict[str, Dict[str, float]]
    
    @property
    def is_viable(self) -> bool:
        """Check if development is viable"""
        return self.net_profit > 0 and self.profit_margin_percent >= 15

class DevelopmentCalculator:
    """Main development viability calculator"""
    
    def __init__(self):
        self.build_cost_presets = self._get_build_cost_presets()
        self.cil_rates = self._get_cil_rates()
    
    def _get_build_cost_presets(self) -> Dict[str, float]:
        """Get build cost presets per square foot"""
        return {
            "apartments_basic": 120,
            "apartments_premium": 180,
            "houses_basic": 100,
            "houses_premium": 140,
            "houses_luxury": 200,
            "commercial": 80,
            "mixed_use": 130
        }
    
    def _get_cil_rates(self) -> Dict[str, float]:
        """Get CIL rates by local authority (per sqm)"""
        return {
            "birmingham": 70,
            "manchester": 80,
            "bristol": 120,
            "cambridge": 150,
            "london_inner": 400,
            "london_outer": 200,
            "default": 100
        }
    
    def calculate_viability(self, inputs: ViabilityInputs) -> ViabilityResults:
        """Calculate complete viability assessment"""
        logger.info(f"Calculating viability for {inputs.project_name}")
        
        # Calculate GDV
        gdv = inputs.gdv
        
        # Calculate all cost components
        land_cost = inputs.land_costs.total
        build_cost = inputs.build_costs.total
        planning_cost = inputs.planning_costs.total
        
        # Calculate finance costs based on total development cost
        pre_finance_cost = land_cost + build_cost + planning_cost
        finance_cost = inputs.finance_costs.calculate_finance_cost(pre_finance_cost)
        
        # Calculate sales costs
        sales_cost = inputs.sales_costs.calculate_total(gdv)
        
        # Calculate developer profit
        developer_profit = gdv * (inputs.developer_profit_percent / 100)
        
        # Total costs
        total_costs = land_cost + build_cost + planning_cost + finance_cost + sales_cost + developer_profit
        
        # Net profit
        net_profit = gdv - total_costs
        profit_margin_percent = (net_profit / gdv * 100) if gdv > 0 else 0
        
        # Residual land value (what could be paid for land)
        costs_excluding_land = total_costs - land_cost
        residual_land_value = gdv - costs_excluding_land
        
        # Land value metrics (assume 1 acre for now - would be calculated from actual site area)
        site_area_acres = 1.0  # This would come from project data
        site_area_sqft = site_area_acres * 43560
        
        land_value_per_acre = residual_land_value / site_area_acres
        land_value_per_sqft = residual_land_value / site_area_sqft
        
        # IRR calculation (simplified)
        irr_percent = self._calculate_irr(inputs, gdv, total_costs)
        
        # Cost breakdown
        cost_breakdown = {
            "land": land_cost,
            "build": build_cost,
            "planning": planning_cost,
            "finance": finance_cost,
            "sales": sales_cost,
            "profit": developer_profit
        }
        
        # Sensitivity analysis
        sensitivity_analysis = self._calculate_sensitivity(inputs)
        
        results = ViabilityResults(
            gdv=gdv,
            total_costs=total_costs,
            developer_profit=developer_profit,
            developer_profit_percent=inputs.developer_profit_percent,
            net_profit=net_profit,
            profit_margin_percent=profit_margin_percent,
            residual_land_value=residual_land_value,
            land_value_per_acre=land_value_per_acre,
            land_value_per_sqft=land_value_per_sqft,
            irr_percent=irr_percent,
            cost_breakdown=cost_breakdown,
            sensitivity_analysis=sensitivity_analysis
        )
        
        logger.info(f"Viability calculated: {'VIABLE' if results.is_viable else 'NOT VIABLE'} - "
                   f"Profit margin: {profit_margin_percent:.1f}%")
        
        return results
    
    def _calculate_irr(self, inputs: ViabilityInputs, gdv: float, total_costs: float) -> float:
        """Calculate Internal Rate of Return (simplified)"""
        try:
            # Simplified IRR calculation
            # Assumes all costs in first period, all revenues at end
            initial_investment = total_costs
            final_return = gdv
            periods = inputs.finance_costs.development_period_months / 12  # Years
            
            if initial_investment <= 0 or final_return <= 0 or periods <= 0:
                return 0
            
            # IRR = (Final Value / Initial Value)^(1/periods) - 1
            irr = ((final_return / initial_investment) ** (1/periods) - 1) * 100
            
            return max(0, min(100, irr))  # Cap between 0% and 100%
        except:
            return 0
    
    def _calculate_sensitivity(self, inputs: ViabilityInputs) -> Dict[str, Dict[str, float]]:
        """Calculate sensitivity analysis for key variables"""
        base_result = self.calculate_viability(inputs)
        base_profit = base_result.net_profit
        
        sensitivity_vars = {
            "gdv": [-10, -5, 0, 5, 10],  # % changes
            "build_costs": [-10, -5, 0, 5, 10],
            "land_cost": [-10, -5, 0, 5, 10],
            "finance_rate": [-2, -1, 0, 1, 2]  # Percentage point changes
        }
        
        sensitivity_results = {}
        
        for var_name, changes in sensitivity_vars.items():
            sensitivity_results[var_name] = {}
            
            for change in changes:
                # Create modified inputs
                test_inputs = self._apply_sensitivity_change(inputs, var_name, change)
                test_result = self.calculate_viability(test_inputs)
                
                profit_change = ((test_result.net_profit - base_profit) / base_profit * 100) if base_profit != 0 else 0
                sensitivity_results[var_name][f"{change:+}%"] = round(profit_change, 1)
        
        return sensitivity_results
    
    def _apply_sensitivity_change(self, inputs: ViabilityInputs, var_name: str, change_percent: float) -> ViabilityInputs:
        """Apply sensitivity change to inputs"""
        # Deep copy inputs (simplified)
        import copy
        test_inputs = copy.deepcopy(inputs)
        
        if var_name == "gdv":
            # Adjust all unit values
            for unit in test_inputs.unit_types:
                unit.value_per_sqft *= (1 + change_percent / 100)
                unit.total_value = unit.count * unit.size_sqft * unit.value_per_sqft
        
        elif var_name == "build_costs":
            test_inputs.build_costs.base_build_cost_sqft *= (1 + change_percent / 100)
        
        elif var_name == "land_cost":
            test_inputs.land_costs.purchase_price *= (1 + change_percent / 100)
        
        elif var_name == "finance_rate":
            test_inputs.finance_costs.interest_rate_percent += change_percent
        
        return test_inputs
    
    def apply_planning_ai_scheme(self, ai_result: Dict[str, Any]) -> ViabilityInputs:
        """Convert Planning AI result to viability inputs"""
        # Extract scheme details from AI analysis
        scheme = ai_result.get("suggested_scheme", {})
        
        unit_types = []
        if "unit_mix" in scheme:
            for unit_name, unit_data in scheme["unit_mix"].items():
                # Default values from AI analysis or market data
                unit_types.append(UnitType(
                    name=unit_name,
                    count=unit_data.get("count", 1),
                    size_sqft=unit_data.get("size_sqft", 800),  # Default size
                    size_sqm=unit_data.get("size_sqm", 0),
                    value_per_sqft=unit_data.get("value_per_sqft", 400),  # Market rate
                    total_value=0  # Will be calculated
                ))
        
        # Default cost assumptions
        land_costs = LandCosts(purchase_price=500000)  # Would come from project data
        
        # Use build cost presets
        build_type = scheme.get("building_type", "houses_basic")
        build_cost_sqft = self.build_cost_presets.get(build_type, 120)
        total_sqft = sum(unit.count * unit.size_sqft for unit in unit_types)
        
        build_costs = BuildCosts(
            base_build_cost_sqft=build_cost_sqft,
            total_sqft=total_sqft
        )
        
        # Planning costs from AI analysis
        planning_costs = PlanningCosts(
            planning_application_fee=scheme.get("planning_fee", 2000),
            cil_total=scheme.get("cil_estimate", 0),
            s106_contributions=scheme.get("s106_estimate", 0)
        )
        
        finance_costs = FinanceCosts()
        sales_costs = SalesCosts()
        
        return ViabilityInputs(
            project_name=ai_result.get("project_name", "AI Generated Scheme"),
            unit_types=unit_types,
            land_costs=land_costs,
            build_costs=build_costs,
            planning_costs=planning_costs,
            finance_costs=finance_costs,
            sales_costs=sales_costs
        )
    
    def export_to_pdf(self, results: ViabilityResults) -> bytes:
        """Export viability assessment to PDF"""
        # This would generate a proper PDF report
        # For now, return a placeholder
        return b"PDF content would be generated here"
    
    def export_to_excel(self, inputs: ViabilityInputs, results: ViabilityResults) -> bytes:
        """Export viability model to Excel"""
        # This would generate an Excel file with full calculations
        # For now, return a placeholder
        return b"Excel content would be generated here"

# Helper functions for easy use
def create_sample_viability() -> ViabilityInputs:
    """Create sample viability assessment for testing"""
    unit_types = [
        UnitType(
            name="2-bed houses",
            count=8,
            size_sqft=900,
            size_sqm=0,
            value_per_sqft=450,
            total_value=0
        ),
        UnitType(
            name="3-bed houses", 
            count=6,
            size_sqft=1200,
            size_sqm=0,
            value_per_sqft=420,
            total_value=0
        )
    ]
    
    land_costs = LandCosts(purchase_price=800000)
    
    total_sqft = sum(unit.count * unit.size_sqft for unit in unit_types)
    build_costs = BuildCosts(
        base_build_cost_sqft=120,
        total_sqft=total_sqft
    )
    
    planning_costs = PlanningCosts(
        planning_application_fee=2500,
        cil_total=45000,
        s106_contributions=25000
    )
    
    finance_costs = FinanceCosts()
    sales_costs = SalesCosts()
    
    return ViabilityInputs(
        project_name="Sample Development",
        unit_types=unit_types,
        land_costs=land_costs,
        build_costs=build_costs,
        planning_costs=planning_costs,
        finance_costs=finance_costs,
        sales_costs=sales_costs
    )

# Global calculator instance
development_calculator = DevelopmentCalculator()

# Export classes and functions
__all__ = [
    "UnitType",
    "LandCosts", 
    "BuildCosts",
    "PlanningCosts",
    "FinanceCosts",
    "SalesCosts",
    "ViabilityInputs",
    "ViabilityResults",
    "DevelopmentCalculator",
    "development_calculator",
    "create_sample_viability"
]