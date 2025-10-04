"""
Companies House API Integration for Company Verification

Provides server-side company verification with proper API key protection.
Supports company search and details retrieval with automatic caching.
"""

import aiohttp
import asyncio
import base64
import json
import hashlib
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
import os
import logging

# Import your caching system
try:
    from cache_system import cache_manager
except ImportError:
    # Fallback in-memory cache
    cache_manager = None

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class CompanyAddress:
    """Company address information"""
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    locality: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    
    @classmethod
    def from_api_response(cls, address_data: Dict[str, Any]) -> 'CompanyAddress':
        """Create address from Companies House API response"""
        return cls(
            address_line_1=address_data.get('address_line_1'),
            address_line_2=address_data.get('address_line_2'),
            locality=address_data.get('locality'),
            region=address_data.get('region'),
            postal_code=address_data.get('postal_code'),
            country=address_data.get('country')
        )

@dataclass
class CompanyOfficer:
    """Company officer/director information"""
    name: str
    officer_role: str
    appointed_on: Optional[str] = None
    date_of_birth: Optional[Dict[str, int]] = None
    nationality: Optional[str] = None
    country_of_residence: Optional[str] = None
    occupation: Optional[str] = None
    
    @classmethod
    def from_api_response(cls, officer_data: Dict[str, Any]) -> 'CompanyOfficer':
        """Create officer from Companies House API response"""
        return cls(
            name=officer_data.get('name', ''),
            officer_role=officer_data.get('officer_role', ''),
            appointed_on=officer_data.get('appointed_on'),
            date_of_birth=officer_data.get('date_of_birth'),
            nationality=officer_data.get('nationality'),
            country_of_residence=officer_data.get('country_of_residence'),
            occupation=officer_data.get('occupation')
        )

@dataclass
class CompanyDetails:
    """Complete company information"""
    company_number: str
    company_name: str
    company_status: str
    company_type: str
    date_of_creation: Optional[str] = None
    date_of_cessation: Optional[str] = None
    registered_office_address: Optional[CompanyAddress] = None
    accounts: Optional[Dict[str, Any]] = None
    annual_return: Optional[Dict[str, Any]] = None
    confirmation_statement: Optional[Dict[str, Any]] = None
    sic_codes: Optional[List[str]] = None
    has_been_liquidated: bool = False
    has_charges: bool = False
    has_insolvency_history: bool = False
    officers: Optional[List[CompanyOfficer]] = None
    jurisdiction: Optional[str] = None
    
    @classmethod
    def from_api_response(cls, company_data: Dict[str, Any], officers_data: Optional[List[Dict[str, Any]]] = None) -> 'CompanyDetails':
        """Create company details from Companies House API response"""
        # Parse registered office address
        address = None
        if 'registered_office_address' in company_data:
            address = CompanyAddress.from_api_response(company_data['registered_office_address'])
        
        # Parse officers
        officers = []
        if officers_data:
            officers = [CompanyOfficer.from_api_response(officer) for officer in officers_data]
        
        return cls(
            company_number=company_data.get('company_number', ''),
            company_name=company_data.get('company_name', ''),
            company_status=company_data.get('company_status', ''),
            company_type=company_data.get('company_type', ''),
            date_of_creation=company_data.get('date_of_creation'),
            date_of_cessation=company_data.get('date_of_cessation'),
            registered_office_address=address,
            accounts=company_data.get('accounts'),
            annual_return=company_data.get('annual_return'),
            confirmation_statement=company_data.get('confirmation_statement'),
            sic_codes=company_data.get('sic_codes'),
            has_been_liquidated=company_data.get('has_been_liquidated', False),
            has_charges=company_data.get('has_charges', False),
            has_insolvency_history=company_data.get('has_insolvency_history', False),
            officers=officers,
            jurisdiction=company_data.get('jurisdiction')
        )

@dataclass
class CompanySearchResult:
    """Company search result"""
    company_number: str
    title: str
    company_status: str
    company_type: str
    date_of_creation: Optional[str] = None
    address_snippet: Optional[str] = None
    
    @classmethod
    def from_api_response(cls, item: Dict[str, Any]) -> 'CompanySearchResult':
        """Create search result from Companies House API response"""
        return cls(
            company_number=item.get('company_number', ''),
            title=item.get('title', ''),
            company_status=item.get('company_status', ''),
            company_type=item.get('company_type', ''),
            date_of_creation=item.get('date_of_creation'),
            address_snippet=item.get('address_snippet')
        )

