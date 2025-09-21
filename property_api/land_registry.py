"""
Land Registry Data Adapter
Integration with HM Land Registry APIs and datasets
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
class LandRegistryTitle:
    """Land Registry title information"""
    title_number: str
    tenure: str
    property_description: str
    proprietor_name: str
    proprietor_address: str
    registered_date: str
    last_sale_date: Optional[str] = None
    last_sale_price: Optional[int] = None
    charges: Optional[List[Dict[str, Any]]] = None


@dataclass 
class PricePaidData:
    """Price paid data from Land Registry"""
    price: int
    date: str
    postcode: str
    property_type: str
    old_new: str
    duration: str
    paon: str
    saon: str
    street: str
    locality: str
    town_city: str
    district: str
    county: str


class LandRegistryAdapter:
    """Adapter for HM Land Registry data sources"""
    
    def __init__(self):
        self.base_urls = {
            'inspire': 'https://landregistry.data.gov.uk/',
            'price_paid': 'http://landregistry.data.gov.uk/data/ppi/',
            'overseas_companies': 'https://landregistry.data.gov.uk/data/oc/',
            'uk_companies': 'https://landregistry.data.gov.uk/data/cc/'
        }
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache = PropertyDataCache('land_registry', ttl_hours=24)
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
    
    async def get_title_data(self, title_number: str) -> Optional[LandRegistryTitle]:
        """
        Get title information by title number
        
        Args:
            title_number: HM Land Registry title number
            
        Returns:
            LandRegistryTitle object or None if not found
        """
        
        # Check cache first
        cache_key = f"title_{title_number}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return LandRegistryTitle(**cached_data)
        
        try:
            await self._rate_limit()
            
            # Note: This is a placeholder - actual Land Registry API access requires
            # authentication and may have different endpoints
            url = f"{self.base_urls['inspire']}app/qonsole/explore?query=title:{title_number}"
            
            # In production, would use proper authenticated API calls
            title_data = await self._mock_title_lookup(title_number)
            
            if title_data:
                # Cache the result
                await self.cache.set(cache_key, asdict(title_data))
                return title_data
            
        except Exception as e:
            print(f"Error fetching title data for {title_number}: {str(e)}")
            return None
        
        return None
    
    async def get_price_paid_data(
        self, 
        postcode: str, 
        limit: int = 100,
        start_date: Optional[str] = None
    ) -> List[PricePaidData]:
        """
        Get price paid data for a postcode area
        
        Args:
            postcode: UK postcode 
            limit: Maximum number of records to return
            start_date: Start date for price data (YYYY-MM-DD)
            
        Returns:
            List of PricePaidData objects
        """
        
        # Normalize postcode
        postcode_clean = self._normalize_postcode(postcode)
        
        # Check cache
        cache_key = f"price_paid_{postcode_clean}_{limit}_{start_date}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return [PricePaidData(**item) for item in cached_data]
        
        try:
            await self._rate_limit()
            
            # Build SPARQL query for price paid data
            # Note: This uses the Land Registry's SPARQL endpoint
            query = self._build_price_paid_query(postcode_clean, limit, start_date)
            
            url = f"{self.base_urls['price_paid']}query"
            
            if self.session:
                async with self.session.post(
                    url,
                    data={'query': query},
                    headers={'Accept': 'application/json'}
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        price_records = self._parse_price_paid_response(data)
                        
                        # Cache results
                        cache_data = [asdict(record) for record in price_records]
                        await self.cache.set(cache_key, cache_data)
                        
                        return price_records
            
        except Exception as e:
            print(f"Error fetching price paid data for {postcode}: {str(e)}")
        
        # Return mock data if API fails
        return await self._mock_price_paid_data(postcode_clean, limit)
    
    async def search_by_address(self, address: str) -> List[Dict[str, Any]]:
        """
        Search for properties by address
        
        Args:
            address: Property address to search for
            
        Returns:
            List of matching property records
        """
        
        # Normalize address for search
        address_clean = self._normalize_address(address)
        
        # Check cache
        cache_key = f"address_search_{hash(address_clean)}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            await self._rate_limit()
            
            # Build address search query
            query = self._build_address_search_query(address_clean)
            
            # In production, would use proper Land Registry API
            search_results = await self._mock_address_search(address_clean)
            
            # Cache results
            await self.cache.set(cache_key, search_results)
            
            return search_results
            
        except Exception as e:
            print(f"Error searching address {address}: {str(e)}")
            return []
    
    async def get_overseas_companies_data(self, title_number: str) -> Optional[Dict[str, Any]]:
        """
        Get overseas companies ownership data
        
        Args:
            title_number: Title number to check
            
        Returns:
            Overseas company information if applicable
        """
        
        cache_key = f"overseas_company_{title_number}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            await self._rate_limit()
            
            # Query overseas companies register
            query = self._build_overseas_companies_query(title_number)
            
            # Mock implementation
            overseas_data = await self._mock_overseas_companies_lookup(title_number)
            
            if overseas_data:
                await self.cache.set(cache_key, overseas_data)
                return overseas_data
            
        except Exception as e:
            print(f"Error fetching overseas companies data for {title_number}: {str(e)}")
        
        return None
    
    def _normalize_postcode(self, postcode: str) -> str:
        """Normalize UK postcode format"""
        
        # Remove spaces and convert to uppercase
        postcode_clean = re.sub(r'\s+', '', postcode.upper())
        
        # Add space before final 3 characters if not present
        if len(postcode_clean) >= 5:
            postcode_clean = f"{postcode_clean[:-3]} {postcode_clean[-3:]}"
        
        return postcode_clean
    
    def _normalize_address(self, address: str) -> str:
        """Normalize address for searching"""
        
        # Convert to title case and remove extra spaces
        address_clean = ' '.join(address.title().split())
        
        # Remove common abbreviations variations
        replacements = {
            'Street': 'St', 'Road': 'Rd', 'Avenue': 'Ave',
            'Lane': 'Ln', 'Close': 'Cl', 'Drive': 'Dr'
        }
        
        for full, abbrev in replacements.items():
            address_clean = address_clean.replace(f' {full}', f' {abbrev}')
        
        return address_clean
    
    def _build_price_paid_query(
        self, 
        postcode: str, 
        limit: int, 
        start_date: Optional[str]
    ) -> str:
        """Build SPARQL query for price paid data"""
        
        date_filter = ""
        if start_date:
            date_filter = f'FILTER (?date >= "{start_date}"^^xsd:date)'
        
        query = f"""
        PREFIX lrppi: <http://landregistry.data.gov.uk/def/ppi/>
        PREFIX lrcommon: <http://landregistry.data.gov.uk/def/common/>
        
        SELECT ?price ?date ?postcode ?propertyType ?newBuild ?duration
               ?paon ?saon ?street ?locality ?town ?district ?county
        WHERE {{
            ?transaction lrppi:pricePaid ?price ;
                         lrppi:transactionDate ?date ;
                         lrppi:propertyAddress ?address .
                         
            ?address lrcommon:postcode "{postcode}" ;
                     lrcommon:paon ?paon ;
                     lrcommon:street ?street ;
                     lrcommon:locality ?locality ;
                     lrcommon:town ?town ;
                     lrcommon:district ?district ;
                     lrcommon:county ?county .
                     
            OPTIONAL {{ ?address lrcommon:saon ?saon }}
            OPTIONAL {{ ?transaction lrppi:propertyType ?propertyType }}
            OPTIONAL {{ ?transaction lrppi:newBuild ?newBuild }}
            OPTIONAL {{ ?transaction lrppi:estateType ?duration }}
            
            {date_filter}
        }}
        ORDER BY DESC(?date)
        LIMIT {limit}
        """
        
        return query
    
    def _build_address_search_query(self, address: str) -> str:
        """Build SPARQL query for address search"""
        
        # Extract components from address
        address_parts = address.split(',')
        
        query = f"""
        PREFIX lrcommon: <http://landregistry.data.gov.uk/def/common/>
        
        SELECT ?address ?paon ?saon ?street ?postcode
        WHERE {{
            ?address lrcommon:street ?street ;
                     lrcommon:paon ?paon ;
                     lrcommon:postcode ?postcode .
                     
            OPTIONAL {{ ?address lrcommon:saon ?saon }}
            
            FILTER (regex(?street, "{address_parts[0] if address_parts else address}", "i"))
        }}
        LIMIT 50
        """
        
        return query
    
    def _build_overseas_companies_query(self, title_number: str) -> str:
        """Build query for overseas companies register"""
        
        query = f"""
        PREFIX lroc: <http://landregistry.data.gov.uk/def/oc/>
        
        SELECT ?companyName ?companyAddress ?countryOfIncorporation ?registrationDate
        WHERE {{
            ?registration lroc:titleNumber "{title_number}" ;
                         lroc:companyRegistrationNumber ?companyNumber ;
                         lroc:companyName ?companyName ;
                         lroc:companyAddress ?companyAddress ;
                         lroc:countryOfIncorporation ?countryOfIncorporation ;
                         lroc:registrationDate ?registrationDate .
        }}
        """
        
        return query
    
    def _parse_price_paid_response(self, response_data: Dict[str, Any]) -> List[PricePaidData]:
        """Parse price paid API response"""
        
        price_records = []
        
        if 'results' in response_data and 'bindings' in response_data['results']:
            for binding in response_data['results']['bindings']:
                
                # Extract values with safe access
                def get_value(key: str) -> str:
                    return binding.get(key, {}).get('value', '')
                
                try:
                    price_record = PricePaidData(
                        price=int(get_value('price')),
                        date=get_value('date'),
                        postcode=get_value('postcode'),
                        property_type=get_value('propertyType'),
                        old_new=get_value('newBuild'),
                        duration=get_value('duration'),
                        paon=get_value('paon'),
                        saon=get_value('saon'),
                        street=get_value('street'),
                        locality=get_value('locality'),
                        town_city=get_value('town'),
                        district=get_value('district'),
                        county=get_value('county')
                    )
                    
                    price_records.append(price_record)
                    
                except (ValueError, KeyError) as e:
                    # Skip malformed records
                    print(f"Skipping malformed price record: {e}")
                    continue
        
        return price_records
    
    # Mock implementations for development/testing
    
    async def _mock_title_lookup(self, title_number: str) -> Optional[LandRegistryTitle]:
        """Mock title lookup for testing"""
        
        # Simulate realistic title data
        mock_titles = {
            'EX123456': LandRegistryTitle(
                title_number='EX123456',
                tenure='Freehold',
                property_description='123 Example Street, Example Town EX1 2MP',
                proprietor_name='John Smith',
                proprietor_address='Same as property address',
                registered_date='2020-03-15',
                last_sale_date='2020-03-10',
                last_sale_price=350000,
                charges=[]
            ),
            'AB987654': LandRegistryTitle(
                title_number='AB987654',
                tenure='Leasehold',
                property_description='Flat 5, Manor Court, High Street AB1 2CD',
                proprietor_name='Sarah Johnson',
                proprietor_address='Same as property address', 
                registered_date='2019-07-22',
                last_sale_date='2019-07-18',
                last_sale_price=225000,
                charges=[
                    {
                        'type': 'Charge',
                        'chargee': 'Example Building Society',
                        'date': '2019-07-22'
                    }
                ]
            )
        }
        
        return mock_titles.get(title_number)
    
    async def _mock_price_paid_data(self, postcode: str, limit: int) -> List[PricePaidData]:
        """Mock price paid data for testing"""
        
        # Generate realistic mock data
        mock_records = []
        
        for i in range(min(limit, 10)):  # Generate up to 10 mock records
            
            price_record = PricePaidData(
                price=300000 + (i * 25000),
                date=f"2023-{6+i:02d}-15",
                postcode=postcode,
                property_type='terraced',
                old_new='established',
                duration='freehold',
                paon=str(10 + i),
                saon='',
                street='Example Street',
                locality='',
                town_city='Example Town',
                district='Example District',
                county='Example County'
            )
            
            mock_records.append(price_record)
        
        return mock_records
    
    async def _mock_address_search(self, address: str) -> List[Dict[str, Any]]:
        """Mock address search for testing"""
        
        # Generate mock search results
        mock_results = [
            {
                'title_number': 'EX123456',
                'address': '123 Example Street, Example Town EX1 2MP',
                'postcode': 'EX1 2MP',
                'tenure': 'Freehold',
                'last_sale_price': 350000,
                'last_sale_date': '2020-03-10'
            },
            {
                'title_number': 'EX123457',
                'address': '125 Example Street, Example Town EX1 2MP',
                'postcode': 'EX1 2MP',
                'tenure': 'Freehold',
                'last_sale_price': 375000,
                'last_sale_date': '2021-05-20'
            }
        ]
        
        # Filter results based on address similarity
        filtered_results = []
        for result in mock_results:
            if any(part.lower() in result['address'].lower() for part in address.split()):
                filtered_results.append(result)
        
        return filtered_results[:5]  # Return top 5 matches
    
    async def _mock_overseas_companies_lookup(self, title_number: str) -> Optional[Dict[str, Any]]:
        """Mock overseas companies lookup"""
        
        # Most properties won't have overseas company ownership
        if title_number.startswith('OC'):
            return {
                'company_name': 'Example Overseas Limited',
                'company_address': '123 International Plaza, Example City, Example Country',
                'country_of_incorporation': 'Example Country',
                'registration_date': '2020-01-15',
                'company_registration_number': 'OC123456'
            }
        
        return None


# Convenience function for getting land registry data
async def get_land_registry_data(
    identifier: str,
    search_type: str = 'title_number'
) -> Optional[Dict[str, Any]]:
    """
    Get Land Registry data by various identifiers
    
    Args:
        identifier: Title number, postcode, or address
        search_type: Type of search ('title_number', 'postcode', 'address')
        
    Returns:
        Dictionary containing Land Registry data
    """
    
    async with LandRegistryAdapter() as adapter:
        
        if search_type == 'title_number':
            title_data = await adapter.get_title_data(identifier)
            if title_data:
                return {
                    'title_data': asdict(title_data),
                    'overseas_companies': await adapter.get_overseas_companies_data(identifier)
                }
        
        elif search_type == 'postcode':
            price_data = await adapter.get_price_paid_data(identifier, limit=20)
            return {
                'price_paid_data': [asdict(record) for record in price_data]
            }
        
        elif search_type == 'address':
            search_results = await adapter.search_by_address(identifier)
            return {
                'address_search': search_results
            }
    
    return None