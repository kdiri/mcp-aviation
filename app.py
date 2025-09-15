"""Main application entry point for Emergency Airport Finder."""

import logging
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from src.data.database import DatabaseManager
from src.data.airport_fetcher import AirportDataFetcher
from src.core.engine import EmergencyAirportFinder
from src.web.api import create_api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
db_manager = None
airport_finder = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global db_manager, airport_finder
    
    logger.info("Starting Emergency Airport Finder...")
    
    # Initialize database and data
    db_manager = DatabaseManager()
    data_fetcher = AirportDataFetcher(db_manager)
    
    # Initialize system data (aircraft specs and airports)
    data_fetcher.initialize_system_data()
    
    # Create airport finder instance
    airport_finder = EmergencyAirportFinder(db_manager)
    
    # Store in app state for access in routes
    app.state.db_manager = db_manager
    app.state.airport_finder = airport_finder
    app.state.data_fetcher = data_fetcher
    
    logger.info("Emergency Airport Finder started successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Emergency Airport Finder...")
    if db_manager:
        db_manager.close()


# Create FastAPI app
app = FastAPI(
    title="Emergency Airport Finder",
    description="Real-time aviation safety tool for finding suitable emergency landing airports",
    version="0.1.0",
    lifespan=lifespan
)

# Include API routes
app.include_router(create_api_router(), prefix="/api")

# Serve static files if directory exists
import os
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    # Simple HTML page with map interface (will create proper template next)
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Emergency Airport Finder</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <style>
            body { margin: 0; font-family: Arial, sans-serif; }
            #map { height: 100vh; }
            .controls { 
                position: absolute; top: 10px; left: 10px; z-index: 1000;
                background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                min-width: 300px;
            }
            .form-group { margin-bottom: 10px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px; }
            button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer; }
            button:hover { background: #005a87; }
            .status { margin-top: 10px; padding: 10px; border-radius: 3px; }
            .status.success { background: #d4edda; color: #155724; }
            .status.error { background: #f8d7da; color: #721c24; }
            
            /* Enhanced aircraft marker styling */
            .aircraft-marker {
                background: none !important;
                border: none !important;
                font-size: 32px;
                text-align: center;
                line-height: 40px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                filter: drop-shadow(0 0 3px rgba(0,100,255,0.8));
            }
        </style>
    </head>
    <body>
        <div class="controls">
            <h3>Emergency Airport Finder</h3>
            <div class="form-group">
                <label for="location">Current Location:</label>
                <input type="text" id="location" placeholder="Enter city, address, postal code, or coordinates">
            </div>
            <div class="form-group">
                <label for="aircraft">Aircraft Type:</label>
                <select id="aircraft">
                    <option value="">Select aircraft...</option>
                </select>
            </div>
            <div class="form-group">
                <label for="radius">Search Radius (nm):</label>
                <input type="number" id="radius" value="100" min="10" max="500">
            </div>
            <button onclick="findAirports()">Find Emergency Airports</button>
            <div id="status" class="status" style="display: none;"></div>
        </div>
        
        <div id="map"></div>
        
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script>
            // Initialize map
            const map = L.map('map').setView([39.8283, -98.5795], 4); // Center of US
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
            
            let currentLocationMarker = null;
            let airportMarkers = [];
            
            // Load aircraft types
            fetch('/api/aircraft')
                .then(response => response.json())
                .then(data => {
                    const select = document.getElementById('aircraft');
                    data.aircraft_types.forEach(type => {
                        const option = document.createElement('option');
                        option.value = type;
                        option.textContent = type;
                        select.appendChild(option);
                    });
                });
            
            // Handle map clicks for location selection
            map.on('click', function(e) {
                const lat = e.latlng.lat.toFixed(6);
                const lon = e.latlng.lng.toFixed(6);
                document.getElementById('location').value = `${lat},${lon}`;
                
                // Update location marker
                if (currentLocationMarker) {
                    map.removeLayer(currentLocationMarker);
                }
                currentLocationMarker = L.marker([lat, lon], {
                    icon: L.divIcon({
                        html: '✈️',
                        iconSize: [40, 40],
                        className: 'aircraft-marker'
                    })
                }).addTo(map);
            });
            
            function showStatus(message, isError = false) {
                const status = document.getElementById('status');
                status.textContent = message;
                status.className = `status ${isError ? 'error' : 'success'}`;
                status.style.display = 'block';
            }
            
            function findAirports() {
                const location = document.getElementById('location').value;
                const aircraft = document.getElementById('aircraft').value;
                const radius = document.getElementById('radius').value;
                
                if (!location || !aircraft) {
                    showStatus('Please enter location and select aircraft type', true);
                    return;
                }
                
                showStatus('Searching for emergency airports...');
                
                fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        location: location,
                        aircraft_type: aircraft,
                        max_distance_nm: parseInt(radius)
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showStatus(data.message, true);
                        return;
                    }
                    
                    // Center map on search location
                    if (data.search_location && data.search_location.latitude && data.search_location.longitude) {
                        const searchLat = data.search_location.latitude;
                        const searchLon = data.search_location.longitude;
                        map.setView([searchLat, searchLon], 10);
                        
                        // Update location marker
                        if (currentLocationMarker) {
                            map.removeLayer(currentLocationMarker);
                        }
                        currentLocationMarker = L.marker([searchLat, searchLon], {
                            icon: L.divIcon({
                                html: '✈️',
                                iconSize: [20, 20],
                                className: 'aircraft-marker'
                            })
                        }).addTo(map);
                        
                        // Update location input to show resolved coordinates
                        document.getElementById('location').value = `${searchLat.toFixed(6)},${searchLon.toFixed(6)}`;
                    }
                    
                    // Clear existing airport markers
                    airportMarkers.forEach(marker => map.removeLayer(marker));
                    airportMarkers = [];
                    
                    // Add airport markers
                    data.recommendations.forEach(rec => {
                        const airport = rec.airport;
                        const isCompatible = rec.warnings.length === 0;
                        
                        const marker = L.marker([airport.coordinates.latitude, airport.coordinates.longitude], {
                            icon: L.divIcon({
                                html: isCompatible ? '🟢' : '🔴',
                                iconSize: [15, 15],
                                className: 'airport-marker'
                            })
                        }).addTo(map);
                        
                        const popupContent = `
                            <b>${airport.name}</b><br>
                            <b>ICAO:</b> ${airport.icao_code}<br>
                            <b>Distance:</b> ${rec.distance_nm.toFixed(1)} nm<br>
                            <b>Bearing:</b> ${rec.bearing_degrees.toFixed(0)}°<br>
                            <b>Runway:</b> ${airport.longest_runway_ft}ft x ${airport.runway_width_ft}ft<br>
                            <b>Surface:</b> ${airport.surface_type}<br>
                            <b>Flight Time:</b> ~${rec.estimated_flight_time_minutes} min<br>
                            ${rec.warnings.length > 0 ? '<br><b>Warnings:</b><br>' + rec.warnings.join('<br>') : ''}
                        `;
                        
                        marker.bindPopup(popupContent);
                        airportMarkers.push(marker);
                    });
                    
                    showStatus(`Found ${data.recommendations.length} airports`);
                })
                .catch(error => {
                    showStatus('Error searching for airports: ' + error.message, true);
                });
            }
        </script>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Emergency Airport Finder"}


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )