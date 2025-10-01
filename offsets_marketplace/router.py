"""
Offsets Marketplace API Router
FastAPI endpoints for biodiversity net gain trading
"""
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, Path, Body
from fastapi.responses import JSONResponse
from decimal import Decimal
from datetime import datetime, date
import uuid
from pydantic import BaseModel

from .schemas import (
    OffsetSupplyListing, OffsetDemandRequest, OffsetMatch, OffsetAgreement,
    HabitatType, ListingStatus, DemandStatus, LocationStrategicSignificance,
    BiodiversityAssessment
)
from .supply import SupplyManager
from .demand import DemandManager
from .matching import MatchingEngine, MatchingCriteria


# Initialize router
router = APIRouter(prefix="/api/offsets", tags=["Biodiversity Offsets Marketplace"])

# Initialize managers (in production these would be injected via dependency injection)
supply_manager = SupplyManager()
demand_manager = DemandManager()
matching_engine = MatchingEngine(supply_manager, demand_manager)


# Request/Response Models
class SupplyListingResponse(BaseModel):
    """Response model for supply listing operations"""
    success: bool
    listing_id: Optional[str] = None
    message: str
    listing: Optional[OffsetSupplyListing] = None


class DemandRequestResponse(BaseModel):
    """Response model for demand request operations"""
    success: bool
    request_id: Optional[str] = None
    message: str
    request: Optional[OffsetDemandRequest] = None


class MatchingResponse(BaseModel):
    """Response model for matching operations"""
    success: bool
    matches: List[OffsetMatch]
    total_matches: int
    message: str


class SearchFilters(BaseModel):
    """Search filter parameters"""
    habitat_types: Optional[List[HabitatType]] = None
    min_units: Optional[Decimal] = None
    max_units: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    postcode_area: Optional[str] = None
    local_authority: Optional[str] = None
    max_distance_km: Optional[int] = None
    coordinates: Optional[tuple[float, float]] = None


# Supply Listings Endpoints

