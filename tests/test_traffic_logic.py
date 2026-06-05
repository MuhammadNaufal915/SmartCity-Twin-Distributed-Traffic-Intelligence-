"""
Unit tests for traffic logic computation.
"""

from __future__ import annotations

from simulation.vehicle import Vehicle, VehicleType
from simulation.traffic_logic import TrafficLogic, TrafficDensityLevel


def test_calculate_density_level() -> None:
    """Verify traffic density mapping based on counts."""
    assert TrafficLogic.calculate_density_level(0) == TrafficDensityLevel.LOW
    assert TrafficLogic.calculate_density_level(10) == TrafficDensityLevel.LOW
    assert TrafficLogic.calculate_density_level(11) == TrafficDensityLevel.MEDIUM
    assert TrafficLogic.calculate_density_level(20) == TrafficDensityLevel.MEDIUM
    assert TrafficLogic.calculate_density_level(21) == TrafficDensityLevel.HIGH
    assert TrafficLogic.calculate_density_level(40) == TrafficDensityLevel.HIGH
    assert TrafficLogic.calculate_density_level(41) == TrafficDensityLevel.CRITICAL
    assert TrafficLogic.calculate_density_level(100) == TrafficDensityLevel.CRITICAL


def test_calculate_green_time() -> None:
    """Verify green light time calculation formula."""
    # Base = 10, LOW bonus = 5
    assert TrafficLogic.calculate_green_time(TrafficDensityLevel.LOW) == 15
    # Base = 10, MEDIUM bonus = 10
    assert TrafficLogic.calculate_green_time(TrafficDensityLevel.MEDIUM) == 20
    # Base = 10, CRITICAL bonus = 30, prediction = True (prediction bonus = 5)
    assert TrafficLogic.calculate_green_time(TrafficDensityLevel.CRITICAL, neighbor_prediction=True) == 45


def test_detect_congestion() -> None:
    """Verify congestion threshold trigger (threshold is 40)."""
    assert not TrafficLogic.detect_congestion(39)
    assert not TrafficLogic.detect_congestion(40)
    assert TrafficLogic.detect_congestion(41)


def test_detect_emergency() -> None:
    """Verify filter for identifying emergency vehicles."""
    vehicles = [
        Vehicle(vehicle_id="1", vehicle_type=VehicleType.CAR),
        Vehicle(vehicle_id="2", vehicle_type=VehicleType.AMBULANCE),
        Vehicle(vehicle_id="3", vehicle_type=VehicleType.TRUCK),
        Vehicle(vehicle_id="4", vehicle_type=VehicleType.POLICE),
    ]
    emergencies = TrafficLogic.detect_emergency(vehicles)
    assert len(emergencies) == 2
    assert emergencies[0].vehicle_id == "2"
    assert emergencies[1].vehicle_id == "4"


def test_get_light_cycle_state() -> None:
    """Verify color state determination from cycle timing."""
    # green_duration = 10, yellow = 3, red = 5, total = 18
    # 0 - 9.99s: GREEN
    # 10 - 12.99s: YELLOW
    # 13 - 17.99s: RED
    assert TrafficLogic.get_light_cycle_state(0.0, 10, 3, 5) == "GREEN"
    assert TrafficLogic.get_light_cycle_state(5.0, 10, 3, 5) == "GREEN"
    assert TrafficLogic.get_light_cycle_state(10.0, 10, 3, 5) == "YELLOW"
    assert TrafficLogic.get_light_cycle_state(12.5, 10, 3, 5) == "YELLOW"
    assert TrafficLogic.get_light_cycle_state(13.0, 10, 3, 5) == "RED"
    assert TrafficLogic.get_light_cycle_state(17.9, 10, 3, 5) == "RED"
    # Overflows to next cycle
    assert TrafficLogic.get_light_cycle_state(18.0, 10, 3, 5) == "GREEN"
    assert TrafficLogic.get_light_cycle_state(28.0, 10, 3, 5) == "YELLOW"
