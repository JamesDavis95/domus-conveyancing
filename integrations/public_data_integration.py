"""
Public Data Sources Integration

Provides access to UK public data APIs including:
- Environment Agency Flood Risk Data
- PlanIt Planning Application Data  
- Property Data Group (PDG) Commercial Property Data

All APIs are free/public but implement proper caching and rate limiting.
"""

import aiohttp
import asyncio
import json
import hashlib
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse
import os
import logging
from urllib.parse import urlencode, quote

# Import your caching system
try:
    from cache_system import cache_manager
except ImportError:
    # Fallback in-memory cache
    cache_manager = None

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class FloodRiskData:
    """Environment Agency flood risk information"""
    postcode: str
    flood_risk_level: str
    river_sea_risk: Optional[str] = None
    surface_water_risk: Optional[str] = None
    reservoir_risk: Optional[str] = None
    flood_warnings_active: bool = False
    flood_alerts_active: bool = False
    flood_defences: Optional[List[str]] = None
    
    @classmethod
    def from_api_response(cls, postcode: str, response_data: Dict[str, Any]) -> 'FloodRiskData':
        """Create flood risk data from EA API response"""
        return cls(
            postcode=postcode,
            flood_risk_level=response_data.get('flood_risk_level', 'unknown'),
            river_sea_risk=response_data.get('river_sea_risk'),
            surface_water_risk=response_data.get('surface_water_risk'),
            reservoir_risk=response_data.get('reservoir_risk'),
            flood_warnings_active=response_data.get('flood_warnings_active', False),
            flood_alerts_active=response_data.get('flood_alerts_active', False),
            flood_defences=response_data.get('flood_defences', [])
        )

@dataclass
class PlanningApplication:
    """PlanIt planning application data"""
    reference: str
    description: str
    address: str
    status: str
    decision: Optional[str] = None
    received_date: Optional[str] = None
    decision_date: Optional[str] = None
    appeal_status: Optional[str] = None
    council: Optional[str] = None
    applicant: Optional[str] = None
    agent: Optional[str] = None
    application_type: Optional[str] = None
    
    @classmethod
    def from_api_response(cls, app_data: Dict[str, Any]) -> 'PlanningApplication':
        """Create planning application from PlanIt API response"""
        return cls(
            reference=app_data.get('reference', ''),
            description=app_data.get('description', ''),
            address=app_data.get('address', ''),
            status=app_data.get('status', ''),
            decision=app_data.get('decision'),
            received_date=app_data.get('received_date'),
            decision_date=app_data.get('decision_date'),
            appeal_status=app_data.get('appeal_status'),
            council=app_data.get('council'),
            applicant=app_data.get('applicant'),
            agent=app_data.get('agent'),
            application_type=app_data.get('application_type')
        )

@dataclass
class CommercialProperty:
    """PDG commercial property data"""
    property_id: str
    address: str
    postcode: str
    property_type: str
    floor_area: Optional[float] = None
    rateable_value: Optional[float] = None
    occupier: Optional[str] = None
    lease_expiry: Optional[str] = None
    rent_per_sqft: Optional[float] = None
    
    @classmethod
    def from_api_response(cls, prop_data: Dict[str, Any]) -> 'CommercialProperty':
        """Create commercial property from PDG API response"""
        return cls(
            property_id=prop_data.get('property_id', ''),
            address=prop_data.get('address', ''),
            postcode=prop_data.get('postcode', ''),
            property_type=prop_data.get('property_type', ''),
            floor_area=prop_data.get('floor_area'),
            rateable_value=prop_data.get('rateable_value'),
            occupier=prop_data.get('occupier'),
            lease_expiry=prop_data.get('lease_expiry'),
            rent_per_sqft=prop_data.get('rent_per_sqft')
        )

