"""
Traffic logic for SmartCity Twin.
Implements traffic density calculation, green time optimization,
congestion detection, and emergency detection algorithms.
"""

from __future__ import annotations

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional

from simulation.vehicle import Vehicle, VehicleType


class TrafficDensityLevel(Enum):
    """Traffic density levels based on vehicle count thresholds."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @property
    def color(self) -> str:
        """Color for GUI display."""
        colors = {
            TrafficDensityLevel.LOW: "#4CAF50",       # Green
            TrafficDensityLevel.MEDIUM: "#FFC107",     # Amber
            TrafficDensityLevel.HIGH: "#FF9800",       # Orange
            TrafficDensityLevel.CRITICAL: "#F44336",   # Red
        }
        return colors.get(self, "#FFFFFF")

    @property
    def density_bonus(self) -> int:
        """Green time bonus based on density level."""
        bonuses = {
            TrafficDensityLevel.LOW: 5,
            TrafficDensityLevel.MEDIUM: 10,
            TrafficDensityLevel.HIGH: 20,
            TrafficDensityLevel.CRITICAL: 30,
        }
        return bonuses.get(self, 0)


class TrafficLogic:
    """
    Core traffic simulation logic engine.
    
    Implements all traffic calculation algorithms used by
    each virtual MCU independently. No shared state.
    """

    # Configuration constants
    BASE_GREEN_TIME: int = 10
    PREDICTION_BONUS: int = 5
    CONGESTION_THRESHOLD: int = 40

    @staticmethod
    def calculate_density_level(vehicle_count: int) -> TrafficDensityLevel:
        """
        Calculate traffic density level from vehicle count.
        
        Thresholds:
            0-10  = LOW
            11-20 = MEDIUM
            21-40 = HIGH
            41+   = CRITICAL
        """
        if vehicle_count <= 10:
            return TrafficDensityLevel.LOW
        elif vehicle_count <= 20:
            return TrafficDensityLevel.MEDIUM
        elif vehicle_count <= 40:
            return TrafficDensityLevel.HIGH
        else:
            return TrafficDensityLevel.CRITICAL

    @classmethod
    def calculate_green_time(
        cls,
        density_level: TrafficDensityLevel,
        neighbor_prediction: bool = False,
    ) -> int:
        """
        Calculate optimal green light duration.
        
        Formula:
            Green Time = Base + Density Bonus + Prediction Bonus
        
        Args:
            density_level: Current traffic density level
            neighbor_prediction: True if neighbor predicts incoming traffic
            
        Returns:
            Optimized green time in seconds
        """
        green_time = cls.BASE_GREEN_TIME
        green_time += density_level.density_bonus

        if neighbor_prediction:
            green_time += cls.PREDICTION_BONUS

        return green_time

    @classmethod
    def detect_congestion(cls, vehicle_count: int) -> bool:
        """
        Detect congestion condition.
        
        Congestion is triggered when vehicle count exceeds 40.
        """
        return vehicle_count > cls.CONGESTION_THRESHOLD

    @staticmethod
    def detect_emergency(vehicles: list[Vehicle]) -> list[Vehicle]:
        """
        Detect emergency vehicles in the current vehicle set.
        
        Returns list of emergency vehicles found.
        """
        return [v for v in vehicles if v.is_emergency]

    @staticmethod
    def calculate_traffic_flow(
        vehicle_count: int,
        green_duration: int,
    ) -> float:
        """
        Calculate traffic flow rate (vehicles per second).
        """
        if green_duration <= 0:
            return 0.0
        return vehicle_count / green_duration

    @staticmethod
    def get_light_cycle_state(
        elapsed_time: float,
        green_duration: int,
        yellow_duration: int = 3,
        red_duration: int = 5,
    ) -> str:
        """
        Determine current traffic light state based on elapsed time.
        
        Cycle: GREEN → YELLOW → RED → repeat
        """
        cycle_length = green_duration + yellow_duration + red_duration
        position = elapsed_time % cycle_length

        if position < green_duration:
            return "GREEN"
        elif position < green_duration + yellow_duration:
            return "YELLOW"
        else:
            return "RED"
