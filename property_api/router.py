"""
Property API FastAPI Router
Provides REST endpoints for external property data integration
"""
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import logging

from . import (
    get_comprehensive_property_report,
    get_property_summary,
    get_land_registry_data,
    get_epc_data,
    get_flood_risk_data,
    get_planning_history,
    cache_stats,
    clear_all_caches,
    PropertyDataAggregator
)

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/property-api", tags=["Property Data"])


# Pydantic models for API requests/responses
class PropertySearchRequest(BaseModel):
    identifier: str = Field(..., description="Property identifier (address, postcode, UPRN)")
    search_type: str = Field("address", description="Type of search: address, postcode, uprn")


class LandRegistrySearchRequest(PropertySearchRequest):
    include_prices: bool = Field(True, description="Include price paid data")
    include_ownership: bool = Field(True, description="Include ownership information")


class PlanningSearchRequest(PropertySearchRequest):
    radius_m: int = Field(100, description="Search radius in meters", ge=50, le=1000)
    years_back: int = Field(10, description="Years of history to retrieve", ge=1, le=20)


class FloodRiskResponse(BaseModel):
    postcode: str
    coordinates: Optional[tuple] = None
    overall_flood_risk: str
    river_and_sea: str
    surface_water: str
    reservoirs: str
    recommendations: List[str]


# Health check endpoint
@router.get("/health", summary="Health Check")
async def health_check():
    """Health check for Property API service"""
    return {"status": "healthy", "service": "property-api"}


# Comprehensive property report
@router.post("/comprehensive-report", 
            summary="Get Comprehensive Property Report",
            description="Generate a comprehensive property report combining data from all sources")
