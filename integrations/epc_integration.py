"""
EPC (Energy Performance Certificate) Integration
Server-side only with Basic Auth - NEVER expose to browser
"""

import os
import httpx
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
import asyncio
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/epc", tags=["EPC"])

class EPCService:
    """EPC API integration using server-side Basic auth"""
    
    def __init__(self):
        # Use the complete Basic auth header from environment
        self.auth_header = os.getenv("EPC_AUTH_BASIC")
        self.base_url = "https://epc.opendatacommunities.org/api/v1"
        
        # Cache settings
        self.cache_ttl_search = 12 * 3600  # 12 hours for search
        self.cache_ttl_cert = 7 * 24 * 3600  # 7 days for certificates
        self.cache = {}  # Use Redis in production
        
        if not self.auth_header:
            logger.warning("EPC Basic auth not configured")
    
    async def search_by_postcode(self, postcode: str) -> List[Dict[str, Any]]:
        """Search EPCs by postcode - server-side only"""
        
        if not self.auth_header:
            raise HTTPException(status_code=503, detail="EPC service not configured")
        
        # Check cache first
        cache_key = f"epc_search:{postcode}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/domestic/search",
                    params={"postcode": postcode},
                    headers={"Authorization": self.auth_header}
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Transform response to our format
                epcs = self._transform_search_results(data.get("rows", []))
                
                # Cache results
                self._set_cache(cache_key, epcs, self.cache_ttl_search)
                
                return epcs
                
        except httpx.HTTPError as e:
            logger.error(f"EPC search error: {e}")
            raise HTTPException(status_code=500, detail="EPC search failed")
    
    async def search_by_uprn(self, uprn: str) -> List[Dict[str, Any]]:
        """Search EPCs by UPRN - server-side only"""
        
        if not self.auth_header:
            raise HTTPException(status_code=503, detail="EPC service not configured")
        
        cache_key = f"epc_uprn:{uprn}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/domestic/search",
                    params={"uprn": uprn},
                    headers={"Authorization": self.auth_header}
                )
                
                response.raise_for_status()
                data = response.json()
                
                epcs = self._transform_search_results(data.get("rows", []))
                self._set_cache(cache_key, epcs, self.cache_ttl_search)
                
                return epcs
                
        except httpx.HTTPError as e:
            logger.error(f"EPC UPRN search error: {e}")
            raise HTTPException(status_code=500, detail="EPC search failed")
    
    async def get_certificate_details(self, lmk_key: str) -> Dict[str, Any]:
        """Get full EPC certificate details - server-side only"""
        
        if not self.auth_header:
            raise HTTPException(status_code=503, detail="EPC service not configured")
        
        cache_key = f"epc_cert:{lmk_key}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/domestic/certificate/{lmk_key}",
                    headers={"Authorization": self.auth_header}
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Transform to our format
                certificate = self._transform_certificate(data.get("rows", [{}])[0])
                
                # Cache for longer period
                self._set_cache(cache_key, certificate, self.cache_ttl_cert)
                
                return certificate
                
        except httpx.HTTPError as e:
            logger.error(f"EPC certificate error: {e}")
            raise HTTPException(status_code=500, detail="EPC certificate fetch failed")
    
    async def get_recommendations(self, lmk_key: str) -> List[Dict[str, Any]]:
        """Get EPC recommendations - server-side only"""
        
        if not self.auth_header:
            raise HTTPException(status_code=503, detail="EPC service not configured")
        
        cache_key = f"epc_recs:{lmk_key}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/domestic/recommendations/{lmk_key}",
                    headers={"Authorization": self.auth_header}
                )
                
                response.raise_for_status()
                data = response.json()
                
                recommendations = self._transform_recommendations(data.get("rows", []))
                self._set_cache(cache_key, recommendations, self.cache_ttl_cert)
                
                return recommendations
                
        except httpx.HTTPError as e:
            logger.error(f"EPC recommendations error: {e}")
            raise HTTPException(status_code=500, detail="EPC recommendations fetch failed")
    
    def _transform_search_results(self, rows: List[Dict]) -> List[Dict[str, Any]]:
        """Transform EPC search results to our format"""
        
        epcs = []
        for row in rows:
            epc = {
                "lmk_key": row.get("lmk-key"),
                "address1": row.get("address1", ""),
                "address2": row.get("address2", ""),
                "address3": row.get("address3", ""),
                "postcode": row.get("postcode", ""),
                "building_reference_number": row.get("building-reference-number"),
                "current_energy_rating": row.get("current-energy-rating", ""),
                "potential_energy_rating": row.get("potential-energy-rating", ""),
                "current_energy_efficiency": row.get("current-energy-efficiency"),
                "potential_energy_efficiency": row.get("potential-energy-efficiency"),
                "property_type": row.get("property-type", ""),
                "built_form": row.get("built-form", ""),
                "inspection_date": row.get("inspection-date", ""),
                "local_authority": row.get("local-authority", ""),
                "constituency": row.get("constituency", ""),
                "county": row.get("county", ""),
                "lodgement_date": row.get("lodgement-date", ""),
                "transaction_type": row.get("transaction-type", ""),
                "environment_impact_current": row.get("environment-impact-current"),
                "environment_impact_potential": row.get("environment-impact-potential"),
                "energy_consumption_current": row.get("energy-consumption-current"),
                "energy_consumption_potential": row.get("energy-consumption-potential"),
                "co2_emissions_current": row.get("co2-emissions-current"),
                "co2_emissions_potential": row.get("co2-emissions-potential"),
                "heating_cost_current": row.get("heating-cost-current"),
                "heating_cost_potential": row.get("heating-cost-potential"),
                "hot_water_cost_current": row.get("hot-water-cost-current"),
                "hot_water_cost_potential": row.get("hot-water-cost-potential"),
                "lighting_cost_current": row.get("lighting-cost-current"),
                "lighting_cost_potential": row.get("lighting-cost-potential"),
                "total_floor_area": row.get("total-floor-area"),
                "mains_gas_flag": row.get("mains-gas-flag"),
                "floor_level": row.get("floor-level"),
                "flat_top_storey": row.get("flat-top-storey"),
                "flat_storey_count": row.get("flat-storey-count")
            }
            epcs.append(epc)
        
        return epcs
    
    def _transform_certificate(self, row: Dict) -> Dict[str, Any]:
        """Transform EPC certificate details to our format"""
        
        return {
            "lmk_key": row.get("lmk-key"),
            "address": f"{row.get('address1', '')} {row.get('address2', '')} {row.get('address3', '')}".strip(),
            "postcode": row.get("postcode", ""),
            "current_energy_rating": row.get("current-energy-rating", ""),
            "potential_energy_rating": row.get("potential-energy-rating", ""),
            "current_energy_efficiency": row.get("current-energy-efficiency"),
            "potential_energy_efficiency": row.get("potential-energy-efficiency"),
            "property_type": row.get("property-type", ""),
            "built_form": row.get("built-form", ""),
            "inspection_date": row.get("inspection-date", ""),
            "lodgement_date": row.get("lodgement-date", ""),
            "total_floor_area": row.get("total-floor-area"),
            "energy_consumption_current": row.get("energy-consumption-current"),
            "co2_emissions_current": row.get("co2-emissions-current"),
            "heating_cost_current": row.get("heating-cost-current"),
            "hot_water_cost_current": row.get("hot-water-cost-current"),
            "lighting_cost_current": row.get("lighting-cost-current"),
            "walls_description": row.get("walls-description", ""),
            "roof_description": row.get("roof-description", ""),
            "windows_description": row.get("windows-description", ""),
            "main_heating_description": row.get("main-heating-description", ""),
            "hot_water_description": row.get("hot-water-description", ""),
            "floor_description": row.get("floor-description", ""),
            "main_fuel": row.get("main-fuel", ""),
            "wind_turbine_count": row.get("wind-turbine-count"),
            "heat_loss_corridor": row.get("heat-loss-corridor", ""),
            "unheated_corridor_length": row.get("unheated-corridor-length"),
            "floor_height": row.get("floor-height"),
            "photo_supply": row.get("photo-supply"),
            "solar_water_heating_flag": row.get("solar-water-heating-flag"),
            "mechanical_ventilation": row.get("mechanical-ventilation", ""),
            "number_habitable_rooms": row.get("number-habitable-rooms"),
            "number_heated_rooms": row.get("number-heated-rooms")
        }
    
    def _transform_recommendations(self, rows: List[Dict]) -> List[Dict[str, Any]]:
        """Transform EPC recommendations to our format"""
        
        recommendations = []
        for row in rows:
            rec = {
                "improvement_item": row.get("improvement-item"),
                "improvement_summary_text": row.get("improvement-summary-text", ""),
                "improvement_descr_text": row.get("improvement-descr-text", ""),
                "improvement_id": row.get("improvement-id"),
                "improvement_id_text": row.get("improvement-id-text", ""),
                "indicative_cost": row.get("indicative-cost", "")
            }
            recommendations.append(rec)
        
        return recommendations
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if key in self.cache:
            item = self.cache[key]
            if datetime.utcnow() < item["expires"]:
                return item["data"]
            else:
                del self.cache[key]
        return None
    
    def _set_cache(self, key: str, data: Any, ttl: int):
        """Set item in cache with TTL"""
        self.cache[key] = {
            "data": data,
            "expires": datetime.utcnow() + timedelta(seconds=ttl)
        }

