"""MCP Server for Emergency Airport Finder - LLM Integration."""

import logging
from typing import Any, Dict

from ..core.engine import EmergencyAirportFinder
from ..data.database import DatabaseManager
from ..data.models import Coordinates

logger = logging.getLogger(__name__)


class MCPServer:
    """Model Context Protocol server for Emergency Airport Finder."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize MCP server with database manager."""
        self.db_manager = db_manager
        self.airport_finder = EmergencyAirportFinder(db_manager)
        
        # Define available tools
        self.tools = {
            "find_emergency_airports": {
                "description": "Find suitable emergency airports for aircraft at given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Location as city name, address, postal code, or coordinates (lat,lon)"
                        },
                        "aircraft_type": {
                            "type": "string",
                            "description": "Aircraft type (e.g., 'Cessna 172', 'Airbus A320', 'Boeing 737-800')"
                        },
                        "max_distance_nm": {
                            "type": "integer",
                            "description": "Maximum search radius in nautical miles (default: 100)",
                            "default": 100
                        }
                    },
                    "required": ["location", "aircraft_type"]
                }
            },
            "get_airport_details": {
                "description": "Get detailed information about a specific airport",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "icao_code": {
                            "type": "string",
                            "description": "ICAO airport code (e.g., 'KJFK', 'LFPG', 'EGLL')"
                        }
                    },
                    "required": ["icao_code"]
                }
            },
            "validate_aircraft_compatibility": {
                "description": "Check if a specific airport can accommodate a given aircraft",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "icao_code": {
                            "type": "string",
                            "description": "ICAO airport code"
                        },
                        "aircraft_type": {
                            "type": "string",
                            "description": "Aircraft type to check compatibility"
                        }
                    },
                    "required": ["icao_code", "aircraft_type"]
                }
            },
            "get_supported_aircraft": {
                "description": "List all supported aircraft types with their specifications",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    
    async def handle_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tool calls."""
        try:
            if tool_name == "find_emergency_airports":
                return await self._find_emergency_airports(parameters)
            elif tool_name == "get_airport_details":
                return await self._get_airport_details(parameters)
            elif tool_name == "validate_aircraft_compatibility":
                return await self._validate_aircraft_compatibility(parameters)
            elif tool_name == "get_supported_aircraft":
                return await self._get_supported_aircraft(parameters)
            else:
                return {
                    "error": "unknown_tool",
                    "message": f"Unknown tool: {tool_name}",
                    "available_tools": list(self.tools.keys())
                }
        except Exception as e:
            logger.error(f"Error handling tool call {tool_name}: {e}")
            return {
                "error": "tool_execution_failed",
                "message": str(e),
                "tool": tool_name
            }
    
    async def _find_emergency_airports(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find emergency airports tool implementation."""
        location = params.get("location")
        aircraft_type = params.get("aircraft_type")
        max_distance_nm = params.get("max_distance_nm", 100)
        
        if not location or not aircraft_type:
            return {
                "error": "missing_parameters",
                "message": "Both location and aircraft_type are required"
            }
        
        try:
            recommendations = self.airport_finder.find_emergency_airports(
                location=location,
                aircraft_type=aircraft_type,
                max_distance_nm=max_distance_nm
            )
            
            # Convert to serializable format
            results = []
            for rec in recommendations:
                result = {
                    "airport": {
                        "icao_code": rec.airport.icao_code,
                        "name": rec.airport.name,
                        "coordinates": {
                            "latitude": rec.airport.coordinates.latitude,
                            "longitude": rec.airport.coordinates.longitude
                        },
                        "elevation_ft": rec.airport.elevation_ft,
                        "longest_runway_ft": rec.airport.longest_runway_ft,
                        "runway_width_ft": rec.airport.runway_width_ft,
                        "surface_type": rec.airport.surface_type
                    },
                    "distance_nm": round(rec.distance_nm, 1),
                    "bearing_degrees": round(rec.bearing_degrees, 0),
                    "compatibility_score": round(rec.compatibility_score, 2),
                    "warnings": rec.warnings,
                    "estimated_flight_time_minutes": rec.estimated_flight_time_minutes,
                    "is_compatible": len(rec.warnings) == 0
                }
                results.append(result)
            
            # Resolve location for context
            resolved_coords = self.airport_finder.location_resolver.resolve_location(location)
            
            return {
                "success": True,
                "search_location": {
                    "latitude": resolved_coords.latitude,
                    "longitude": resolved_coords.longitude,
                    "original_input": location
                },
                "aircraft_type": aircraft_type,
                "max_distance_nm": max_distance_nm,
                "total_found": len(results),
                "compatible_count": len([r for r in results if r["is_compatible"]]),
                "airports": results
            }
            
        except Exception as e:
            return {
                "error": "search_failed",
                "message": f"Failed to find airports: {str(e)}",
                "location": location,
                "aircraft_type": aircraft_type
            }
    
    async def _get_airport_details(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get airport details tool implementation."""
        icao_code = params.get("icao_code", "").upper()
        
        if not icao_code:
            return {
                "error": "missing_parameter",
                "message": "icao_code parameter is required"
            }
        
        try:
            result = self.db_manager.conn.execute("""
                SELECT icao_code, name, latitude, longitude, elevation_ft,
                       longest_runway_ft, runway_width_ft, surface_type,
                       weight_capacity_lbs, contact_info, last_updated
                FROM airports
                WHERE icao_code = ?
            """, (icao_code,)).fetchone()
            
            if not result:
                return {
                    "error": "airport_not_found",
                    "message": f"Airport {icao_code} not found in database",
                    "icao_code": icao_code
                }
            
            return {
                "success": True,
                "airport": {
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
                    "last_updated": str(result[10]) if result[10] else None
                }
            }
            
        except Exception as e:
            return {
                "error": "database_error",
                "message": f"Failed to retrieve airport details: {str(e)}",
                "icao_code": icao_code
            }
    
    async def _validate_aircraft_compatibility(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate aircraft compatibility tool implementation."""
        icao_code = params.get("icao_code", "").upper()
        aircraft_type = params.get("aircraft_type")
        
        if not icao_code or not aircraft_type:
            return {
                "error": "missing_parameters",
                "message": "Both icao_code and aircraft_type are required"
            }
        
        try:
            # Get airport details
            airport_result = self.db_manager.conn.execute("""
                SELECT icao_code, name, latitude, longitude, elevation_ft,
                       longest_runway_ft, runway_width_ft, surface_type,
                       weight_capacity_lbs, contact_info, last_updated
                FROM airports
                WHERE icao_code = ?
            """, (icao_code,)).fetchone()
            
            if not airport_result:
                return {
                    "error": "airport_not_found",
                    "message": f"Airport {icao_code} not found",
                    "icao_code": icao_code
                }
            
            # Get aircraft specs
            aircraft_specs = self.db_manager.get_aircraft_specs(aircraft_type)
            if not aircraft_specs:
                return {
                    "error": "aircraft_not_found",
                    "message": f"Aircraft type '{aircraft_type}' not supported",
                    "aircraft_type": aircraft_type,
                    "supported_aircraft": self.db_manager.get_all_aircraft_types()
                }
            
            # Create airport object
            from ..data.models import Airport
            airport = Airport(
                icao_code=airport_result[0],
                name=airport_result[1],
                coordinates=Coordinates(airport_result[2], airport_result[3]),
                elevation_ft=airport_result[4] or 0,
                longest_runway_ft=airport_result[5] or 0,
                runway_width_ft=airport_result[6] or 0,
                surface_type=airport_result[7] or "unknown",
                weight_capacity_lbs=airport_result[8],
                contact_info=airport_result[9]
            )
            
            # Check compatibility
            from ..core.engine import AirportMatcher
            compatible, warnings = AirportMatcher.validate_compatibility(airport, aircraft_specs)
            compatibility_score = AirportMatcher.calculate_compatibility_score(airport, aircraft_specs)
            
            return {
                "success": True,
                "airport": {
                    "icao_code": airport.icao_code,
                    "name": airport.name,
                    "runway_length_ft": airport.longest_runway_ft,
                    "runway_width_ft": airport.runway_width_ft,
                    "surface_type": airport.surface_type
                },
                "aircraft": {
                    "type": aircraft_specs.aircraft_type,
                    "min_runway_length_ft": aircraft_specs.min_runway_length_ft,
                    "min_runway_width_ft": aircraft_specs.min_runway_width_ft,
                    "category": aircraft_specs.category
                },
                "compatibility": {
                    "is_compatible": compatible,
                    "score": round(compatibility_score, 2),
                    "warnings": warnings
                }
            }
            
        except Exception as e:
            return {
                "error": "validation_failed",
                "message": f"Failed to validate compatibility: {str(e)}",
                "icao_code": icao_code,
                "aircraft_type": aircraft_type
            }
    
    async def _get_supported_aircraft(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get supported aircraft tool implementation."""
        try:
            aircraft_types = self.db_manager.get_all_aircraft_types()
            
            # Get detailed specs for each aircraft
            aircraft_details = []
            for aircraft_type in aircraft_types:
                specs = self.db_manager.get_aircraft_specs(aircraft_type)
                if specs:
                    aircraft_details.append({
                        "aircraft_type": specs.aircraft_type,
                        "min_runway_length_ft": specs.min_runway_length_ft,
                        "min_runway_width_ft": specs.min_runway_width_ft,
                        "max_weight_lbs": specs.max_weight_lbs,
                        "approach_speed_kts": specs.approach_speed_kts,
                        "category": specs.category
                    })
            
            return {
                "success": True,
                "total_count": len(aircraft_details),
                "aircraft": aircraft_details
            }
            
        except Exception as e:
            return {
                "error": "database_error",
                "message": f"Failed to retrieve aircraft list: {str(e)}"
            }
    
    def get_tools_manifest(self) -> Dict[str, Any]:
        """Get MCP tools manifest for registration."""
        return {
            "tools": self.tools,
            "server_info": {
                "name": "emergency-airport-finder",
                "version": "1.0.0",
                "description": "Emergency Airport Finder MCP Server for aviation safety"
            }
        }