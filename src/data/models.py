"""Data models for the Emergency Airport Finder system."""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class Coordinates:
    """Geographic coordinates."""
    latitude: float
    longitude: float
    
    def __post_init__(self):
        """Validate coordinates are within valid ranges."""
        if not -90 <= self.latitude <= 90:
            raise ValueError(f"Invalid latitude: {self.latitude}")
        if not -180 <= self.longitude <= 180:
            raise ValueError(f"Invalid longitude: {self.longitude}")


@dataclass
class Airport:
    """Airport information and specifications."""
    icao_code: str
    name: str
    coordinates: Coordinates
    elevation_ft: int
    longest_runway_ft: int
    runway_width_ft: int
    surface_type: str
    weight_capacity_lbs: Optional[int] = None
    contact_info: Optional[str] = None
    last_updated: Optional[datetime] = None


@dataclass
class AircraftSpecs:
    """Aircraft specifications and runway requirements."""
    aircraft_type: str
    min_runway_length_ft: int
    min_runway_width_ft: int
    max_weight_lbs: int
    approach_speed_kts: int
    category: str  # "light", "medium", "heavy", "super"


@dataclass
class AirportRecommendation:
    """Airport recommendation with distance and compatibility info."""
    airport: Airport
    distance_nm: float
    bearing_degrees: float
    compatibility_score: float
    warnings: List[str]
    estimated_flight_time_minutes: Optional[int] = None


@dataclass
class ErrorResponse:
    """Standardized error response format."""
    error_code: str
    message: str
    details: Optional[dict] = None
    suggestions: List[str] = None