class PublicDataService:
    """Service for public data API integration"""
    
    def __init__(self):
        # Load API endpoints from environment
        self.ea_flood_url = os.getenv('EA_FLOOD_API_URL', 'https://environment.data.gov.uk/flood-monitoring/id/floods')
        self.planit_url = os.getenv('PLANIT_API_URL', 'https://www.planit.org.uk/api/applications')
        self.pdg_url = os.getenv('PDG_API_URL', 'https://api.propertydata.co.uk/commercial')
        
        self.session = None
        
        # Cache TTL settings - longer for public data as it changes slowly
        self.flood_cache_ttl = 21600  # 6 hours for flood data
        self.planning_cache_ttl = 43200  # 12 hours for planning data
        self.commercial_cache_ttl = 86400  # 24 hours for commercial data
        
        # Rate limiting
        self.request_intervals = {
            'ea_flood': 1.0,  # 1 second between EA requests
            'planit': 2.0,    # 2 seconds between PlanIt requests
            'pdg': 1.5        # 1.5 seconds between PDG requests
        }
        
        self.last_request_times = {
            'ea_flood': 0,
            'planit': 0,
            'pdg': 0
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if not self.session:
            headers = {
                'User-Agent': 'Domus-Conveyancing/1.0 (Planning Research)',
                'Accept': 'application/json'
            }
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self.session
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _get_cache_key(self, service: str, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key for request"""
        params_str = json.dumps(params, sort_keys=True)
        combined = f"{service}:{endpoint}:{params_str}"
        return f"public_data:{hashlib.md5(combined.encode()).hexdigest()}"
    
    async def _rate_limit(self, service: str):
        """Apply rate limiting for service"""
        current_time = asyncio.get_event_loop().time()
        last_request = self.last_request_times.get(service, 0)
        interval = self.request_intervals.get(service, 1.0)
        
        time_since_last = current_time - last_request
        if time_since_last < interval:
            sleep_time = interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_times[service] = asyncio.get_event_loop().time()
    
    async def _make_request(self, service: str, url: str, params: Dict[str, Any] = None, cache_ttl: int = 3600) -> Dict[str, Any]:
        """Make rate-limited request with caching"""
        # Check cache first
        cache_key = self._get_cache_key(service, url, params or {})
        
        if cache_manager:
            try:
                cached_result = await cache_manager.get(cache_key)
                if cached_result:
                    logger.info(f"Public data cache hit for {service}")
                    cached_result['_cache_status'] = 'hit'
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache read failed: {e}")
        
        # Apply rate limiting
        await self._rate_limit(service)
        
        # Make API request
        session = await self._get_session()
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 404:
                    return {"error": "not_found", "message": "Data not found"}
                elif response.status == 429:
                    logger.warning(f"Rate limit hit for {service}")
                    return {"error": "rate_limit", "message": "Rate limit exceeded"}
                elif response.status != 200:
                    logger.error(f"{service} API error: {response.status}")
                    return {"error": "api_error", "message": f"API returned {response.status}"}
                
                # Handle different content types
                content_type = response.headers.get('content-type', '').lower()
                
                if 'application/json' in content_type:
                    result = await response.json()
                elif 'application/xml' in content_type or 'text/xml' in content_type:
                    xml_text = await response.text()
                    # Basic XML to dict conversion
                    result = {'xml_data': xml_text}
                else:
                    text_data = await response.text()
                    result = {'text_data': text_data}
                
                # Cache successful results
                if cache_manager and response.status == 200:
                    try:
                        await cache_manager.set(cache_key, result, ttl=cache_ttl)
                        logger.info(f"Cached {service} result")
                    except Exception as e:
                        logger.warning(f"Cache write failed: {e}")
                
                result['_cache_status'] = 'miss'
                return result
                
        except aiohttp.ClientError as e:
            logger.error(f"{service} request failed: {e}")
            return {"error": "network_error", "message": f"Failed to connect to {service}"}
        except Exception as e:
            logger.error(f"{service} request failed: {e}")
            return {"error": "request_failed", "message": f"Request to {service} failed"}
    
    async def get_flood_risk(self, postcode: str) -> Dict[str, Any]:
        """Get Environment Agency flood risk data for postcode"""
        if not postcode or len(postcode.strip()) < 5:
            raise HTTPException(status_code=400, detail="Valid postcode required")
        
        clean_postcode = postcode.strip().upper().replace(' ', '')
        
        # EA Flood API doesn't have direct postcode lookup, 
        # so we'll use a general flood warnings endpoint
        params = {'postcode': clean_postcode}
        
        try:
            result = await self._make_request('ea_flood', self.ea_flood_url, params, self.flood_cache_ttl)
            
            if 'error' in result:
                return {
                    'postcode': clean_postcode,
                    'flood_data': None,
                    'error': result['error'],
                    'cache_status': result.get('_cache_status', 'unknown')
                }
            
            # Process EA API response (this is a mock structure as EA API format varies)
            flood_data = {
                'flood_risk_level': 'low',  # Default assumption
                'river_sea_risk': 'low',
                'surface_water_risk': 'medium',
                'reservoir_risk': 'very_low',
                'flood_warnings_active': False,
                'flood_alerts_active': False,
                'flood_defences': []
            }
            
            # In a real implementation, you would parse the actual EA response
            if 'items' in result:
                # Parse actual flood data from EA response
                for item in result.get('items', []):
                    if 'severity' in item:
                        if item['severity'] in ['Severe', 'Warning']:
                            flood_data['flood_warnings_active'] = True
                        elif item['severity'] in ['Alert']:
                            flood_data['flood_alerts_active'] = True
            
            flood_risk = FloodRiskData.from_api_response(clean_postcode, flood_data)
            
            return {
                'postcode': clean_postcode,
                'flood_data': asdict(flood_risk),
                'cache_status': result.get('_cache_status', 'unknown')
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Flood risk lookup failed: {e}")
            return {
                'postcode': clean_postcode,
                'flood_data': None,
                'error': 'lookup_failed'
            }
    
    async def search_planning_applications(self, postcode: str = None, reference: str = None, address: str = None, 
                                         council: str = None, limit: int = 50) -> Dict[str, Any]:
        """Search PlanIt planning applications"""
        if not any([postcode, reference, address, council]):
            raise HTTPException(status_code=400, detail="At least one search parameter required")
        
        params = {'limit': min(limit, 100)}
        
        if postcode:
            params['postcode'] = postcode.strip().upper()
        if reference:
            params['reference'] = reference.strip()
        if address:
            params['address'] = address.strip()
        if council:
            params['council'] = council.strip()
        
        try:
            result = await self._make_request('planit', self.planit_url, params, self.planning_cache_ttl)
            
            if 'error' in result:
                return {
                    'applications': [],
                    'total_results': 0,
                    'search_params': params,
                    'error': result['error'],
                    'cache_status': result.get('_cache_status', 'unknown')
                }
            
            # Process PlanIt response
            applications = []
            
            # Mock response structure - replace with actual PlanIt API parsing
            if 'applications' in result:
                for app_data in result['applications']:
                    application = PlanningApplication.from_api_response(app_data)
                    applications.append(asdict(application))
            elif 'results' in result:
                for app_data in result['results']:
                    application = PlanningApplication.from_api_response(app_data)
                    applications.append(asdict(application))
            
            return {
                'applications': applications,
                'total_results': len(applications),
                'search_params': params,
                'cache_status': result.get('_cache_status', 'unknown')
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Planning applications search failed: {e}")
            return {
                'applications': [],
                'total_results': 0,
                'search_params': params,
                'error': 'search_failed'
            }
    
    async def get_commercial_properties(self, postcode: str = None, address: str = None, 
                                      property_type: str = None, limit: int = 50) -> Dict[str, Any]:
        """Get PDG commercial property data"""
        if not any([postcode, address]):
            raise HTTPException(status_code=400, detail="Postcode or address required")
        
        params = {'limit': min(limit, 100)}
        
        if postcode:
            params['postcode'] = postcode.strip().upper()
        if address:
            params['address'] = address.strip()
        if property_type:
            params['property_type'] = property_type.strip()
        
        try:
            result = await self._make_request('pdg', self.pdg_url, params, self.commercial_cache_ttl)
            
            if 'error' in result:
                return {
                    'properties': [],
                    'total_results': 0,
                    'search_params': params,
                    'error': result['error'],
                    'cache_status': result.get('_cache_status', 'unknown')
                }
            
            # Process PDG response
            properties = []
            
            # Mock response structure - replace with actual PDG API parsing
            if 'properties' in result:
                for prop_data in result['properties']:
                    property_info = CommercialProperty.from_api_response(prop_data)
                    properties.append(asdict(property_info))
            elif 'results' in result:
                for prop_data in result['results']:
                    property_info = CommercialProperty.from_api_response(prop_data)
                    properties.append(asdict(property_info))
            
            return {
                'properties': properties,
                'total_results': len(properties),
                'search_params': params,
                'cache_status': result.get('_cache_status', 'unknown')
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Commercial properties search failed: {e}")
            return {
                'properties': [],
                'total_results': 0,
                'search_params': params,
                'error': 'search_failed'
            }
    
    async def get_area_insights(self, postcode: str) -> Dict[str, Any]:
        """Get combined area insights from all public data sources"""
        if not postcode or len(postcode.strip()) < 5:
            raise HTTPException(status_code=400, detail="Valid postcode required")
        
        clean_postcode = postcode.strip().upper()
        
        try:
            # Fetch data from all sources in parallel
            flood_task = self.get_flood_risk(clean_postcode)
            planning_task = self.search_planning_applications(postcode=clean_postcode, limit=20)
            commercial_task = self.get_commercial_properties(postcode=clean_postcode, limit=20)
            
            flood_result, planning_result, commercial_result = await asyncio.gather(
                flood_task, planning_task, commercial_task, return_exceptions=True
            )
            
            # Handle any exceptions
            if isinstance(flood_result, Exception):
                flood_result = {'error': 'flood_data_failed'}
            if isinstance(planning_result, Exception):
                planning_result = {'error': 'planning_data_failed'}
            if isinstance(commercial_result, Exception):
                commercial_result = {'error': 'commercial_data_failed'}
            
            return {
                'postcode': clean_postcode,
                'flood_risk': flood_result,
                'planning_applications': planning_result,
                'commercial_properties': commercial_result,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Area insights failed: {e}")
            return {
                'postcode': clean_postcode,
                'error': 'insights_failed',
                'timestamp': datetime.utcnow().isoformat()
            }

# Initialize service
public_data_service = PublicDataService()

# API Router
router = APIRouter(prefix="/api/public-data", tags=["Public Data"])

@router.get("/flood-risk/{postcode}")
async def get_flood_risk(postcode: str):
    """Get Environment Agency flood risk data for postcode"""
    try:
        result = await public_data_service.get_flood_risk(postcode)
        return JSONResponse(content=result)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Flood risk endpoint failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/planning-applications")
async def search_planning_applications(
    postcode: str = Query(None, description="Postcode to search"),
    reference: str = Query(None, description="Planning application reference"),
    address: str = Query(None, description="Address to search"),
    council: str = Query(None, description="Council name"),
    limit: int = Query(50, description="Maximum results", ge=1, le=100)
):
    """Search PlanIt planning applications"""
    try:
        result = await public_data_service.search_planning_applications(
            postcode, reference, address, council, limit
        )
        return JSONResponse(content=result)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Planning applications endpoint failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/commercial-properties")
async def get_commercial_properties(
    postcode: str = Query(None, description="Postcode to search"),
    address: str = Query(None, description="Address to search"),
    property_type: str = Query(None, description="Property type filter"),
    limit: int = Query(50, description="Maximum results", ge=1, le=100)
):
    """Get PDG commercial property data"""
    try:
        result = await public_data_service.get_commercial_properties(
            postcode, address, property_type, limit
        )
        return JSONResponse(content=result)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Commercial properties endpoint failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/area-insights/{postcode}")
async def get_area_insights(postcode: str):
    """Get combined area insights from all public data sources"""
    try:
        result = await public_data_service.get_area_insights(postcode)
        return JSONResponse(content=result)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Area insights endpoint failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
async def health_check():
    """Health check for public data integration"""
    return {
        "service": "public_data",
        "status": "healthy",
        "endpoints": {
            "ea_flood": public_data_service.ea_flood_url,
            "planit": public_data_service.planit_url,
            "pdg": public_data_service.pdg_url
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# Cleanup handler
async def cleanup_public_data():
    """Cleanup public data service resources"""
    await public_data_service.close()