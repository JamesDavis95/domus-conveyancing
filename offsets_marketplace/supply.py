"""
Offsets Supply Management
Handles landowner offset supply listings and habitat baseline data
"""
from typing import Dict, List, Any, Optional, Tuple
import asyncio
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid
import json
from dataclasses import asdict

from .schemas import (
    OffsetSupplyListing, HabitatUnit, HabitatType, HabitatCondition,
    LocationStrategicSignificance, ListingStatus, BiodiversityAssessment
)


class SupplyManager:
    """
    Manages biodiversity offset supply listings from landowners
    """
    
    def __init__(self):
        # In production, this would use a proper database
        self._listings: Dict[str, OffsetSupplyListing] = {}
        self._assessments: Dict[str, BiodiversityAssessment] = {}
        
        # DEFRA biodiversity metric lookup tables
        self.habitat_distinctiveness_scores = {
            HabitatType.GRASSLAND_MODIFIED: 2,
            HabitatType.GRASSLAND_SPECIES_POOR: 3,
            HabitatType.GRASSLAND_SPECIES_RICH: 6,
            HabitatType.HEATHLAND_LOWLAND: 6,
            HabitatType.HEATHLAND_UPLAND: 6,
            HabitatType.WOODLAND_BROADLEAF: 6,
            HabitatType.WOODLAND_CONIFEROUS: 4,
            HabitatType.WOODLAND_MIXED: 5,
            HabitatType.WETLAND_FRESHWATER: 6,
            HabitatType.WETLAND_COASTAL: 7,
            HabitatType.SCRUBLAND: 3,
            HabitatType.URBAN_TREES: 4,
            HabitatType.ARABLE: 2,
            HabitatType.DEVELOPED_SEALED: 0
        }
        
        self.condition_multipliers = {
            HabitatCondition.GOOD: Decimal("3.0"),
            HabitatCondition.MODERATE: Decimal("2.0"),
            HabitatCondition.POOR: Decimal("1.5"),
            HabitatCondition.NA: Decimal("1.0")
        }
    
    async def create_supply_listing(
        self,
        landowner_details: Dict[str, str],
        site_details: Dict[str, Any],
        habitat_data: List[Dict[str, Any]],
        pricing_terms: Dict[str, Any]
    ) -> OffsetSupplyListing:
        """
        Create new biodiversity offset supply listing
        
        Args:
            landowner_details: Landowner contact information
            site_details: Site location and description
            habitat_data: List of habitat units with baseline data
            pricing_terms: Pricing and delivery terms
            
        Returns:
            Created OffsetSupplyListing
        """
        
        # Process habitat units
        habitat_units = []
        for habitat_data_item in habitat_data:
            habitat_unit = await self._process_habitat_unit(habitat_data_item)
            habitat_units.append(habitat_unit)
        
        # Create listing
        listing = OffsetSupplyListing(
            landowner_id=landowner_details.get('landowner_id', str(uuid.uuid4())),
            landowner_name=landowner_details['name'],
            landowner_contact=landowner_details['contact'],
            
            site_name=site_details['name'],
            site_description=site_details.get('description'),
            postcode=site_details['postcode'],
            coordinates=site_details.get('coordinates'),
            total_site_area_hectares=Decimal(str(site_details['area_hectares'])),
            
            available_habitat_units=habitat_units,
            
            delivery_start_date=pricing_terms.get('delivery_start_date', 
                                                date.today() + timedelta(days=30)),
            delivery_completion_date=pricing_terms.get('delivery_completion_date',
                                                     date.today() + timedelta(days=730)),
            monitoring_period_years=pricing_terms.get('monitoring_years', 30),
            
            price_per_unit=Decimal(str(pricing_terms['price_per_unit'])),
            minimum_unit_purchase=Decimal(str(pricing_terms.get('minimum_purchase', 0.1))),
            payment_terms=pricing_terms.get('payment_terms', "50% on signature, 50% on delivery"),
            
            land_tenure=pricing_terms.get('land_tenure', 'freehold'),
            planning_permission_reference=site_details.get('planning_reference'),
            environmental_permits=site_details.get('permits', []),
            
            status=ListingStatus.DRAFT
        )
        
        # Store listing
        self._listings[listing.listing_id] = listing
        
        return listing
    
    async def _process_habitat_unit(self, habitat_data: Dict[str, Any]) -> HabitatUnit:
        """Process and validate habitat unit data"""
        
        habitat_type = HabitatType(habitat_data['habitat_type'])
        condition = HabitatCondition(habitat_data['condition'])
        area = Decimal(str(habitat_data['area_hectares']))
        
        # Get distinctiveness score from DEFRA metrics
        distinctiveness_score = self.habitat_distinctiveness_scores.get(habitat_type, 2)
        
        # Get condition score
        condition_score = self.condition_multipliers.get(condition, Decimal("1.0"))
        
        # Strategic significance
        strategic_significance = LocationStrategicSignificance(
            habitat_data.get('strategic_significance', 'low')
        )
        
        habitat_unit = HabitatUnit(
            habitat_type=habitat_type,
            condition=condition,
            area_hectares=area,
            distinctiveness_score=distinctiveness_score,
            condition_score=condition_score,
            strategic_significance=strategic_significance
        )
        
        return habitat_unit
    
    async def update_listing_status(
        self,
        listing_id: str,
        status: ListingStatus,
        notes: Optional[str] = None
    ) -> bool:
        """Update listing status"""
        
        if listing_id not in self._listings:
            return False
        
        listing = self._listings[listing_id]
        listing.status = status
        listing.last_updated = datetime.now()
        
        return True
    
    async def reserve_units(
        self,
        listing_id: str,
        units_to_reserve: Decimal,
        reservation_expires: Optional[datetime] = None
    ) -> bool:
        """Reserve units in a listing"""
        
        if listing_id not in self._listings:
            return False
        
        listing = self._listings[listing_id]
        
        # Check availability
        if listing.units_available < units_to_reserve:
            return False
        
        # Reserve units
        listing.units_reserved += units_to_reserve
        listing.last_updated = datetime.now()
        
        return True
    
    async def sell_units(
        self,
        listing_id: str,
        units_to_sell: Decimal
    ) -> bool:
        """Mark units as sold"""
        
        if listing_id not in self._listings:
            return False
        
        listing = self._listings[listing_id]
        
        # Check if enough units are available (including reserved)
        total_committed = listing.units_reserved + listing.units_sold
        available_to_sell = (listing.total_biodiversity_units or Decimal("0")) - total_committed
        
        if available_to_sell < units_to_sell:
            return False
        
        # Convert reserved units to sold if needed
        if listing.units_reserved >= units_to_sell:
            listing.units_reserved -= units_to_sell
            listing.units_sold += units_to_sell
        else:
            # Sell remaining reserved and some unreserved
            remaining_to_sell = units_to_sell - listing.units_reserved
            listing.units_sold += listing.units_reserved + remaining_to_sell
            listing.units_reserved = Decimal("0")
        
        listing.last_updated = datetime.now()
        
        # Update status if fully sold
        if listing.units_available <= 0:
            listing.status = ListingStatus.SOLD
        
        return True
    
    async def get_listing(self, listing_id: str) -> Optional[OffsetSupplyListing]:
        """Get supply listing by ID"""
        return self._listings.get(listing_id)
    
    async def search_supply_listings(
        self,
        habitat_types: Optional[List[HabitatType]] = None,
        min_units: Optional[Decimal] = None,
        max_price_per_unit: Optional[Decimal] = None,
        max_distance_km: Optional[int] = None,
        center_coordinates: Optional[Tuple[float, float]] = None,
        local_authorities: Optional[List[str]] = None,
        delivery_by_date: Optional[date] = None,
        status_filter: Optional[List[ListingStatus]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[OffsetSupplyListing]:
        """
        Search supply listings with filters
        
        Args:
            habitat_types: Filter by habitat types
            min_units: Minimum biodiversity units available
            max_price_per_unit: Maximum price per unit
            max_distance_km: Maximum distance from center coordinates
            center_coordinates: Center point for distance filtering
            local_authorities: Filter by local authority
            delivery_by_date: Must be deliverable by this date
            status_filter: Filter by listing status
            limit: Maximum results to return
            offset: Pagination offset
            
        Returns:
            List of matching supply listings
        """
        
        results = []
        
        for listing in self._listings.values():
            
            # Status filter
            if status_filter and listing.status not in status_filter:
                continue
            
            # Units filter
            if min_units and listing.units_available < min_units:
                continue
            
            # Price filter  
            if max_price_per_unit and listing.price_per_unit > max_price_per_unit:
                continue
            
            # Habitat type filter
            if habitat_types:
                listing_habitat_types = {unit.habitat_type for unit in listing.available_habitat_units}
                if not any(ht in listing_habitat_types for ht in habitat_types):
                    continue
            
            # Delivery date filter
            if delivery_by_date and listing.delivery_completion_date > delivery_by_date:
                continue
            
            # Distance filter (simplified - would use proper geospatial in production)
            if max_distance_km and center_coordinates and listing.coordinates:
                distance = self._calculate_distance(center_coordinates, listing.coordinates)
                if distance > max_distance_km:
                    continue
            
            # Local authority filter (would need proper lookup)
            if local_authorities:
                # Simplified - would use postcode to LA mapping
                pass
            
            results.append(listing)
        
        # Sort by created date (most recent first)
        results.sort(key=lambda x: x.created_date, reverse=True)
        
        # Apply pagination
        return results[offset:offset + limit]
    
    async def get_supply_statistics(self) -> Dict[str, Any]:
        """Get supply marketplace statistics"""
        
        active_listings = [l for l in self._listings.values() if l.status == ListingStatus.ACTIVE]
        
        if not active_listings:
            return {
                'total_listings': 0,
                'active_listings': 0,
                'total_units_available': Decimal("0"),
                'average_price_per_unit': Decimal("0"),
                'habitat_type_distribution': {},
                'location_distribution': {}
            }
        
        total_units = sum(listing.units_available for listing in active_listings)
        total_value = sum(listing.total_value for listing in active_listings)
        avg_price = total_value / total_units if total_units > 0 else Decimal("0")
        
        # Habitat distribution
        habitat_distribution = {}
        for listing in active_listings:
            for habitat_unit in listing.available_habitat_units:
                habitat_type = habitat_unit.habitat_type.value
                if habitat_type not in habitat_distribution:
                    habitat_distribution[habitat_type] = {
                        'listings': 0,
                        'total_units': Decimal("0"),
                        'total_area_hectares': Decimal("0")
                    }
                
                habitat_distribution[habitat_type]['listings'] += 1
                habitat_distribution[habitat_type]['total_units'] += habitat_unit.baseline_units or Decimal("0")
                habitat_distribution[habitat_type]['total_area_hectares'] += habitat_unit.area_hectares
        
        return {
            'total_listings': len(self._listings),
            'active_listings': len(active_listings),
            'total_units_available': total_units,
            'average_price_per_unit': avg_price,
            'habitat_type_distribution': habitat_distribution,
            'price_range': {
                'min': min(l.price_per_unit for l in active_listings) if active_listings else Decimal("0"),
                'max': max(l.price_per_unit for l in active_listings) if active_listings else Decimal("0"),
                'average': avg_price
            }
        }
    
    def _calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates (simplified)"""
        # Simplified distance calculation - would use proper geospatial library in production
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
    
    # Mock data generation for development
    
    async def create_mock_supply_listings(self, count: int = 10) -> List[OffsetSupplyListing]:
        """Create mock supply listings for development"""
        
        mock_listings = []
        
        # Sample data for variety
        habitat_types = list(HabitatType)
        conditions = list(HabitatCondition)
        postcodes = ['OX1 2AB', 'CB2 1TN', 'GL7 1XY', 'BA1 2CD', 'EX4 6PT']
        site_names = [
            'Meadowbrook Farm Conservation Area',
            'Riverside Wetland Restoration',
            'Oakwood Biodiversity Enhancement',
            'Chalky Downs Grassland Project', 
            'Millfield Woodland Creation'
        ]
        
        for i in range(count):
            # Generate habitat units
            num_habitats = min(3, max(1, i % 4))  # 1-3 habitat types per listing
            habitat_units = []
            
            for j in range(num_habitats):
                habitat_type = habitat_types[((i * 3) + j) % len(habitat_types)]
                condition = conditions[j % len(conditions)]
                
                # Skip non-applicable conditions for certain habitats
                if habitat_type == HabitatType.DEVELOPED_SEALED and condition != HabitatCondition.NA:
                    condition = HabitatCondition.NA
                
                area = Decimal(str(round(0.5 + (i * 0.3) + (j * 0.2), 2)))
                
                habitat_unit = HabitatUnit(
                    habitat_type=habitat_type,
                    condition=condition,
                    area_hectares=area,
                    distinctiveness_score=self.habitat_distinctiveness_scores.get(habitat_type, 2),
                    condition_score=self.condition_multipliers.get(condition, Decimal("1.0")),
                    strategic_significance=LocationStrategicSignificance.LOW if i % 3 == 0 else LocationStrategicSignificance.MEDIUM
                )
                
                habitat_units.append(habitat_unit)
            
            # Calculate total site area
            total_area = sum(unit.area_hectares for unit in habitat_units) * Decimal("1.2")  # Add buffer
            
            # Create listing
            listing = OffsetSupplyListing(
                landowner_id=f"landowner_{i+1}",
                landowner_name=f"Landowner {i+1}",
                landowner_contact=f"landowner{i+1}@example.com",
                
                site_name=site_names[i % len(site_names)],
                site_description=f"High quality {habitat_units[0].habitat_type.value.replace('_', ' ')} restoration site",
                postcode=postcodes[i % len(postcodes)],
                coordinates=(51.5 + (i * 0.01), -1.2 + (i * 0.01)),
                total_site_area_hectares=total_area,
                
                available_habitat_units=habitat_units,
                
                delivery_start_date=date.today() + timedelta(days=30 + (i * 10)),
                delivery_completion_date=date.today() + timedelta(days=365 + (i * 60)),
                monitoring_period_years=30,
                
                price_per_unit=Decimal(str(15000 + (i * 500))),  # £15,000-20,000 per unit
                minimum_unit_purchase=Decimal("0.1"),
                payment_terms="50% on signature, 50% on delivery",
                
                land_tenure="freehold",
                status=ListingStatus.ACTIVE if i % 4 != 0 else ListingStatus.DRAFT
            )
            
            self._listings[listing.listing_id] = listing
            mock_listings.append(listing)
        
        return mock_listings
    
    async def export_listing_to_dict(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """Export listing data for integration with other systems"""
        
        listing = await self.get_listing(listing_id)
        if not listing:
            return None
        
        # Convert to dictionary with proper serialization
        listing_dict = {
            'listing_id': listing.listing_id,
            'landowner_details': {
                'id': listing.landowner_id,
                'name': listing.landowner_name,
                'contact': listing.landowner_contact
            },
            'site_details': {
                'name': listing.site_name,
                'description': listing.site_description,
                'postcode': listing.postcode,
                'coordinates': listing.coordinates,
                'total_area_hectares': float(listing.total_site_area_hectares)
            },
            'biodiversity_data': {
                'total_units': float(listing.total_biodiversity_units or 0),
                'units_available': float(listing.units_available),
                'habitat_units': [
                    {
                        'habitat_type': unit.habitat_type.value,
                        'condition': unit.condition.value,
                        'area_hectares': float(unit.area_hectares),
                        'biodiversity_units': float(unit.baseline_units or 0),
                        'distinctiveness_score': unit.distinctiveness_score,
                        'condition_score': float(unit.condition_score),
                        'strategic_significance': unit.strategic_significance.value
                    }
                    for unit in listing.available_habitat_units
                ]
            },
            'commercial_terms': {
                'price_per_unit': float(listing.price_per_unit),
                'total_value': float(listing.total_value),
                'minimum_purchase': float(listing.minimum_unit_purchase),
                'payment_terms': listing.payment_terms,
                'delivery_timeline': {
                    'start_date': listing.delivery_start_date.isoformat(),
                    'completion_date': listing.delivery_completion_date.isoformat(),
                    'monitoring_years': listing.monitoring_period_years
                }
            },
            'legal_details': {
                'land_tenure': listing.land_tenure,
                'planning_permission': listing.planning_permission_reference,
                'environmental_permits': listing.environmental_permits
            },
            'status': {
                'current_status': listing.status.value,
                'created_date': listing.created_date.isoformat(),
                'last_updated': listing.last_updated.isoformat(),
                'expiry_date': listing.expiry_date.isoformat() if listing.expiry_date else None
            }
        }
        
        return listing_dict