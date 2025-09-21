"""
Offsets Marketplace Schemas
Pydantic models for biodiversity net gain trading system
"""
from typing import Dict, List, Any, Optional, Union, Literal
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid


class HabitatType(str, Enum):
    """DEFRA biodiversity metric habitat classifications"""
    GRASSLAND_MODIFIED = "grassland_modified"
    GRASSLAND_SPECIES_POOR = "grassland_species_poor"  
    GRASSLAND_SPECIES_RICH = "grassland_species_rich"
    HEATHLAND_LOWLAND = "heathland_lowland"
    HEATHLAND_UPLAND = "heathland_upland"
    WOODLAND_BROADLEAF = "woodland_broadleaf"
    WOODLAND_CONIFEROUS = "woodland_coniferous"
    WOODLAND_MIXED = "woodland_mixed"
    WETLAND_FRESHWATER = "wetland_freshwater"
    WETLAND_COASTAL = "wetland_coastal"
    SCRUBLAND = "scrubland"
    URBAN_TREES = "urban_trees"
    ARABLE = "arable"
    DEVELOPED_SEALED = "developed_sealed"


class HabitatCondition(str, Enum):
    """Habitat condition categories per DEFRA metrics"""
    GOOD = "good"
    MODERATE = "moderate" 
    POOR = "poor"
    NA = "not_applicable"


class LocationStrategicSignificance(str, Enum):
    """Strategic significance for location-based multipliers"""
    HIGH = "high"           # Nature Recovery Network core areas
    MEDIUM = "medium"       # Nature corridors and stepping stones  
    LOW = "low"            # Standard countryside
    VERY_HIGH = "very_high" # Irreplaceable habitats nearby


class ListingStatus(str, Enum):
    """Status of offset supply listings"""
    DRAFT = "draft"
    ACTIVE = "active"
    RESERVED = "reserved"
    SOLD = "sold"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class DemandStatus(str, Enum):
    """Status of offset demand requests"""
    SEARCHING = "searching"
    MATCHED = "matched"
    CONTRACTED = "contracted"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AgreementStatus(str, Enum):
    """Legal agreement status"""
    DRAFT = "draft"
    UNDER_NEGOTIATION = "under_negotiation"
    SIGNED = "signed"
    COMPLETED = "completed"
    BREACHED = "breached"


# Core habitat and biodiversity models
class HabitatUnit(BaseModel):
    """Single habitat unit within a biodiversity calculation"""
    
    habitat_type: HabitatType
    condition: HabitatCondition
    area_hectares: Decimal = Field(..., gt=0, description="Area in hectares")
    
    # DEFRA metric factors
    distinctiveness_score: int = Field(..., ge=1, le=8, description="Habitat distinctiveness (1-8)")
    condition_score: Decimal = Field(..., ge=1, le=3, description="Condition assessment (1-3)")
    strategic_significance: LocationStrategicSignificance = Field(default=LocationStrategicSignificance.LOW)
    
    # Calculated values
    baseline_units: Optional[Decimal] = Field(None, description="Biodiversity units (calculated)")
    
    @validator('baseline_units', always=True)
    def calculate_baseline_units(cls, v, values):
        """Calculate biodiversity units using DEFRA formula"""
        if all(k in values for k in ['area_hectares', 'distinctiveness_score', 'condition_score']):
            area = values['area_hectares']
            distinctiveness = values['distinctiveness_score'] 
            condition = values['condition_score']
            
            # Strategic significance multipliers
            strategic_multipliers = {
                LocationStrategicSignificance.VERY_HIGH: 1.5,
                LocationStrategicSignificance.HIGH: 1.15,
                LocationStrategicSignificance.MEDIUM: 1.1,
                LocationStrategicSignificance.LOW: 1.0
            }
            
            strategic_mult = strategic_multipliers.get(
                values.get('strategic_significance', LocationStrategicSignificance.LOW), 
                1.0
            )
            
            return area * distinctiveness * condition * strategic_mult
        
        return v


