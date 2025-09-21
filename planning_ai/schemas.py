"""
Pydantic models for Planning AI system
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ConstraintType(str, Enum):
    GREEN_BELT = "green_belt"
    FLOOD_ZONE = "flood_zone"
    CONSERVATION_AREA = "conservation_area"
    TREE_PRESERVATION_ORDER = "tree_preservation_order"
    HIGHWAYS_ACCESS = "highways_access"
    SSSI = "site_of_special_scientific_interest"
    AONB = "area_of_outstanding_natural_beauty"
    LISTED_BUILDING = "listed_building"
    SCHEDULED_MONUMENT = "scheduled_monument"


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SiteInput(BaseModel):
    """Input data for site analysis"""
    uprn: Optional[str] = None
    address: str
    postcode: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    local_planning_authority: str
    site_area_sqm: Optional[float] = None
    proposed_use: Optional[str] = None
    proposal_description: Optional[str] = None


class Constraint(BaseModel):
    """Planning constraint detected on or near a site"""
    constraint_id: str
    type: ConstraintType
    severity: SeverityLevel
    title: str
    description: str
    source: str
    distance_m: Optional[float] = None  # Distance from site if nearby
    geometry: Optional[Dict[str, Any]] = None  # GeoJSON geometry
    metadata: Dict[str, Any] = Field(default_factory=dict)
    policy_references: List[str] = Field(default_factory=list)


class Score(BaseModel):
    """AI-generated approval probability score"""
    site_id: str
    model_version: str
    approval_probability: float = Field(..., ge=0, le=1)
    confidence_score: float = Field(..., ge=0, le=1)
    rationale: str
    key_factors: List[str] = Field(default_factory=list)
    similar_cases: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class Recommendation(BaseModel):
    """AI-generated recommendation to improve planning prospects"""
    recommendation_id: str
    title: str
    description: str
    category: str  # e.g., "design", "policy", "consultation", "mitigation"
    impact_delta: float = Field(..., ge=-1, le=1)  # Expected score improvement
    rationale: str
    policy_basis: List[str] = Field(default_factory=list)
    priority: SeverityLevel = SeverityLevel.MEDIUM


class DocArtifact(BaseModel):
    """Generated planning document artifact"""
    document_id: str
    site_id: str
    document_type: str  # e.g., "planning_statement", "design_and_access"
    file_path: str
    file_hash: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    template_version: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PropertyData(BaseModel):
    """Property data for planning analysis"""
    property_id: str
    address: str
    postcode: str
    uprn: Optional[str] = None
    coordinates: tuple[float, float]
    property_type: Optional[str] = None
    council_tax_band: Optional[str] = None
    epc_rating: Optional[str] = None
    flood_zone: Optional[str] = None
    conservation_area: Optional[bool] = None
    listed_building: Optional[bool] = None
    planning_history: List[Dict[str, Any]] = Field(default_factory=list)


class PlanningAnalysis(BaseModel):
    """Complete planning analysis result"""
    site: SiteInput
    constraints: List[Constraint] = Field(default_factory=list)
    score: Optional[Score] = None
    recommendations: List[Recommendation] = Field(default_factory=list)
    analysis_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)