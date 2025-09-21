"""
Property API Package
External property data integration for Domus Planning AI Platform
"""

from .aggregator import (
    PropertyDataAggregator,
    PropertySummary,
    get_comprehensive_property_report,
    get_property_summary
)

from .land_registry import (
    LandRegistryAdapter,
    LandRegistryData,
    get_land_registry_data
)

from .epc_data import (
    EPCDataAdapter,
    EPCData,
    get_epc_data
)

from .flood_risk import (
    FloodRiskAdapter,
    FloodRiskData,
    get_flood_risk_data
)

from .planning_history import (
    PlanningHistoryAdapter,
    PlanningApplication,
    get_planning_history
)

from .cache import (
    PropertyDataCache,
    CacheManager,
    get_cache,
    cache_stats,
    clear_all_caches
)

__version__ = "1.0.0"

__all__ = [
    # Main aggregator
    'PropertyDataAggregator',
    'PropertySummary',
    'get_comprehensive_property_report',
    'get_property_summary',
    
    # Individual adapters
    'LandRegistryAdapter',
    'LandRegistryData',
    'get_land_registry_data',
    
    'EPCDataAdapter', 
    'EPCData',
    'get_epc_data',
    
    'FloodRiskAdapter',
    'FloodRiskData',
    'get_flood_risk_data',
    
    'PlanningHistoryAdapter',
    'PlanningApplication',
    'get_planning_history',
    
    # Cache system
    'PropertyDataCache',
    'CacheManager',
    'get_cache',
    'cache_stats',
    'clear_all_caches'
]

from .land_registry import LandRegistryAdapter, get_land_registry_data
from .epc_data import EPCDataAdapter, get_epc_data
from .flood_risk import FloodRiskAdapter, get_flood_risk_data
from .planning_history import PlanningHistoryAdapter, get_planning_history
from .cache import PropertyDataCache, CacheManager
from .aggregator import PropertyDataAggregator, get_comprehensive_property_data

__version__ = "1.0.0"
__all__ = [
    "LandRegistryAdapter",
    "EPCDataAdapter", 
    "FloodRiskAdapter",
    "PlanningHistoryAdapter",
    "PropertyDataCache",
    "CacheManager",
    "PropertyDataAggregator",
    "get_land_registry_data",
    "get_epc_data",
    "get_flood_risk_data", 
    "get_planning_history",
    "get_comprehensive_property_data"
]