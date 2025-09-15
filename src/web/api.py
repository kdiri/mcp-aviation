"""API routes for the Emergency Airport Finder web interface."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Union, Optional
import logging

logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    """Request model for airport search."""
    location: str
    aircraft_type: str
    max_distance_nm: int = 100


class AirportResponse(BaseModel):
    """Response model for airport information."""
    icao_code: str
    name: str
    coordinates: dict
    elevation_ft: int
    longest_runway_ft: int
    runway_width_ft: int
    surface_type: str


class RecommendationResponse(BaseModel):
    """Response model for airport recommendations."""
    airport: AirportResponse
    distance_nm: float
    bearing_degrees: float
    compatibility_score: float
    warnings: List[str]
    estimated_flight_time_minutes: Optional[int]


class SearchResponse(BaseModel):
    """Response model for search results."""
    recommendations: List[RecommendationResponse]
    search_location: dict
    aircraft_type: str
    total_found: int


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    details: Optional[dict] = None


def create_api_router() -> APIRouter:
    """Create and configure the API router."""
    router = APIRouter()
    
    @router.post("/search", response_model=Union[SearchResponse, ErrorResponse])
    async def search_airports(request: SearchRequest, app_request: Request):
        """Search for emergency airports based on location and aircraft type."""
        try:
            airport_finder = app_request.app.state.airport_finder
            
            # Find emergency airports
            recommendations = airport_finder.find_emergency_airports(
                location=request.location,
                aircraft_type=request.aircraft_type,
                max_distance_nm=request.max_distance_nm
            )
            
            # Convert to response format
            response_recommendations = []
            for rec in recommendations:
                airport_response = AirportResponse(
                    icao_code=rec.airport.icao_code,
                    name=rec.airport.name,
                    coordinates={
                        "latitude": rec.airport.coordinates.latitude,
                        "longitude": rec.airport.coordinates.longitude
                    },
                    elevation_ft=rec.airport.elevation_ft,
                    longest_runway_ft=rec.airport.longest_runway_ft,
                    runway_width_ft=rec.airport.runway_width_ft,
                    surface_type=rec.airport.surface_type
                )
                
                recommendation_response = RecommendationResponse(
                    airport=airport_response,
                    distance_nm=rec.distance_nm,
                    bearing_degrees=rec.bearing_degrees,
                    compatibility_score=rec.compatibility_score,
                    warnings=rec.warnings,
                    estimated_flight_time_minutes=rec.estimated_flight_time_minutes
                )
                
                response_recommendations.append(recommendation_response)
            
            # Get the resolved coordinates for response
            location_resolver = airport_finder.location_resolver
            resolved_coords = location_resolver.resolve_location(request.location)
            search_location = {
                "latitude": resolved_coords.latitude,
                "longitude": resolved_coords.longitude,
                "original_input": request.location
            }
            
            return SearchResponse(
                recommendations=response_recommendations,
                search_location=search_location,
                aircraft_type=request.aircraft_type,
                total_found=len(response_recommendations)
            )
            
        except ValueError as e:
            logger.warning(f"Invalid search request: {e}")
            return ErrorResponse(
                error="invalid_request",
                message=str(e),
                details={"location": request.location, "aircraft_type": request.aircraft_type}
            )
        except Exception as e:
            logger.error(f"Search error: {e}")
            return ErrorResponse(
                error="search_failed",
                message="Failed to search for airports",
                details={"error": str(e)}
            )
    
    @router.get("/aircraft")
    async def get_aircraft_types(app_request: Request):
        """Get list of supported aircraft types."""
        try:
            airport_finder = app_request.app.state.airport_finder
            aircraft_types = airport_finder.get_supported_aircraft_types()
            
            return {
                "aircraft_types": aircraft_types,
                "total_count": len(aircraft_types)
            }
            
        except Exception as e:
            logger.error(f"Failed to get aircraft types: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve aircraft types")
    
    @router.get("/status")
    async def get_system_status(app_request: Request):
        """Get system status and data information."""
        try:
            data_fetcher = app_request.app.state.data_fetcher
            status = data_fetcher.get_data_status()
            
            return {
                "status": "operational",
                "data": status,
                "version": "0.1.0"
            }
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve system status")
    
    @router.get("/airport/{icao_code}")
    async def get_airport_details(icao_code: str, app_request: Request):
        """Get detailed information about a specific airport."""
        try:
            db_manager = app_request.app.state.db_manager
            
            # Query airport from database
            result = db_manager.conn.execute("""
                SELECT icao_code, name, latitude, longitude, elevation_ft,
                       longest_runway_ft, runway_width_ft, surface_type,
                       weight_capacity_lbs, contact_info, last_updated
                FROM airports
                WHERE icao_code = ?
            """, (icao_code.upper(),)).fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail=f"Airport {icao_code} not found")
            
            airport_data = {
                "icao_code": result[0],
                "name": result[1],
                "coordinates": {
                    "latitude": result[2],
                    "longitude": result[3]
                },
                "elevation_ft": result[4],
                "longest_runway_ft": result[5],
                "runway_width_ft": result[6],
                "surface_type": result[7],
                "weight_capacity_lbs": result[8],
                "contact_info": result[9],
                "last_updated": result[10]
            }
            
            return airport_data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get airport details for {icao_code}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve airport details")
    
    return router