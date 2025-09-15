"""Core engine for emergency airport finding and matching."""

import math
import logging
from typing import List, Union, Optional

from ..data.models import (
    Airport, AircraftSpecs, AirportRecommendation, 
    Coordinates
)
from ..data.database import DatabaseManager

logger = logging.getLogger(__name__)


class DistanceCalculator:
    """Handles distance and bearing calculations using great circle formulas."""
    
    @staticmethod
    def great_circle_distance(coord1: Coordinates, coord2: Coordinates) -> float:
        """Calculate great circle distance between two points in nautical miles."""
        # Convert to radians
        lat1, lon1 = math.radians(coord1.latitude), math.radians(coord1.longitude)
        lat2, lon2 = math.radians(coord2.latitude), math.radians(coord2.longitude)
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in nautical miles
        earth_radius_nm = 3440.065
        
        return earth_radius_nm * c
    
    @staticmethod
    def calculate_bearing(from_coord: Coordinates, to_coord: Coordinates) -> float:
        """Calculate bearing from one coordinate to another in degrees."""
        lat1, lon1 = math.radians(from_coord.latitude), math.radians(from_coord.longitude)
        lat2, lon2 = math.radians(to_coord.latitude), math.radians(to_coord.longitude)
        
        dlon = lon2 - lon1
        
        y = math.sin(dlon) * math.cos(lat2)
        x = (math.cos(lat1) * math.sin(lat2) - 
             math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
        
        bearing = math.atan2(y, x)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360  # Normalize to 0-360
        
        return bearing


class AirportMatcher:
    """Handles airport compatibility checking and filtering."""
    
    @staticmethod
    def validate_compatibility(airport: Airport, aircraft: AircraftSpecs) -> tuple[bool, List[str]]:
        """Check if airport is compatible with aircraft. Returns (compatible, warnings)."""
        warnings = []
        compatible = True
        
        # Check runway length
        if airport.longest_runway_ft < aircraft.min_runway_length_ft:
            compatible = False
            warnings.append(
                f"Runway too short: {airport.longest_runway_ft}ft < {aircraft.min_runway_length_ft}ft required"
            )
        
        # Check runway width (with 5ft tolerance for measurement variations)
        width_tolerance = 5
        if (airport.runway_width_ft and 
            airport.runway_width_ft < (aircraft.min_runway_width_ft - width_tolerance)):
            compatible = False
            warnings.append(
                f"Runway too narrow: {airport.runway_width_ft}ft < {aircraft.min_runway_width_ft}ft required"
            )
        
        # Check weight capacity if available
        if (airport.weight_capacity_lbs and 
            aircraft.max_weight_lbs > airport.weight_capacity_lbs):
            warnings.append(
                f"Weight capacity may be exceeded: {aircraft.max_weight_lbs}lbs > {airport.weight_capacity_lbs}lbs"
            )
        
        # Check surface type
        if airport.surface_type.lower() in ['grass', 'dirt', 'gravel']:
            if aircraft.category in ['heavy', 'super']:
                warnings.append(
                    f"Soft surface ({airport.surface_type}) may not be suitable for {aircraft.category} aircraft"
                )
        
        return compatible, warnings
    
    @staticmethod
    def calculate_compatibility_score(airport: Airport, aircraft: AircraftSpecs) -> float:
        """Calculate compatibility score (0-1) based on how well airport matches aircraft."""
        score = 1.0
        
        # Runway length score (more is better, up to 150% of requirement)
        length_ratio = airport.longest_runway_ft / aircraft.min_runway_length_ft
        if length_ratio < 1.0:
            score *= length_ratio  # Penalty for insufficient length
        elif length_ratio > 1.5:
            score *= 1.0  # No bonus beyond 150%
        else:
            score *= (0.8 + 0.2 * (length_ratio - 1.0) / 0.5)  # Bonus for extra length
        
        # Surface type score
        surface_scores = {
            'asphalt': 1.0, 'concrete': 1.0, 'paved': 1.0,
            'grass': 0.7, 'gravel': 0.6, 'dirt': 0.5, 'unknown': 0.8
        }
        surface_score = surface_scores.get(airport.surface_type.lower(), 0.8)
        score *= surface_score
        
        return min(score, 1.0)


class LocationResolver:
    """Handles location input resolution to coordinates."""
    
    def __init__(self):
        """Initialize with geocoding capability."""
        from ..integrations.geocoding_client import GeocodingClient
        self.geocoding_client = GeocodingClient()
    
    def resolve_location(self, location: Union[Coordinates, str]) -> Coordinates:
        """Resolve location input to coordinates."""
        if isinstance(location, Coordinates):
            return location
        
        if isinstance(location, str):
            location = location.strip()
            
            # Try to parse "lat,lon" format first
            try:
                parts = location.split(',')
                if len(parts) == 2:
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
                    return Coordinates(lat, lon)
            except ValueError:
                pass
            
            # Try geocoding for city names, postal codes, addresses
            try:
                coords = self.geocoding_client.geocode(location)
                if coords:
                    return coords
                else:
                    raise ValueError(f"Could not geocode location: {location}")
            except Exception as e:
                logger.error(f"Geocoding failed for '{location}': {e}")
                raise ValueError(f"Cannot resolve location '{location}': {e}")
        
        raise ValueError(f"Invalid location type: {type(location)}")


class EmergencyAirportFinder:
    """Main service class for finding emergency airports."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize with database manager."""
        self.db = db_manager
        self.location_resolver = LocationResolver()
        self.distance_calc = DistanceCalculator()
        self.airport_matcher = AirportMatcher()
    
    def find_emergency_airports(
        self, 
        location: Union[Coordinates, str], 
        aircraft_type: str,
        max_distance_nm: int = 100
    ) -> List[AirportRecommendation]:
        """Find suitable emergency airports for given location and aircraft."""
        try:
            # Resolve location to coordinates
            coords = self.location_resolver.resolve_location(location)
            
            # Get aircraft specifications
            aircraft_specs = self.db.get_aircraft_specs(aircraft_type)
            if not aircraft_specs:
                raise ValueError(f"Unknown aircraft type: {aircraft_type}")
            
            # Get nearby airports
            nearby_airports = self.db.get_airports_within_radius(coords, max_distance_nm)
            
            recommendations = []
            
            for airport in nearby_airports:
                # Calculate distance and bearing
                distance = self.distance_calc.great_circle_distance(coords, airport.coordinates)
                bearing = self.distance_calc.calculate_bearing(coords, airport.coordinates)
                
                # Check compatibility
                compatible, warnings = self.airport_matcher.validate_compatibility(
                    airport, aircraft_specs
                )
                
                # Calculate compatibility score
                score = self.airport_matcher.calculate_compatibility_score(
                    airport, aircraft_specs
                )
                
                # Estimate flight time (rough calculation)
                # Assume average speed based on aircraft category
                speed_kts = {
                    'light': 120, 'medium': 200, 'heavy': 250, 'super': 280
                }.get(aircraft_specs.category, 180)
                
                flight_time = int((distance / speed_kts) * 60) if distance > 0 else 0
                
                recommendation = AirportRecommendation(
                    airport=airport,
                    distance_nm=distance,
                    bearing_degrees=bearing,
                    compatibility_score=score,
                    warnings=warnings,
                    estimated_flight_time_minutes=flight_time
                )
                
                recommendations.append(recommendation)
            
            # Sort by distance, but prioritize compatible airports
            recommendations.sort(key=lambda r: (
                0 if len(r.warnings) == 0 else 1,  # Compatible first
                r.distance_nm  # Then by distance
            ))
            
            # If no suitable airports found within radius, expand search
            if not any(len(r.warnings) == 0 for r in recommendations):
                logger.warning(f"No suitable airports found within {max_distance_nm}nm, expanding search")
                if max_distance_nm < 200:
                    return self.find_emergency_airports(location, aircraft_type, max_distance_nm * 2)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error finding emergency airports: {e}")
            raise
    
    def get_aircraft_requirements(self, aircraft_type: str) -> Optional[AircraftSpecs]:
        """Get aircraft specifications for given type."""
        return self.db.get_aircraft_specs(aircraft_type)
    
    def get_supported_aircraft_types(self) -> List[str]:
        """Get list of all supported aircraft types."""
        return self.db.get_all_aircraft_types()