# Initialize service
epc_service = EPCService()

# Routes - all server-side, never expose EPC auth to browser
@router.get("/search/postcode/{postcode}")
async def search_epc_by_postcode(postcode: str):
    """Search EPCs by postcode - shows in Constraints tab"""
    
    try:
        epcs = await epc_service.search_by_postcode(postcode)
        
        return {
            "epcs": epcs,
            "source": "EPC Open Data Communities",
            "cache": "hit" if f"epc_search:{postcode}" in epc_service.cache else "miss",
            "retrieved_at": datetime.utcnow().isoformat(),
            "ttl_seconds": epc_service.cache_ttl_search
        }
        
    except Exception as e:
        logger.error(f"EPC search error: {e}")
        return {
            "epcs": [],
            "error": "EPC search temporarily unavailable",
            "source": "EPC Open Data Communities"
        }

@router.get("/search/uprn/{uprn}")
async def search_epc_by_uprn(uprn: str):
    """Search EPCs by UPRN"""
    
    try:
        epcs = await epc_service.search_by_uprn(uprn)
        
        return {
            "epcs": epcs,
            "source": "EPC Open Data Communities",
            "cache": "hit" if f"epc_uprn:{uprn}" in epc_service.cache else "miss",
            "retrieved_at": datetime.utcnow().isoformat(),
            "ttl_seconds": epc_service.cache_ttl_search
        }
        
    except Exception as e:
        logger.error(f"EPC UPRN search error: {e}")
        return {
            "epcs": [],
            "error": "EPC search temporarily unavailable",
            "source": "EPC Open Data Communities"
        }

