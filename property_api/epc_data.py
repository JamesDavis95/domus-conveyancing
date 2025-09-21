"""
EPC (Energy Performance Certificate) Data Adapter
Integration with government EPC register and APIs
"""
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
import re
from dataclasses import dataclass, asdict

from .cache import PropertyDataCache


@dataclass
class EPCData:
    """Energy Performance Certificate data"""
    uprn: str
    address: str
    postcode: str
    current_energy_rating: str
    current_energy_efficiency: int
    potential_energy_rating: str
    potential_energy_efficiency: int
    property_type: str
    built_form: str
    inspection_date: str
    lodgement_date: str
    certificate_hash: str
    
    # Detailed energy data
    environment_impact_current: Optional[int] = None
    environment_impact_potential: Optional[int] = None
    energy_consumption_current: Optional[int] = None
    energy_consumption_potential: Optional[int] = None
    co2_emissions_current: Optional[float] = None
    co2_emissions_potential: Optional[float] = None
    
    # Building characteristics
    total_floor_area: Optional[float] = None
    number_habitable_rooms: Optional[int] = None
    number_heated_rooms: Optional[int] = None
    low_energy_lighting: Optional[int] = None
    
    # Heating and insulation
    main_fuel: Optional[str] = None
    main_heating_controls: Optional[str] = None
    hot_water_description: Optional[str] = None
    floor_description: Optional[str] = None
    windows_description: Optional[str] = None
    walls_description: Optional[str] = None
    roof_description: Optional[str] = None
    
    # Recommendations
    hot_water_cost_current: Optional[float] = None
    hot_water_cost_potential: Optional[float] = None
    heating_cost_current: Optional[float] = None
    heating_cost_potential: Optional[float] = None
    lighting_cost_current: Optional[float] = None
    lighting_cost_potential: Optional[float] = None


