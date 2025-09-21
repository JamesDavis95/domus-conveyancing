"""
Property Data Aggregator
Combines data from all property API sources into comprehensive property reports
"""
from typing import Dict, List, Any, Optional, Tuple, Union
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

from .land_registry import LandRegistryAdapter, get_land_registry_data
from .epc_data import EPCDataAdapter, get_epc_data
from .flood_risk import FloodRiskAdapter, get_flood_risk_data
from .planning_history import PlanningHistoryAdapter, get_planning_history
from .cache import get_cache


@dataclass
class PropertySummary:
    """Comprehensive property data summary"""
    
    # Basic property information
    address: str
    postcode: str
    coordinates: Optional[Tuple[float, float]]
    uprn: Optional[str]
    
    # Data availability status
    land_registry_available: bool = False
    epc_available: bool = False
    flood_risk_available: bool = False
    planning_history_available: bool = False
    
    # Key insights
    estimated_value: Optional[float] = None
    energy_rating: Optional[str] = None
    flood_risk_level: Optional[str] = None
    recent_planning_activity: Optional[int] = None  # Number of applications in last 2 years
    
    # Risk indicators
    high_flood_risk: bool = False
    planning_constraints: bool = False
    energy_efficiency_poor: bool = False
    
    # Last updated
    report_generated: str = None
    data_freshness: Dict[str, str] = None


