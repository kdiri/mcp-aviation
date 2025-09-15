"""Geocoding client using OpenStreetMap Nominatim API."""

import requests
import logging
from typing import Optional, Dict, Any

from ..data.models import Coordinates
from ..core.cache import cache_result, geocoding_cache

logger = logging.getLogger(__name__)


class GeocodingClient:
    """Client for geocoding addresses using OpenStreetMap Nominatim."""
    
    def __init__(self):
        """Initialize the geocoding client."""
        self.base_url = "https://nominatim.openstreetmap.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Emergency-Airport-Finder/1.0 (https://github.com/emergency-airport-finder)'
        })
    
    @cache_result(geocoding_cache, lambda self, address: f"geocode:{address.lower().strip()}", ttl=1800)
    def geocode(self, address: str) -> Optional[Coordinates]:
        """Geocode an address to coordinates."""
        try:
            # Clean and encode the address
            address = address.strip()
            if not address:
                return None
            
            # Make request to Nominatim
            url = f"{self.base_url}/search"
            params = {
                'q': address,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data and len(data) > 0:
                result = data[0]
                lat = float(result['lat'])
                lon = float(result['lon'])
                
                logger.info(f"Geocoded '{address}' to {lat}, {lon}")
                return Coordinates(lat, lon)
            
            logger.warning(f"No geocoding results for: {address}")
            return None
            
        except requests.RequestException as e:
            logger.error(f"Geocoding request failed for '{address}': {e}")
            return None
        except (ValueError, KeyError) as e:
            logger.error(f"Failed to parse geocoding response for '{address}': {e}")
            return None
    
    def reverse_geocode(self, coordinates: Coordinates) -> Optional[Dict[str, Any]]:
        """Reverse geocode coordinates to address information."""
        try:
            url = f"{self.base_url}/reverse"
            params = {
                'lat': coordinates.latitude,
                'lon': coordinates.longitude,
                'format': 'json',
                'addressdetails': 1
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'address' in data:
                return data['address']
            
            return None
            
        except Exception as e:
            logger.error(f"Reverse geocoding failed for {coordinates}: {e}")
            return None