@router.post("/supply/create", response_model=SupplyListingResponse)
async def create_supply_listing(
    listing_data: OffsetSupplyListing = Body(..., description="Supply listing data")
):
    """
    Create a new biodiversity offset supply listing
    
    Creates a new listing for landowners offering biodiversity units.
    Includes habitat assessment and DEFRA metric calculations.
    """
    try:
        listing = await supply_manager.create_supply_listing(
            landowner_name=listing_data.landowner_name,
            site_name=listing_data.site_name,
            postcode=listing_data.postcode,
            coordinates=listing_data.coordinates,
            total_area_hectares=listing_data.total_area_hectares,
            habitat_units=listing_data.habitat_units,
            price_per_unit=listing_data.price_per_unit,
            delivery_timeframe_months=listing_data.delivery_timeframe_months,
            description=listing_data.description
        )
        
        return SupplyListingResponse(
            success=True,
            listing_id=listing.listing_id,
            message="Supply listing created successfully",
            listing=listing
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create supply listing: {str(e)}")


@router.get("/supply/{listing_id}", response_model=SupplyListingResponse)
async def get_supply_listing(
    listing_id: str = Path(..., description="Supply listing ID")
):
    """Get supply listing by ID"""
    
    listing = await supply_manager.get_listing(listing_id)
    
    if not listing:
        raise HTTPException(status_code=404, detail="Supply listing not found")
    
    return SupplyListingResponse(
        success=True,
        listing_id=listing_id,
        message="Supply listing retrieved successfully",
        listing=listing
    )


@router.get("/supply", response_model=Dict[str, Any])
async def search_supply_listings(
    habitat_types: Optional[List[HabitatType]] = Query(None, description="Filter by habitat types"),
    min_units: Optional[Decimal] = Query(None, description="Minimum biodiversity units"),
    max_units: Optional[Decimal] = Query(None, description="Maximum biodiversity units"),
    max_price: Optional[Decimal] = Query(None, description="Maximum price per unit"),
    postcode_area: Optional[str] = Query(None, description="Postcode area (e.g., 'OX', 'M')", max_length=4),
    local_authority: Optional[str] = Query(None, description="Local authority name"),
    status_filter: Optional[List[ListingStatus]] = Query([ListingStatus.ACTIVE], description="Listing status"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Results offset for pagination")
):
    """
    Search biodiversity offset supply listings
    
    Supports filtering by habitat type, location, price, and availability.
    Returns paginated results with comprehensive listing details.
    """
    try:
        
        listings = await supply_manager.search_supply_listings(
            habitat_types=habitat_types,
            min_units=min_units,
            max_units=max_units,
            max_price=max_price,
            postcode_area=postcode_area,
            local_authority=local_authority,
            status_filter=status_filter,
            limit=limit,
            offset=offset
        )
        
        # Get total count for pagination
        total_count = len(listings) + offset  # Simplified - would need proper count in production
        
        return {
            "success": True,
            "listings": listings,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": len(listings) == limit
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.put("/supply/{listing_id}/status", response_model=SupplyListingResponse)
async def update_supply_status(
    listing_id: str = Path(..., description="Supply listing ID"),
    status: ListingStatus = Body(..., description="New listing status")
):
    """Update supply listing status"""
    
    success = await supply_manager.update_listing_status(listing_id, status)
    
    if not success:
        raise HTTPException(status_code=404, detail="Supply listing not found")
    
    listing = await supply_manager.get_listing(listing_id)
    
    return SupplyListingResponse(
        success=True,
        listing_id=listing_id,
        message=f"Listing status updated to {status.value}",
        listing=listing
    )


@router.post("/supply/{listing_id}/reserve", response_model=Dict[str, Any])
async def reserve_units(
    listing_id: str = Path(..., description="Supply listing ID"),
    units: Decimal = Body(..., description="Number of units to reserve", gt=0)
):
    """Reserve biodiversity units from a supply listing"""
    
    try:
        success = await supply_manager.reserve_units(listing_id, units)
        
        if not success:
            raise HTTPException(status_code=400, detail="Unable to reserve units - insufficient availability or listing not found")
        
        listing = await supply_manager.get_listing(listing_id)
        
        return {
            "success": True,
            "message": f"Reserved {units} units successfully",
            "listing_id": listing_id,
            "reserved_units": float(units),
            "remaining_available": float(listing.units_available) if listing else 0
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reservation failed: {str(e)}")


# Demand Requests Endpoints

@router.post("/demand/create", response_model=DemandRequestResponse)
async def create_demand_request(
    request_data: OffsetDemandRequest = Body(..., description="Demand request data")
):
    """
    Create a new biodiversity offset demand request
    
    Creates a request for developers needing to purchase biodiversity units.
    Includes site assessment and BNG requirement calculations.
    """
    try:
        
        demand_request = await demand_manager.create_demand_request(
            developer_name=request_data.developer_name,
            project_name=request_data.project_name,
            development_postcode=request_data.development_postcode,
            development_coordinates=request_data.development_coordinates,
            biodiversity_assessment=request_data.biodiversity_assessment,
            required_habitat_types=request_data.required_habitat_types,
            max_price_per_unit=request_data.max_price_per_unit,
            required_by_date=request_data.required_by_date,
            preferred_local_authorities=request_data.preferred_local_authorities,
            max_distance_km=request_data.max_distance_km,
            same_national_character_area=request_data.same_national_character_area
        )
        
        return DemandRequestResponse(
            success=True,
            request_id=demand_request.request_id,
            message="Demand request created successfully",
            request=demand_request
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create demand request: {str(e)}")


@router.get("/demand/{request_id}", response_model=DemandRequestResponse)
async def get_demand_request(
    request_id: str = Path(..., description="Demand request ID")
):
    """Get demand request by ID"""
    
    request = await demand_manager.get_demand_request(request_id)
    
    if not request:
        raise HTTPException(status_code=404, detail="Demand request not found")
    
    return DemandRequestResponse(
        success=True,
        request_id=request_id,
        message="Demand request retrieved successfully",
        request=request
    )


@router.get("/demand", response_model=Dict[str, Any])
async def search_demand_requests(
    habitat_types: Optional[List[HabitatType]] = Query(None, description="Required habitat types"),
    min_units: Optional[Decimal] = Query(None, description="Minimum required units"),
    max_units: Optional[Decimal] = Query(None, description="Maximum required units"),
    min_price: Optional[Decimal] = Query(None, description="Minimum price per unit"),
    local_authority: Optional[str] = Query(None, description="Preferred local authority"),
    status_filter: Optional[List[DemandStatus]] = Query([DemandStatus.SEARCHING], description="Request status"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Results offset for pagination")
):
    """
    Search biodiversity offset demand requests
    
    Allows suppliers to find developers looking for offsets.
    Supports filtering by requirements, location, and budget.
    """
    try:
        
        requests = await demand_manager.search_demand_requests(
            habitat_types=habitat_types,
            min_units=min_units,
            max_units=max_units,
            min_price=min_price,
            local_authority=local_authority,
            status_filter=status_filter,
            limit=limit,
            offset=offset
        )
        
        total_count = len(requests) + offset
        
        return {
            "success": True,
            "requests": requests,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": len(requests) == limit
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.put("/demand/{request_id}/status", response_model=DemandRequestResponse)
async def update_demand_status(
    request_id: str = Path(..., description="Demand request ID"),
    status: DemandStatus = Body(..., description="New request status")
):
    """Update demand request status"""
    
    success = await demand_manager.update_demand_status(request_id, status)
    
    if not success:
        raise HTTPException(status_code=404, detail="Demand request not found")
    
    request = await demand_manager.get_demand_request(request_id)
    
    return DemandRequestResponse(
        success=True,
        request_id=request_id,
        message=f"Request status updated to {status.value}",
        request=request
    )


# Matching Endpoints

@router.post("/matching/find", response_model=MatchingResponse)
async def find_matches(
    demand_request_id: Optional[str] = Body(None, description="Specific demand request to match"),
    supply_listing_id: Optional[str] = Body(None, description="Specific supply listing to match"),
    criteria: Optional[MatchingCriteria] = Body(None, description="Custom matching criteria"),
    max_matches: int = Body(50, ge=1, le=100, description="Maximum matches to return")
):
    """
    Find matches between supply and demand
    
    Advanced matching algorithm considering habitat compatibility,
    location preferences, timeline requirements, and pricing.
    """
    try:
        
        matches = await matching_engine.find_matches(
            demand_request_id=demand_request_id,
            supply_listing_id=supply_listing_id,
            criteria=criteria,
            max_matches=max_matches
        )
        
        return MatchingResponse(
            success=True,
            matches=matches,
            total_matches=len(matches),
            message=f"Found {len(matches)} potential matches"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")


@router.get("/matching/{match_id}", response_model=Dict[str, Any])
async def get_match(
    match_id: str = Path(..., description="Match ID")
):
    """Get detailed match information by ID"""
    
    match = await matching_engine.get_match(match_id)
    
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    return {
        "success": True,
        "match": match,
        "message": "Match retrieved successfully"
    }


@router.post("/matching/{match_id}/accept", response_model=Dict[str, Any])
async def accept_match(
    match_id: str = Path(..., description="Match ID")
):
    """Accept a potential match and proceed to agreement"""
    
    success = await matching_engine.accept_match(match_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Unable to accept match - match not found or no longer valid")
    
    return {
        "success": True,
        "message": "Match accepted successfully",
        "next_steps": "Agreement draft will be generated and parties will be notified"
    }


@router.post("/matching/{match_id}/reject", response_model=Dict[str, Any])
async def reject_match(
    match_id: str = Path(..., description="Match ID"),
    reason: Optional[str] = Body(None, description="Rejection reason")
):
    """Reject a potential match"""
    
    success = await matching_engine.reject_match(match_id, reason)
    
    if not success:
        raise HTTPException(status_code=400, detail="Unable to reject match - match not found")
    
    return {
        "success": True,
        "message": "Match rejected",
        "reason": reason or "No reason provided"
    }


@router.get("/demand/{request_id}/matches", response_model=MatchingResponse)
async def get_matches_for_demand(
    request_id: str = Path(..., description="Demand request ID")
):
    """Get all matches for a specific demand request"""
    
    matches = await matching_engine.get_matches_for_demand(request_id)
    
    return MatchingResponse(
        success=True,
        matches=matches,
        total_matches=len(matches),
        message=f"Found {len(matches)} matches for demand request"
    )


@router.get("/supply/{listing_id}/matches", response_model=MatchingResponse)
async def get_matches_for_supply(
    listing_id: str = Path(..., description="Supply listing ID")
):
    """Get all matches for a specific supply listing"""
    
    matches = await matching_engine.get_matches_for_supply(listing_id)
    
    return MatchingResponse(
        success=True,
        matches=matches,
        total_matches=len(matches),
        message=f"Found {len(matches)} matches for supply listing"
    )


@router.post("/matching/optimal-combination", response_model=MatchingResponse)
async def find_optimal_match_combination(
    demand_request_id: str = Body(..., description="Demand request ID"),
    max_suppliers: int = Body(3, ge=1, le=5, description="Maximum number of suppliers in combination")
):
    """
    Find optimal combination of suppliers to meet demand requirements
    
    Uses advanced algorithms to find the best combination of multiple suppliers
    when no single supplier can meet all requirements.
    """
    try:
        
        matches = await matching_engine.find_optimal_match_combination(
            demand_request_id, max_suppliers
        )
        
        total_units = sum(float(match.matched_units) for match in matches)
        total_value = sum(float(match.total_value) for match in matches)
        
        return MatchingResponse(
            success=True,
            matches=matches,
            total_matches=len(matches),
            message=f"Found optimal combination: {len(matches)} suppliers, {total_units:.2f} units, £{total_value:,.2f} total value"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


# Analytics and Statistics Endpoints

@router.get("/analytics/market-overview", response_model=Dict[str, Any])
async def get_market_overview():
    """
    Get comprehensive market overview and statistics
    
    Provides insights into current market conditions, pricing trends,
    and matching success rates.
    """
    try:
        
        # Get statistics from all managers
        supply_stats = await supply_manager.get_supply_statistics()
        demand_stats = await demand_manager.get_demand_statistics()
        matching_stats = await matching_engine.get_matching_statistics()
        
        # Calculate market indicators
        total_supply_units = supply_stats.get('total_units_available', 0)
        total_demand_units = demand_stats.get('total_units_required', 0)
        
        market_balance = "balanced"
        if total_supply_units > total_demand_units * 1.2:
            market_balance = "oversupply"
        elif total_demand_units > total_supply_units * 1.2:
            market_balance = "undersupply"
        
        return {
            "success": True,
            "market_overview": {
                "market_balance": market_balance,
                "total_supply_units": total_supply_units,
                "total_demand_units": total_demand_units,
                "supply_demand_ratio": round(
                    total_supply_units / total_demand_units, 2
                ) if total_demand_units > 0 else 0,
                "average_supply_price": supply_stats.get('average_price_per_unit', 0),
                "average_demand_budget": demand_stats.get('average_max_price', 0)
            },
            "supply_statistics": supply_stats,
            "demand_statistics": demand_stats,
            "matching_statistics": matching_stats,
            "generated_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")


@router.get("/analytics/pricing-suggestions/{listing_id}", response_model=Dict[str, Any])
async def get_pricing_suggestions(
    listing_id: str = Path(..., description="Supply listing ID"),
    target_match_score: float = Query(0.7, ge=0.1, le=1.0, description="Target match score")
):
    """
    Get AI-powered pricing suggestions to improve matching potential
    
    Analyzes current matching performance and suggests price adjustments
    to optimize match quality and market positioning.
    """
    
    suggestion = await matching_engine.suggest_price_adjustment(
        listing_id, target_match_score
    )
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Supply listing not found")
    
    return {
        "success": True,
        "pricing_suggestion": suggestion,
        "target_match_score": target_match_score,
        "generated_at": datetime.now().isoformat()
    }


# Health and Status Endpoints

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """API health check endpoint"""
    
    return {
        "success": True,
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {
            "supply_manager": "operational",
            "demand_manager": "operational", 
            "matching_engine": "operational"
        }
    }


@router.get("/", response_model=Dict[str, Any])
async def marketplace_info():
    """
    Biodiversity Offsets Marketplace API Information
    
    Provides overview of available endpoints and capabilities.
    """
    
    return {
        "name": "Domus Biodiversity Offsets Marketplace API",
        "version": "1.0.0",
        "description": "API for trading biodiversity net gain offsets with DEFRA metric integration",
        "features": [
            "Supply listing management for landowners",
            "Demand request processing for developers", 
            "Advanced habitat compatibility matching",
            "DEFRA biodiversity metric v4.0 calculations",
            "Location-based matching with distance optimization",
            "Timeline compatibility checking",
            "Price optimization suggestions",
            "Multi-supplier combination matching",
            "Comprehensive market analytics"
        ],
        "endpoints": {
            "supply": "/api/offsets/supply",
            "demand": "/api/offsets/demand", 
            "matching": "/api/offsets/matching",
            "analytics": "/api/offsets/analytics"
        },
        "documentation": "/docs",
        "compliance": "UK Biodiversity Net Gain regulations 2024"
    }