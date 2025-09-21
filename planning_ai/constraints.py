"""
Planning Constraints Detection Engine
Rules engine to detect planning constraints affecting development sites
"""
from typing import List, Dict, Any, Optional
import asyncio
from dataclasses import dataclass
import math

from .schemas import SiteInput, Constraint, ConstraintType, SeverityLevel


@dataclass
class ConstraintRule:
    """Definition of a constraint detection rule"""
    constraint_type: ConstraintType
    title: str
    description: str
    source: str
    geometry_check: Optional[str] = None  # PostGIS query or similar
    buffer_distance: Optional[int] = None  # meters
    severity_rules: Dict[str, SeverityLevel] = None


class ConstraintsEngine:
    """Engine for detecting planning constraints on development sites"""
    
    def __init__(self):
        self.constraint_rules = self._initialize_rules()
    
    def _initialize_rules(self) -> List[ConstraintRule]:
        """Initialize constraint detection rules"""
        return [
            ConstraintRule(
                constraint_type=ConstraintType.GREEN_BELT,
                title="Green Belt Designation",
                description="Site is within or adjacent to Green Belt land",
                source="Local Planning Authority Designations",
                buffer_distance=50,
                severity_rules={
                    "within": SeverityLevel.CRITICAL,
                    "adjacent": SeverityLevel.HIGH
                }
            ),
            ConstraintRule(
                constraint_type=ConstraintType.FLOOD_ZONE,
                title="Flood Risk Zone",
                description="Site is within Environment Agency flood risk areas",
                source="Environment Agency Flood Risk Maps",
                severity_rules={
                    "zone_1": SeverityLevel.LOW,
                    "zone_2": SeverityLevel.MEDIUM,
                    "zone_3": SeverityLevel.HIGH,
                    "zone_3b": SeverityLevel.CRITICAL
                }
            ),
            ConstraintRule(
                constraint_type=ConstraintType.CONSERVATION_AREA,
                title="Conservation Area",
                description="Site is within a designated Conservation Area",
                source="Historic England / Local Planning Authority",
                buffer_distance=100,
                severity_rules={
                    "within": SeverityLevel.HIGH,
                    "adjacent": SeverityLevel.MEDIUM
                }
            ),
            ConstraintRule(
                constraint_type=ConstraintType.TREE_PRESERVATION_ORDER,
                title="Tree Preservation Order",
                description="Protected trees on or adjacent to the site",
                source="Local Planning Authority TPO Register",
                buffer_distance=25,
                severity_rules={
                    "on_site": SeverityLevel.HIGH,
                    "adjacent": SeverityLevel.MEDIUM
                }
            ),
            ConstraintRule(
                constraint_type=ConstraintType.HIGHWAYS_ACCESS,
                title="Highways Access Constraints",
                description="Limited highway access or visibility constraints",
                source="Highways Authority Records",
                severity_rules={
                    "major_road": SeverityLevel.HIGH,
                    "restricted_access": SeverityLevel.MEDIUM,
                    "visibility_splay": SeverityLevel.MEDIUM
                }
            ),
            ConstraintRule(
                constraint_type=ConstraintType.SSSI,
                title="Site of Special Scientific Interest",
                description="Site is within or adjacent to an SSSI",
                source="Natural England Designations",
                buffer_distance=500,
                severity_rules={
                    "within": SeverityLevel.CRITICAL,
                    "impact_zone": SeverityLevel.HIGH
                }
            ),
            ConstraintRule(
                constraint_type=ConstraintType.AONB,
                title="Area of Outstanding Natural Beauty",
                description="Site is within an AONB designation",
                source="Natural England AONB Designations",
                buffer_distance=100,
                severity_rules={
                    "within": SeverityLevel.HIGH,
                    "adjacent": SeverityLevel.MEDIUM
                }
            ),
            ConstraintRule(
                constraint_type=ConstraintType.LISTED_BUILDING,
                title="Listed Building",
                description="Listed buildings on or near the site",
                source="Historic England Listed Buildings Register",
                buffer_distance=50,
                severity_rules={
                    "grade_1": SeverityLevel.CRITICAL,
                    "grade_2_star": SeverityLevel.HIGH,
                    "grade_2": SeverityLevel.MEDIUM
                }
            ),
            ConstraintRule(
                constraint_type=ConstraintType.SCHEDULED_MONUMENT,
                title="Scheduled Ancient Monument",
                description="Scheduled monument on or adjacent to the site",
                source="Historic England Scheduled Monuments",
                buffer_distance=100,
                severity_rules={
                    "within": SeverityLevel.CRITICAL,
                    "adjacent": SeverityLevel.HIGH
                }
            )
        ]
    
    async def analyze_constraints(self, site: SiteInput) -> List[Constraint]:
        """
        Analyze a site for planning constraints
        
        Args:
            site: Site information to analyze
            
        Returns:
            List of detected constraints
        """
        
        constraints = []
        
        # Run constraint checks
        for rule in self.constraint_rules:
            detected_constraints = await self._check_constraint_rule(site, rule)
            constraints.extend(detected_constraints)
        
        return constraints
    
    async def _check_constraint_rule(self, site: SiteInput, rule: ConstraintRule) -> List[Constraint]:
        """Check a specific constraint rule against a site"""
        
        constraints = []
        
        # Simulate constraint detection based on site location
        # In production, this would query actual GIS databases
        
        constraint_data = await self._simulate_constraint_check(site, rule)
        
        for data in constraint_data:
            constraint = Constraint(
                constraint_id=f"{rule.constraint_type.value}_{data['id']}",
                type=rule.constraint_type,
                severity=data['severity'],
                title=rule.title,
                description=f"{rule.description}. {data['details']}",
                source=rule.source,
                distance_m=data.get('distance_m'),
                geometry=data.get('geometry'),
                metadata=data.get('metadata', {}),
                policy_references=data.get('policy_references', [])
            )
            constraints.append(constraint)
        
        return constraints
    
    async def _simulate_constraint_check(self, site: SiteInput, rule: ConstraintRule) -> List[Dict[str, Any]]:
        """
        Simulate constraint detection for demo purposes
        In production, this would query real GIS databases
        """
        
        # Simple simulation based on postcode patterns and coordinates
        constraints_found = []
        
        # Simulate some constraints based on location patterns
        if rule.constraint_type == ConstraintType.FLOOD_ZONE:
            # Simulate flood zones near rivers (simplified)
            if self._near_water_feature(site.latitude, site.longitude):
                constraints_found.append({
                    'id': 'flood_001',
                    'severity': SeverityLevel.MEDIUM,
                    'details': 'Site is within Flood Zone 2 (medium probability)',
                    'distance_m': 0,
                    'metadata': {'zone': '2', 'source': 'EA'},
                    'policy_references': ['NPPF Para 159-169']
                })
        
        elif rule.constraint_type == ConstraintType.GREEN_BELT:
            # Simulate Green Belt around major cities
            if self._near_major_city(site.latitude, site.longitude):
                constraints_found.append({
                    'id': 'gb_001', 
                    'severity': SeverityLevel.HIGH,
                    'details': 'Site is within designated Green Belt land',
                    'distance_m': 0,
                    'metadata': {'designation_date': '1955'},
                    'policy_references': ['NPPF Para 137-151', 'Local Plan Policy GB1']
                })
        
        elif rule.constraint_type == ConstraintType.CONSERVATION_AREA:
            # Simulate conservation areas in historic locations
            if self._in_historic_area(site.postcode):
                constraints_found.append({
                    'id': 'ca_001',
                    'severity': SeverityLevel.MEDIUM,
                    'details': 'Site is within Historic Town Centre Conservation Area',
                    'distance_m': 0,
                    'metadata': {'designation_date': '1975', 'character_appraisal': True},
                    'policy_references': ['Local Plan Policy HE1', 'Conservation Area Appraisal']
                })
        
        elif rule.constraint_type == ConstraintType.TREE_PRESERVATION_ORDER:
            # Simulate TPOs on residential sites
            if 'residential' in (site.proposed_use or '').lower():
                constraints_found.append({
                    'id': 'tpo_001',
                    'severity': SeverityLevel.MEDIUM,
                    'details': 'Mature Oak tree subject to TPO on site boundary',
                    'distance_m': 15,
                    'metadata': {'tree_species': 'Oak', 'tpo_reference': 'TPO/2019/001'},
                    'policy_references': ['Local Plan Policy NE3']
                })
        
        return constraints_found
    
    def _near_water_feature(self, lat: float, lon: float) -> bool:
        """Simulate proximity to water features"""
        # Very simplified - in reality would query OS water layer
        return (lat * 1000) % 7 < 2  # Pseudo-random based on coordinates
    
    def _near_major_city(self, lat: float, lon: float) -> bool:
        """Simulate Green Belt around major cities"""
        # Simplified check for areas around major cities
        major_cities = [
            (51.5074, -0.1278),  # London
            (53.4808, -2.2426),  # Manchester  
            (52.4862, -1.8904),  # Birmingham
        ]
        
        for city_lat, city_lon in major_cities:
            distance = math.sqrt((lat - city_lat)**2 + (lon - city_lon)**2)
            if 0.1 < distance < 0.3:  # Rough Green Belt zone
                return True
        return False
    
    def _in_historic_area(self, postcode: str) -> bool:
        """Simulate historic conservation areas"""
        # Very simplified - check for certain postcode patterns
        historic_patterns = ['OX', 'CB', 'BA', 'YO', 'CT', 'EX']
        return any(postcode.startswith(pattern) for pattern in historic_patterns)


# Singleton engine instance
constraints_engine = ConstraintsEngine()


async def analyze_site_constraints(site: SiteInput) -> List[Constraint]:
    """Convenience function to analyze site constraints"""
    return await constraints_engine.analyze_constraints(site)


def detect_planning_constraints(site: SiteInput) -> List[Constraint]:
    """
    Detect planning constraints synchronously (wrapper for async function)
    Required for compatibility with existing router imports
    """
    import asyncio
    
    # Check if we're in an async context
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context, create a task
        return asyncio.create_task(constraints_engine.analyze_constraints(site))
    except RuntimeError:
        # No running event loop, run synchronously
        return asyncio.run(constraints_engine.analyze_constraints(site))