# Emergency Airport Finder

A real-time aviation safety tool that helps pilots quickly identify the nearest suitable airports for emergency landings. The system considers aircraft specifications, airport runway capabilities, and current location to provide instantaneous recommendations.

## Features

- **Real-time airport search** with sub-2-second response times
- **Aircraft-specific filtering** based on runway requirements
- **Interactive map interface** with color-coded airport markers
- **Great circle distance calculations** for accurate navigation
- **Comprehensive aircraft database** with runway specifications
- **Cached airport data** from OurAirports.com for offline capability
- **Docker containerized** for easy deployment

## Quick Start

### Local Setup (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd emergency-airport-finder
   ```

2. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   # Using pip
   pip install -r requirements.txt
   
   # Or using uv (faster)
   uv pip install -r requirements.txt
   ```

4. **Run the application (data will initialize automatically on first run):**
   ```bash
   source venv/bin/activate && python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the application:**
   - Web interface: http://localhost:8000
   - API documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/api/status

**Note**: On first run, the system will automatically:
- Initialize aircraft specifications database
- Download and cache airport data from OurAirports.com (~30 seconds)
- Set up spatial indexing for fast queries

7. **Test the system:**
   ```bash
   python test_system.py
   ```

### Using Docker (Alternative)

1. **Clone and build:**
   ```bash
   git clone <repository-url>
   cd emergency-airport-finder
   docker-compose up --build
   ```

2. **Access the application:**
   - Web interface: http://localhost:8000
   - API documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/api/status

## Usage

### Web Interface

1. **Start the application** (if not already running):
   ```bash
   source venv/bin/activate && python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Open http://localhost:8000** in your browser

3. **Use the interface:**
   - Click on the map or enter coordinates for your current location
   - Select your aircraft type from the dropdown
   - Set search radius (default: 100 nautical miles)
   - Click "Find Emergency Airports"

The map will display:
- 🟢 **Green markers**: Compatible airports for your aircraft
- 🔴 **Red markers**: Incompatible airports (runway too short, etc.)
- ✈️ **Blue plane**: Your current position

### API Usage

**Search for airports:**
```bash
curl "http://localhost:8000/api/emergency-airports?location=New York&aircraft=Cessna 172&max_distance=50"
```

**Get supported aircraft:**
```bash
curl "http://localhost:8000/api/aircraft"
```

**Get airport details:**
```bash
curl "http://localhost:8000/api/airport/KJFK"
```

### MCP Server Usage

**Start MCP server:**
```bash
source venv/bin/activate
python mcp_server.py
```

**Use with AI assistants** that support Model Context Protocol

## Supported Aircraft

The system includes specifications for common aircraft types:

- **Light Aircraft**: Cessna 172, Cessna 182, Piper Cherokee
- **Medium Aircraft**: King Air 350, Citation CJ4
- **Commercial Aircraft**: Boeing 737-800, Airbus A320, Boeing 777-300ER, Airbus A380

## Data Sources

- **Airport Data**: OurAirports.com (comprehensive global coverage)
- **Runway Specifications**: Integrated runway length, width, and surface data
- **Aircraft Specs**: Curated database of runway requirements by aircraft type

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Interface │    │   FastAPI Server │    │   DuckDB Cache  │
│   (Leaflet.js)  │◄──►│   (Python)       │◄──►│   (Airports)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  External APIs   │
                       │  (OurAirports)   │
                       └──────────────────┘
```

## Development

### Project Structure

```
emergency-airport-finder/
├── src/
│   ├── core/           # Core engine and algorithms
│   ├── data/           # Database and data models
│   ├── web/            # Web interface and API
│   ├── integrations/   # External service clients
│   └── mcp/            # MCP server (future)
├── app.py              # Main application entry point
├── Dockerfile          # Container configuration
└── docker-compose.yml  # Development setup
```

### Adding New Aircraft

Edit `src/data/initial_data.py` and add aircraft specifications:

```python
AircraftSpecs(
    aircraft_type="Your Aircraft",
    min_runway_length_ft=2000,
    min_runway_width_ft=75,
    max_weight_lbs=5000,
    approach_speed_kts=80,
    category="light"  # light, medium, heavy, super
)
```

### Running Tests

```bash
# Activate virtual environment first
source venv/bin/activate

# Test core functionality
python test_system.py

# Test with specific location
python -c "
from src.core.engine import *
from src.data.database import DatabaseManager
db = DatabaseManager()
finder = EmergencyAirportFinder(db)
results = finder.find_emergency_airports('40.7128,-74.0060', 'Cessna 172')
print(f'Found {len(results)} airports')
"
```

## Performance

- **Response Time**: < 2 seconds for typical searches
- **Database**: Spatial indexing for fast proximity queries
- **Caching**: Multi-level caching with TTL support
- **Scalability**: Handles concurrent requests efficiently
- **Monitoring**: Built-in performance metrics and slow query detection

### Performance Testing

Run comprehensive performance tests:
```bash
# Activate virtual environment first
source venv/bin/activate

# System integration test
python test_system.py

# MCP server functionality test  
python test_mcp_server.py

# Test API endpoints
curl "http://localhost:8000/api/emergency-airports?location=New York&aircraft=Cessna 172&max_distance=50"
```

### Monitoring

The system includes built-in performance monitoring:
- Function execution times
- Cache hit rates  
- Error tracking
- Slow operation detection

## Safety Notice

**⚠️ IMPORTANT DISCLAIMER ⚠️**

This tool is for educational and demonstration purposes only. It should NOT be used as the sole source of information for actual emergency aviation decisions. Always consult official aviation resources, air traffic control, and follow proper emergency procedures.

The aviation industry has sophisticated emergency response systems developed by experts over decades. This prototype is meant to explore data engineering approaches to aviation safety challenges.

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Support

For questions or issues:
- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review the system status at `/api/status`