class CompaniesHouseService:
    """Service for Companies House API integration"""
    
    def __init__(self):
        self.api_key = os.getenv('COMPANIES_HOUSE_API_KEY')
        if not self.api_key:
            logger.warning("COMPANIES_HOUSE_API_KEY not found in environment")
            self.api_key = None
        
        self.base_url = "https://api.company-information.service.gov.uk"
        self.session = None
        
        # Cache TTL settings
        self.search_cache_ttl = 3600  # 1 hour for search results
        self.company_cache_ttl = 86400  # 24 hours for company details
        self.officers_cache_ttl = 86400  # 24 hours for officers
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with authentication"""
        if not self.session:
            # Companies House API uses basic auth with API key as username
            auth_string = f"{self.api_key}:"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded_auth}',
                'Accept': 'application/json',
                'User-Agent': 'Domus-Conveyancing/1.0'
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        
        return self.session
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key for request"""
        # Create deterministic key from endpoint and params
        params_str = json.dumps(params, sort_keys=True)
        combined = f"{endpoint}:{params_str}"
        return f"companies_house:{hashlib.md5(combined.encode()).hexdigest()}"
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None, cache_ttl: int = 3600) -> Dict[str, Any]:
        """Make authenticated request to Companies House API with caching"""
        if not self.api_key:
            raise HTTPException(status_code=503, detail="Companies House API not configured")
        
        # Check cache first
        cache_key = self._get_cache_key(endpoint, params or {})
        
        if cache_manager:
            try:
                cached_result = await cache_manager.get(cache_key)
                if cached_result:
                    logger.info(f"Companies House cache hit for {endpoint}")
                    # Add cache metadata
                    if isinstance(cached_result, dict):
                        cached_result['_cache_status'] = 'hit'
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache read failed: {e}")
        
        # Make API request
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 404:
                    return {"error": "not_found", "message": "Company not found"}
                elif response.status == 429:
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")
                elif response.status != 200:
                    logger.error(f"Companies House API error: {response.status}")
                    raise HTTPException(status_code=503, detail="Companies House service unavailable")
                
                result = await response.json()
                
                # Cache successful results
                if cache_manager and response.status == 200:
                    try:
                        await cache_manager.set(cache_key, result, ttl=cache_ttl)
                        logger.info(f"Cached Companies House result for {endpoint}")
                    except Exception as e:
                        logger.warning(f"Cache write failed: {e}")
                
                # Add cache metadata
                result['_cache_status'] = 'miss'
                return result
                
        except aiohttp.ClientError as e:
            logger.error(f"Companies House request failed: {e}")
            raise HTTPException(status_code=503, detail="Failed to connect to Companies House")
    
    async def search_companies(self, query: str, items_per_page: int = 20, start_index: int = 0) -> Dict[str, Any]:
        """Search for companies by name"""
        if not query or len(query.strip()) < 2:
            raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
        
        params = {
            'q': query.strip(),
            'items_per_page': min(items_per_page, 100),  # API limit
            'start_index': start_index
        }
        
        try:
            result = await self._make_request('/search/companies', params, self.search_cache_ttl)
            
            if 'error' in result:
                return {
                    'companies': [],
                    'total_results': 0,
                    'items_per_page': items_per_page,
                    'start_index': start_index,
                    'query': query,
                    'error': result['error'],
                    'cache_status': result.get('_cache_status', 'unknown')
                }
            
            # Transform API response
            companies = []
            if 'items' in result:
                companies = [CompanySearchResult.from_api_response(item) for item in result['items']]
            
            return {
                'companies': [asdict(company) for company in companies],
                'total_results': result.get('total_results', 0),
                'items_per_page': result.get('items_per_page', items_per_page),
                'start_index': result.get('start_index', start_index),
                'query': query,
                'cache_status': result.get('_cache_status', 'unknown')
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Company search failed: {e}")
            return {
                'companies': [],
                'total_results': 0,
                'items_per_page': items_per_page,
                'start_index': start_index,
                'query': query,
                'error': 'search_failed'
            }
    
    async def get_company_details(self, company_number: str, include_officers: bool = True) -> Dict[str, Any]:
        """Get detailed company information"""
        if not company_number:
            raise HTTPException(status_code=400, detail="Company number is required")
        
        # Clean company number
        clean_number = company_number.strip().upper()
        
        try:
            # Get company details
            company_result = await self._make_request(f'/company/{clean_number}', cache_ttl=self.company_cache_ttl)
            
            if 'error' in company_result:
                return {
                    'company': None,
                    'error': company_result['error'],
                    'cache_status': company_result.get('_cache_status', 'unknown')
                }
            
            # Get officers if requested
            officers_data = None
            if include_officers:
                officers_result = await self._make_request(f'/company/{clean_number}/officers', cache_ttl=self.officers_cache_ttl)
                if 'items' in officers_result:
                    officers_data = officers_result['items']
            
            # Transform API response
            company = CompanyDetails.from_api_response(company_result, officers_data)
            
            return {
                'company': asdict(company),
                'cache_status': company_result.get('_cache_status', 'unknown')
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get company details failed: {e}")
            return {
                'company': None,
                'error': 'lookup_failed'
            }
    
    async def get_company_officers(self, company_number: str, items_per_page: int = 35, start_index: int = 0) -> Dict[str, Any]:
        """Get company officers/directors"""
        if not company_number:
            raise HTTPException(status_code=400, detail="Company number is required")
        
        clean_number = company_number.strip().upper()
        
        params = {
            'items_per_page': min(items_per_page, 100),  # API limit
            'start_index': start_index
        }
        
        try:
            result = await self._make_request(f'/company/{clean_number}/officers', params, self.officers_cache_ttl)
            
            if 'error' in result:
                return {
                    'officers': [],
                    'total_results': 0,
                    'items_per_page': items_per_page,
                    'start_index': start_index,
                    'company_number': clean_number,
                    'error': result['error'],
                    'cache_status': result.get('_cache_status', 'unknown')
                }
            
            # Transform API response
            officers = []
            if 'items' in result:
                officers = [CompanyOfficer.from_api_response(item) for item in result['items']]
            
            return {
                'officers': [asdict(officer) for officer in officers],
                'total_results': result.get('total_results', 0),
                'items_per_page': result.get('items_per_page', items_per_page),
                'start_index': result.get('start_index', start_index),
                'company_number': clean_number,
                'cache_status': result.get('_cache_status', 'unknown')
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get company officers failed: {e}")
            return {
                'officers': [],
                'total_results': 0,
                'items_per_page': items_per_page,
                'start_index': start_index,
                'company_number': clean_number,
                'error': 'lookup_failed'
            }

# Initialize service
companies_house_service = CompaniesHouseService()

# API Router
router = APIRouter(prefix="/api/companies-house", tags=["Companies House"])

@router.get("/search")
async def search_companies(
    q: str = Query(..., description="Company name to search for", min_length=2),
    items_per_page: int = Query(20, description="Results per page", ge=1, le=100),
    start_index: int = Query(0, description="Starting index for pagination", ge=0)
):
    """Search for companies by name"""
    try:
        result = await companies_house_service.search_companies(q, items_per_page, start_index)
        return JSONResponse(content=result)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Company search endpoint failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/company/{company_number}")
async def get_company_details(
    company_number: str,
    include_officers: bool = Query(True, description="Include officers in response")
):
    """Get detailed company information"""
    try:
        result = await companies_house_service.get_company_details(company_number, include_officers)
        return JSONResponse(content=result)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Company details endpoint failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/company/{company_number}/officers")
async def get_company_officers(
    company_number: str,
    items_per_page: int = Query(35, description="Officers per page", ge=1, le=100),
    start_index: int = Query(0, description="Starting index for pagination", ge=0)
):
    """Get company officers/directors"""
    try:
        result = await companies_house_service.get_company_officers(company_number, items_per_page, start_index)
        return JSONResponse(content=result)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Company officers endpoint failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
async def health_check():
    """Health check for Companies House integration"""
    return {
        "service": "companies_house",
        "status": "healthy" if companies_house_service.api_key else "missing_api_key",
        "timestamp": datetime.utcnow().isoformat()
    }

# Cleanup handler
async def cleanup_companies_house():
    """Cleanup Companies House service resources"""
    await companies_house_service.close()