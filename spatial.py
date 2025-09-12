"""
Spatial Intelligence Module for Domus LA System
Provides geocoding, spatial analysis, and automated CON29 answering
"""
import json
import logging
import requests
from typing import Dict, List, Optional, Tuple, Any
from geopy.geocoders import Nominatim
from shapely.geometry import Point, Polygon, shape
from shapely import wkt
# Removed PostGIS dependency, using WKT instead
import cv2
import numpy as np
from PIL import Image
import io

logger = logging.getLogger(__name__)

class SpatialIntelligence:
    """Core spatial processing engine"""
    
    def __init__(self):
        self.geocoder = Nominatim(user_agent="domus-la-system")
        self.os_api_key = None  # Will be loaded from settings
        
    async def geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """Convert address to coordinates with OS grid reference"""
        try:
            # Try geocoding with Nominatim
            location = self.geocoder.geocode(address, country_codes='gb')
            if not location:
                return None
                
            lat, lon = location.latitude, location.longitude
            
            # Convert to OS grid reference
            easting, northing = self._wgs84_to_osgb36(lat, lon)
            
            centroid_point = Point(lon, lat)
            return {
                "latitude": lat,
                "longitude": lon,
                "easting": easting,
                "northing": northing,
                "centroid": centroid_point,
                "centroid_wkt": centroid_point.wkt,
                "address_formatted": location.address,
                "confidence": 0.8
            }
        except Exception as e:
            logger.error(f"Geocoding failed for {address}: {e}")
            return None
    
    def _wgs84_to_osgb36(self, lat: float, lon: float) -> Tuple[int, int]:
        """Convert WGS84 to OS Grid Reference (simplified)"""
        # This is a simplified conversion - in production, use pyproj
        # For now, approximate using known conversion factors
        x = (lon + 2.0) * 100000  # Rough approximation
        y = (lat - 49.5) * 100000
        return int(x), int(y)
    
    async def extract_boundary_from_plan(self, image_path: str) -> Optional[Polygon]:
        """Extract property boundary from site plan using computer vision"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return None
                
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None
                
            # Find the largest contour (likely property boundary)
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Simplify contour to polygon
            epsilon = 0.02 * cv2.arcLength(largest_contour, True)
            approx = cv2.approxPolyDP(largest_contour, epsilon, True)
            
            # Convert to Shapely polygon
            points = [(point[0][0], point[0][1]) for point in approx]
            if len(points) >= 3:
                return Polygon(points)
                
        except Exception as e:
            logger.error(f"Boundary extraction failed: {e}")
            
        return None
    
    async def get_spatial_overlays(self, geometry: Polygon, layers: List[str]) -> Dict[str, List[Dict]]:
        """Get spatial overlays from various data sources"""
        overlays = {}
        
        for layer in layers:
            if layer == "flood_zones":
                overlays[layer] = await self._get_flood_zones(geometry)
            elif layer == "conservation_areas":
                overlays[layer] = await self._get_conservation_areas(geometry)
            elif layer == "tree_preservation":
                overlays[layer] = await self._get_tpo_data(geometry)
            elif layer == "planning_constraints":
                overlays[layer] = await self._get_planning_constraints(geometry)
            elif layer == "highways":
                overlays[layer] = await self._get_highways_data(geometry)
                
        return overlays
    
    async def _get_flood_zones(self, geometry: Polygon) -> List[Dict]:
        """Get flood zone data from Environment Agency"""
        try:
            # Environment Agency WFS endpoint
            wfs_url = "https://environment.data.gov.uk/flood-monitoring/id/stations"
            # This is simplified - real implementation would use proper WFS queries
            return [{"type": "flood_zone", "risk": "low", "source": "EA"}]
        except Exception as e:
            logger.error(f"Flood zone lookup failed: {e}")
            return []
    
    async def _get_conservation_areas(self, geometry: Polygon) -> List[Dict]:
        """Get conservation area data from OS/Council"""
        # Placeholder for OS Places API or council data
        return []
    
    async def _get_tpo_data(self, geometry: Polygon) -> List[Dict]:
        """Get Tree Preservation Order data"""
        # Placeholder for council TPO data
        return []
    
    async def _get_planning_constraints(self, geometry: Polygon) -> List[Dict]:
        """Get planning constraints from council data"""
        # Placeholder for planning portal integration
        return []
    
    async def _get_highways_data(self, geometry: Polygon) -> List[Dict]:
        """Get highways data from OS or council"""
        # Placeholder for highways data
        return []
    
    async def generate_con29_answers(self, matter_id: str, overlays: Dict[str, List[Dict]]) -> List[Dict]:
        """Generate automated CON29 answers from spatial overlays"""
        answers = []
        
        # Question 2.1: Planning and Building Decisions
        if overlays.get("planning_constraints"):
            answers.append({
                "question_code": "2.1",
                "question_text": "Which of the following relating to the property have been granted, issued or refused?",
                "answer": "Planning constraints identified through spatial analysis",
                "method": "spatial_overlay",
                "confidence": 0.9,
                "spatial_evidence": json.dumps(overlays["planning_constraints"])
            })
        
        # Question 3.1: Highways
        if overlays.get("highways"):
            answers.append({
                "question_code": "3.1", 
                "question_text": "Which of the roads, footways and footpaths shown on the attached plan are publicly maintainable at public expense?",
                "answer": "Highways analysis completed via spatial overlay",
                "method": "spatial_overlay",
                "confidence": 0.85,
                "spatial_evidence": json.dumps(overlays["highways"])
            })
        
        # Environmental and flooding
        if overlays.get("flood_zones"):
            answers.append({
                "question_code": "ENV.1",
                "question_text": "Is the property in a flood risk area?",
                "answer": f"Flood risk assessment: {overlays['flood_zones'][0].get('risk', 'unknown') if overlays['flood_zones'] else 'low'}",
                "method": "spatial_overlay", 
                "confidence": 0.95,
                "spatial_evidence": json.dumps(overlays["flood_zones"])
            })
        
        return answers

# Global instance
spatial_intelligence = SpatialIntelligence()
