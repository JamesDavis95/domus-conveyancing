"""
Offsets Demand Management
Handles developer offset needs and biodiversity net gain requirements
"""
from typing import Dict, List, Any, Optional, Tuple
import asyncio
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid
import json

from .schemas import (
    OffsetDemandRequest, HabitatType, DemandStatus, BiodiversityAssessment,
    HabitatUnit, HabitatCondition, LocationStrategicSignificance
)


class DemandManager:
    """
    Manages biodiversity offset demand requests from developers
    """
    
    def __init__(self):
        # In production, this would use a proper database
        self._demand_requests: Dict[str, OffsetDemandRequest] = {}
        self._biodiversity_assessments: Dict[str, BiodiversityAssessment] = {}
        
        # BNG calculation parameters
        self.bng_percentage_requirement = Decimal("10")  # 10% net gain requirement
        self.temporal_multipliers = {
            'immediate': Decimal("1.0"),
            'within_1_year': Decimal("0.95"),
            'within_2_years': Decimal("0.90"),
            'within_3_years': Decimal("0.85"),
            'beyond_3_years': Decimal("0.80")
        }
    
    async def create_demand_request(
        self,
        developer_details: Dict[str, str],
        project_details: Dict[str, Any],
        biodiversity_assessment: BiodiversityAssessment,
        requirements: Dict[str, Any]
    ) -> OffsetDemandRequest:
        """
        Create new biodiversity offset demand request
        
        Args:
            developer_details: Developer contact information
            project_details: Development project details
            biodiversity_assessment: Site biodiversity assessment
            requirements: Offset requirements and preferences
            
        Returns:
            Created OffsetDemandRequest
        """
        
        # Calculate actual offset requirements
        required_units = await self._calculate_offset_requirement(biodiversity_assessment)
        
        # Determine acceptable habitat types for offsetting
        acceptable_habitats = await self._determine_acceptable_habitats(biodiversity_assessment)
        
        # Create demand request
        demand_request = OffsetDemandRequest(
            developer_id=developer_details.get('developer_id', str(uuid.uuid4())),
            developer_name=developer_details['name'],
            developer_contact=developer_details['contact'],
            
            project_name=project_details['name'],
            project_description=project_details['description'],
            development_postcode=project_details['postcode'],
            development_coordinates=project_details.get('coordinates'),
            planning_application_reference=project_details['planning_reference'],
            
            biodiversity_assessment=biodiversity_assessment,
            required_habitat_types=acceptable_habitats,
            required_units=required_units,
            
            max_distance_km=requirements.get('max_distance_km', 50),
            preferred_local_authorities=requirements.get('preferred_authorities', []),
            same_national_character_area=requirements.get('same_nca', True),
            
            required_by_date=requirements.get('required_by_date', 
                                           date.today() + timedelta(days=365)),
            delivery_timeline_months=requirements.get('delivery_timeline', 24),
            
            max_price_per_unit=Decimal(str(requirements['max_price_per_unit'])),
            preferred_payment_terms=requirements.get('payment_terms', 'Flexible'),
            
            status=DemandStatus.SEARCHING
        )
        
        # Store assessment and request
        self._biodiversity_assessments[biodiversity_assessment.assessment_id] = biodiversity_assessment
        self._demand_requests[demand_request.request_id] = demand_request
        
        return demand_request
    
    async def _calculate_offset_requirement(self, assessment: BiodiversityAssessment) -> Decimal:
        """
        Calculate biodiversity offset requirements based on assessment
        
        Args:
            assessment: BiodiversityAssessment object
            
        Returns:
            Required biodiversity units to offset losses
        """
        
        # Calculate net loss (negative net change means loss)
        net_change = assessment.net_unit_change or Decimal("0")
        
        if net_change >= 0:
            # No offset required - development achieves net gain on-site
            return Decimal("0")
        
        # Calculate offset requirement
        # Absolute loss + BNG requirement
        absolute_loss = abs(net_change)
        bng_requirement = assessment.net_gain_required or Decimal("0")
        
        total_offset_required = absolute_loss + bng_requirement
        
        return total_offset_required
    
    async def _determine_acceptable_habitats(self, assessment: BiodiversityAssessment) -> List[HabitatType]:
        """
        Determine acceptable habitat types for offsetting based on lost habitats
        
        Args:
            assessment: BiodiversityAssessment object
            
        Returns:
            List of acceptable habitat types for offsetting
        """
        
        # Extract habitat types being lost
        baseline_habitats = {unit.habitat_type for unit in assessment.baseline_habitats}
        post_dev_habitats = {unit.habitat_type for unit in assessment.post_development_habitats}
        
        lost_habitat_types = baseline_habitats - post_dev_habitats
        
        # Hierarchy of acceptable offsets (simplified version)
        habitat_hierarchy = {
            HabitatType.WOODLAND_BROADLEAF: [
                HabitatType.WOODLAND_BROADLEAF,
                HabitatType.WOODLAND_MIXED,
                HabitatType.SCRUBLAND,
                HabitatType.GRASSLAND_SPECIES_RICH
            ],
            HabitatType.GRASSLAND_SPECIES_RICH: [
                HabitatType.GRASSLAND_SPECIES_RICH,
                HabitatType.GRASSLAND_SPECIES_POOR,
                HabitatType.WETLAND_FRESHWATER
            ],
            HabitatType.WETLAND_FRESHWATER: [
                HabitatType.WETLAND_FRESHWATER,
                HabitatType.WETLAND_COASTAL,
                HabitatType.GRASSLAND_SPECIES_RICH
            ],
            HabitatType.HEATHLAND_LOWLAND: [
                HabitatType.HEATHLAND_LOWLAND,
                HabitatType.HEATHLAND_UPLAND,
                HabitatType.GRASSLAND_SPECIES_RICH,
                HabitatType.SCRUBLAND
            ]
        }
        
        acceptable_habitats = set()
        
        # Add acceptable offsets for each lost habitat type
        for lost_habitat in lost_habitat_types:
            if lost_habitat in habitat_hierarchy:
                acceptable_habitats.update(habitat_hierarchy[lost_habitat])
            else:
                # Default acceptable habitats
                acceptable_habitats.add(lost_habitat)
        
        # If no specific lost habitats, accept most habitat types
        if not acceptable_habitats:
            acceptable_habitats = {
                HabitatType.GRASSLAND_SPECIES_RICH,
                HabitatType.WOODLAND_BROADLEAF,
                HabitatType.WETLAND_FRESHWATER,
                HabitatType.HEATHLAND_LOWLAND,
                HabitatType.SCRUBLAND
            }
        
        return list(acceptable_habitats)
    
    async def update_demand_status(
        self,
        request_id: str,
        status: DemandStatus,
        notes: Optional[str] = None
    ) -> bool:
        """Update demand request status"""
        
        if request_id not in self._demand_requests:
            return False
        
        request = self._demand_requests[request_id]
        request.status = status
        request.last_updated = datetime.now()
        
        return True
    
    async def get_demand_request(self, request_id: str) -> Optional[OffsetDemandRequest]:
        """Get demand request by ID"""
        return self._demand_requests.get(request_id)
    
    async def search_demand_requests(
        self,
        habitat_types: Optional[List[HabitatType]] = None,
        min_units: Optional[Decimal] = None,
        max_units: Optional[Decimal] = None,
        min_budget: Optional[Decimal] = None,
        max_distance_km: Optional[int] = None,
        center_coordinates: Optional[Tuple[float, float]] = None,
        local_authorities: Optional[List[str]] = None,
        required_by_date: Optional[date] = None,
        status_filter: Optional[List[DemandStatus]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[OffsetDemandRequest]:
        """
        Search demand requests with filters
        
        Args:
            habitat_types: Filter by required habitat types
            min_units: Minimum biodiversity units required
            max_units: Maximum biodiversity units required  
            min_budget: Minimum budget available
            max_distance_km: Maximum distance from center coordinates
            center_coordinates: Center point for distance filtering
            local_authorities: Filter by development location
            required_by_date: Must be required by this date
            status_filter: Filter by request status
            limit: Maximum results to return
            offset: Pagination offset
            
        Returns:
            List of matching demand requests
        """
        
        results = []
        
        for request in self._demand_requests.values():
            
            # Status filter
            if status_filter and request.status not in status_filter:
                continue
            
            # Units filter
            if min_units and request.required_units < min_units:
                continue
            
            if max_units and request.required_units > max_units:
                continue
            
            # Budget filter
            if min_budget and (request.total_budget or Decimal("0")) < min_budget:
                continue
            
            # Habitat type filter
            if habitat_types:
                request_habitat_types = set(request.required_habitat_types)
                if not any(ht in request_habitat_types for ht in habitat_types):
                    continue
            
            # Required by date filter
            if required_by_date and request.required_by_date > required_by_date:
                continue
            
            # Distance filter (simplified)
            if max_distance_km and center_coordinates and request.development_coordinates:
                distance = self._calculate_distance(center_coordinates, request.development_coordinates)
                if distance > max_distance_km:
                    continue
            
            results.append(request)
        
        # Sort by created date (most recent first)
        results.sort(key=lambda x: x.created_date, reverse=True)
        
        # Apply pagination
        return results[offset:offset + limit]
    
    async def get_demand_statistics(self) -> Dict[str, Any]:
        """Get demand marketplace statistics"""
        
        active_requests = [r for r in self._demand_requests.values() if r.status == DemandStatus.SEARCHING]
        
        if not active_requests:
            return {
                'total_requests': 0,
                'searching_requests': 0,
                'total_units_demanded': Decimal("0"),
                'total_budget_available': Decimal("0"),
                'habitat_demand_distribution': {},
                'location_distribution': {}
            }
        
        total_units = sum(request.required_units for request in active_requests)
        total_budget = sum(request.total_budget or Decimal("0") for request in active_requests)
        
        # Habitat demand distribution
        habitat_demand = {}
        for request in active_requests:
            for habitat_type in request.required_habitat_types:
                habitat_name = habitat_type.value
                if habitat_name not in habitat_demand:
                    habitat_demand[habitat_name] = {
                        'requests': 0,
                        'total_units': Decimal("0"),
                        'total_budget': Decimal("0")
                    }
                
                habitat_demand[habitat_name]['requests'] += 1
                habitat_demand[habitat_name]['total_units'] += request.required_units
                habitat_demand[habitat_name]['total_budget'] += request.total_budget or Decimal("0")
        
        return {
            'total_requests': len(self._demand_requests),
            'searching_requests': len(active_requests),
            'total_units_demanded': total_units,
            'total_budget_available': total_budget,
            'habitat_demand_distribution': habitat_demand,
            'average_units_per_request': total_units / len(active_requests) if active_requests else Decimal("0"),
            'budget_range': {
                'min': min(r.total_budget or Decimal("0") for r in active_requests) if active_requests else Decimal("0"),
                'max': max(r.total_budget or Decimal("0") for r in active_requests) if active_requests else Decimal("0"),
                'average': total_budget / len(active_requests) if active_requests else Decimal("0")
            }
        }
    
    def _calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates (simplified)"""
        import math
        
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Haversine formula approximation
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2)**2)
        
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Earth's radius in kilometers
        
        return c * r
    
    # Assessment creation helpers
    
    async def create_biodiversity_assessment_from_survey(
        self,
        site_reference: str,
        postcode: str,
        survey_data: Dict[str, Any]
    ) -> BiodiversityAssessment:
        """
        Create biodiversity assessment from ecological survey data
        
        Args:
            site_reference: Site reference or name
            postcode: Site postcode
            survey_data: Ecological survey data
            
        Returns:
            BiodiversityAssessment object
        """
        
        # Process baseline habitat data
        baseline_habitats = []
        for habitat_data in survey_data.get('baseline_habitats', []):
            habitat_unit = HabitatUnit(
                habitat_type=HabitatType(habitat_data['habitat_type']),
                condition=HabitatCondition(habitat_data['condition']),
                area_hectares=Decimal(str(habitat_data['area_hectares'])),
                distinctiveness_score=habitat_data['distinctiveness_score'],
                condition_score=Decimal(str(habitat_data['condition_score'])),
                strategic_significance=LocationStrategicSignificance(
                    habitat_data.get('strategic_significance', 'low')
                )
            )
            baseline_habitats.append(habitat_unit)
        
        # Process post-development habitat data
        post_dev_habitats = []
        for habitat_data in survey_data.get('post_development_habitats', []):
            habitat_unit = HabitatUnit(
                habitat_type=HabitatType(habitat_data['habitat_type']),
                condition=HabitatCondition(habitat_data['condition']),
                area_hectares=Decimal(str(habitat_data['area_hectares'])),
                distinctiveness_score=habitat_data['distinctiveness_score'],
                condition_score=Decimal(str(habitat_data['condition_score'])),
                strategic_significance=LocationStrategicSignificance(
                    habitat_data.get('strategic_significance', 'low')
                )
            )
            post_dev_habitats.append(habitat_unit)
        
        # Create assessment
        assessment = BiodiversityAssessment(
            site_reference=site_reference,
            postcode=postcode,
            coordinates=survey_data.get('coordinates'),
            local_authority=survey_data.get('local_authority', 'Unknown'),
            
            assessment_date=date.fromisoformat(survey_data.get('assessment_date', date.today().isoformat())),
            assessor_name=survey_data.get('assessor_name', 'Unknown'),
            assessor_qualification=survey_data.get('assessor_qualification', 'CEcol'),
            methodology_version=survey_data.get('methodology_version', '4.0'),
            
            baseline_habitats=baseline_habitats,
            post_development_habitats=post_dev_habitats,
            
            bng_percentage_required=Decimal(str(survey_data.get('bng_percentage', 10)))
        )
        
        return assessment
    
    # Mock data generation
    
    async def create_mock_demand_requests(self, count: int = 10) -> List[OffsetDemandRequest]:
        """Create mock demand requests for development"""
        
        mock_requests = []
        
        # Sample data
        project_types = [
            'Residential Development',
            'Commercial Office Complex', 
            'Industrial Warehouse',
            'Retail Park',
            'Mixed Use Development',
            'Infrastructure Project',
            'Educational Facility',
            'Healthcare Development'
        ]
        
        postcodes = ['OX2 6JX', 'CB3 0FB', 'GL50 1DZ', 'BA2 7AY', 'EX1 3PB']
        authorities = ['Oxford City Council', 'Cambridge City Council', 'Gloucester City Council']
        
        for i in range(count):
            
            # Create mock biodiversity assessment
            baseline_habitats = []
            
            # Generate 1-3 baseline habitat types
            num_habitats = max(1, (i % 3) + 1)
            habitat_types = [HabitatType.GRASSLAND_MODIFIED, HabitatType.ARABLE, HabitatType.SCRUBLAND]
            
            total_baseline_units = Decimal("0")
            
            for j in range(num_habitats):
                habitat_type = habitat_types[j % len(habitat_types)]
                area = Decimal(str(round(0.5 + (j * 0.3), 2)))
                
                habitat_unit = HabitatUnit(
                    habitat_type=habitat_type,
                    condition=HabitatCondition.POOR if j % 2 == 0 else HabitatCondition.MODERATE,
                    area_hectares=area,
                    distinctiveness_score=2 if habitat_type == HabitatType.ARABLE else 3,
                    condition_score=Decimal("1.5" if j % 2 == 0 else "2.0"),
                    strategic_significance=LocationStrategicSignificance.LOW
                )
                
                baseline_habitats.append(habitat_unit)
                total_baseline_units += habitat_unit.baseline_units or Decimal("0")
            
            # Minimal post-development habitats (mostly sealed)
            post_dev_habitats = [
                HabitatUnit(
                    habitat_type=HabitatType.DEVELOPED_SEALED,
                    condition=HabitatCondition.NA,
                    area_hectares=sum(h.area_hectares for h in baseline_habitats) * Decimal("0.8"),
                    distinctiveness_score=0,
                    condition_score=Decimal("1.0"),
                    strategic_significance=LocationStrategicSignificance.LOW
                )
            ]
            
            assessment = BiodiversityAssessment(
                site_reference=f"DEV-{i+1:03d}",
                postcode=postcodes[i % len(postcodes)],
                coordinates=(51.5 + (i * 0.01), -1.2 + (i * 0.01)),
                local_authority=authorities[i % len(authorities)],
                
                assessment_date=date.today() - timedelta(days=i * 5),
                assessor_name=f"Ecologist {i+1}",
                assessor_qualification="CEcol MCIEEM",
                methodology_version="4.0",
                
                baseline_habitats=baseline_habitats,
                post_development_habitats=post_dev_habitats,
                bng_percentage_required=Decimal("10")
            )
            
            # Calculate required units (loss + 10% net gain)
            net_loss = abs(assessment.net_unit_change or Decimal("0"))
            bng_requirement = assessment.net_gain_required or Decimal("0")
            required_units = net_loss + bng_requirement
            
            # Acceptable habitats for offsetting
            acceptable_habitats = [
                HabitatType.GRASSLAND_SPECIES_RICH,
                HabitatType.WOODLAND_BROADLEAF,
                HabitatType.WETLAND_FRESHWATER
            ]
            
            demand_request = OffsetDemandRequest(
                developer_id=f"developer_{i+1}",
                developer_name=f"Developer Ltd {i+1}",
                developer_contact=f"developer{i+1}@example.com",
                
                project_name=f"{project_types[i % len(project_types)]} {i+1}",
                project_description=f"Development of {project_types[i % len(project_types)].lower()} with associated infrastructure",
                development_postcode=postcodes[i % len(postcodes)],
                development_coordinates=(51.5 + (i * 0.01), -1.2 + (i * 0.01)),
                planning_application_reference=f"23/{1000+i:04d}/FUL",
                
                biodiversity_assessment=assessment,
                required_habitat_types=acceptable_habitats,
                required_units=required_units,
                
                max_distance_km=50 + (i * 10),
                preferred_local_authorities=[authorities[i % len(authorities)]],
                same_national_character_area=True,
                
                required_by_date=date.today() + timedelta(days=180 + (i * 30)),
                delivery_timeline_months=24,
                
                max_price_per_unit=Decimal(str(18000 + (i * 1000))),  # £18,000-28,000 per unit
                preferred_payment_terms="Phased payments linked to delivery milestones",
                
                status=DemandStatus.SEARCHING
            )
            
            # Store assessment and request
            self._biodiversity_assessments[assessment.assessment_id] = assessment
            self._demand_requests[demand_request.request_id] = demand_request
            mock_requests.append(demand_request)
        
        return mock_requests
    
    async def export_demand_to_dict(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Export demand request data for integration with other systems"""
        
        request = await self.get_demand_request(request_id)
        if not request:
            return None
        
        # Convert to dictionary with proper serialization
        request_dict = {
            'request_id': request.request_id,
            'developer_details': {
                'id': request.developer_id,
                'name': request.developer_name,
                'contact': request.developer_contact
            },
            'project_details': {
                'name': request.project_name,
                'description': request.project_description,
                'postcode': request.development_postcode,
                'coordinates': request.development_coordinates,
                'planning_reference': request.planning_application_reference
            },
            'offset_requirements': {
                'required_units': float(request.required_units),
                'acceptable_habitat_types': [ht.value for ht in request.required_habitat_types],
                'max_distance_km': request.max_distance_km,
                'preferred_authorities': request.preferred_local_authorities,
                'same_character_area': request.same_national_character_area
            },
            'timeline': {
                'required_by': request.required_by_date.isoformat(),
                'delivery_timeline_months': request.delivery_timeline_months
            },
            'budget': {
                'max_price_per_unit': float(request.max_price_per_unit),
                'total_budget': float(request.total_budget or 0),
                'payment_terms': request.preferred_payment_terms
            },
            'biodiversity_assessment': {
                'assessment_id': request.biodiversity_assessment.assessment_id,
                'baseline_units': float(request.biodiversity_assessment.baseline_biodiversity_units or 0),
                'post_dev_units': float(request.biodiversity_assessment.post_development_units or 0),
                'net_change': float(request.biodiversity_assessment.net_unit_change or 0),
                'net_gain_required': float(request.biodiversity_assessment.net_gain_required or 0)
            },
            'status': {
                'current_status': request.status.value,
                'created_date': request.created_date.isoformat(),
                'last_updated': request.last_updated.isoformat()
            }
        }
        
        return request_dict