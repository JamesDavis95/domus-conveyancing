"""
Planning Recommendation Engine
Suggests design/policy adjustments to improve approval odds
"""
from typing import List, Dict, Any
import uuid

from .schemas import SiteInput, Constraint, Score, Recommendation, SeverityLevel


class RecommendationEngine:
    """Engine for generating planning improvement recommendations"""
    
    def __init__(self):
        self.recommendation_strategies = self._initialize_strategies()
    
    def _initialize_strategies(self) -> Dict[str, Any]:
        """Initialize recommendation strategies by constraint type"""
        return {
            "green_belt": {
                "strategies": [
                    {
                        "title": "Demonstrate Very Special Circumstances",
                        "category": "policy",
                        "description": "Prepare detailed case for very special circumstances that clearly outweigh Green Belt harm",
                        "impact_delta": 0.3,
                        "rationale": "Green Belt policy allows development in very special circumstances (NPPF Para 147-150)",
                        "policy_basis": ["NPPF Para 147-150", "Local Plan Green Belt Policy"]
                    },
                    {
                        "title": "Reduce Development Footprint",
                        "category": "design", 
                        "description": "Minimize building footprint and height to reduce visual impact on Green Belt openness",
                        "impact_delta": 0.2,
                        "rationale": "Reduced scale development causes less harm to Green Belt openness",
                        "policy_basis": ["NPPF Para 149", "Green Belt Design Guidance"]
                    }
                ]
            },
            "flood_zone": {
                "strategies": [
                    {
                        "title": "Sequential Test Compliance", 
                        "category": "policy",
                        "description": "Demonstrate no suitable alternative sites in lower flood risk areas",
                        "impact_delta": 0.25,
                        "rationale": "Sequential Test is required for development in flood risk areas",
                        "policy_basis": ["NPPF Para 162", "PPG Flood Risk"]
                    },
                    {
                        "title": "Flood Resilient Design",
                        "category": "design",
                        "description": "Incorporate flood resilient design measures including raised floor levels and flood barriers",
                        "impact_delta": 0.2,
                        "rationale": "Flood resilient design reduces vulnerability and demonstrates risk management",
                        "policy_basis": ["NPPF Para 165", "Building Regulations Part C"]
                    }
                ]
            },
            "conservation_area": {
                "strategies": [
                    {
                        "title": "Heritage Impact Assessment",
                        "category": "consultation",
                        "description": "Commission detailed Heritage Impact Assessment to demonstrate preservation of character",
                        "impact_delta": 0.25,
                        "rationale": "Heritage assessment demonstrates understanding of conservation area significance",
                        "policy_basis": ["NPPF Para 194-196", "Local Plan Heritage Policy"]
                    },
                    {
                        "title": "Traditional Materials and Design",
                        "category": "design", 
                        "description": "Use traditional materials and proportions that respect conservation area character",
                        "impact_delta": 0.3,
                        "rationale": "Appropriate design preserves and enhances conservation area character",
                        "policy_basis": ["NPPF Para 197", "Conservation Area Appraisal"]
                    }
                ]
            },
            "tree_preservation_order": {
                "strategies": [
                    {
                        "title": "Arboricultural Impact Assessment",
                        "category": "consultation",
                        "description": "Commission BS5837 compliant tree survey and impact assessment",
                        "impact_delta": 0.2,
                        "rationale": "Professional tree assessment demonstrates protection measures",
                        "policy_basis": ["BS5837:2012", "Local Plan Tree Policy"]
                    },
                    {
                        "title": "Tree Protection During Construction", 
                        "category": "mitigation",
                        "description": "Implement comprehensive tree protection measures during construction phase",
                        "impact_delta": 0.15,
                        "rationale": "Proper protection prevents damage to protected trees",
                        "policy_basis": ["BS5837:2012", "Tree Protection Conditions"]
                    }
                ]
            },
            "highways_access": {
                "strategies": [
                    {
                        "title": "Transport Statement",
                        "category": "consultation",
                        "description": "Prepare detailed Transport Statement demonstrating acceptable highway impact",
                        "impact_delta": 0.25,
                        "rationale": "Transport assessment addresses highway authority concerns",
                        "policy_basis": ["NPPF Para 108-111", "Local Transport Policy"]
                    },
                    {
                        "title": "Visibility Splay Improvements",
                        "category": "design",
                        "description": "Provide adequate visibility splays and improve access arrangements", 
                        "impact_delta": 0.2,
                        "rationale": "Improved visibility ensures highway safety",
                        "policy_basis": ["Highway Design Standards", "Manual for Streets"]
                    }
                ]
            }
        }
    
    async def generate_recommendations(
        self, 
        site: SiteInput, 
        constraints: List[Constraint], 
        score: Score
    ) -> List[Recommendation]:
        """
        Generate recommendations to improve planning prospects
        
        Args:
            site: Site information
            constraints: Detected constraints
            score: Current approval score
            
        Returns:
            List of recommendations to improve approval odds
        """
        
        recommendations = []
        
        # Generate constraint-specific recommendations
        for constraint in constraints:
            constraint_recommendations = self._get_constraint_recommendations(constraint)
            recommendations.extend(constraint_recommendations)
        
        # Add general recommendations based on score
        if score.approval_probability < 0.5:
            recommendations.extend(self._get_general_low_score_recommendations(site, score))
        
        # Add site-specific recommendations
        recommendations.extend(self._get_site_specific_recommendations(site))
        
        # Sort by impact and priority
        recommendations.sort(key=lambda r: (r.priority.value, -r.impact_delta))
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def _get_constraint_recommendations(self, constraint: Constraint) -> List[Recommendation]:
        """Get recommendations for a specific constraint"""
        
        recommendations = []
        constraint_type = constraint.type.value
        
        strategies = self.recommendation_strategies.get(constraint_type, {}).get("strategies", [])
        
        for strategy in strategies:
            # Adjust impact based on constraint severity
            severity_multiplier = {
                SeverityLevel.LOW: 1.0,
                SeverityLevel.MEDIUM: 0.8, 
                SeverityLevel.HIGH: 0.6,
                SeverityLevel.CRITICAL: 0.4
            }.get(constraint.severity, 0.8)
            
            adjusted_impact = strategy["impact_delta"] * severity_multiplier
            
            recommendation = Recommendation(
                recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                title=strategy["title"],
                description=strategy["description"],
                category=strategy["category"],
                impact_delta=adjusted_impact,
                rationale=strategy["rationale"],
                policy_basis=strategy["policy_basis"],
                priority=self._calculate_priority(constraint.severity, adjusted_impact)
            )
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _get_general_low_score_recommendations(self, site: SiteInput, score: Score) -> List[Recommendation]:
        """Generate general recommendations for low-scoring applications"""
        
        recommendations = []
        
        if score.approval_probability < 0.3:
            recommendations.append(Recommendation(
                recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                title="Pre-Application Consultation",
                description="Engage in comprehensive pre-application discussions with the Local Planning Authority",
                category="consultation",
                impact_delta=0.2,
                rationale="Pre-application advice identifies concerns early and demonstrates collaborative approach",
                policy_basis=["Local Validation Requirements", "Pre-App Service Standards"],
                priority=SeverityLevel.HIGH
            ))
        
        if score.approval_probability < 0.4:
            recommendations.append(Recommendation(
                recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                title="Community Consultation", 
                description="Undertake proactive community engagement to address local concerns",
                category="consultation",
                impact_delta=0.15,
                rationale="Community support can influence planning committee decisions positively",
                policy_basis=["Statement of Community Involvement", "NPPF Para 39-46"],
                priority=SeverityLevel.MEDIUM
            ))
        
        return recommendations
    
    def _get_site_specific_recommendations(self, site: SiteInput) -> List[Recommendation]:
        """Generate site-specific recommendations"""
        
        recommendations = []
        
        # Recommendations based on proposed use
        if site.proposed_use and "residential" in site.proposed_use.lower():
            recommendations.append(Recommendation(
                recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                title="Affordable Housing Provision",
                description="Consider policy-compliant affordable housing provision to meet local needs",
                category="policy",
                impact_delta=0.1,
                rationale="Affordable housing provision meets policy requirements and local needs",
                policy_basis=["Local Plan Housing Policy", "NPPF Para 62-65"],
                priority=SeverityLevel.MEDIUM
            ))
        
        return recommendations
    
    def _calculate_priority(self, constraint_severity: SeverityLevel, impact_delta: float) -> SeverityLevel:
        """Calculate recommendation priority based on constraint severity and impact"""
        
        if constraint_severity == SeverityLevel.CRITICAL or impact_delta > 0.25:
            return SeverityLevel.HIGH
        elif constraint_severity == SeverityLevel.HIGH or impact_delta > 0.15:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW


# Singleton engine instance
recommendation_engine = RecommendationEngine()


async def generate_site_recommendations(
    site: SiteInput, 
    constraints: List[Constraint], 
    score: Score
) -> List[Recommendation]:
    """Convenience function to generate site recommendations"""
    return await recommendation_engine.generate_recommendations(site, constraints, score)


def generate_recommendations(site: SiteInput, constraints: List[Constraint], score: Score) -> List[Recommendation]:
    """
    Generate recommendations synchronously (wrapper for async function)
    Required for compatibility with existing router imports
    """
    import asyncio
    
    # Check if we're in an async context
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context, create a task
        return asyncio.create_task(recommendation_engine.generate_recommendations(site, constraints, score))
    except RuntimeError:
        # No running event loop, run synchronously
        return asyncio.run(recommendation_engine.generate_recommendations(site, constraints, score))