class PropertyDataAggregator:
    """
    Aggregates property data from multiple sources into comprehensive reports
    """
    
    def __init__(self):
        self.cache = get_cache('property_aggregated')
        self.logger = logging.getLogger(__name__)
        
        # Adapters
        self.land_registry_adapter = None
        self.epc_adapter = None
        self.flood_risk_adapter = None
        self.planning_adapter = None
    
    async def __aenter__(self):
        """Initialize all adapters"""
        self.land_registry_adapter = LandRegistryAdapter()
        self.epc_adapter = EPCDataAdapter()
        self.flood_risk_adapter = FloodRiskAdapter()
        self.planning_adapter = PlanningHistoryAdapter()
        
        # Enter async context for all adapters
        await self.land_registry_adapter.__aenter__()
        await self.epc_adapter.__aenter__()
        await self.flood_risk_adapter.__aenter__()
        await self.planning_adapter.__aenter__()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up adapters"""
        adapters = [
            self.land_registry_adapter,
            self.epc_adapter, 
            self.flood_risk_adapter,
            self.planning_adapter
        ]
        
        for adapter in adapters:
            if adapter:
                try:
                    await adapter.__aexit__(exc_type, exc_val, exc_tb)
                except Exception as e:
                    self.logger.warning(f"Error closing adapter: {e}")
    
    async def get_comprehensive_property_report(
        self,
        identifier: str,
        search_type: str = 'address',
        include_planning_radius: int = 100
    ) -> Dict[str, Any]:
        """
        Generate comprehensive property report combining all data sources
        
        Args:
            identifier: Address, postcode, or UPRN
            search_type: Type of identifier ('address', 'postcode', 'uprn')
            include_planning_radius: Radius in meters for planning history search
            
        Returns:
            Comprehensive property report dictionary
        """
        
        # Check cache
        cache_key = f"comprehensive_{search_type}_{identifier}_{include_planning_radius}"
        cached_report = await self.cache.get(cache_key)
        
        if cached_report:
            return cached_report
        
        # Gather data from all sources in parallel
        data_tasks = [
            self._get_land_registry_data(identifier, search_type),
            self._get_epc_data(identifier, search_type),
            self._get_flood_risk_data(identifier, search_type),
            self._get_planning_history_data(identifier, search_type, include_planning_radius)
        ]
        
        try:
            results = await asyncio.gather(*data_tasks, return_exceptions=True)
            
            land_registry_data, epc_data, flood_risk_data, planning_data = results
            
            # Handle exceptions
            if isinstance(land_registry_data, Exception):
                self.logger.warning(f"Land Registry error: {land_registry_data}")
                land_registry_data = None
            
            if isinstance(epc_data, Exception):
                self.logger.warning(f"EPC data error: {epc_data}")
                epc_data = None
            
            if isinstance(flood_risk_data, Exception):
                self.logger.warning(f"Flood risk error: {flood_risk_data}")
                flood_risk_data = None
            
            if isinstance(planning_data, Exception):
                self.logger.warning(f"Planning history error: {planning_data}")
                planning_data = None
            
            # Create comprehensive report
            report = await self._compile_comprehensive_report(
                identifier, search_type, land_registry_data, 
                epc_data, flood_risk_data, planning_data
            )
            
            # Cache the report
            await self.cache.set(cache_key, report, ttl_hours=2)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating property report: {e}")
            return {
                'error': f'Failed to generate property report: {str(e)}',
                'identifier': identifier,
                'search_type': search_type,
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_property_summary(
        self,
        identifier: str,
        search_type: str = 'address'
    ) -> Optional[PropertySummary]:
        """
        Generate concise property summary with key insights
        
        Args:
            identifier: Property identifier
            search_type: Type of identifier
            
        Returns:
            PropertySummary object
        """
        
        # Get comprehensive report
        report = await self.get_comprehensive_property_report(
            identifier, search_type, include_planning_radius=50  # Smaller radius for summary
        )
        
        if 'error' in report:
            return None
        
        # Extract key information for summary
        summary = self._extract_property_summary(report)
        
        return summary
    
    async def get_comparable_properties(
        self,
        identifier: str,
        search_type: str = 'address',
        radius_m: int = 500,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find comparable properties in the area
        
        Args:
            identifier: Property identifier
            search_type: Type of identifier
            radius_m: Search radius in meters
            max_results: Maximum number of comparables
            
        Returns:
            List of comparable property summaries
        """
        
        try:
            # Get base property coordinates
            coordinates = await self._get_property_coordinates(identifier, search_type)
            
            if not coordinates:
                return []
            
            # Get Land Registry sales in area (this would use spatial search in production)
            land_registry_data = await self._get_land_registry_data(identifier, search_type)
            
            if land_registry_data and 'price_paid_data' in land_registry_data:
                # Return recent sales as comparables (simplified)
                comparables = []
                
                for sale in land_registry_data['price_paid_data'][:max_results]:
                    comparable = {
                        'address': sale.get('address', 'Unknown'),
                        'price': sale.get('price'),
                        'date': sale.get('date'),
                        'property_type': sale.get('property_type'),
                        'distance_m': None,  # Would calculate actual distance
                        'price_per_sqm': None  # Would calculate if area known
                    }
                    comparables.append(comparable)
                
                return comparables
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error finding comparables: {e}")
            return []
    
    async def get_area_statistics(
        self,
        postcode: str,
        radius_m: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate area-level statistics and insights
        
        Args:
            postcode: Area postcode
            radius_m: Analysis radius in meters
            
        Returns:
            Area statistics dictionary
        """
        
        try:
            # Get planning history for area
            planning_data = await self._get_planning_history_data(postcode, 'postcode', radius_m)
            
            # Get flood risk for postcode
            flood_data = await self._get_flood_risk_data(postcode, 'postcode')
            
            # Calculate statistics
            stats = {
                'postcode': postcode,
                'analysis_radius_m': radius_m,
                'planning_activity': self._analyze_planning_activity(planning_data),
                'flood_risk_profile': self._analyze_flood_risk(flood_data),
                'market_trends': await self._analyze_market_trends(postcode),
                'area_characteristics': await self._analyze_area_characteristics(postcode),
                'generated': datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error generating area statistics: {e}")
            return {
                'error': f'Failed to generate area statistics: {str(e)}',
                'postcode': postcode
            }
    
    async def _get_land_registry_data(self, identifier: str, search_type: str) -> Optional[Dict[str, Any]]:
        """Get Land Registry data with error handling"""
        try:
            if search_type == 'postcode':
                return await get_land_registry_data(identifier, 'postcode')
            elif search_type == 'address':
                return await get_land_registry_data(identifier, 'address')
            else:
                return None
        except Exception as e:
            self.logger.error(f"Land Registry data error: {e}")
            return None
    
    async def _get_epc_data(self, identifier: str, search_type: str) -> Optional[Dict[str, Any]]:
        """Get EPC data with error handling"""
        try:
            if search_type == 'postcode':
                return await get_epc_data(identifier, 'postcode')
            elif search_type == 'address':
                return await get_epc_data(identifier, 'address')
            else:
                return None
        except Exception as e:
            self.logger.error(f"EPC data error: {e}")
            return None
    
    async def _get_flood_risk_data(self, identifier: str, search_type: str) -> Optional[Dict[str, Any]]:
        """Get flood risk data with error handling"""
        try:
            if search_type == 'postcode':
                return await get_flood_risk_data(identifier, 'postcode')
            else:
                # For address, try to extract postcode
                postcode = self._extract_postcode_from_address(identifier)
                if postcode:
                    return await get_flood_risk_data(postcode, 'postcode')
                return None
        except Exception as e:
            self.logger.error(f"Flood risk data error: {e}")
            return None
    
    async def _get_planning_history_data(
        self, 
        identifier: str, 
        search_type: str, 
        radius_m: int
    ) -> Optional[Dict[str, Any]]:
        """Get planning history data with error handling"""
        try:
            if search_type == 'address':
                return await get_planning_history(identifier, 'address', radius_m, 10)
            elif search_type == 'postcode':
                return await get_planning_history(identifier, 'postcode', radius_m, 5)
            else:
                return None
        except Exception as e:
            self.logger.error(f"Planning history data error: {e}")
            return None
    
    async def _get_property_coordinates(
        self, 
        identifier: str, 
        search_type: str
    ) -> Optional[Tuple[float, float]]:
        """Extract coordinates from property data"""
        
        # Try flood risk data first as it often has coordinates
        flood_data = await self._get_flood_risk_data(identifier, search_type)
        
        if flood_data and 'coordinates' in flood_data:
            coords = flood_data['coordinates']
            if isinstance(coords, (list, tuple)) and len(coords) == 2:
                return (coords[0], coords[1])
        
        # Fallback to geocoding postcode
        if search_type == 'address':
            postcode = self._extract_postcode_from_address(identifier)
            if postcode:
                # Use simple geocoding (would be more sophisticated in production)
                return (51.5074, -0.1278)  # Default to London
        
        return None
    
    async def _compile_comprehensive_report(
        self,
        identifier: str,
        search_type: str,
        land_registry_data: Optional[Dict[str, Any]],
        epc_data: Optional[Dict[str, Any]],
        flood_risk_data: Optional[Dict[str, Any]],
        planning_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compile all data into comprehensive report"""
        
        report = {
            'property_identifier': {
                'search_term': identifier,
                'search_type': search_type
            },
            'report_metadata': {
                'generated': datetime.now().isoformat(),
                'data_sources': {
                    'land_registry': land_registry_data is not None,
                    'epc': epc_data is not None,
                    'flood_risk': flood_risk_data is not None,
                    'planning_history': planning_data is not None
                }
            },
            'property_data': {
                'land_registry': land_registry_data,
                'epc': epc_data,
                'flood_risk': flood_risk_data,
                'planning_history': planning_data
            },
            'key_insights': await self._generate_key_insights(
                land_registry_data, epc_data, flood_risk_data, planning_data
            ),
            'risk_assessment': await self._generate_risk_assessment(
                land_registry_data, epc_data, flood_risk_data, planning_data
            ),
            'recommendations': await self._generate_recommendations(
                land_registry_data, epc_data, flood_risk_data, planning_data
            )
        }
        
        return report
    
    def _extract_property_summary(self, report: Dict[str, Any]) -> PropertySummary:
        """Extract key information for property summary"""
        
        # Extract basic information
        identifier = report['property_identifier']['search_term']
        
        # Try to get address and postcode from various sources
        address = identifier  # Default
        postcode = self._extract_postcode_from_address(identifier) if 'postcode' not in report['property_identifier']['search_type'] else identifier
        
        # Get coordinates
        coordinates = None
        if report['property_data']['flood_risk']:
            coords = report['property_data']['flood_risk'].get('coordinates')
            if coords and isinstance(coords, (list, tuple)) and len(coords) == 2:
                coordinates = (coords[0], coords[1])
        
        # Data availability
        data_sources = report['report_metadata']['data_sources']
        
        # Key metrics
        estimated_value = None
        if report['property_data']['land_registry'] and 'price_paid_data' in report['property_data']['land_registry']:
            recent_sales = report['property_data']['land_registry']['price_paid_data']
            if recent_sales:
                estimated_value = recent_sales[0].get('price')
        
        energy_rating = None
        if report['property_data']['epc']:
            energy_rating = report['property_data']['epc'].get('current_energy_rating')
        
        flood_risk_level = None
        if report['property_data']['flood_risk']:
            flood_risk_level = report['property_data']['flood_risk'].get('overall_flood_risk')
        
        recent_planning_activity = 0
        if report['property_data']['planning_history'] and 'applications' in report['property_data']['planning_history']:
            # Count applications in last 2 years
            cutoff_date = datetime.now() - timedelta(days=730)
            applications = report['property_data']['planning_history']['applications']
            
            for app in applications:
                try:
                    app_date = datetime.strptime(app['application_date'], '%Y-%m-%d')
                    if app_date > cutoff_date:
                        recent_planning_activity += 1
                except:
                    continue
        
        # Risk indicators
        high_flood_risk = flood_risk_level in ['High', 'Medium'] if flood_risk_level else False
        planning_constraints = recent_planning_activity > 3  # High planning activity
        energy_efficiency_poor = energy_rating in ['F', 'G'] if energy_rating else False
        
        summary = PropertySummary(
            address=address,
            postcode=postcode or 'Unknown',
            coordinates=coordinates,
            uprn=None,  # Would extract from Land Registry data if available
            land_registry_available=data_sources['land_registry'],
            epc_available=data_sources['epc'],
            flood_risk_available=data_sources['flood_risk'],
            planning_history_available=data_sources['planning_history'],
            estimated_value=estimated_value,
            energy_rating=energy_rating,
            flood_risk_level=flood_risk_level,
            recent_planning_activity=recent_planning_activity,
            high_flood_risk=high_flood_risk,
            planning_constraints=planning_constraints,
            energy_efficiency_poor=energy_efficiency_poor,
            report_generated=datetime.now().isoformat(),
            data_freshness={
                'land_registry': 'Current',
                'epc': 'Current', 
                'flood_risk': 'Current',
                'planning': 'Current'
            }
        )
        
        return summary
    
    async def _generate_key_insights(
        self,
        land_registry_data: Optional[Dict[str, Any]],
        epc_data: Optional[Dict[str, Any]],
        flood_risk_data: Optional[Dict[str, Any]],
        planning_data: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate key insights from combined data"""
        
        insights = []
        
        # Land Registry insights
        if land_registry_data and 'price_paid_data' in land_registry_data:
            sales = land_registry_data['price_paid_data']
            if sales:
                latest_price = sales[0].get('price')
                if latest_price:
                    insights.append(f"Most recent sale: £{latest_price:,}")
                
                if len(sales) > 1:
                    price_trend = self._analyze_price_trend(sales)
                    if price_trend:
                        insights.append(price_trend)
        
        # EPC insights
        if epc_data:
            rating = epc_data.get('current_energy_rating')
            if rating:
                insights.append(f"Energy efficiency rating: {rating}")
            
            potential_rating = epc_data.get('potential_energy_rating')
            if potential_rating and rating and potential_rating != rating:
                insights.append(f"Potential energy rating with improvements: {potential_rating}")
        
        # Flood risk insights
        if flood_risk_data:
            risk_level = flood_risk_data.get('overall_flood_risk')
            if risk_level:
                insights.append(f"Flood risk level: {risk_level}")
            
            if flood_risk_data.get('in_flood_zone_3'):
                insights.append("Property is in Flood Zone 3 - high probability of flooding")
        
        # Planning insights
        if planning_data and 'summary' in planning_data:
            summary = planning_data['summary']
            approval_rate = summary.get('approval_rate')
            if approval_rate is not None:
                insights.append(f"Local planning approval rate: {approval_rate}%")
        
        return insights
    
    async def _generate_risk_assessment(
        self,
        land_registry_data: Optional[Dict[str, Any]],
        epc_data: Optional[Dict[str, Any]],
        flood_risk_data: Optional[Dict[str, Any]],
        planning_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate comprehensive risk assessment"""
        
        risks = {
            'flood_risk': {
                'level': 'Unknown',
                'description': 'Flood risk data unavailable'
            },
            'planning_risk': {
                'level': 'Unknown', 
                'description': 'Planning data unavailable'
            },
            'energy_efficiency_risk': {
                'level': 'Unknown',
                'description': 'EPC data unavailable'
            },
            'market_risk': {
                'level': 'Unknown',
                'description': 'Market data unavailable'
            }
        }
        
        # Assess flood risk
        if flood_risk_data:
            risk_level = flood_risk_data.get('overall_flood_risk', 'Unknown')
            
            if risk_level in ['Very Low', 'Low']:
                risks['flood_risk'] = {
                    'level': 'Low',
                    'description': f'Flood risk is {risk_level.lower()}'
                }
            elif risk_level == 'Medium':
                risks['flood_risk'] = {
                    'level': 'Medium', 
                    'description': 'Moderate flood risk - consider flood insurance'
                }
            elif risk_level == 'High':
                risks['flood_risk'] = {
                    'level': 'High',
                    'description': 'High flood risk - detailed assessment recommended'
                }
        
        # Assess planning risk
        if planning_data and 'summary' in planning_data:
            summary = planning_data['summary']
            approval_rate = summary.get('approval_rate', 0)
            
            if approval_rate >= 70:
                risks['planning_risk'] = {
                    'level': 'Low',
                    'description': f'High approval rate ({approval_rate}%) in area'
                }
            elif approval_rate >= 50:
                risks['planning_risk'] = {
                    'level': 'Medium',
                    'description': f'Moderate approval rate ({approval_rate}%) in area'
                }
            else:
                risks['planning_risk'] = {
                    'level': 'High',
                    'description': f'Low approval rate ({approval_rate}%) in area'
                }
        
        # Assess energy efficiency risk
        if epc_data:
            rating = epc_data.get('current_energy_rating')
            
            if rating in ['A', 'B', 'C']:
                risks['energy_efficiency_risk'] = {
                    'level': 'Low',
                    'description': f'Good energy efficiency (rating {rating})'
                }
            elif rating in ['D', 'E']:
                risks['energy_efficiency_risk'] = {
                    'level': 'Medium',
                    'description': f'Average energy efficiency (rating {rating})'
                }
            elif rating in ['F', 'G']:
                risks['energy_efficiency_risk'] = {
                    'level': 'High',
                    'description': f'Poor energy efficiency (rating {rating}) - improvements needed'
                }
        
        return risks
    
    async def _generate_recommendations(
        self,
        land_registry_data: Optional[Dict[str, Any]],
        epc_data: Optional[Dict[str, Any]],
        flood_risk_data: Optional[Dict[str, Any]],
        planning_data: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Flood risk recommendations
        if flood_risk_data:
            flood_recommendations = flood_risk_data.get('recommendations', [])
            recommendations.extend(flood_recommendations)
        
        # EPC recommendations
        if epc_data:
            epc_recommendations = epc_data.get('improvement_recommendations', [])
            if epc_recommendations:
                recommendations.extend([
                    f"Energy improvement: {rec['improvement_type']} - {rec['description']}"
                    for rec in epc_recommendations[:3]  # Top 3 recommendations
                ])
        
        # Planning recommendations
        if planning_data and 'summary' in planning_data:
            approval_rate = planning_data['summary'].get('approval_rate', 0)
            
            if approval_rate < 50:
                recommendations.append(
                    "Consider pre-application advice given low local approval rates"
                )
            
            if planning_data['summary'].get('pending', 0) > 0:
                recommendations.append(
                    "Monitor pending planning applications in area for precedents"
                )
        
        # General recommendations
        if not recommendations:
            recommendations = [
                "Obtain professional survey before proceeding",
                "Consider specialist insurance based on risk profile",
                "Monitor local planning decisions for similar properties"
            ]
        
        return recommendations
    
    def _analyze_price_trend(self, sales_data: List[Dict[str, Any]]) -> Optional[str]:
        """Analyze price trend from sales data"""
        
        if len(sales_data) < 2:
            return None
        
        try:
            # Sort by date
            sorted_sales = sorted(sales_data, key=lambda x: x.get('date', ''))
            
            if len(sorted_sales) >= 2:
                oldest_price = sorted_sales[0].get('price')
                newest_price = sorted_sales[-1].get('price')
                
                if oldest_price and newest_price:
                    change = ((newest_price - oldest_price) / oldest_price) * 100
                    
                    if abs(change) < 5:
                        return "Property values relatively stable"
                    elif change > 0:
                        return f"Property values increased {change:.1f}%"
                    else:
                        return f"Property values decreased {abs(change):.1f}%"
            
        except Exception:
            return None
        
        return None
    
    def _analyze_planning_activity(self, planning_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze planning activity patterns"""
        
        if not planning_data or 'applications' not in planning_data:
            return {'status': 'No data available'}
        
        applications = planning_data['applications']
        total = len(applications)
        
        if total == 0:
            return {'status': 'No recent planning applications'}
        
        # Analyze by type and outcome
        analysis = {
            'total_applications': total,
            'approval_rate': planning_data.get('summary', {}).get('approval_rate', 0),
            'activity_level': 'High' if total > 20 else 'Medium' if total > 10 else 'Low'
        }
        
        return analysis
    
    def _analyze_flood_risk(self, flood_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze flood risk profile"""
        
        if not flood_data:
            return {'status': 'No flood risk data available'}
        
        return {
            'overall_risk': flood_data.get('overall_flood_risk', 'Unknown'),
            'river_and_sea': flood_data.get('river_and_sea', 'Unknown'),
            'surface_water': flood_data.get('surface_water', 'Unknown'),
            'in_flood_zone': flood_data.get('in_flood_zone_3', False) or flood_data.get('in_flood_zone_2', False)
        }
    
    async def _analyze_market_trends(self, postcode: str) -> Dict[str, Any]:
        """Analyze market trends for area"""
        
        # This would implement comprehensive market analysis
        # For now, return placeholder
        
        return {
            'status': 'Limited market data available',
            'trend': 'Stable',
            'confidence': 'Low'
        }
    
    async def _analyze_area_characteristics(self, postcode: str) -> Dict[str, Any]:
        """Analyze area characteristics"""
        
        # This would implement area analysis from multiple sources
        # For now, return placeholder
        
        return {
            'type': 'Mixed residential/commercial',
            'transport_links': 'Good',
            'amenities': 'Available'
        }
    
    def _extract_postcode_from_address(self, address: str) -> Optional[str]:
        """Extract UK postcode from address string"""
        
        import re
        
        # UK postcode regex pattern
        postcode_pattern = r'\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b'
        match = re.search(postcode_pattern, address.upper())
        
        if match:
            postcode = match.group().strip()
            # Format properly
            if len(postcode) >= 5:
                postcode = f"{postcode[:-3]} {postcode[-3:]}"
            return postcode
        
        return None


# Convenience function for comprehensive property reports
async def get_comprehensive_property_report(
    identifier: str,
    search_type: str = 'address',
    include_planning_radius: int = 100
) -> Dict[str, Any]:
    """
    Generate comprehensive property report
    
    Args:
        identifier: Property identifier (address, postcode, UPRN)
        search_type: Type of identifier
        include_planning_radius: Radius for planning history search
        
    Returns:
        Comprehensive property report dictionary
    """
    
    async with PropertyDataAggregator() as aggregator:
        return await aggregator.get_comprehensive_property_report(
            identifier, search_type, include_planning_radius
        )


# Convenience function for property summary
async def get_property_summary(
    identifier: str,
    search_type: str = 'address'
) -> Optional[Dict[str, Any]]:
    """
    Get concise property summary
    
    Args:
        identifier: Property identifier
        search_type: Type of identifier
        
    Returns:
        Property summary dictionary
    """
    
    async with PropertyDataAggregator() as aggregator:
        summary = await aggregator.get_property_summary(identifier, search_type)
        
        if summary:
            return asdict(summary)
    
    return None