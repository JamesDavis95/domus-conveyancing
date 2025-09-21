"""
Planning AI Scoring Engine
Provides approval probability and rationale for planning applications
"""
from typing import Dict, List, Optional
import asyncio
import json
from datetime import datetime
import uuid

from .schemas import SiteInput, Score, Constraint


class PlanningScorer:
    """AI-powered planning approval probability scorer"""
    
    def __init__(self, model_version: str = "v1.0"):
        self.model_version = model_version
        self.base_weights = {
            "green_belt": -0.4,
            "flood_zone": -0.3,
            "conservation_area": -0.2,
            "tree_preservation_order": -0.15,
            "highways_access": -0.25,
            "sssi": -0.45,
            "aonb": -0.2,
            "listed_building": -0.35,
            "scheduled_monument": -0.4
        }
    
    async def score_site(self, site: SiteInput, constraints: List[Constraint]) -> Score:
        """
        Calculate approval probability based on site and constraints
        
        Args:
            site: Site information
            constraints: List of planning constraints
            
        Returns:
            Score with probability, confidence, and rationale
        """
        
        # Base probability (varies by LPA and use type)
        base_probability = self._get_base_probability(site)
        
        # Apply constraint penalties
        constraint_impact = self._calculate_constraint_impact(constraints)
        
        # Final probability
        final_probability = max(0.0, min(1.0, base_probability + constraint_impact))
        
        # Generate rationale
        rationale, key_factors = self._generate_rationale(
            site, constraints, base_probability, constraint_impact, final_probability
        )
        
        # Calculate confidence based on data quality and constraint clarity
        confidence = self._calculate_confidence(constraints)
        
        return Score(
            site_id=f"site_{uuid.uuid4().hex[:8]}",
            model_version=self.model_version,
            approval_probability=final_probability,
            confidence_score=confidence,
            rationale=rationale,
            key_factors=key_factors,
            similar_cases=[]  # TODO: Implement case similarity search
        )
    
    def _get_base_probability(self, site: SiteInput) -> float:
        """Calculate base approval probability by LPA and use type"""
        
        # Base rates by common use types (simplified)
        use_type_rates = {
            "residential": 0.75,
            "commercial": 0.65,
            "industrial": 0.60,
            "retail": 0.70,
            "office": 0.72,
            "mixed_use": 0.68
        }
        
        # Extract use type from proposal
        detected_use = "residential"  # Default
        if site.proposed_use:
            for use_type in use_type_rates.keys():
                if use_type.lower() in site.proposed_use.lower():
                    detected_use = use_type
                    break
        
        return use_type_rates.get(detected_use, 0.65)
    
    def _calculate_constraint_impact(self, constraints: List[Constraint]) -> float:
        """Calculate cumulative impact of all constraints"""
        
        total_impact = 0.0
        
        for constraint in constraints:
            # Get base weight for constraint type
            base_weight = self.base_weights.get(constraint.type.value, -0.1)
            
            # Adjust by severity
            severity_multiplier = {
                "low": 0.3,
                "medium": 0.7,
                "high": 1.0,
                "critical": 1.5
            }.get(constraint.severity.value, 1.0)
            
            # Adjust by distance (if applicable)
            distance_multiplier = 1.0
            if constraint.distance_m is not None:
                if constraint.distance_m > 500:
                    distance_multiplier = 0.3
                elif constraint.distance_m > 100:
                    distance_multiplier = 0.6
            
            constraint_impact = base_weight * severity_multiplier * distance_multiplier
            total_impact += constraint_impact
        
        return total_impact
    
    def _generate_rationale(
        self, 
        site: SiteInput, 
        constraints: List[Constraint],
        base_prob: float,
        constraint_impact: float,
        final_prob: float
    ) -> tuple[str, List[str]]:
        """Generate human-readable rationale for the score"""
        
        key_factors = []
        rationale_parts = []
        
        # Base assessment
        if base_prob > 0.7:
            rationale_parts.append(f"The proposed {site.proposed_use or 'development'} "
                                 f"in {site.local_planning_authority} has a favorable base approval rate.")
        elif base_prob < 0.6:
            rationale_parts.append(f"The proposed {site.proposed_use or 'development'} "
                                 f"faces baseline challenges in {site.local_planning_authority}.")
        
        # Constraint analysis
        high_impact_constraints = [c for c in constraints if c.severity.value in ["high", "critical"]]
        
        if high_impact_constraints:
            constraint_names = [c.title for c in high_impact_constraints[:3]]
            rationale_parts.append(f"Significant constraints include: {', '.join(constraint_names)}.")
            key_factors.extend(constraint_names)
        
        # Overall assessment
        if final_prob > 0.8:
            rationale_parts.append("The application has strong prospects for approval.")
        elif final_prob > 0.6:
            rationale_parts.append("The application has reasonable prospects, with some challenges to address.")
        elif final_prob > 0.4:
            rationale_parts.append("The application faces significant challenges requiring careful planning.")
        else:
            rationale_parts.append("The application faces severe constraints requiring substantial mitigation.")
        
        # Add policy guidance hint
        if constraints:
            rationale_parts.append("Consider pre-application advice to address key constraints.")
        
        return " ".join(rationale_parts), key_factors
    
    def _calculate_confidence(self, constraints: List[Constraint]) -> float:
        """Calculate confidence score based on data quality"""
        
        if not constraints:
            return 0.6  # Medium confidence with minimal data
        
        # Higher confidence with more constraint data sources
        data_sources = set(c.source for c in constraints)
        source_confidence = min(1.0, len(data_sources) * 0.2 + 0.4)
        
        # Higher confidence with detailed constraint metadata
        detailed_constraints = sum(1 for c in constraints if c.metadata)
        detail_confidence = min(1.0, detailed_constraints * 0.15 + 0.5)
        
        return (source_confidence + detail_confidence) / 2


# Singleton scorer instance
scorer = PlanningScorer()


async def score_planning_application(site: SiteInput, constraints: List[Constraint]) -> Score:
    """Convenience function to score a planning application"""
    return await scorer.score_site(site, constraints)


def calculate_approval_probability(site: SiteInput, constraints: List[Constraint], model_version: str = "v1.0") -> Score:
    """
    Calculate approval probability synchronously (wrapper for async function)
    Required for compatibility with existing router imports
    """
    import asyncio
    
    # Check if we're in an async context
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context, create a task
        return asyncio.create_task(scorer.score_site(site, constraints))
    except RuntimeError:
        # No running event loop, run synchronously
        return asyncio.run(scorer.score_site(site, constraints))