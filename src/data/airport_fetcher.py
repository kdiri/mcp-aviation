"""Airport data fetcher that coordinates data loading from external sources."""

import logging
from datetime import datetime, timedelta

from .database import DatabaseManager
from .initial_data import initialize_aircraft_data
from ..integrations.ourairports_client import OurAirportsClient

logger = logging.getLogger(__name__)


class AirportDataFetcher:
    """Manages fetching and caching of airport data."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize with database manager."""
        self.db = db_manager
        self.ourairports_client = OurAirportsClient()
    
    def initialize_system_data(self):
        """Initialize system with aircraft specs and airport data."""
        logger.info("Initializing system data...")
        
        # Initialize aircraft specifications
        initialize_aircraft_data(self.db)
        
        # Check if we need to fetch airport data
        if self._needs_airport_data_refresh():
            logger.info("Fetching fresh airport data...")
            self.fetch_and_store_airports()
        else:
            logger.info("Using cached airport data")
    
    def _needs_airport_data_refresh(self) -> bool:
        """Check if airport data needs to be refreshed."""
        try:
            # Check if we have any airports in the database
            result = self.db.conn.execute("""
                SELECT COUNT(*), MAX(last_updated) 
                FROM airports 
                WHERE longest_runway_ft > 0
            """).fetchone()
            
            count, last_updated = result
            
            # If no airports or data is older than 30 days, refresh
            if count == 0:
                return True
            
            if last_updated:
                if isinstance(last_updated, str):
                    last_updated = datetime.fromisoformat(last_updated)
                
                if datetime.now() - last_updated > timedelta(days=30):
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Could not check airport data age: {e}")
            return True
    
    def fetch_and_store_airports(self) -> int:
        """Fetch airport data from external sources and store in database."""
        try:
            logger.info("Fetching airports from OurAirports...")
            
            # Fetch airports and runway data
            airports = self.ourairports_client.fetch_airports()
            runways_data = self.ourairports_client.fetch_runways()
            
            # Update airports with runway specifications
            airports_with_runways = self.ourairports_client.update_airports_with_runway_data(
                airports, runways_data
            )
            
            # Store in database
            stored_count = 0
            for airport in airports_with_runways:
                if self.db.insert_airport(airport):
                    stored_count += 1
                
                # Log progress for large datasets
                if stored_count % 1000 == 0:
                    logger.info(f"Stored {stored_count} airports...")
            
            logger.info(f"Successfully stored {stored_count} airports")
            return stored_count
            
        except Exception as e:
            logger.error(f"Failed to fetch and store airports: {e}")
            return 0
    
    def get_data_status(self) -> dict:
        """Get status of cached data."""
        try:
            # Airport count and last update
            airport_result = self.db.conn.execute("""
                SELECT COUNT(*), MAX(last_updated) 
                FROM airports 
                WHERE longest_runway_ft > 0
            """).fetchone()
            
            # Aircraft count
            aircraft_result = self.db.conn.execute("""
                SELECT COUNT(*) FROM aircraft_specs
            """).fetchone()
            
            airport_count, last_updated = airport_result
            aircraft_count = aircraft_result[0]
            
            return {
                'airports_count': airport_count,
                'aircraft_count': aircraft_count,
                'last_updated': last_updated,
                'data_age_days': self._calculate_data_age_days(last_updated)
            }
            
        except Exception as e:
            logger.error(f"Failed to get data status: {e}")
            return {
                'airports_count': 0,
                'aircraft_count': 0,
                'last_updated': None,
                'data_age_days': None
            }
    
    def _calculate_data_age_days(self, last_updated) -> int:
        """Calculate age of data in days."""
        if not last_updated:
            return None
        
        try:
            if isinstance(last_updated, str):
                last_updated = datetime.fromisoformat(last_updated)
            
            age = datetime.now() - last_updated
            return age.days
            
        except Exception:
            return None