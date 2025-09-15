#!/usr/bin/env python3
"""Test script for Emergency Airport Finder MCP Server."""

import asyncio
import json
import logging
from src.mcp.server import MCPServer
from src.data.database import DatabaseManager
from src.data.airport_fetcher import AirportDataFetcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_mcp_server():
    """Test MCP server functionality."""
    logger.info("Testing Emergency Airport Finder MCP Server...")
    
    # Initialize
    db_manager = DatabaseManager()
    data_fetcher = AirportDataFetcher(db_manager)
    data_fetcher.initialize_system_data()
    
    mcp_server = MCPServer(db_manager)
    
    # Test 1: Get tools manifest
    logger.info("Test 1: Getting tools manifest...")
    manifest = mcp_server.get_tools_manifest()
    print(f"Available tools: {list(manifest['tools'].keys())}")
    print()
    
    # Test 2: Find emergency airports
    logger.info("Test 2: Finding emergency airports for A320 near Paris...")
    result = await mcp_server.handle_tool_call("find_emergency_airports", {
        "location": "Paris, France",
        "aircraft_type": "Airbus A320",
        "max_distance_nm": 50
    })
    
    if result.get("success"):
        print(f"Found {result['total_found']} airports, {result['compatible_count']} compatible")
        print("Top 3 compatible airports:")
        compatible_airports = [a for a in result['airports'] if a['is_compatible']]
        for i, airport in enumerate(compatible_airports[:3]):
            print(f"  {i+1}. {airport['airport']['name']} ({airport['airport']['icao_code']})")
            print(f"     Distance: {airport['distance_nm']} nm")
            print(f"     Runway: {airport['airport']['longest_runway_ft']}ft")
    else:
        print(f"Error: {result}")
    print()
    
    # Test 3: Get airport details
    logger.info("Test 3: Getting CDG airport details...")
    result = await mcp_server.handle_tool_call("get_airport_details", {
        "icao_code": "LFPG"
    })
    
    if result.get("success"):
        airport = result['airport']
        print(f"Airport: {airport['name']} ({airport['icao_code']})")
        print(f"Location: {airport['coordinates']['latitude']}, {airport['coordinates']['longitude']}")
        print(f"Runway: {airport['longest_runway_ft']}ft x {airport['runway_width_ft']}ft")
        print(f"Surface: {airport['surface_type']}")
    else:
        print(f"Error: {result}")
    print()
    
    # Test 4: Validate compatibility
    logger.info("Test 4: Validating A320 compatibility with CDG...")
    result = await mcp_server.handle_tool_call("validate_aircraft_compatibility", {
        "icao_code": "LFPG",
        "aircraft_type": "Airbus A320"
    })
    
    if result.get("success"):
        comp = result['compatibility']
        print(f"Compatible: {comp['is_compatible']}")
        print(f"Score: {comp['score']}")
        if comp['warnings']:
            print(f"Warnings: {comp['warnings']}")
        else:
            print("No warnings")
    else:
        print(f"Error: {result}")
    print()
    
    # Test 5: Get supported aircraft
    logger.info("Test 5: Getting supported aircraft...")
    result = await mcp_server.handle_tool_call("get_supported_aircraft", {})
    
    if result.get("success"):
        print(f"Supported aircraft ({result['total_count']}):")
        for aircraft in result['aircraft']:
            print(f"  - {aircraft['aircraft_type']} ({aircraft['category']})")
            print(f"    Min runway: {aircraft['min_runway_length_ft']}ft x {aircraft['min_runway_width_ft']}ft")
    else:
        print(f"Error: {result}")
    
    # Cleanup
    db_manager.close()
    logger.info("MCP Server test completed!")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())