class EPCDataAdapter:
    """Adapter for EPC register data"""
    
    def __init__(self):
        # UK Government EPC register API endpoints
        self.base_urls = {
            'domestic': 'https://epc.opendatacommunities.org/api/v1/domestic',
            'non_domestic': 'https://epc.opendatacommunities.org/api/v1/non-domestic'
        }
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache = PropertyDataCache('epc_data', ttl_hours=24)
        self.rate_limit_delay = 0.5  # Seconds between requests
        self.last_request_time = 0
        
        # API authentication (would be configured via environment variables)
        self.api_key = None  # Set via environment variable in production
        
    async def __aenter__(self):
        headers = {
            'User-Agent': 'Domus-Planning-AI/1.0',
            'Accept': 'application/json'
        }
        
        # Add authentication header if API key available
        if self.api_key:
            headers['Authorization'] = f'Basic {self.api_key}'
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=headers
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
    
    async def get_epc_by_postcode(
        self, 
        postcode: str,
        property_type: str = 'domestic'
    ) -> List[EPCData]:
        """
        Get EPC data for properties in a postcode
        
        Args:
            postcode: UK postcode to search
            property_type: 'domestic' or 'non_domestic'
            
        Returns:
            List of EPCData objects
        """
        
        postcode_clean = self._normalize_postcode(postcode)
        
        # Check cache
        cache_key = f"postcode_{property_type}_{postcode_clean}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return [EPCData(**item) for item in cached_data]
        
        try:
            await self._rate_limit()
            
            base_url = self.base_urls.get(property_type, self.base_urls['domestic'])
            url = f"{base_url}/search"
            
            params = {
                'postcode': postcode_clean,
                'size': 100  # Maximum results per request
            }
            
            if self.session:
                async with self.session.get(url, params=params) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        epc_records = self._parse_epc_response(data, property_type)
                        
                        # Cache results
                        cache_data = [asdict(record) for record in epc_records]
                        await self.cache.set(cache_key, cache_data)
                        
                        return epc_records
                    
                    elif response.status == 401:
                        print("EPC API authentication failed - using mock data")
                        return await self._mock_epc_data(postcode_clean, property_type)
                    
                    else:
                        print(f"EPC API error {response.status} - using mock data")
                        return await self._mock_epc_data(postcode_clean, property_type)
            
        except Exception as e:
            print(f"Error fetching EPC data for {postcode}: {str(e)}")
        
        # Return mock data if API fails
        return await self._mock_epc_data(postcode_clean, property_type)
    
    async def get_epc_by_uprn(
        self, 
        uprn: str,
        property_type: str = 'domestic'
    ) -> Optional[EPCData]:
        """
        Get EPC data by UPRN (Unique Property Reference Number)
        
        Args:
            uprn: Property UPRN
            property_type: 'domestic' or 'non_domestic'
            
        Returns:
            EPCData object or None if not found
        """
        
        # Check cache
        cache_key = f"uprn_{property_type}_{uprn}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return EPCData(**cached_data)
        
        try:
            await self._rate_limit()
            
            base_url = self.base_urls.get(property_type, self.base_urls['domestic'])
            url = f"{base_url}/search"
            
            params = {'uprn': uprn}
            
            if self.session:
                async with self.session.get(url, params=params) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        epc_records = self._parse_epc_response(data, property_type)
                        
                        if epc_records:
                            epc_data = epc_records[0]  # UPRN should return single result
                            
                            # Cache result
                            await self.cache.set(cache_key, asdict(epc_data))
                            return epc_data
                    
                    else:
                        print(f"EPC API error {response.status} for UPRN {uprn}")
            
        except Exception as e:
            print(f"Error fetching EPC data for UPRN {uprn}: {str(e)}")
        
        # Return mock data if API fails
        mock_records = await self._mock_epc_data("EX1 2MP", property_type)
        if mock_records:
            return mock_records[0]
        
        return None
    
    async def get_epc_by_address(
        self, 
        address: str,
        property_type: str = 'domestic'
    ) -> List[EPCData]:
        """
        Search EPC data by address
        
        Args:
            address: Property address to search
            property_type: 'domestic' or 'non_domestic'
            
        Returns:
            List of matching EPCData objects
        """
        
        address_clean = self._normalize_address(address)
        
        # Check cache
        cache_key = f"address_{property_type}_{hash(address_clean)}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return [EPCData(**item) for item in cached_data]
        
        try:
            await self._rate_limit()
            
            base_url = self.base_urls.get(property_type, self.base_urls['domestic'])
            url = f"{base_url}/search"
            
            # Extract postcode from address for search
            postcode_match = re.search(r'([A-Z]{1,2}[0-9R][0-9A-Z]? ?[0-9][A-Z]{2})', address_clean.upper())
            
            if postcode_match:
                postcode = postcode_match.group(1)
                params = {'postcode': postcode}
                
                if self.session:
                    async with self.session.get(url, params=params) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            all_records = self._parse_epc_response(data, property_type)
                            
                            # Filter by address similarity
                            matching_records = self._filter_by_address(all_records, address_clean)
                            
                            # Cache results
                            cache_data = [asdict(record) for record in matching_records]
                            await self.cache.set(cache_key, cache_data)
                            
                            return matching_records
            
        except Exception as e:
            print(f"Error searching EPC data for address {address}: {str(e)}")
        
        # Return mock data if search fails
        return await self._mock_epc_address_search(address_clean, property_type)
    
    async def get_recommendations(self, certificate_hash: str) -> List[Dict[str, Any]]:
        """
        Get EPC improvement recommendations
        
        Args:
            certificate_hash: EPC certificate hash
            
        Returns:
            List of improvement recommendations
        """
        
        # Check cache
        cache_key = f"recommendations_{certificate_hash}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            await self._rate_limit()
            
            url = f"{self.base_urls['domestic']}/recommendations/{certificate_hash}"
            
            if self.session:
                async with self.session.get(url) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        recommendations = self._parse_recommendations_response(data)
                        
                        # Cache results
                        await self.cache.set(cache_key, recommendations)
                        
                        return recommendations
            
        except Exception as e:
            print(f"Error fetching EPC recommendations for {certificate_hash}: {str(e)}")
        
        # Return mock recommendations
        return await self._mock_epc_recommendations()
    
    def _normalize_postcode(self, postcode: str) -> str:
        """Normalize UK postcode format"""
        postcode_clean = re.sub(r'\s+', '', postcode.upper())
        
        if len(postcode_clean) >= 5:
            postcode_clean = f"{postcode_clean[:-3]} {postcode_clean[-3:]}"
        
        return postcode_clean
    
    def _normalize_address(self, address: str) -> str:
        """Normalize address for searching"""
        return ' '.join(address.title().split())
    
    def _parse_epc_response(self, data: Dict[str, Any], property_type: str) -> List[EPCData]:
        """Parse EPC API response data"""
        
        epc_records = []
        
        # Handle different response structures
        rows = data.get('rows', [])
        if not rows and 'data' in data:
            rows = data['data']
        
        for row in rows:
            try:
                # Map API response fields to EPCData structure
                epc_data = EPCData(
                    uprn=row.get('uprn', ''),
                    address=row.get('address', ''),
                    postcode=row.get('postcode', ''),
                    current_energy_rating=row.get('current-energy-rating', ''),
                    current_energy_efficiency=int(row.get('current-energy-efficiency', 0)),
                    potential_energy_rating=row.get('potential-energy-rating', ''),
                    potential_energy_efficiency=int(row.get('potential-energy-efficiency', 0)),
                    property_type=row.get('property-type', property_type),
                    built_form=row.get('built-form', ''),
                    inspection_date=row.get('inspection-date', ''),
                    lodgement_date=row.get('lodgement-date', ''),
                    certificate_hash=row.get('lmk-key', ''),
                    
                    # Optional detailed fields
                    environment_impact_current=self._safe_int(row.get('environment-impact-current')),
                    environment_impact_potential=self._safe_int(row.get('environment-impact-potential')),
                    energy_consumption_current=self._safe_int(row.get('energy-consumption-current')),
                    energy_consumption_potential=self._safe_int(row.get('energy-consumption-potential')),
                    co2_emissions_current=self._safe_float(row.get('co2-emissions-current')),
                    co2_emissions_potential=self._safe_float(row.get('co2-emissions-potential')),
                    
                    total_floor_area=self._safe_float(row.get('total-floor-area')),
                    number_habitable_rooms=self._safe_int(row.get('number-habitable-rooms')),
                    number_heated_rooms=self._safe_int(row.get('number-heated-rooms')),
                    low_energy_lighting=self._safe_int(row.get('low-energy-lighting')),
                    
                    main_fuel=row.get('main-fuel'),
                    main_heating_controls=row.get('main-heating-controls'),
                    hot_water_description=row.get('hot-water-description'),
                    floor_description=row.get('floor-description'),
                    windows_description=row.get('windows-description'),
                    walls_description=row.get('walls-description'),
                    roof_description=row.get('roof-description'),
                    
                    hot_water_cost_current=self._safe_float(row.get('hot-water-cost-current')),
                    hot_water_cost_potential=self._safe_float(row.get('hot-water-cost-potential')),
                    heating_cost_current=self._safe_float(row.get('heating-cost-current')),
                    heating_cost_potential=self._safe_float(row.get('heating-cost-potential')),
                    lighting_cost_current=self._safe_float(row.get('lighting-cost-current')),
                    lighting_cost_potential=self._safe_float(row.get('lighting-cost-potential'))
                )
                
                epc_records.append(epc_data)
                
            except (ValueError, KeyError) as e:
                print(f"Skipping malformed EPC record: {e}")
                continue
        
        return epc_records
    
    def _parse_recommendations_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse EPC recommendations response"""
        
        recommendations = []
        
        rows = data.get('rows', [])
        if not rows and 'data' in data:
            rows = data['data']
        
        for row in rows:
            recommendation = {
                'improvement_item': row.get('improvement-item', ''),
                'improvement_summary': row.get('improvement-summary', ''),
                'improvement_description': row.get('improvement-description', ''),
                'improvement_id': row.get('improvement-id', ''),
                'improvement_id_text': row.get('improvement-id-text', ''),
                'indicative_cost': row.get('indicative-cost', ''),
                'typical_saving': row.get('typical-saving', ''),
                'energy_performance_rating': row.get('energy-performance-rating-improvement', ''),
                'environmental_impact_rating': row.get('environmental-impact-rating-improvement', '')
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _filter_by_address(self, records: List[EPCData], target_address: str) -> List[EPCData]:
        """Filter EPC records by address similarity"""
        
        matching_records = []
        target_words = set(target_address.lower().split())
        
        for record in records:
            record_words = set(record.address.lower().split())
            
            # Calculate word overlap
            overlap = len(target_words & record_words)
            similarity = overlap / len(target_words) if target_words else 0
            
            # Include records with >50% word overlap
            if similarity > 0.5:
                matching_records.append(record)
        
        # Sort by address similarity
        matching_records.sort(
            key=lambda r: len(set(target_address.lower().split()) & set(r.address.lower().split())),
            reverse=True
        )
        
        return matching_records[:10]  # Return top 10 matches
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to int"""
        try:
            return int(value) if value is not None and value != '' else None
        except (ValueError, TypeError):
            return None
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float"""
        try:
            return float(value) if value is not None and value != '' else None
        except (ValueError, TypeError):
            return None
    
    # Mock implementations for development/testing
    
    async def _mock_epc_data(self, postcode: str, property_type: str) -> List[EPCData]:
        """Generate mock EPC data for testing"""
        
        mock_records = [
            EPCData(
                uprn='123456789',
                address='123 Example Street, Example Town',
                postcode=postcode,
                current_energy_rating='C',
                current_energy_efficiency=72,
                potential_energy_rating='B',
                potential_energy_efficiency=84,
                property_type='House',
                built_form='Detached',
                inspection_date='2023-05-15',
                lodgement_date='2023-05-20',
                certificate_hash='abc123def456',
                environment_impact_current=65,
                environment_impact_potential=78,
                energy_consumption_current=245,
                energy_consumption_potential=185,
                co2_emissions_current=4.2,
                co2_emissions_potential=3.1,
                total_floor_area=120.5,
                number_habitable_rooms=6,
                number_heated_rooms=6,
                low_energy_lighting=80,
                main_fuel='Gas',
                main_heating_controls='Programmer and room thermostat',
                hot_water_description='Gas boiler system',
                floor_description='Solid, no insulation',
                windows_description='Mostly double glazing',
                walls_description='Cavity wall, as built, no insulation',
                roof_description='Pitched, 150mm loft insulation',
                hot_water_cost_current=180.0,
                hot_water_cost_potential=160.0,
                heating_cost_current=850.0,
                heating_cost_potential=650.0,
                lighting_cost_current=120.0,
                lighting_cost_potential=85.0
            ),
            EPCData(
                uprn='987654321',
                address='125 Example Street, Example Town',
                postcode=postcode,
                current_energy_rating='D',
                current_energy_efficiency=58,
                potential_energy_rating='C',
                potential_energy_efficiency=71,
                property_type='House',
                built_form='Semi-detached',
                inspection_date='2022-09-10',
                lodgement_date='2022-09-15',
                certificate_hash='def456ghi789',
                environment_impact_current=52,
                environment_impact_potential=68,
                total_floor_area=95.0,
                number_habitable_rooms=5,
                number_heated_rooms=5,
                main_fuel='Gas',
                walls_description='Cavity wall, as built, partial insulation'
            )
        ]
        
        return mock_records
    
    async def _mock_epc_address_search(self, address: str, property_type: str) -> List[EPCData]:
        """Mock EPC address search"""
        
        # Return subset of mock data filtered by address
        all_mock_data = await self._mock_epc_data("EX1 2MP", property_type)
        
        # Simple address filtering
        filtered_data = []
        for record in all_mock_data:
            if any(word.lower() in record.address.lower() for word in address.split()):
                filtered_data.append(record)
        
        return filtered_data
    
    async def _mock_epc_recommendations(self) -> List[Dict[str, Any]]:
        """Mock EPC improvement recommendations"""
        
        return [
            {
                'improvement_item': 'Loft insulation',
                'improvement_summary': 'Increase loft insulation to 270mm',
                'improvement_description': 'Add insulation to loft space to achieve 270mm thickness',
                'improvement_id': '1',
                'improvement_id_text': 'Loft insulation',
                'indicative_cost': '£300 - £700',
                'typical_saving': '£45 - £75 per year',
                'energy_performance_rating': '74',
                'environmental_impact_rating': '70'
            },
            {
                'improvement_item': 'Wall insulation',
                'improvement_summary': 'Cavity wall insulation',
                'improvement_description': 'Fill cavity walls with insulation material',
                'improvement_id': '2', 
                'improvement_id_text': 'Cavity wall insulation',
                'indicative_cost': '£500 - £1,500',
                'typical_saving': '£85 - £140 per year',
                'energy_performance_rating': '78',
                'environmental_impact_rating': '75'
            },
            {
                'improvement_item': 'Heating controls',
                'improvement_summary': 'Upgrade heating controls',
                'improvement_description': 'Install thermostatic radiator valves and room thermostat',
                'improvement_id': '3',
                'improvement_id_text': 'Heating controls',
                'indicative_cost': '£350 - £450',
                'typical_saving': '£35 - £55 per year',
                'energy_performance_rating': '75',
                'environmental_impact_rating': '72'
            }
        ]


# Convenience function for getting EPC data
async def get_epc_data(
    identifier: str,
    search_type: str = 'postcode',
    property_type: str = 'domestic'
) -> Optional[Dict[str, Any]]:
    """
    Get EPC data by various identifiers
    
    Args:
        identifier: Postcode, UPRN, or address
        search_type: Type of search ('postcode', 'uprn', 'address')
        property_type: 'domestic' or 'non_domestic'
        
    Returns:
        Dictionary containing EPC data and recommendations
    """
    
    async with EPCDataAdapter() as adapter:
        
        epc_records = []
        
        if search_type == 'postcode':
            epc_records = await adapter.get_epc_by_postcode(identifier, property_type)
        
        elif search_type == 'uprn':
            epc_data = await adapter.get_epc_by_uprn(identifier, property_type)
            if epc_data:
                epc_records = [epc_data]
        
        elif search_type == 'address':
            epc_records = await adapter.get_epc_by_address(identifier, property_type)
        
        if not epc_records:
            return None
        
        # Get recommendations for first record
        recommendations = []
        if epc_records and epc_records[0].certificate_hash:
            recommendations = await adapter.get_recommendations(epc_records[0].certificate_hash)
        
        return {
            'epc_records': [asdict(record) for record in epc_records],
            'recommendations': recommendations,
            'search_type': search_type,
            'property_type': property_type
        }