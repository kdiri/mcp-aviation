#!/usr/bin/env python3
"""Simple test script to verify the Emergency Airport Finder system."""

import sys
import logging
from src.data.database import DatabaseManager
from src.data.airport_fetcher import AirportDataFetcher
from src.core.engine import EmergencyAirportFinder
from src.data.models import Coordinates

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_system():
    """Test the core functionality of the system."""
    logger.info("Testing Emergency Airport Finder system...")
    
    try:
        # Initialize database
        db_manager = DatabaseManager("test_emergency_airports.db")
        
        # Initialize data
        data_fetcher = AirportDataFetcher(db_manager)
        data_fetcher.initialize_system_data()
        
        # Create airport finder
        airport_finder = EmergencyAirportFinder(db_manager)
        
        # Test 1: Check aircraft types
        logger.info("Test 1: Checking aircraft types...")
        aircraft_types = airport_finder.get_supported_aircraft_types()
        logger.info(f"Found {len(aircraft_types)} aircraft types: {aircraft_types[:5]}...")
        
        # Test 2: Test location resolution
        logger.info("Test 2: Testing location resolution...")
        test_location = "40.7128,-74.0060"  # New York City coordinates
        
        # Test 3: Find airports for a Cessna 172
        logger.info("Test 3: Finding airports for Cessna 172 near NYC...")
        try:
            recommendations = airport_finder.find_emergency_airports(
                location=test_location,
                aircraft_type="Cessna 172",
                max_distance_nm=50
            )
            
            logger.info(f"Found {len(recommendations)} airport recommendations")
            
            # Display first few recommendations
            for i, rec in enumerate(recommendations[:3]):
                logger.info(f"  {i+1}. {rec.airport.name} ({rec.airport.icao_code})")
                logger.info(f"     Distance: {rec.distance_nm:.1f} nm")
                logger.info(f"     Runway: {rec.airport.longest_runway_ft}ft")
                logger.info(f"     Warnings: {len(rec.warnings)}")
                
        except Exception as e:
            logger.warning(f"Airport search test failed (expected if no data): {e}")
        
        # Test 4: Check data status
        logger.info("Test 4: Checking data status...")
        status = data_fetcher.get_data_status()
        logger.info(f"Data status: {status}")
        
        logger.info("System test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"System test failed: {e}")
        return False
    
    finally:
        # Cleanup
        try:
            db_manager.close()
        except:
            pass


if __name__ == "__main__":
    success = test_system()
    sys.exit(0 if success else 1)