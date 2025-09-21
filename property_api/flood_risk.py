"""
Flood Risk Data Adapter
Integration with Environment Agency flood risk APIs and datasets
"""
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import aiohttp
import json
from datetime import datetime
import re
from dataclasses import dataclass, asdict

from .cache import PropertyDataCache


@dataclass
class FloodRiskData:
    """Flood risk assessment data"""
    postcode: str
    coordinates: Tuple[float, float]
    
    # Flood risk levels (Very Low, Low, Medium, High)
    river_and_sea: str
    surface_water: str
    reservoirs: str
    groundwater: Optional[str] = None
    
    # Detailed risk information
    in_flood_zone_2: bool = False
    in_flood_zone_3: bool = False
    coastal_flood_risk: Optional[str] = None
    
    # Surface water details
    surface_water_depth_30yr: Optional[str] = None
    surface_water_depth_100yr: Optional[str] = None
    surface_water_depth_1000yr: Optional[str] = None
    
    # River flood details
    river_flood_warnings: List[str] = None
    river_flood_alerts: List[str] = None
    
    # Historical flooding
    historic_flooding: bool = False
    historic_flood_events: Optional[List[Dict[str, Any]]] = None
    
    # Defences
    flood_defences: Optional[List[Dict[str, Any]]] = None
    
    # Risk summary
    overall_flood_risk: str = "Unknown"
    risk_summary: str = ""
    recommendations: List[str] = None


