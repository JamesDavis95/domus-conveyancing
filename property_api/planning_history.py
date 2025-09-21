"""
Planning History Data Adapter  
Integration with local planning authority APIs and datasets
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
class PlanningApplication:
    """Planning application record"""
    reference: str
    address: str
    description: str
    status: str
    decision: Optional[str]
    application_date: str
    decision_date: Optional[str]
    authority: str
    
    # Application details
    applicant_name: Optional[str] = None
    agent_name: Optional[str] = None
    application_type: Optional[str] = None
    development_type: Optional[str] = None
    
    # Coordinates and mapping
    coordinates: Optional[Tuple[float, float]] = None
    uprn: Optional[str] = None
    
    # Decision details
    decision_level: Optional[str] = None  # Committee, Delegated, etc.
    conditions: Optional[List[str]] = None
    reasons_for_refusal: Optional[List[str]] = None
    
    # Appeal information
    appeal_reference: Optional[str] = None
    appeal_decision: Optional[str] = None
    appeal_date: Optional[str] = None
    
    # Consultation
    consultation_start: Optional[str] = None
    consultation_end: Optional[str] = None
    neighbour_comments: Optional[int] = None
    
    # Documents
    documents: Optional[List[Dict[str, str]]] = None
    
    # Additional metadata
    parish: Optional[str] = None
    ward: Optional[str] = None
    case_officer: Optional[str] = None


class PlanningHistoryAdapter:
    """Adapter for planning authority data sources"""
    
    def __init__(self):
        # Planning portal and authority API endpoints
        self.base_urls = {
            'planning_portal': 'https://www.planningportal.co.uk/api/',
            'idox_api': 'https://pa.{authority}.gov.uk/online-applications/api/',
            'acolnet_api': 'https://planning.{authority}.gov.uk/acolnet/api/',
            'generic_api': 'https://{authority}.gov.uk/planning/api/'
        }
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache = PropertyDataCache('planning_history', ttl_hours=6)  # Shorter TTL for planning data
        self.rate_limit_delay = 2.0  # Conservative rate limiting
        self.last_request_time = 0
        
        # Authority system mappings (simplified - would be comprehensive in production)
        self.authority_systems = {
            'Camden': 'idox',
            'Westminster': 'idox', 
            'Hackney': 'acolnet',
            'Islington': 'idox',
            'Tower Hamlets': 'idox'
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=45),
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
    
    async def get_planning_history_by_address(
        self, 
        address: str, 
        radius_m: int = 100,
        years_back: int = 10
    ) -> List[PlanningApplication]:
        """
        Get planning history for an address and surrounding area
        
        Args:
            address: Property address
            radius_m: Search radius in meters 
            years_back: Number of years to search back
            
        Returns:
            List of PlanningApplication objects
        """
        
        # Normalize address
        address_clean = self._normalize_address(address)
        
        # Check cache
        cache_key = f"address_{hash(address_clean)}_{radius_m}_{years_back}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return [PlanningApplication(**item) for item in cached_data]
        
        try:
            # Determine planning authority from address
            authority = await self._determine_authority(address_clean)
            
            if authority:
                # Get applications from authority API
                applications = await self._search_authority_applications(
                    authority, address_clean, radius_m, years_back
                )
            else:
                # Fallback to mock data
                applications = await self._mock_planning_history(address_clean, radius_m, years_back)
            
            # Cache results
            cache_data = [asdict(app) for app in applications]
            await self.cache.set(cache_key, cache_data)
            
            return applications
            
        except Exception as e:
            print(f"Error fetching planning history for {address}: {str(e)}")
        
        # Return mock data on error
        return await self._mock_planning_history(address_clean, radius_m, years_back)
    
    async def get_planning_history_by_postcode(
        self, 
        postcode: str,
        years_back: int = 5
    ) -> List[PlanningApplication]:
        """
        Get planning applications for a postcode area
        
        Args:
            postcode: UK postcode
            years_back: Number of years to search back
            
        Returns:
            List of PlanningApplication objects
        """
        
        postcode_clean = self._normalize_postcode(postcode)
        
        # Check cache
        cache_key = f"postcode_{postcode_clean}_{years_back}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return [PlanningApplication(**item) for item in cached_data]
        
        try:
            # Determine authority from postcode
            authority = await self._determine_authority_by_postcode(postcode_clean)
            
            if authority:
                applications = await self._search_postcode_applications(
                    authority, postcode_clean, years_back
                )
            else:
                applications = await self._mock_postcode_planning_history(postcode_clean, years_back)
            
            # Cache results
            cache_data = [asdict(app) for app in applications]
            await self.cache.set(cache_key, cache_data)
            
            return applications
            
        except Exception as e:
            print(f"Error fetching planning history for postcode {postcode}: {str(e)}")
        
        return await self._mock_postcode_planning_history(postcode_clean, years_back)
    
    async def get_application_details(
        self, 
        reference: str, 
        authority: Optional[str] = None
    ) -> Optional[PlanningApplication]:
        """
        Get detailed information for a specific planning application
        
        Args:
            reference: Planning application reference
            authority: Planning authority name (if known)
            
        Returns:
            Detailed PlanningApplication object
        """
        
        # Check cache
        cache_key = f"application_{reference}_{authority or 'unknown'}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return PlanningApplication(**cached_data)
        
        try:
            if not authority:
                authority = await self._determine_authority_by_reference(reference)
            
            if authority:
                application = await self._get_application_from_authority(authority, reference)
                
                if application:
                    # Cache result
                    await self.cache.set(cache_key, asdict(application))
                    return application
            
        except Exception as e:
            print(f"Error fetching application details for {reference}: {str(e)}")
        
        # Return mock application
        return await self._mock_application_details(reference, authority)
    
    async def get_recent_decisions(
        self, 
        coordinates: Tuple[float, float],
        radius_m: int = 500,
        months_back: int = 12
    ) -> List[PlanningApplication]:
        """
        Get recent planning decisions near coordinates
        
        Args:
            coordinates: Latitude, longitude tuple
            radius_m: Search radius in meters
            months_back: Number of months to search back
            
        Returns:
            List of recent decisions
        """
        
        latitude, longitude = coordinates
        
        # Check cache
        cache_key = f"recent_{latitude}_{longitude}_{radius_m}_{months_back}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return [PlanningApplication(**item) for item in cached_data]
        
        try:
            # Determine authority from coordinates
            authority = await self._determine_authority_by_coordinates(coordinates)
            
            if authority:
                applications = await self._search_recent_decisions(
                    authority, coordinates, radius_m, months_back
                )
            else:
                applications = await self._mock_recent_decisions(coordinates, radius_m, months_back)
            
            # Cache results
            cache_data = [asdict(app) for app in applications]
            await self.cache.set(cache_key, cache_data)
            
            return applications
            
        except Exception as e:
            print(f"Error fetching recent decisions near {coordinates}: {str(e)}")
        
        return await self._mock_recent_decisions(coordinates, radius_m, months_back)
    
    async def _determine_authority(self, address: str) -> Optional[str]:
        """Determine planning authority from address"""
        
        # Simple authority mapping based on location keywords
        # In production, would use comprehensive postcode/boundary lookup
        
        address_lower = address.lower()
        
        london_boroughs = {
            'camden': 'Camden',
            'westminster': 'Westminster',
            'hackney': 'Hackney',
            'islington': 'Islington',
            'tower hamlets': 'Tower Hamlets'
        }
        
        for keyword, authority in london_boroughs.items():
            if keyword in address_lower:
                return authority
        
        # Default fallback
        return None
    
    async def _determine_authority_by_postcode(self, postcode: str) -> Optional[str]:
        """Determine planning authority from postcode"""
        
        # Simplified mapping - production would use comprehensive postcode database
        postcode_prefixes = {
            'WC1': 'Camden',
            'WC2': 'Westminster', 
            'E8': 'Hackney',
            'N1': 'Islington',
            'E14': 'Tower Hamlets'
        }
        
        for prefix, authority in postcode_prefixes.items():
            if postcode.startswith(prefix):
                return authority
        
        return None
    
    async def _determine_authority_by_coordinates(self, coordinates: Tuple[float, float]) -> Optional[str]:
        """Determine authority from coordinates"""
        
        # Simplified - would use proper boundary checking in production
        latitude, longitude = coordinates
        
        # London area authorities
        if 51.4 < latitude < 51.6 and -0.3 < longitude < 0.1:
            return 'Westminster'  # Default London authority
        
        return None
    
    async def _determine_authority_by_reference(self, reference: str) -> Optional[str]:
        """Determine authority from planning reference format"""
        
        # Different authorities use different reference formats
        reference_patterns = {
            r'^\d{4}/\d{4}/[A-Z]+$': 'Camden',  # e.g., 2023/1234/FUL
            r'^[A-Z]{2}\d{2}/\d{5}$': 'Westminster',  # e.g., WM23/12345
            r'^\d{2}/\d{5}/[A-Z]+$': 'Hackney'  # e.g., 23/12345/FUL
        }
        
        for pattern, authority in reference_patterns.items():
            if re.match(pattern, reference):
                return authority
        
        return None
    
    async def _search_authority_applications(
        self, 
        authority: str, 
        address: str,
        radius_m: int, 
        years_back: int
    ) -> List[PlanningApplication]:
        """Search applications from authority API"""
        
        system = self.authority_systems.get(authority, 'generic')
        
        try:
            await self._rate_limit()
            
            if system == 'idox':
                return await self._search_idox_applications(authority, address, radius_m, years_back)
            elif system == 'acolnet':
                return await self._search_acolnet_applications(authority, address, radius_m, years_back)
            else:
                return await self._search_generic_applications(authority, address, radius_m, years_back)
            
        except Exception as e:
            print(f"Error searching {authority} applications: {e}")
            return await self._mock_planning_history(address, radius_m, years_back)
    
    async def _search_idox_applications(
        self, 
        authority: str, 
        address: str, 
        radius_m: int, 
        years_back: int
    ) -> List[PlanningApplication]:
        """Search Idox Public Access system"""
        
        # This would implement actual Idox API integration
        # For now, return mock data
        return await self._mock_planning_history(address, radius_m, years_back)
    
    async def _search_acolnet_applications(
        self, 
        authority: str, 
        address: str, 
        radius_m: int, 
        years_back: int
    ) -> List[PlanningApplication]:
        """Search Acolnet planning system"""
        
        # This would implement actual Acolnet API integration
        # For now, return mock data
        return await self._mock_planning_history(address, radius_m, years_back)
    
    async def _search_generic_applications(
        self, 
        authority: str, 
        address: str, 
        radius_m: int, 
        years_back: int
    ) -> List[PlanningApplication]:
        """Search generic planning system"""
        
        # This would implement generic API integration
        # For now, return mock data
        return await self._mock_planning_history(address, radius_m, years_back)
    
    async def _search_postcode_applications(
        self, 
        authority: str, 
        postcode: str, 
        years_back: int
    ) -> List[PlanningApplication]:
        """Search applications by postcode"""
        
        # Implementation varies by authority system
        return await self._mock_postcode_planning_history(postcode, years_back)
    
    async def _get_application_from_authority(
        self, 
        authority: str, 
        reference: str
    ) -> Optional[PlanningApplication]:
        """Get detailed application from authority"""
        
        # Implementation varies by authority system
        return await self._mock_application_details(reference, authority)
    
    async def _search_recent_decisions(
        self, 
        authority: str, 
        coordinates: Tuple[float, float], 
        radius_m: int, 
        months_back: int
    ) -> List[PlanningApplication]:
        """Search recent decisions by location"""
        
        # Implementation varies by authority system
        return await self._mock_recent_decisions(coordinates, radius_m, months_back)
    
    def _normalize_address(self, address: str) -> str:
        """Normalize address for searching"""
        return ' '.join(address.title().split())
    
    def _normalize_postcode(self, postcode: str) -> str:
        """Normalize UK postcode format"""
        postcode_clean = re.sub(r'\s+', '', postcode.upper())
        
        if len(postcode_clean) >= 5:
            postcode_clean = f"{postcode_clean[:-3]} {postcode_clean[-3:]}"
        
        return postcode_clean
    
    # Mock implementations for development
    
    async def _mock_planning_history(
        self, 
        address: str, 
        radius_m: int, 
        years_back: int
    ) -> List[PlanningApplication]:
        """Generate mock planning history"""
        
        applications = []
        
        # Generate 3-8 mock applications
        num_apps = hash(address) % 6 + 3
        
        for i in range(num_apps):
            app_date = datetime.now() - timedelta(days=(i * 200 + hash(address) % 365))
            decision_date = app_date + timedelta(days=56 + hash(address) % 28)  # 8-12 weeks
            
            # Vary application types
            app_types = ['FUL', 'HOU', 'LBC', 'ADV', 'TPO']
            app_type = app_types[i % len(app_types)]
            
            # Vary decisions
            decisions = ['Approved', 'Refused', 'Withdrawn', 'Pending']
            decision_weights = [0.7, 0.2, 0.05, 0.05]
            decision = decisions[hash(f"{address}_{i}") % len(decisions)]
            
            # Generate realistic reference
            year = app_date.year
            ref_num = hash(f"{address}_{i}") % 9999 + 1000
            reference = f"{year}/{ref_num:04d}/{app_type}"
            
            # Generate address variation
            base_number = hash(address) % 200 + 1
            app_address = f"{base_number + i * 2} Example Street, Example Town EX1 2MP"
            
            application = PlanningApplication(
                reference=reference,
                address=app_address,
                description=self._generate_mock_description(app_type, i),
                status='Decided' if decision != 'Pending' else 'Under Consideration',
                decision=decision if decision != 'Pending' else None,
                application_date=app_date.strftime('%Y-%m-%d'),
                decision_date=decision_date.strftime('%Y-%m-%d') if decision != 'Pending' else None,
                authority='Example Borough Council',
                applicant_name=f'Applicant {i+1}',
                agent_name=f'Planning Agent {i+1}' if i % 3 == 0 else None,
                application_type=app_type,
                development_type='Residential' if app_type in ['FUL', 'HOU'] else 'Other',
                coordinates=(51.5074 + (i * 0.001), -0.1278 + (i * 0.001)),
                decision_level='Delegated' if i % 4 != 0 else 'Committee',
                conditions=self._generate_mock_conditions(app_type) if decision == 'Approved' else None,
                reasons_for_refusal=self._generate_mock_refusal_reasons() if decision == 'Refused' else None,
                consultation_start=(app_date + timedelta(days=7)).strftime('%Y-%m-%d'),
                consultation_end=(app_date + timedelta(days=28)).strftime('%Y-%m-%d'),
                neighbour_comments=hash(f"{reference}_comments") % 5,
                case_officer=f'Officer {chr(65 + i % 26)}. Smith',
                ward='Example Ward',
                parish=None
            )
            
            applications.append(application)
        
        return applications
    
    async def _mock_postcode_planning_history(self, postcode: str, years_back: int) -> List[PlanningApplication]:
        """Mock planning history by postcode"""
        return await self._mock_planning_history(f"Example Street, {postcode}", 100, years_back)
    
    async def _mock_application_details(self, reference: str, authority: Optional[str]) -> PlanningApplication:
        """Mock detailed application"""
        
        # Generate detailed mock application
        app_date = datetime.now() - timedelta(days=hash(reference) % 365)
        decision_date = app_date + timedelta(days=56)
        
        return PlanningApplication(
            reference=reference,
            address=f"{hash(reference) % 200 + 1} Example Street, Example Town EX1 2MP",
            description="Single storey rear extension and loft conversion with dormer windows",
            status='Decided',
            decision='Approved',
            application_date=app_date.strftime('%Y-%m-%d'),
            decision_date=decision_date.strftime('%Y-%m-%d'),
            authority=authority or 'Example Borough Council',
            applicant_name='John Smith',
            agent_name='Planning Consultants Ltd',
            application_type='HOU',
            development_type='Residential',
            coordinates=(51.5074, -0.1278),
            decision_level='Delegated',
            conditions=[
                'Development in accordance with approved plans',
                'Materials to match existing building',
                'Works to commence within 3 years'
            ],
            consultation_start=(app_date + timedelta(days=7)).strftime('%Y-%m-%d'),
            consultation_end=(app_date + timedelta(days=28)).strftime('%Y-%m-%d'),
            neighbour_comments=2,
            documents=[
                {'type': 'Location Plan', 'url': f'https://planning.example.gov.uk/docs/{reference}_location.pdf'},
                {'type': 'Site Plan', 'url': f'https://planning.example.gov.uk/docs/{reference}_site.pdf'},
                {'type': 'Decision Notice', 'url': f'https://planning.example.gov.uk/docs/{reference}_decision.pdf'}
            ],
            case_officer='Sarah Johnson',
            ward='Example Ward'
        )
    
    async def _mock_recent_decisions(
        self, 
        coordinates: Tuple[float, float], 
        radius_m: int, 
        months_back: int
    ) -> List[PlanningApplication]:
        """Mock recent decisions"""
        
        # Generate recent decisions near coordinates
        decisions = []
        
        for i in range(5):  # Generate 5 recent decisions
            decision_date = datetime.now() - timedelta(days=i * 30 + 10)  # Last few months
            
            decision = PlanningApplication(
                reference=f"2024/{1000+i:04d}/FUL",
                address=f"{10+i*2} Nearby Street, Example Town EX1 2MP",
                description=f"Example development {i+1}",
                status='Decided',
                decision=['Approved', 'Refused'][i % 2],
                application_date=(decision_date - timedelta(days=56)).strftime('%Y-%m-%d'),
                decision_date=decision_date.strftime('%Y-%m-%d'),
                authority='Example Borough Council',
                decision_level='Delegated',
                coordinates=(coordinates[0] + (i * 0.0001), coordinates[1] + (i * 0.0001))
            )
            
            decisions.append(decision)
        
        return decisions
    
    def _generate_mock_description(self, app_type: str, index: int) -> str:
        """Generate realistic mock descriptions"""
        
        descriptions = {
            'FUL': [
                'Erection of two storey detached dwelling with associated parking',
                'Change of use from office to residential (3 flats)',
                'Demolition of existing building and erection of 4 storey residential block'
            ],
            'HOU': [
                'Single storey rear extension',
                'Loft conversion with rear dormer window',
                'Two storey side extension and rear extension'
            ],
            'LBC': [
                'Internal alterations to listed building',
                'Replacement windows to match existing',
                'Installation of disabled access ramp'
            ],
            'ADV': [
                'Installation of illuminated fascia sign',
                'Replacement shop front signage',
                'Digital advertising display'
            ],
            'TPO': [
                'Fell protected oak tree - diseased',
                'Crown reduction of protected lime trees',
                'Prune protected sycamore - safety reasons'
            ]
        }
        
        type_descriptions = descriptions.get(app_type, ['Development proposal'])
        return type_descriptions[index % len(type_descriptions)]
    
    def _generate_mock_conditions(self, app_type: str) -> List[str]:
        """Generate mock planning conditions"""
        
        standard_conditions = [
            'Development in accordance with approved plans',
            'Materials to be agreed in writing',
            'Works to commence within 3 years'
        ]
        
        if app_type == 'HOU':
            standard_conditions.extend([
                'Obscure glazing to be installed and retained',
                'No additional windows without planning permission'
            ])
        elif app_type == 'FUL':
            standard_conditions.extend([
                'Landscaping scheme to be submitted and approved',
                'Parking spaces to be provided prior to occupation',
                'Refuse storage details to be submitted'
            ])
        
        return standard_conditions
    
    def _generate_mock_refusal_reasons(self) -> List[str]:
        """Generate mock reasons for refusal"""
        
        return [
            'Unacceptable impact on character and appearance of the area',
            'Insufficient parking provision contrary to adopted standards',
            'Unacceptable impact on residential amenity of neighbouring properties'
        ]


# Convenience function for getting planning history
async def get_planning_history(
    identifier: str,
    search_type: str = 'address',
    radius_m: int = 100,
    years_back: int = 10
) -> Optional[Dict[str, Any]]:
    """
    Get planning history by various identifiers
    
    Args:
        identifier: Address, postcode, or coordinates
        search_type: Type of search ('address', 'postcode', 'coordinates')
        radius_m: Search radius for address/coordinate searches
        years_back: Years of history to retrieve
        
    Returns:
        Dictionary containing planning applications and summary
    """
    
    async with PlanningHistoryAdapter() as adapter:
        
        applications = []
        
        if search_type == 'address':
            applications = await adapter.get_planning_history_by_address(
                identifier, radius_m, years_back
            )
        
        elif search_type == 'postcode':
            applications = await adapter.get_planning_history_by_postcode(
                identifier, years_back
            )
        
        elif search_type == 'coordinates':
            try:
                lat_str, lng_str = identifier.split(',')
                latitude = float(lat_str.strip())
                longitude = float(lng_str.strip())
                applications = await adapter.get_recent_decisions(
                    (latitude, longitude), radius_m, years_back * 12  # Convert years to months
                )
            except (ValueError, IndexError):
                return None
        
        if applications:
            # Generate summary statistics
            total_apps = len(applications)
            approved = len([app for app in applications if app.decision == 'Approved'])
            refused = len([app for app in applications if app.decision == 'Refused'])
            pending = len([app for app in applications if app.status == 'Under Consideration'])
            
            approval_rate = (approved / (approved + refused)) * 100 if (approved + refused) > 0 else 0
            
            return {
                'applications': [asdict(app) for app in applications],
                'summary': {
                    'total_applications': total_apps,
                    'approved': approved,
                    'refused': refused,
                    'pending': pending,
                    'approval_rate': round(approval_rate, 1)
                },
                'search_parameters': {
                    'identifier': identifier,
                    'search_type': search_type,
                    'radius_m': radius_m,
                    'years_back': years_back
                }
            }
    
    return None