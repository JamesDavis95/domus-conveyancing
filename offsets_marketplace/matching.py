"""
Offsets Matching Engine
Rules engine for matching supply and demand with location, unit type, and timeframe optimization
"""
from typing import Dict, List, Any, Optional, Tuple
import asyncio
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid
import math
from dataclasses import dataclass

from .schemas import (
    OffsetSupplyListing, OffsetDemandRequest, OffsetMatch, HabitatType,
    ListingStatus, DemandStatus, LocationStrategicSignificance
)
from .supply import SupplyManager
from .demand import DemandManager


@dataclass
class MatchingCriteria:
    """Criteria for matching supply and demand"""
    
    # Distance preferences
    max_distance_km: int = 100
    distance_weight: float = 0.25
    
    # Habitat matching
    habitat_match_weight: float = 0.35
    allow_habitat_substitution: bool = True
    
    # Location preferences  
    location_weight: float = 0.20
    prefer_same_authority: bool = True
    
    # Timeline compatibility
    timeline_weight: float = 0.15
    timeline_buffer_months: int = 6
    
    # Price compatibility
    price_weight: float = 0.05
    price_tolerance_percent: float = 20.0
    
    # Minimum match score threshold
    minimum_match_score: float = 0.4


class MatchingEngine:
    """
    Advanced matching engine for biodiversity offset supply and demand
    """
    
    def __init__(self, supply_manager: SupplyManager, demand_manager: DemandManager):
        self.supply_manager = supply_manager
        self.demand_manager = demand_manager
        
        # Stored matches
        self._matches: Dict[str, OffsetMatch] = {}
        
        # Habitat compatibility matrix (DEFRA metric based)
        self.habitat_compatibility = {
            HabitatType.GRASSLAND_SPECIES_RICH: {
                HabitatType.GRASSLAND_SPECIES_RICH: 1.0,
                HabitatType.GRASSLAND_SPECIES_POOR: 0.8,
                HabitatType.GRASSLAND_MODIFIED: 0.6,
                HabitatType.WETLAND_FRESHWATER: 0.7,
                HabitatType.SCRUBLAND: 0.5
            },
            HabitatType.WOODLAND_BROADLEAF: {
                HabitatType.WOODLAND_BROADLEAF: 1.0,
                HabitatType.WOODLAND_MIXED: 0.9,
                HabitatType.WOODLAND_CONIFEROUS: 0.7,
                HabitatType.SCRUBLAND: 0.6,
                HabitatType.GRASSLAND_SPECIES_RICH: 0.4
            },
            HabitatType.WETLAND_FRESHWATER: {
                HabitatType.WETLAND_FRESHWATER: 1.0,
                HabitatType.WETLAND_COASTAL: 0.8,
                HabitatType.GRASSLAND_SPECIES_RICH: 0.6,
                HabitatType.SCRUBLAND: 0.3
            },
            HabitatType.HEATHLAND_LOWLAND: {
                HabitatType.HEATHLAND_LOWLAND: 1.0,
                HabitatType.HEATHLAND_UPLAND: 0.9,
                HabitatType.GRASSLAND_SPECIES_RICH: 0.7,
                HabitatType.SCRUBLAND: 0.8
            }
        }
        
        # Strategic significance compatibility
        self.strategic_compatibility = {
            LocationStrategicSignificance.VERY_HIGH: 1.2,
            LocationStrategicSignificance.HIGH: 1.1,
            LocationStrategicSignificance.MEDIUM: 1.0,
            LocationStrategicSignificance.LOW: 0.9
        }
    
    async def find_matches(
        self,
        demand_request_id: Optional[str] = None,
        supply_listing_id: Optional[str] = None,
        criteria: Optional[MatchingCriteria] = None,
        max_matches: int = 50
    ) -> List[OffsetMatch]:
        """
        Find matches between supply and demand
        
        Args:
            demand_request_id: Specific demand to match (optional)
            supply_listing_id: Specific supply to match (optional)  
            criteria: Matching criteria (uses defaults if None)
            max_matches: Maximum number of matches to return
            
        Returns:
            List of potential matches sorted by match score
        """
        
        if criteria is None:
            criteria = MatchingCriteria()
        
        matches = []
        
        # Get demand requests to match
        if demand_request_id:
            demand_request = await self.demand_manager.get_demand_request(demand_request_id)
            demand_requests = [demand_request] if demand_request else []
        else:
            demand_requests = await self.demand_manager.search_demand_requests(
                status_filter=[DemandStatus.SEARCHING]
            )
        
        # Get supply listings to match
        if supply_listing_id:
            supply_listing = await self.supply_manager.get_listing(supply_listing_id)
            supply_listings = [supply_listing] if supply_listing else []
        else:
            supply_listings = await self.supply_manager.search_supply_listings(
                status_filter=[ListingStatus.ACTIVE],
                min_units=Decimal("0.1")  # Only listings with available units
            )
        
        # Generate all possible matches
        for demand in demand_requests:
            if not demand:
                continue
                
            for supply in supply_listings:
                if not supply or supply.units_available <= 0:
                    continue
                
                # Quick compatibility check
                if not await self._quick_compatibility_check(demand, supply, criteria):
                    continue
                
                # Calculate detailed match
                match = await self._calculate_match(demand, supply, criteria)
                
                if match and match.overall_match_score >= criteria.minimum_match_score:
                    matches.append(match)
        
        # Sort by match score (highest first)
        matches.sort(key=lambda x: x.overall_match_score or 0, reverse=True)
        
        # Store matches
        for match in matches[:max_matches]:
            self._matches[match.match_id] = match
        
        return matches[:max_matches]
    
    async def _quick_compatibility_check(
        self,
        demand: OffsetDemandRequest,
        supply: OffsetSupplyListing,
        criteria: MatchingCriteria
    ) -> bool:
        """Quick compatibility check to filter obviously incompatible matches"""
        
        # Check if supply has enough units
        if supply.units_available < demand.required_units:
            return False
        
        # Check price compatibility
        if supply.price_per_unit > demand.max_price_per_unit * (1 + criteria.price_tolerance_percent / 100):
            return False
        
        # Check timeline compatibility
        if supply.delivery_completion_date > demand.required_by_date:
            return False
        
        # Check habitat type compatibility
        supply_habitat_types = {unit.habitat_type for unit in supply.available_habitat_units}
        demand_habitat_types = set(demand.required_habitat_types)
        
        # Check if any supply habitats are acceptable for demand
        habitat_compatible = False
        for supply_habitat in supply_habitat_types:
            for demand_habitat in demand_habitat_types:
                compatibility = self.habitat_compatibility.get(demand_habitat, {}).get(supply_habitat, 0)
                if compatibility > 0:
                    habitat_compatible = True
                    break
            if habitat_compatible:
                break
        
        if not habitat_compatible:
            return False
        
        # Check distance (if coordinates available)
        if (demand.development_coordinates and supply.coordinates and 
            criteria.max_distance_km > 0):
            
            distance = self._calculate_distance(
                demand.development_coordinates, 
                supply.coordinates
            )
            
            if distance > criteria.max_distance_km:
                return False
        
        return True
    
    async def _calculate_match(
        self,
        demand: OffsetDemandRequest,
        supply: OffsetSupplyListing,
        criteria: MatchingCriteria
    ) -> Optional[OffsetMatch]:
        """Calculate detailed match score and create OffsetMatch object"""
        
        # Calculate individual scoring components
        habitat_score = await self._calculate_habitat_match_score(demand, supply)
        location_score = await self._calculate_location_preference_score(demand, supply, criteria)
        timeline_compatibility = await self._check_timeline_compatibility(demand, supply, criteria)
        
        # Calculate distance
        distance_km = Decimal("0")
        if demand.development_coordinates and supply.coordinates:
            distance_km = Decimal(str(self._calculate_distance(
                demand.development_coordinates, 
                supply.coordinates
            )))
        
        # Determine matched units (minimum of required and available)
        matched_units = min(demand.required_units, supply.units_available)
        
        # Use supply pricing (could be negotiated in real implementation)
        unit_price = supply.price_per_unit
        total_value = matched_units * unit_price
        
        # Create match object
        match = OffsetMatch(
            supply_listing_id=supply.listing_id,
            demand_request_id=demand.request_id,
            matched_units=matched_units,
            unit_price=unit_price,
            total_value=total_value,
            distance_km=distance_km,
            habitat_type_match_score=habitat_score,
            location_preference_score=location_score,
            timeline_compatibility=timeline_compatibility,
            expires_date=datetime.now() + timedelta(days=30)  # 30-day match expiry
        )
        
        return match
    
    async def _calculate_habitat_match_score(
        self,
        demand: OffsetDemandRequest,
        supply: OffsetSupplyListing
    ) -> Decimal:
        """Calculate habitat type compatibility score"""
        
        supply_habitats = supply.available_habitat_units
        demand_habitat_types = set(demand.required_habitat_types)
        
        # Calculate weighted compatibility score
        total_compatibility = Decimal("0")
        total_weight = Decimal("0")
        
        for habitat_unit in supply_habitats:
            unit_weight = habitat_unit.baseline_units or Decimal("0")
            
            if unit_weight <= 0:
                continue
            
            # Find best compatibility score for this habitat unit
            best_compatibility = Decimal("0")
            
            for demand_habitat in demand_habitat_types:
                compatibility = Decimal(str(
                    self.habitat_compatibility.get(demand_habitat, {}).get(
                        habitat_unit.habitat_type, 0
                    )
                ))
                
                # Apply strategic significance bonus
                strategic_multiplier = Decimal(str(
                    self.strategic_compatibility.get(
                        habitat_unit.strategic_significance, 1.0
                    )
                ))
                
                adjusted_compatibility = compatibility * strategic_multiplier
                best_compatibility = max(best_compatibility, adjusted_compatibility)
            
            total_compatibility += best_compatibility * unit_weight
            total_weight += unit_weight
        
        if total_weight > 0:
            # Normalize to 0-1 scale
            score = total_compatibility / total_weight
            return min(score, Decimal("1.0"))
        
        return Decimal("0")
    
    async def _calculate_location_preference_score(
        self,
        demand: OffsetDemandRequest,
        supply: OffsetSupplyListing,
        criteria: MatchingCriteria
    ) -> Decimal:
        """Calculate location preference match score"""
        
        score = Decimal("0")
        
        # Same local authority preference
        if criteria.prefer_same_authority and demand.preferred_local_authorities:
            # Would need proper postcode to authority mapping in production
            # For now, use simplified matching
            if any(auth.lower() in supply.postcode.lower() 
                   for auth in demand.preferred_local_authorities):
                score += Decimal("0.5")
        
        # National Character Area preference (simplified)
        if demand.same_national_character_area:
            # In production, would use proper NCA mapping
            score += Decimal("0.3")
        
        # Distance scoring (closer is better)
        if demand.development_coordinates and supply.coordinates:
            distance = self._calculate_distance(
                demand.development_coordinates, 
                supply.coordinates
            )
            
            # Normalize distance score (closer = higher score)
            max_distance = demand.max_distance_km
            if distance <= max_distance:
                distance_score = 1.0 - (distance / max_distance)
                score += Decimal(str(distance_score * 0.2))
        
        return min(score, Decimal("1.0"))
    
    async def _check_timeline_compatibility(
        self,
        demand: OffsetDemandRequest,
        supply: OffsetSupplyListing,
        criteria: MatchingCriteria
    ) -> bool:
        """Check if delivery timelines are compatible"""
        
        # Supply must be deliverable before demand requirement
        required_by = demand.required_by_date
        deliverable_by = supply.delivery_completion_date
        
        # Add buffer for timeline flexibility
        required_by_with_buffer = required_by + timedelta(
            days=criteria.timeline_buffer_months * 30
        )
        
        return deliverable_by <= required_by_with_buffer
    
    def _calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between coordinates using Haversine formula"""
        
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(dlon/2)**2)
        
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Earth's radius in kilometers
        
        return c * r
    
    async def get_match(self, match_id: str) -> Optional[OffsetMatch]:
        """Get match by ID"""
        return self._matches.get(match_id)
    
    async def accept_match(self, match_id: str) -> bool:
        """Accept a potential match"""
        
        if match_id not in self._matches:
            return False
        
        match = self._matches[match_id]
        match.match_status = "accepted"
        
        # Reserve units in supply listing
        await self.supply_manager.reserve_units(
            match.supply_listing_id,
            match.matched_units
        )
        
        # Update demand status
        await self.demand_manager.update_demand_status(
            match.demand_request_id,
            DemandStatus.MATCHED
        )
        
        return True
    
    async def reject_match(self, match_id: str, reason: Optional[str] = None) -> bool:
        """Reject a potential match"""
        
        if match_id not in self._matches:
            return False
        
        match = self._matches[match_id]
        match.match_status = "rejected"
        
        return True
    
    async def get_matches_for_demand(self, demand_request_id: str) -> List[OffsetMatch]:
        """Get all matches for a specific demand request"""
        
        matches = [
            match for match in self._matches.values()
            if match.demand_request_id == demand_request_id
        ]
        
        # Sort by match score
        matches.sort(key=lambda x: x.overall_match_score or 0, reverse=True)
        
        return matches
    
    async def get_matches_for_supply(self, supply_listing_id: str) -> List[OffsetMatch]:
        """Get all matches for a specific supply listing"""
        
        matches = [
            match for match in self._matches.values()
            if match.supply_listing_id == supply_listing_id
        ]
        
        # Sort by match score
        matches.sort(key=lambda x: x.overall_match_score or 0, reverse=True)
        
        return matches
    
    async def get_matching_statistics(self) -> Dict[str, Any]:
        """Get matching engine statistics"""
        
        all_matches = list(self._matches.values())
        
        if not all_matches:
            return {
                'total_matches': 0,
                'average_match_score': 0,
                'accepted_matches': 0,
                'rejected_matches': 0,
                'pending_matches': 0
            }
        
        # Calculate statistics
        total_matches = len(all_matches)
        average_score = sum(match.overall_match_score or 0 for match in all_matches) / total_matches
        
        status_counts = {}
        for match in all_matches:
            status = match.match_status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Distance statistics
        distances = [float(match.distance_km) for match in all_matches if match.distance_km]
        
        return {
            'total_matches': total_matches,
            'average_match_score': round(float(average_score), 3),
            'accepted_matches': status_counts.get('accepted', 0),
            'rejected_matches': status_counts.get('rejected', 0),
            'pending_matches': status_counts.get('potential', 0),
            'distance_statistics': {
                'average_km': round(sum(distances) / len(distances), 1) if distances else 0,
                'min_km': round(min(distances), 1) if distances else 0,
                'max_km': round(max(distances), 1) if distances else 0
            },
            'habitat_match_statistics': await self._calculate_habitat_match_stats(all_matches)
        }
    
    async def _calculate_habitat_match_stats(self, matches: List[OffsetMatch]) -> Dict[str, Any]:
        """Calculate habitat matching statistics"""
        
        if not matches:
            return {'average_habitat_score': 0, 'high_quality_matches': 0}
        
        habitat_scores = [float(match.habitat_type_match_score) for match in matches]
        average_habitat_score = sum(habitat_scores) / len(habitat_scores)
        high_quality_matches = sum(1 for score in habitat_scores if score > 0.8)
        
        return {
            'average_habitat_score': round(average_habitat_score, 3),
            'high_quality_matches': high_quality_matches,
            'high_quality_percentage': round((high_quality_matches / len(matches)) * 100, 1)
        }
    
    # Advanced matching features
    
    async def find_optimal_match_combination(
        self,
        demand_request_id: str,
        max_suppliers: int = 3
    ) -> List[OffsetMatch]:
        """
        Find optimal combination of suppliers to meet demand requirements
        
        This is useful when no single supplier can meet all requirements,
        but a combination of suppliers can provide an optimal solution.
        """
        
        demand = await self.demand_manager.get_demand_request(demand_request_id)
        if not demand:
            return []
        
        # Find all potential matches
        all_matches = await self.find_matches(demand_request_id=demand_request_id, max_matches=100)
        
        # Use greedy algorithm to find optimal combination
        selected_matches = []
        remaining_units = demand.required_units
        used_suppliers = set()
        
        # Sort matches by efficiency (match score per unit)
        efficiency_sorted_matches = sorted(
            all_matches,
            key=lambda m: (m.overall_match_score or 0) / float(m.matched_units),
            reverse=True
        )
        
        for match in efficiency_sorted_matches:
            
            # Skip if we've already used this supplier
            if match.supply_listing_id in used_suppliers:
                continue
            
            # Skip if we don't need more units
            if remaining_units <= 0:
                break
            
            # Skip if we've reached max suppliers
            if len(selected_matches) >= max_suppliers:
                break
            
            # Adjust matched units if we don't need the full amount
            if match.matched_units > remaining_units:
                match.matched_units = remaining_units
                match.total_value = match.matched_units * match.unit_price
            
            selected_matches.append(match)
            remaining_units -= match.matched_units
            used_suppliers.add(match.supply_listing_id)
        
        return selected_matches
    
    async def suggest_price_adjustment(
        self,
        supply_listing_id: str,
        target_match_score: float = 0.7
    ) -> Optional[Dict[str, Any]]:
        """
        Suggest price adjustments to improve matching potential
        """
        
        supply = await self.supply_manager.get_listing(supply_listing_id)
        if not supply:
            return None
        
        # Find current matches
        current_matches = await self.get_matches_for_supply(supply_listing_id)
        
        if not current_matches:
            return {
                'suggestion': 'reduce_price',
                'current_price': float(supply.price_per_unit),
                'suggested_price': float(supply.price_per_unit * Decimal("0.9")),
                'reason': 'No current matches found - consider reducing price by 10%'
            }
        
        # Calculate average match score
        avg_score = sum(match.overall_match_score or 0 for match in current_matches) / len(current_matches)
        
        if avg_score < target_match_score:
            # Suggest price reduction
            reduction_factor = (target_match_score - avg_score) / target_match_score
            suggested_price = supply.price_per_unit * (1 - Decimal(str(reduction_factor * 0.2)))
            
            return {
                'suggestion': 'reduce_price',
                'current_price': float(supply.price_per_unit),
                'suggested_price': float(suggested_price),
                'current_avg_match_score': round(float(avg_score), 3),
                'target_match_score': target_match_score,
                'reason': f'Average match score ({avg_score:.3f}) below target ({target_match_score})'
            }
        
        return {
            'suggestion': 'maintain_price',
            'current_price': float(supply.price_per_unit),
            'current_avg_match_score': round(float(avg_score), 3),
            'reason': 'Current pricing appears optimal for match quality'
        }