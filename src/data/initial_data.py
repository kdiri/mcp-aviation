"""Initial data for aircraft specifications and sample airports."""

from .models import AircraftSpecs

# Common aircraft specifications with runway requirements
AIRCRAFT_SPECIFICATIONS = [
    # Light Aircraft
    AircraftSpecs(
        aircraft_type="Cessna 172",
        min_runway_length_ft=1200,
        min_runway_width_ft=50,
        max_weight_lbs=2550,
        approach_speed_kts=65,
        category="light"
    ),
    AircraftSpecs(
        aircraft_type="Cessna 182",
        min_runway_length_ft=1400,
        min_runway_width_ft=50,
        max_weight_lbs=3100,
        approach_speed_kts=70,
        category="light"
    ),
    AircraftSpecs(
        aircraft_type="Piper Cherokee",
        min_runway_length_ft=1200,
        min_runway_width_ft=50,
        max_weight_lbs=2450,
        approach_speed_kts=68,
        category="light"
    ),
    
    # Medium Aircraft
    AircraftSpecs(
        aircraft_type="King Air 350",
        min_runway_length_ft=3300,
        min_runway_width_ft=75,
        max_weight_lbs=15000,
        approach_speed_kts=110,
        category="medium"
    ),
    AircraftSpecs(
        aircraft_type="Citation CJ4",
        min_runway_length_ft=3560,
        min_runway_width_ft=100,
        max_weight_lbs=17110,
        approach_speed_kts=120,
        category="medium"
    ),
    
    # Commercial Aircraft
    AircraftSpecs(
        aircraft_type="Boeing 737-800",
        min_runway_length_ft=6000,
        min_runway_width_ft=100,  # More realistic
        max_weight_lbs=174200,
        approach_speed_kts=140,
        category="heavy"
    ),
    AircraftSpecs(
        aircraft_type="Airbus A320",
        min_runway_length_ft=5090,
        min_runway_width_ft=100,  # More realistic - A320 can use narrower runways
        max_weight_lbs=169756,
        approach_speed_kts=135,
        category="heavy"
    ),
    AircraftSpecs(
        aircraft_type="Boeing 777-300ER",
        min_runway_length_ft=9800,
        min_runway_width_ft=150,
        max_weight_lbs=775000,
        approach_speed_kts=155,
        category="heavy"
    ),
    AircraftSpecs(
        aircraft_type="Airbus A380",
        min_runway_length_ft=9800,
        min_runway_width_ft=150,
        max_weight_lbs=1267000,
        approach_speed_kts=165,
        category="super"
    ),
]


def initialize_aircraft_data(db_manager):
    """Initialize database with aircraft specifications."""
    for specs in AIRCRAFT_SPECIFICATIONS:
        db_manager.insert_aircraft_specs(specs)
    print(f"Initialized {len(AIRCRAFT_SPECIFICATIONS)} aircraft specifications")