async def comprehensive_property_report(
    request: PropertySearchRequest,
    include_planning_radius: int = Query(100, description="Radius for planning history search", ge=50, le=1000)
) -> Dict[str, Any]:
    """Get comprehensive property report from all data sources"""
    
    try:
        report = await get_comprehensive_property_report(
            identifier=request.identifier,
            search_type=request.search_type,
            include_planning_radius=include_planning_radius
        )
        
        if 'error' in report:
            raise HTTPException(status_code=404, detail=report['error'])
        
        return report
        
    except Exception as e:
        logger.error(f"Error generating comprehensive report: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Property summary
@router.post("/summary",
            summary="Get Property Summary", 
            description="Get a concise property summary with key insights")
async def property_summary(request: PropertySearchRequest) -> Dict[str, Any]:
    """Get concise property summary"""
    
    try:
        summary = await get_property_summary(
            identifier=request.identifier,
            search_type=request.search_type
        )
        
        if not summary:
            raise HTTPException(
                status_code=404, 
                detail="Property data not found or unavailable"
            )
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating property summary: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Land Registry data endpoints
@router.post("/land-registry",
            summary="Get Land Registry Data",
            description="Retrieve Land Registry title and price paid data")
async def land_registry_data(request: LandRegistrySearchRequest) -> Dict[str, Any]:
    """Get Land Registry data for property"""
    
    try:
        data = await get_land_registry_data(
            identifier=request.identifier,
            search_type=request.search_type
        )
        
        if not data:
            raise HTTPException(
                status_code=404,
                detail="Land Registry data not found for this property"
            )
        
        # Filter response based on request parameters
        if not request.include_prices and 'price_paid_data' in data:
            data.pop('price_paid_data', None)
        
        if not request.include_ownership and 'title_data' in data:
            title_data = data.get('title_data', {})
            title_data.pop('proprietors', None)
            title_data.pop('charges', None)
        
        return data
        
    except Exception as e:
        logger.error(f"Error fetching Land Registry data: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# EPC data endpoints
@router.post("/epc",
            summary="Get Energy Performance Certificate Data",
            description="Retrieve EPC data including energy ratings and improvement recommendations")
async def epc_data(request: PropertySearchRequest) -> Dict[str, Any]:
    """Get EPC data for property"""
    
    try:
        data = await get_epc_data(
            identifier=request.identifier,
            search_type=request.search_type
        )
        
        if not data:
            raise HTTPException(
                status_code=404,
                detail="EPC data not found for this property"
            )
        
        return data
        
    except Exception as e:
        logger.error(f"Error fetching EPC data: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Flood risk endpoints
@router.post("/flood-risk",
            summary="Get Flood Risk Assessment",
            description="Retrieve comprehensive flood risk data from Environment Agency")
async def flood_risk_data(request: PropertySearchRequest) -> Dict[str, Any]:
    """Get flood risk data for property"""
    
    try:
        data = await get_flood_risk_data(
            identifier=request.identifier,
            search_type=request.search_type
        )
        
        if not data:
            raise HTTPException(
                status_code=404,
                detail="Flood risk data not found for this location"
            )
        
        return data
        
    except Exception as e:
        logger.error(f"Error fetching flood risk data: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Planning history endpoints
@router.post("/planning-history",
            summary="Get Planning History",
            description="Retrieve planning application history for property and surrounding area")
async def planning_history_data(request: PlanningSearchRequest) -> Dict[str, Any]:
    """Get planning history for property"""
    
    try:
        data = await get_planning_history(
            identifier=request.identifier,
            search_type=request.search_type,
            radius_m=request.radius_m,
            years_back=request.years_back
        )
        
        if not data:
            raise HTTPException(
                status_code=404,
                detail="Planning history data not found for this area"
            )
        
        return data
        
    except Exception as e:
        logger.error(f"Error fetching planning history: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Comparable properties endpoint
@router.get("/comparables/{identifier}",
           summary="Find Comparable Properties",
           description="Find comparable properties in the area based on recent sales")
async def comparable_properties(
    identifier: str = Path(..., description="Property identifier"),
    search_type: str = Query("address", description="Type of search"),
    radius_m: int = Query(500, description="Search radius in meters", ge=100, le=2000),
    max_results: int = Query(10, description="Maximum number of comparables", ge=1, le=50)
) -> Dict[str, Any]:
    """Find comparable properties"""
    
    try:
        async with PropertyDataAggregator() as aggregator:
            comparables = await aggregator.get_comparable_properties(
                identifier=identifier,
                search_type=search_type,
                radius_m=radius_m,
                max_results=max_results
            )
        
        return {
            'search_parameters': {
                'identifier': identifier,
                'search_type': search_type,
                'radius_m': radius_m,
                'max_results': max_results
            },
            'comparables': comparables,
            'count': len(comparables)
        }
        
    except Exception as e:
        logger.error(f"Error finding comparables: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Area statistics endpoint
@router.get("/area-stats/{postcode}",
           summary="Get Area Statistics",
           description="Get comprehensive statistics for a postcode area")
async def area_statistics(
    postcode: str = Path(..., description="Postcode for area analysis"),
    radius_m: int = Query(1000, description="Analysis radius in meters", ge=500, le=5000)
) -> Dict[str, Any]:
    """Get area statistics and insights"""
    
    try:
        async with PropertyDataAggregator() as aggregator:
            stats = await aggregator.get_area_statistics(
                postcode=postcode,
                radius_m=radius_m
            )
        
        if 'error' in stats:
            raise HTTPException(status_code=404, detail=stats['error'])
        
        return stats
        
    except Exception as e:
        logger.error(f"Error generating area statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Cache management endpoints
@router.get("/cache/stats",
           summary="Get Cache Statistics",
           description="Get statistics for all property data caches")
async def get_cache_statistics() -> Dict[str, Any]:
    """Get cache statistics"""
    
    try:
        stats = await cache_stats()
        return {
            'cache_statistics': stats,
            'timestamp': str(__import__('datetime').datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Error fetching cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/cache/clear",
            summary="Clear All Caches",
            description="Clear all property data caches (admin operation)")
async def clear_property_caches() -> Dict[str, Any]:
    """Clear all caches"""
    
    try:
        results = await clear_all_caches()
        
        cleared_count = sum(1 for success in results.values() if success)
        total_caches = len(results)
        
        return {
            'message': f'Cleared {cleared_count}/{total_caches} caches',
            'results': results,
            'timestamp': str(__import__('datetime').datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Error clearing caches: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Batch processing endpoints
@router.post("/batch/summaries",
            summary="Get Multiple Property Summaries",
            description="Get summaries for multiple properties in one request")
async def batch_property_summaries(
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """Get summaries for multiple properties"""
    
    identifiers = request.get("identifiers", [])
    search_type = request.get("search_type", "address")
    
    if len(identifiers) > 50:  # Limit batch size
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 properties per batch request"
        )
    
    try:
        results = []
        
        async with PropertyDataAggregator() as aggregator:
            # Process in parallel
            import asyncio
            
            async def get_single_summary(identifier: str):
                try:
                    summary = await aggregator.get_property_summary(identifier, search_type)
                    return {
                        'identifier': identifier,
                        'success': True,
                        'data': summary.__dict__ if summary else None
                    }
                except Exception as e:
                    return {
                        'identifier': identifier,
                        'success': False,
                        'error': str(e)
                    }
            
            # Limit concurrent requests
            semaphore = asyncio.Semaphore(10)
            
            async def process_with_semaphore(identifier):
                async with semaphore:
                    return await get_single_summary(identifier)
            
            tasks = [process_with_semaphore(identifier) for identifier in identifiers]
            results = await asyncio.gather(*tasks)
        
        successful = sum(1 for result in results if result['success'])
        
        return {
            'batch_results': results,
            'summary': {
                'total_requested': len(identifiers),
                'successful': successful,
                'failed': len(identifiers) - successful
            },
            'timestamp': str(__import__('datetime').datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# API documentation helper
@router.get("/",
           summary="Property API Documentation",
           description="Get information about available Property API endpoints")
async def api_documentation() -> Dict[str, Any]:
    """Property API endpoint documentation"""
    
    return {
        'service': 'Domus Property API',
        'version': '1.0.0',
        'description': 'External property data integration service',
        'endpoints': {
            'comprehensive_report': 'POST /property-api/comprehensive-report - Full property report',
            'summary': 'POST /property-api/summary - Property summary',
            'land_registry': 'POST /property-api/land-registry - Land Registry data',
            'epc': 'POST /property-api/epc - Energy Performance Certificate data',
            'flood_risk': 'POST /property-api/flood-risk - Flood risk assessment',
            'planning_history': 'POST /property-api/planning-history - Planning application history',
            'comparables': 'GET /property-api/comparables/{identifier} - Comparable properties',
            'area_stats': 'GET /property-api/area-stats/{postcode} - Area statistics',
            'batch_summaries': 'POST /property-api/batch/summaries - Multiple property summaries'
        },
        'data_sources': [
            'HM Land Registry',
            'Energy Performance Certificate Database',
            'Environment Agency Flood Risk Data',
            'Local Planning Authority Systems'
        ],
        'caching': 'Intelligent caching with configurable TTL per data source',
        'rate_limiting': 'Built-in rate limiting for external API calls'
    }