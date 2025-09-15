"""Database operations using DuckDB for airport and aircraft data."""

import duckdb
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .models import Airport, AircraftSpecs, Coordinates

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages DuckDB database operations for airport and aircraft data."""
    
    def __init__(self, db_path: str = "data/emergency_airports.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = duckdb.connect(str(self.db_path))
        self._create_tables()
        self._create_indexes()
    
    def _create_tables(self):
        """Create database tables for airports and aircraft specifications."""
        # Airports table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS airports (
                icao_code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                elevation_ft INTEGER,
                longest_runway_ft INTEGER,
                runway_width_ft INTEGER,
                surface_type TEXT,
                weight_capacity_lbs INTEGER,
                contact_info TEXT,
                last_updated TIMESTAMP
            )
        """)
        
        # Aircraft specifications table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS aircraft_specs (
                aircraft_type TEXT PRIMARY KEY,
                min_runway_length_ft INTEGER NOT NULL,
                min_runway_width_ft INTEGER NOT NULL,
                max_weight_lbs INTEGER NOT NULL,
                approach_speed_kts INTEGER,
                category TEXT NOT NULL
            )
        """)
        
        self.conn.commit()
    
    def _create_indexes(self):
        """Create spatial and performance indexes."""
        try:
            # Spatial index for lat/lon lookups
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_airports_location 
                ON airports (latitude, longitude)
            """)
            
            # Index for runway specifications
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_airports_runway 
                ON airports (longest_runway_ft, runway_width_ft)
            """)
            
            self.conn.commit()
        except Exception as e:
            logger.warning(f"Could not create indexes: {e}")
    
    def insert_airport(self, airport: Airport) -> bool:
        """Insert or update airport data."""
        try:
            self.conn.execute("""
                INSERT OR REPLACE INTO airports 
                (icao_code, name, latitude, longitude, elevation_ft, 
                 longest_runway_ft, runway_width_ft, surface_type, 
                 weight_capacity_lbs, contact_info, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                airport.icao_code, airport.name,
                airport.coordinates.latitude, airport.coordinates.longitude,
                airport.elevation_ft, airport.longest_runway_ft,
                airport.runway_width_ft, airport.surface_type,
                airport.weight_capacity_lbs, airport.contact_info,
                airport.last_updated or datetime.now()
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to insert airport {airport.icao_code}: {e}")
            return False
    
    def get_airports_within_radius(self, center: Coordinates, radius_nm: float) -> List[Airport]:
        """Get airports within specified radius using great circle distance."""
        # Convert nautical miles to degrees (approximate)
        radius_deg = radius_nm / 60.0
        
        try:
            result = self.conn.execute("""
                SELECT icao_code, name, latitude, longitude, elevation_ft,
                       longest_runway_ft, runway_width_ft, surface_type,
                       weight_capacity_lbs, contact_info, last_updated,
                       -- Great circle distance calculation
                       3959 * acos(
                           cos(radians(?)) * cos(radians(latitude)) * 
                           cos(radians(longitude) - radians(?)) + 
                           sin(radians(?)) * sin(radians(latitude))
                       ) * 0.868976 as distance_nm  -- Convert to nautical miles
                FROM airports
                WHERE latitude BETWEEN ? - ? AND ? + ?
                  AND longitude BETWEEN ? - ? AND ? + ?
                  AND longest_runway_ft IS NOT NULL
                ORDER BY distance_nm
                LIMIT 100
            """, (
                center.latitude, center.longitude, center.latitude,
                center.latitude, radius_deg, center.latitude, radius_deg,
                center.longitude, radius_deg, center.longitude, radius_deg
            )).fetchall()
            
            airports = []
            for row in result:
                airport = Airport(
                    icao_code=row[0],
                    name=row[1],
                    coordinates=Coordinates(row[2], row[3]),
                    elevation_ft=row[4] or 0,
                    longest_runway_ft=row[5] or 0,
                    runway_width_ft=row[6] or 0,
                    surface_type=row[7] or "unknown",
                    weight_capacity_lbs=row[8],
                    contact_info=row[9],
                    last_updated=row[10]
                )
                airports.append(airport)
            
            return airports
            
        except Exception as e:
            logger.error(f"Failed to query airports: {e}")
            return []
    
    def insert_aircraft_specs(self, specs: AircraftSpecs) -> bool:
        """Insert or update aircraft specifications."""
        try:
            self.conn.execute("""
                INSERT OR REPLACE INTO aircraft_specs 
                (aircraft_type, min_runway_length_ft, min_runway_width_ft,
                 max_weight_lbs, approach_speed_kts, category)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                specs.aircraft_type, specs.min_runway_length_ft,
                specs.min_runway_width_ft, specs.max_weight_lbs,
                specs.approach_speed_kts, specs.category
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to insert aircraft specs {specs.aircraft_type}: {e}")
            return False
    
    def get_aircraft_specs(self, aircraft_type: str) -> Optional[AircraftSpecs]:
        """Get aircraft specifications by type."""
        try:
            result = self.conn.execute("""
                SELECT aircraft_type, min_runway_length_ft, min_runway_width_ft,
                       max_weight_lbs, approach_speed_kts, category
                FROM aircraft_specs
                WHERE aircraft_type = ?
            """, (aircraft_type,)).fetchone()
            
            if result:
                return AircraftSpecs(
                    aircraft_type=result[0],
                    min_runway_length_ft=result[1],
                    min_runway_width_ft=result[2],
                    max_weight_lbs=result[3],
                    approach_speed_kts=result[4],
                    category=result[5]
                )
            return None
            
        except Exception as e:
            logger.error(f"Failed to get aircraft specs for {aircraft_type}: {e}")
            return None
    
    def get_all_aircraft_types(self) -> List[str]:
        """Get list of all supported aircraft types."""
        try:
            result = self.conn.execute("""
                SELECT aircraft_type FROM aircraft_specs ORDER BY aircraft_type
            """).fetchall()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Failed to get aircraft types: {e}")
            return []
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()