class BiodiversityAssessment(BaseModel):
    """Complete biodiversity assessment for a site"""
    
    assessment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    site_reference: str = Field(..., description="Site reference or name")
    
    # Location data
    postcode: str
    coordinates: Optional[tuple] = None
    local_authority: str
    
    # Assessment metadata  
    assessment_date: date
    assessor_name: str
    assessor_qualification: str
    methodology_version: str = Field(default="4.0", description="DEFRA biodiversity metric version")
    
    # Habitat data
    baseline_habitats: List[HabitatUnit] = Field(..., description="Existing habitat units")
    post_development_habitats: List[HabitatUnit] = Field(default_factory=list, description="Habitat after development")
    
    # Calculated totals
    baseline_biodiversity_units: Optional[Decimal] = Field(None, description="Total baseline units")
    post_development_units: Optional[Decimal] = Field(None, description="Total post-development units")
    net_unit_change: Optional[Decimal] = Field(None, description="Net change in biodiversity units")
    
    # Additional requirements
    bng_percentage_required: Decimal = Field(default=Decimal("10"), description="BNG percentage requirement")
    net_gain_required: Optional[Decimal] = Field(None, description="Minimum net gain units required")
    
    @validator('baseline_biodiversity_units', always=True)
    def calculate_baseline_total(cls, v, values):
        """Calculate total baseline units"""
        if 'baseline_habitats' in values:
            return sum(habitat.baseline_units or 0 for habitat in values['baseline_habitats'])
        return v
    
    @validator('post_development_units', always=True) 
    def calculate_post_development_total(cls, v, values):
        """Calculate total post-development units"""
        if 'post_development_habitats' in values:
            return sum(habitat.baseline_units or 0 for habitat in values['post_development_habitats'])
        return v
    
    @validator('net_unit_change', always=True)
    def calculate_net_change(cls, v, values):
        """Calculate net unit change"""
        baseline = values.get('baseline_biodiversity_units', 0) or 0
        post_dev = values.get('post_development_units', 0) or 0
        return post_dev - baseline
    
    @validator('net_gain_required', always=True)
    def calculate_net_gain_required(cls, v, values):
        """Calculate required net gain"""
        baseline = values.get('baseline_biodiversity_units', 0) or 0
        bng_percentage = values.get('bng_percentage_required', Decimal("10")) or Decimal("10")
        return baseline * (bng_percentage / 100)


# Supply side models
class OffsetSupplyListing(BaseModel):
    """Biodiversity offset supply listing from landowners"""
    
    listing_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Landowner details
    landowner_id: str
    landowner_name: str
    landowner_contact: str
    
    # Site information
    site_name: str
    site_description: Optional[str] = None
    postcode: str
    coordinates: Optional[tuple] = None
    total_site_area_hectares: Decimal = Field(..., gt=0)
    
    # Offset details
    available_habitat_units: List[HabitatUnit] = Field(..., description="Available offset habitats")
    total_biodiversity_units: Optional[Decimal] = Field(None, description="Total units available")
    
    # Delivery timeline
    delivery_start_date: date = Field(..., description="When offset delivery begins")
    delivery_completion_date: date = Field(..., description="When offset fully established")
    monitoring_period_years: int = Field(default=30, ge=10, le=50, description="Monitoring commitment period")
    
    # Pricing and terms
    price_per_unit: Decimal = Field(..., gt=0, description="Price per biodiversity unit (£)")
    minimum_unit_purchase: Decimal = Field(default=Decimal("0.1"), description="Minimum purchase quantity")
    payment_terms: str = Field(default="50% on signature, 50% on delivery")
    
    # Legal and compliance
    land_tenure: Literal["freehold", "leasehold", "option_agreement"] = "freehold"
    planning_permission_reference: Optional[str] = None
    environmental_permits: List[str] = Field(default_factory=list)
    
    # Status and availability
    status: ListingStatus = ListingStatus.DRAFT
    units_reserved: Decimal = Field(default=Decimal("0"), description="Units already reserved")
    units_sold: Decimal = Field(default=Decimal("0"), description="Units already sold")
    
    # Metadata
    created_date: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    expiry_date: Optional[date] = None
    
    @validator('total_biodiversity_units', always=True)
    def calculate_total_units(cls, v, values):
        """Calculate total available units"""
        if 'available_habitat_units' in values:
            return sum(habitat.baseline_units or 0 for habitat in values['available_habitat_units'])
        return v
    
    @property
    def units_available(self) -> Decimal:
        """Calculate remaining available units"""
        total = self.total_biodiversity_units or Decimal("0")
        reserved = self.units_reserved or Decimal("0") 
        sold = self.units_sold or Decimal("0")
        return total - reserved - sold
    
    @property
    def total_value(self) -> Decimal:
        """Calculate total listing value"""
        return (self.total_biodiversity_units or Decimal("0")) * self.price_per_unit


