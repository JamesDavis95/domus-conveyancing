"""
Package initialization for Offsets Marketplace
"""

from .schemas import (
    OffsetSupplyListing,
    OffsetDemandRequest, 
    OffsetMatch,
    OffsetAgreement,
    HabitatUnit,
    HabitatType,
    HabitatCondition,
    BiodiversityAssessment,
    ListingStatus,
    DemandStatus,
    LocationStrategicSignificance
)

from .supply import SupplyManager
from .demand import DemandManager  
from .matching import MatchingEngine, MatchingCriteria
from .router import router

__version__ = "1.0.0"
__author__ = "Domus Planning Platform"
__description__ = "Biodiversity Net Gain Offsets Marketplace with DEFRA metric integration"

# Export main classes
__all__ = [
    # Data Models
    "OffsetSupplyListing",
    "OffsetDemandRequest", 
    "OffsetMatch",
    "OffsetAgreement",
    "HabitatUnit",
    "HabitatType",
    "HabitatCondition", 
    "BiodiversityAssessment",
    "ListingStatus",
    "DemandStatus",
    "LocationStrategicSignificance",
    # "CreateSupplyListingRequest",  # Removed, does not exist
    # "CreateDemandRequestBody",  # Removed, does not exist
    
    # Core Managers
    "SupplyManager",
    "DemandManager",
    "MatchingEngine", 
    "MatchingCriteria",
    
    # API Router
    "router"
]