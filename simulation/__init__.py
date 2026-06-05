"""
Simulation module for SmartCity Twin.
Contains vehicle models, traffic generation, traffic logic,
and emergency event handling.
"""

from simulation.vehicle import Vehicle, VehicleType
from simulation.traffic_logic import TrafficDensityLevel, TrafficLogic
from simulation.traffic_generator import TrafficGenerator
from simulation.emergency_events import EmergencyEvent, EmergencyManager

__all__ = [
    'Vehicle',
    'VehicleType',
    'TrafficDensityLevel',
    'TrafficLogic',
    'TrafficGenerator',
    'EmergencyEvent',
    'EmergencyManager',
]