# Demand side models  
class OffsetDemandRequest(BaseModel):
    """Biodiversity offset demand from developers"""
    
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Developer details
    developer_id: str
    developer_name: str
    developer_contact: str
    
    # Development project
    project_name: str
    project_description: str
    development_postcode: str
    development_coordinates: Optional[tuple] = None
    planning_application_reference: str
    
    # Offset requirements
    biodiversity_assessment: BiodiversityAssessment
    required_habitat_types: List[HabitatType] = Field(..., description="Acceptable habitat types for offsetting")
    required_units: Decimal = Field(..., gt=0, description="Biodiversity units needed")
    
    # Location preferences
    max_distance_km: int = Field(default=50, ge=5, le=200, description="Maximum distance from development")
    preferred_local_authorities: List[str] = Field(default_factory=list)
    same_national_character_area: bool = Field(default=True, description="Prefer same landscape character area")
    
    # Timeline requirements
    required_by_date: date = Field(..., description="Date offset must be secured by")
    delivery_timeline_months: int = Field(default=24, ge=6, le=120, description="Acceptable delivery timeline")
    
    # Budget and terms
    max_price_per_unit: Decimal = Field(..., gt=0, description="Maximum price per unit (£)")
    total_budget: Optional[Decimal] = None
    preferred_payment_terms: str = Field(default="Flexible")
    
    # Status
    status: DemandStatus = DemandStatus.SEARCHING
    
    # Metadata
    created_date: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    @validator('total_budget', always=True)
    def calculate_budget(cls, v, values):
        """Calculate total budget if not specified"""
        if v is None and 'required_units' in values and 'max_price_per_unit' in values:
            return values['required_units'] * values['max_price_per_unit']
        return v


# Matching and transaction models
class OffsetMatch(BaseModel):
    """Potential match between supply and demand"""
    
    match_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Matched parties
    supply_listing_id: str
    demand_request_id: str
    
    # Match details
    matched_units: Decimal = Field(..., gt=0, description="Units in this match")
    unit_price: Decimal = Field(..., gt=0, description="Agreed price per unit")
    total_value: Decimal = Field(..., description="Total transaction value")
    
    # Match quality metrics
    distance_km: Decimal = Field(..., description="Distance between development and offset site")
    habitat_type_match_score: Decimal = Field(..., ge=0, le=1, description="Habitat compatibility score (0-1)")
    location_preference_score: Decimal = Field(..., ge=0, le=1, description="Location preference match (0-1)")
    timeline_compatibility: bool = Field(..., description="Timeline compatibility")
    
    # Overall match score (calculated)
    overall_match_score: Optional[Decimal] = Field(None, ge=0, le=1, description="Overall match quality (0-1)")
    
    # Status
    match_status: Literal["potential", "proposed", "accepted", "rejected", "expired"] = "potential"
    
    # Timestamps
    matched_date: datetime = Field(default_factory=datetime.now)
    expires_date: Optional[datetime] = None
    
    @validator('total_value', always=True)
    def calculate_total_value(cls, v, values):
        """Calculate total transaction value"""
        if 'matched_units' in values and 'unit_price' in values:
            return values['matched_units'] * values['unit_price']
        return v
    
    @validator('overall_match_score', always=True)
    def calculate_match_score(cls, v, values):
        """Calculate overall match quality score"""
        # Weight different factors
        habitat_score = values.get('habitat_type_match_score', 0) * 0.4
        location_score = values.get('location_preference_score', 0) * 0.3
        
        # Distance penalty (closer is better)
        distance = values.get('distance_km', 100)
        distance_score = max(0, 1 - (distance / 100)) * 0.2  # Penalty increases with distance
        
        # Timeline compatibility 
        timeline_score = 0.1 if values.get('timeline_compatibility', False) else 0
        
        return habitat_score + location_score + distance_score + timeline_score


class OffsetAgreement(BaseModel):
    """Legal agreement for biodiversity offset transaction"""
    
    agreement_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Related records
    supply_listing_id: str
    demand_request_id: str  
    match_id: str
    
    # Parties
    landowner_details: Dict[str, Any] = Field(..., description="Landowner legal details")
    developer_details: Dict[str, Any] = Field(..., description="Developer legal details")
    
    # Transaction details
    biodiversity_units: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)
    total_value: Decimal = Field(..., gt=0)
    
    # Legal terms
    agreement_type: Literal["section_106", "conservation_covenant", "private_agreement"] = "conservation_covenant"
    monitoring_requirements: Dict[str, Any] = Field(..., description="Monitoring and reporting obligations")
    delivery_milestones: List[Dict[str, Any]] = Field(..., description="Delivery schedule and milestones")
    
    # Payment schedule
    payment_schedule: List[Dict[str, Any]] = Field(..., description="Payment terms and schedule")
    
    # Risk and compliance
    insurance_requirements: List[str] = Field(default_factory=list)
    default_penalties: Dict[str, Any] = Field(default_factory=dict)
    force_majeure_clauses: List[str] = Field(default_factory=list)
    
    # Document management
    agreement_document_url: Optional[str] = None
    supporting_documents: List[str] = Field(default_factory=list)
    
    # Status tracking
    status: AgreementStatus = AgreementStatus.DRAFT
    
    # Key dates
    agreement_date: Optional[date] = None
    commencement_date: Optional[date] = None
    completion_due_date: Optional[date] = None
    
    # Metadata
    created_date: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)