class FloodRiskAdapter:
    """Adapter for Environment Agency flood risk data"""
    
    def __init__(self):
        # Environment Agency API endpoints
        self.base_urls = {
            'flood_warnings': 'https://environment.data.gov.uk/flood-monitoring/id/floods',
            'flood_zones': 'https://environment.data.gov.uk/spatial/flood-map-for-planning/',
            'real_time_api': 'https://check-for-flooding.service.gov.uk/api/',
            'postcode_api': 'https://api.gov.uk/ea/floods/postcode/'
        }
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache = PropertyDataCache('flood_risk', ttl_hours=24)
        self.rate_limit_delay = 1.0  # Seconds between requests
        self.last_request_time = 0
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Domus-Planning-AI/1.0',
                'Accept': 'application/json'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        
        self.last_request_time = asyncio.get_event_loop().time()
    
    async def get_flood_risk_by_postcode(self, postcode: str) -> Optional[FloodRiskData]:
        """
        Get comprehensive flood risk data by postcode
        
        Args:
            postcode: UK postcode
            
        Returns:
            FloodRiskData object or None if not found
        """
        
        postcode_clean = self._normalize_postcode(postcode)
        
        # Check cache
        cache_key = f"postcode_{postcode_clean}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return FloodRiskData(**cached_data)
        
        try:
            # Get coordinates for postcode first
            coordinates = await self._get_postcode_coordinates(postcode_clean)
            if not coordinates:
                coordinates = (51.5074, -0.1278)  # Default to London
            
            # Get flood risk data from multiple sources
            flood_data_tasks = [
                self._get_postcode_flood_risk(postcode_clean),
                self._get_coordinate_flood_risk(coordinates),
                self._get_flood_warnings(coordinates),
                self._get_historic_flooding(coordinates)
            ]
            
            results = await asyncio.gather(*flood_data_tasks, return_exceptions=True)
            
            # Combine results
            postcode_risk, coordinate_risk, warnings, historic = results
            
            # Handle exceptions
            if isinstance(postcode_risk, Exception):
                postcode_risk = {}
            if isinstance(coordinate_risk, Exception):
                coordinate_risk = {}
            if isinstance(warnings, Exception):
                warnings = {}
            if isinstance(historic, Exception):
                historic = {}
            
            # Create comprehensive flood risk data
            flood_risk = self._combine_flood_data(
                postcode_clean, coordinates, postcode_risk, 
                coordinate_risk, warnings, historic
            )
            
            # Cache result
            await self.cache.set(cache_key, asdict(flood_risk))
            
            return flood_risk
            
        except Exception as e:
            print(f"Error fetching flood risk data for {postcode}: {str(e)}")
        
        # Return mock data if APIs fail
        return await self._mock_flood_risk_data(postcode_clean)
    
    async def get_flood_risk_by_coordinates(
        self, 
        latitude: float, 
        longitude: float
    ) -> Optional[FloodRiskData]:
        """
        Get flood risk data by coordinates
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            FloodRiskData object
        """
        
        coordinates = (latitude, longitude)
        
        # Check cache
        cache_key = f"coords_{latitude}_{longitude}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return FloodRiskData(**cached_data)
        
        try:
            # Get postcode from coordinates (reverse geocoding)
            postcode = await self._get_coordinates_postcode(coordinates)
            
            # Get flood data
            coordinate_risk = await self._get_coordinate_flood_risk(coordinates)
            warnings = await self._get_flood_warnings(coordinates)
            historic = await self._get_historic_flooding(coordinates)
            
            # Create flood risk data
            flood_risk = self._combine_flood_data(
                postcode or "Unknown", coordinates, {}, 
                coordinate_risk, warnings, historic
            )
            
            # Cache result
            await self.cache.set(cache_key, asdict(flood_risk))
            
            return flood_risk
            
        except Exception as e:
            print(f"Error fetching flood risk data for coordinates {latitude}, {longitude}: {str(e)}")
        
        # Return mock data
        return await self._mock_flood_risk_data("EX1 2MP", coordinates)
    
    async def _get_postcode_flood_risk(self, postcode: str) -> Dict[str, Any]:
        """Get flood risk data from postcode API"""
        
        try:
            await self._rate_limit()
            
            # Try Government's check-for-flooding service
            url = f"https://check-for-flooding.service.gov.uk/api/postcode/{postcode}"
            
            if self.session:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_postcode_flood_response(data)
            
        except Exception as e:
            print(f"Error fetching postcode flood risk: {e}")
        
        return {}
    
    async def _get_coordinate_flood_risk(self, coordinates: Tuple[float, float]) -> Dict[str, Any]:
        """Get flood risk data from coordinate-based APIs"""
        
        latitude, longitude = coordinates
        
        try:
            await self._rate_limit()
            
            # Environment Agency spatial data services
            # Note: This would require proper API integration in production
            
            flood_data = {
                'flood_zone_2': await self._check_flood_zone(coordinates, 2),
                'flood_zone_3': await self._check_flood_zone(coordinates, 3),
                'surface_water_risk': await self._get_surface_water_risk(coordinates),
                'river_risk': await self._get_river_flood_risk(coordinates)
            }
            
            return flood_data
            
        except Exception as e:
            print(f"Error fetching coordinate flood risk: {e}")
        
        return {}
    
    async def _get_flood_warnings(self, coordinates: Tuple[float, float]) -> Dict[str, Any]:
        """Get current flood warnings and alerts"""
        
        try:
            await self._rate_limit()
            
            # Environment Agency flood warnings API
            url = f"{self.base_urls['flood_warnings']}"
            
            if self.session:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Filter warnings by proximity to coordinates
                        relevant_warnings = self._filter_warnings_by_location(
                            data, coordinates
                        )
                        
                        return {
                            'warnings': relevant_warnings.get('warnings', []),
                            'alerts': relevant_warnings.get('alerts', [])
                        }
            
        except Exception as e:
            print(f"Error fetching flood warnings: {e}")
        
        return {'warnings': [], 'alerts': []}
    
    async def _get_historic_flooding(self, coordinates: Tuple[float, float]) -> Dict[str, Any]:
        """Get historic flooding data"""
        
        try:
            # This would integrate with Environment Agency historic flood maps
            # For now, return mock data
            
            return {
                'historic_flooding': False,
                'historic_events': []
            }
            
        except Exception as e:
            print(f"Error fetching historic flooding data: {e}")
        
        return {'historic_flooding': False, 'historic_events': []}
    
    async def _get_postcode_coordinates(self, postcode: str) -> Optional[Tuple[float, float]]:
        """Get coordinates for postcode using geocoding service"""
        
        try:
            # Use free postcode API
            url = f"https://api.postcodes.io/postcodes/{postcode}"
            
            if self.session:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['status'] == 200:
                            result = data['result']
                            return (result['latitude'], result['longitude'])
            
        except Exception as e:
            print(f"Error geocoding postcode {postcode}: {e}")
        
        return None
    
    async def _get_coordinates_postcode(self, coordinates: Tuple[float, float]) -> Optional[str]:
        """Reverse geocode coordinates to postcode"""
        
        latitude, longitude = coordinates
        
        try:
            # Use free reverse geocoding API
            url = f"https://api.postcodes.io/postcodes?lon={longitude}&lat={latitude}"
            
            if self.session:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['status'] == 200 and data['result']:
                            return data['result'][0]['postcode']
            
        except Exception as e:
            print(f"Error reverse geocoding coordinates: {e}")
        
        return None
    
    async def _check_flood_zone(self, coordinates: Tuple[float, float], zone: int) -> bool:
        """Check if coordinates are in specific flood zone"""
        
        # This would use Environment Agency WFS services in production
        # For now, return mock data based on coordinates
        
        latitude, longitude = coordinates
        
        # Mock logic - areas near rivers more likely to be in flood zones
        if zone == 2:
            return abs(latitude - 51.5) < 0.01 and abs(longitude + 0.1) < 0.01
        elif zone == 3:
            return abs(latitude - 51.5) < 0.005 and abs(longitude + 0.1) < 0.005
        
        return False
    
    async def _get_surface_water_risk(self, coordinates: Tuple[float, float]) -> Dict[str, Any]:
        """Get surface water flood risk assessment"""
        
        # Mock implementation
        return {
            'risk_level': 'Low',
            'depth_30yr': '0-0.3m',
            'depth_100yr': '0.3-0.6m',
            'depth_1000yr': '0.6-1.2m'
        }
    
    async def _get_river_flood_risk(self, coordinates: Tuple[float, float]) -> Dict[str, Any]:
        """Get river flood risk assessment"""
        
        # Mock implementation
        return {
            'risk_level': 'Very Low',
            'main_river_distance': '500m',
            'watercourse_type': 'Minor watercourse'
        }
    
    def _combine_flood_data(
        self, 
        postcode: str,
        coordinates: Tuple[float, float],
        postcode_data: Dict[str, Any],
        coordinate_data: Dict[str, Any],
        warnings_data: Dict[str, Any],
        historic_data: Dict[str, Any]
    ) -> FloodRiskData:
        """Combine flood data from multiple sources"""
        
        # Extract and combine risk levels
        river_sea_risk = (
            postcode_data.get('river_and_sea', 'Very Low') or
            coordinate_data.get('river_risk', {}).get('risk_level', 'Very Low')
        )
        
        surface_water_risk = (
            postcode_data.get('surface_water', 'Low') or
            coordinate_data.get('surface_water_risk', {}).get('risk_level', 'Low')
        )
        
        reservoir_risk = postcode_data.get('reservoirs', 'Very Low')
        
        # Determine overall risk
        risk_levels = {'Very Low': 1, 'Low': 2, 'Medium': 3, 'High': 4}
        max_risk_value = max(
            risk_levels.get(river_sea_risk, 1),
            risk_levels.get(surface_water_risk, 1),
            risk_levels.get(reservoir_risk, 1)
        )
        overall_risk = [k for k, v in risk_levels.items() if v == max_risk_value][0]
        
        # Generate risk summary
        risk_summary = self._generate_risk_summary(
            river_sea_risk, surface_water_risk, reservoir_risk
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            river_sea_risk, surface_water_risk, reservoir_risk,
            coordinate_data.get('flood_zone_2', False),
            coordinate_data.get('flood_zone_3', False)
        )
        
        return FloodRiskData(
            postcode=postcode,
            coordinates=coordinates,
            river_and_sea=river_sea_risk,
            surface_water=surface_water_risk,
            reservoirs=reservoir_risk,
            groundwater=postcode_data.get('groundwater', 'Very Low'),
            in_flood_zone_2=coordinate_data.get('flood_zone_2', False),
            in_flood_zone_3=coordinate_data.get('flood_zone_3', False),
            surface_water_depth_30yr=coordinate_data.get('surface_water_risk', {}).get('depth_30yr'),
            surface_water_depth_100yr=coordinate_data.get('surface_water_risk', {}).get('depth_100yr'),
            surface_water_depth_1000yr=coordinate_data.get('surface_water_risk', {}).get('depth_1000yr'),
            river_flood_warnings=warnings_data.get('warnings', []),
            river_flood_alerts=warnings_data.get('alerts', []),
            historic_flooding=historic_data.get('historic_flooding', False),
            historic_flood_events=historic_data.get('historic_events', []),
            overall_flood_risk=overall_risk,
            risk_summary=risk_summary,
            recommendations=recommendations
        )
    
    def _parse_postcode_flood_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse postcode flood risk API response"""
        
        # This would parse the actual API response structure
        # Mock implementation based on expected structure
        
        return {
            'river_and_sea': data.get('riverAndSeaRisk', 'Very Low'),
            'surface_water': data.get('surfaceWaterRisk', 'Low'),
            'reservoirs': data.get('reservoirRisk', 'Very Low'),
            'groundwater': data.get('groundwaterRisk', 'Very Low')
        }
    
    def _filter_warnings_by_location(
        self, 
        warnings_data: Dict[str, Any], 
        coordinates: Tuple[float, float]
    ) -> Dict[str, Any]:
        """Filter flood warnings by proximity to coordinates"""
        
        # This would implement proper geographic filtering
        # For now, return empty lists
        
        return {
            'warnings': [],
            'alerts': []
        }
    
    def _generate_risk_summary(
        self, 
        river_sea: str, 
        surface_water: str, 
        reservoir: str
    ) -> str:
        """Generate human-readable risk summary"""
        
        risk_descriptions = {
            'Very Low': 'very low',
            'Low': 'low', 
            'Medium': 'medium',
            'High': 'high'
        }
        
        summary_parts = []
        
        if river_sea != 'Very Low':
            summary_parts.append(f"River and sea flooding risk is {risk_descriptions[river_sea]}")
        
        if surface_water != 'Very Low':
            summary_parts.append(f"Surface water flooding risk is {risk_descriptions[surface_water]}")
        
        if reservoir != 'Very Low':
            summary_parts.append(f"Reservoir flooding risk is {risk_descriptions[reservoir]}")
        
        if not summary_parts:
            return "This area has very low flood risk from all sources."
        
        return ". ".join(summary_parts) + "."
    
    def _generate_recommendations(
        self, 
        river_sea: str, 
        surface_water: str, 
        reservoir: str,
        in_zone_2: bool,
        in_zone_3: bool
    ) -> List[str]:
        """Generate flood risk recommendations"""
        
        recommendations = []
        
        if in_zone_3:
            recommendations.extend([
                "Flood Risk Assessment required for planning applications",
                "Consider flood-resistant construction methods",
                "Ensure safe access/egress during flooding",
                "Consider flood warning systems"
            ])
        elif in_zone_2:
            recommendations.extend([
                "Flood Risk Assessment may be required",
                "Consider sustainable drainage systems (SuDS)",
                "Review flood emergency procedures"
            ])
        
        if surface_water in ['Medium', 'High']:
            recommendations.extend([
                "Implement sustainable drainage systems (SuDS)",
                "Consider permeable paving surfaces",
                "Ensure adequate surface water drainage"
            ])
        
        if river_sea in ['Medium', 'High']:
            recommendations.extend([
                "Register for flood warnings",
                "Prepare a flood plan",
                "Consider flood insurance"
            ])
        
        if not recommendations:
            recommendations = [
                "Monitor flood risk information regularly",
                "Consider climate change impacts on future flood risk"
            ]
        
        return recommendations
    
    def _normalize_postcode(self, postcode: str) -> str:
        """Normalize UK postcode format"""
        postcode_clean = re.sub(r'\s+', '', postcode.upper())
        
        if len(postcode_clean) >= 5:
            postcode_clean = f"{postcode_clean[:-3]} {postcode_clean[-3:]}"
        
        return postcode_clean
    
    # Mock implementations
    
    async def _mock_flood_risk_data(
        self, 
        postcode: str, 
        coordinates: Optional[Tuple[float, float]] = None
    ) -> FloodRiskData:
        """Generate mock flood risk data for testing"""
        
        if coordinates is None:
            coordinates = (51.5074, -0.1278)  # Default to London
        
        # Vary risk based on postcode for testing
        postcode_hash = hash(postcode) % 4
        
        risk_levels = ['Very Low', 'Low', 'Medium', 'High']
        
        river_sea = risk_levels[postcode_hash % 4]
        surface_water = risk_levels[(postcode_hash + 1) % 4]
        reservoir = risk_levels[0]  # Usually very low
        
        in_zone_2 = postcode_hash >= 2
        in_zone_3 = postcode_hash >= 3
        
        risk_summary = self._generate_risk_summary(river_sea, surface_water, reservoir)
        recommendations = self._generate_recommendations(
            river_sea, surface_water, reservoir, in_zone_2, in_zone_3
        )
        
        return FloodRiskData(
            postcode=postcode,
            coordinates=coordinates,
            river_and_sea=river_sea,
            surface_water=surface_water,
            reservoirs=reservoir,
            groundwater='Very Low',
            in_flood_zone_2=in_zone_2,
            in_flood_zone_3=in_zone_3,
            surface_water_depth_30yr='0-0.3m' if surface_water != 'Very Low' else None,
            surface_water_depth_100yr='0.3-0.6m' if surface_water in ['Medium', 'High'] else None,
            surface_water_depth_1000yr='0.6-1.2m' if surface_water == 'High' else None,
            river_flood_warnings=[],
            river_flood_alerts=[],
            historic_flooding=postcode_hash >= 3,
            historic_flood_events=[
                {
                    'date': '2007-07-20',
                    'type': 'Surface water flooding',
                    'severity': 'Minor'
                }
            ] if postcode_hash >= 3 else [],
            overall_flood_risk=max([river_sea, surface_water, reservoir], 
                                 key=lambda x: ['Very Low', 'Low', 'Medium', 'High'].index(x)),
            risk_summary=risk_summary,
            recommendations=recommendations
        )


# Convenience function for getting flood risk data
async def get_flood_risk_data(
    identifier: str,
    search_type: str = 'postcode'
) -> Optional[Dict[str, Any]]:
    """
    Get flood risk data by postcode or coordinates
    
    Args:
        identifier: Postcode or "lat,lng" coordinates
        search_type: 'postcode' or 'coordinates'
        
    Returns:
        Dictionary containing flood risk data
    """
    
    async with FloodRiskAdapter() as adapter:
        
        if search_type == 'postcode':
            flood_risk = await adapter.get_flood_risk_by_postcode(identifier)
        
        elif search_type == 'coordinates':
            try:
                lat_str, lng_str = identifier.split(',')
                latitude = float(lat_str.strip())
                longitude = float(lng_str.strip())
                flood_risk = await adapter.get_flood_risk_by_coordinates(latitude, longitude)
            except (ValueError, IndexError):
                return None
        
        else:
            return None
        
        if flood_risk:
            return asdict(flood_risk)
    
    return None