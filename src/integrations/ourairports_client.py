"""Client for fetching airport data from OurAirports.com API."""

import requests
import csv
import logging
from typing import List, Optional
from datetime import datetime
from io import StringIO

from ..data.models import Airport, Coordinates

logger = logging.getLogger(__name__)


class OurAirportsClient:
    """Client for OurAirports.com data API."""
    
    BASE_URL = "https://davidmegginson.github.io/ourairports-data"
    
    def __init__(self):
        """Initialize the client."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Emergency-Airport-Finder/1.0'
        })
    
    def fetch_airports(self, airport_types: List[str] = None) -> List[Airport]:
        """Fetch airport data from OurAirports CSV files."""
        if airport_types is None:
            airport_types = ['large_airport', 'medium_airport', 'small_airport']
        
        airports = []
        
        try:
            # Fetch airports CSV
            response = self.session.get(f"{self.BASE_URL}/airports.csv", timeout=30)
            response.raise_for_status()
            
            # Parse CSV data
            csv_data = StringIO(response.text)
            reader = csv.DictReader(csv_data)
            
            for row in reader:
                # Filter by airport type
                if row['type'] not in airport_types:
                    continue
                
                # Skip airports without ICAO codes or coordinates
                if not row['ident'] or not row['latitude_deg'] or not row['longitude_deg']:
                    continue
                
                try:
                    airport = self._parse_airport_row(row)
                    if airport:
                        airports.append(airport)
                except Exception as e:
                    logger.warning(f"Failed to parse airport {row.get('ident', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Fetched {len(airports)} airports from OurAirports")
            return airports
            
        except Exception as e:
            logger.error(f"Failed to fetch airports from OurAirports: {e}")
            return []
    
    def fetch_runways(self) -> dict:
        """Fetch runway data and return as dict keyed by airport ident."""
        runways_by_airport = {}
        
        try:
            response = self.session.get(f"{self.BASE_URL}/runways.csv", timeout=30)
            response.raise_for_status()
            
            csv_data = StringIO(response.text)
            reader = csv.DictReader(csv_data)
            
            for row in reader:
                airport_ident = row['airport_ident']
                if airport_ident not in runways_by_airport:
                    runways_by_airport[airport_ident] = []
                
                runway_info = {
                    'length_ft': self._safe_int(row['length_ft']),
                    'width_ft': self._safe_int(row['width_ft']),
                    'surface': row['surface'] or 'unknown'
                }
                runways_by_airport[airport_ident].append(runway_info)
            
            logger.info(f"Fetched runway data for {len(runways_by_airport)} airports")
            return runways_by_airport
            
        except Exception as e:
            logger.error(f"Failed to fetch runway data: {e}")
            return {}
    
    def _parse_airport_row(self, row: dict) -> Optional[Airport]:
        """Parse a single airport row from CSV data."""
        try:
            # Basic airport info
            icao_code = row['ident']
            name = row['name']
            
            # Coordinates
            lat = float(row['latitude_deg'])
            lon = float(row['longitude_deg'])
            coordinates = Coordinates(lat, lon)
            
            # Elevation
            elevation_ft = self._safe_int(row['elevation_ft']) or 0
            
            # For now, use placeholder runway data - will be updated with actual runway data
            airport = Airport(
                icao_code=icao_code,
                name=name,
                coordinates=coordinates,
                elevation_ft=elevation_ft,
                longest_runway_ft=0,  # Will be updated from runway data
                runway_width_ft=0,    # Will be updated from runway data
                surface_type='unknown',  # Will be updated from runway data
                last_updated=datetime.now()
            )
            
            return airport
            
        except Exception as e:
            logger.warning(f"Failed to parse airport row: {e}")
            return None
    
    def _safe_int(self, value: str) -> Optional[int]:
        """Safely convert string to int, return None if invalid."""
        try:
            return int(float(value)) if value and value.strip() else None
        except (ValueError, TypeError):
            return None
    
    def update_airports_with_runway_data(self, airports: List[Airport], runways_data: dict) -> List[Airport]:
        """Update airport objects with runway specifications."""
        updated_airports = []
        
        for airport in airports:
            if airport.icao_code in runways_data:
                runways = runways_data[airport.icao_code]
                
                if runways:
                    # Find longest runway
                    longest_runway = max(runways, key=lambda r: r['length_ft'] or 0)
                    
                    # Update airport with runway data
                    airport.longest_runway_ft = longest_runway['length_ft'] or 0
                    airport.runway_width_ft = longest_runway['width_ft'] or 0
                    airport.surface_type = longest_runway['surface'] or 'unknown'
                    
                    # Only include airports with meaningful runway data
                    if airport.longest_runway_ft > 500:  # Minimum 500ft runway
                        updated_airports.append(airport)
            
        logger.info(f"Updated {len(updated_airports)} airports with runway data")
        return updated_airports