# Search and filtering models
class SupplySearchFilters(BaseModel):
    """Search filters for supply listings"""
    
    # Location filters
    postcode_area: Optional[str] = None
    max_distance_km: Optional[int] = None
    local_authorities: Optional[List[str]] = None
    coordinates: Optional[tuple] = None
    
    # Habitat filters
    habitat_types: Optional[List[HabitatType]] = None
    min_condition_score: Optional[Decimal] = None
    strategic_significance: Optional[List[LocationStrategicSignificance]] = None
    
    # Unit filters
    min_units_available: Optional[Decimal] = None
    max_units_available: Optional[Decimal] = None
    
    # Pricing filters
    max_price_per_unit: Optional[Decimal] = None
    min_price_per_unit: Optional[Decimal] = None
    
    # Timeline filters
    available_from_date: Optional[date] = None
    delivery_by_date: Optional[date] = None
    
    # Status filters
    status: Optional[List[ListingStatus]] = None
    
    # Sorting
    sort_by: Literal["price", "distance", "units", "created_date"] = "created_date"
    sort_order: Literal["asc", "desc"] = "desc"


class DemandSearchFilters(BaseModel):
    """Search filters for demand requests"""
    
    # Location filters
    postcode_area: Optional[str] = None
    max_distance_km: Optional[int] = None
    local_authorities: Optional[List[str]] = None
    
    # Requirement filters  
    min_required_units: Optional[Decimal] = None
    max_required_units: Optional[Decimal] = None
    habitat_types: Optional[List[HabitatType]] = None
    
    # Budget filters
    min_budget: Optional[Decimal] = None
    max_budget: Optional[Decimal] = None
    
    # Timeline filters
    required_by_date: Optional[date] = None
    
    # Status filters
    status: Optional[List[DemandStatus]] = None
    
    # Sorting
    sort_by: Literal["budget", "units", "deadline", "created_date"] = "created_date"
    sort_order: Literal["asc", "desc"] = "desc"


# API response models
class SupplyListingResponse(BaseModel):
    """API response for supply listing queries"""
    
    listings: List[OffsetSupplyListing]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    
    # Summary statistics
    total_units_available: Decimal
    price_range: Dict[str, Decimal]  # min, max, average
    location_summary: Dict[str, int]  # count by local authority


class DemandRequestResponse(BaseModel):
    """API response for demand request queries"""
    
    requests: List[OffsetDemandRequest] 
    total_count: int
    page: int
    page_size: int
    has_next: bool
    
    # Summary statistics
    total_units_demanded: Decimal
    budget_range: Dict[str, Decimal]  # min, max, average
    habitat_demand_summary: Dict[HabitatType, int]


class MatchResponse(BaseModel):
    """API response for match queries"""
    
    matches: List[OffsetMatch]
    total_count: int
    
    # Match quality statistics
    average_match_score: Decimal
    high_quality_matches: int  # Score > 0.7
    distance_statistics: Dict[str, Decimal]


class MarketSummary(BaseModel):
    """Overall marketplace statistics"""
    
    # Supply statistics
    total_listings: int
    active_listings: int
    total_units_for_sale: Decimal
    average_price_per_unit: Decimal
    
    # Demand statistics  
    total_demand_requests: int
    searching_requests: int
    total_units_demanded: Decimal
    total_market_value: Decimal
    
    # Transaction statistics
    completed_transactions: int
    total_units_transacted: Decimal
    total_transaction_value: Decimal
    
    # Market health indicators
    supply_demand_ratio: Decimal
    average_time_to_match_days: Decimal
    market_clearance_rate: Decimal  # Percentage of demand being met


# Commission and reporting models
class CommissionStructure(BaseModel):
    """Commission structure for marketplace transactions"""
    
    # Commission rates
    landowner_commission_percent: Decimal = Field(default=Decimal("2.5"), description="Commission from landowner (%)")
    developer_commission_percent: Decimal = Field(default=Decimal("2.5"), description="Commission from developer (%)")
    
    # Minimum fees
    minimum_commission_amount: Decimal = Field(default=Decimal("500"), description="Minimum commission per transaction")
    
    # Success fees
    success_fee_percent: Decimal = Field(default=Decimal("1.0"), description="Additional success fee (%)")
    
    # Payment terms
    commission_payment_terms: str = Field(default="On completion of legal agreement")


class TransactionReport(BaseModel):
    """Detailed transaction report for commission and audit purposes"""
    
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agreement_id: str
    
    # Transaction summary
    transaction_date: date
    biodiversity_units: Decimal
    unit_price: Decimal
    total_transaction_value: Decimal
    
    # Commission breakdown
    landowner_commission: Decimal
    developer_commission: Decimal 
    success_fee: Decimal
    total_commission: Decimal
    
    # Payment tracking
    commission_invoice_sent: bool = False
    commission_paid: bool = False
    payment_date: Optional[date] = None
    
    # Reporting metadata
    generated_date: datetime = Field(default_factory=datetime.now)
    generated_by: str