@router.get("/certificate/{lmk_key}")
async def get_epc_certificate(lmk_key: str):
    """Get full EPC certificate details"""
    
    try:
        certificate = await epc_service.get_certificate_details(lmk_key)
        
        return {
            "certificate": certificate,
            "source": "EPC Open Data Communities",
            "cache": "hit" if f"epc_cert:{lmk_key}" in epc_service.cache else "miss",
            "retrieved_at": datetime.utcnow().isoformat(),
            "ttl_seconds": epc_service.cache_ttl_cert
        }
        
    except Exception as e:
        logger.error(f"EPC certificate error: {e}")
        return {
            "certificate": None,
            "error": "EPC certificate temporarily unavailable",
            "source": "EPC Open Data Communities"
        }

@router.get("/recommendations/{lmk_key}")
async def get_epc_recommendations(lmk_key: str):
    """Get EPC recommendations"""
    
    try:
        recommendations = await epc_service.get_recommendations(lmk_key)
        
        return {
            "recommendations": recommendations,
            "source": "EPC Open Data Communities",
            "cache": "hit" if f"epc_recs:{lmk_key}" in epc_service.cache else "miss",
            "retrieved_at": datetime.utcnow().isoformat(),
            "ttl_seconds": epc_service.cache_ttl_cert
        }
        
    except Exception as e:
        logger.error(f"EPC recommendations error: {e}")
        return {
            "recommendations": [],
            "error": "EPC recommendations temporarily unavailable",
            "source": "EPC Open Data Communities"
        }

# Export for main app integration
__all__ = ["router", "epc_service"]