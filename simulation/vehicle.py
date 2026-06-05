"""
Vehicle model for SmartCity Twin.
Defines vehicle types and the Vehicle dataclass used
throughout the traffic simulation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class VehicleType(Enum):
    """Types of vehicles in the simulation."""
    CAR = auto()
    BUS = auto()
    TRUCK = auto()
    AMBULANCE = auto()
    FIRE_TRUCK = auto()
    POLICE = auto()

    @property
    def is_emergency(self) -> bool:
        """Check if this vehicle type is an emergency vehicle."""
        return self in (VehicleType.AMBULANCE, VehicleType.FIRE_TRUCK, VehicleType.POLICE)

    @property
    def display_name(self) -> str:
        """Human-readable name for display."""
        names = {
            VehicleType.CAR: "Car",
            VehicleType.BUS: "Bus",
            VehicleType.TRUCK: "Truck",
            VehicleType.AMBULANCE: "Ambulance",
            VehicleType.FIRE_TRUCK: "Fire Truck",
            VehicleType.POLICE: "Police",
        }
        return names.get(self, self.name)

    @property
    def color(self) -> str:
        """Color code for GUI rendering."""
        colors = {
            VehicleType.CAR: "#4FC3F7",       # Light blue
            VehicleType.BUS: "#FFB74D",        # Orange
            VehicleType.TRUCK: "#A1887F",      # Brown
            VehicleType.AMBULANCE: "#EF5350",  # Red
            VehicleType.FIRE_TRUCK: "#FF7043", # Deep orange
            VehicleType.POLICE: "#5C6BC0",     # Indigo
        }
        return colors.get(self, "#FFFFFF")


@dataclass
class Vehicle:
    """
    Represents a vehicle in the traffic simulation.
    
    Each vehicle has a unique ID, type, origin and destination
    junctions, and movement properties.
    """
    vehicle_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    vehicle_type: VehicleType = VehicleType.CAR
    origin: str = ""
    destination: str = ""
    speed: float = 1.0
    progress: float = 0.0  # 0.0 = at origin, 1.0 = at destination

    @property
    def is_emergency(self) -> bool:
        """Check if this is an emergency vehicle."""
        return self.vehicle_type.is_emergency

    def to_dict(self) -> dict:
        """Serialize vehicle to dictionary."""
        return {
            'vehicle_id': self.vehicle_id,
            'vehicle_type': self.vehicle_type.name,
            'origin': self.origin,
            'destination': self.destination,
            'speed': self.speed,
            'progress': self.progress,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Vehicle:
        """Deserialize vehicle from dictionary."""
        return cls(
            vehicle_id=data.get('vehicle_id', str(uuid.uuid4())[:8]),
            vehicle_type=VehicleType[data.get('vehicle_type', 'CAR')],
            origin=data.get('origin', ''),
            destination=data.get('destination', ''),
            speed=data.get('speed', 1.0),
            progress=data.get('progress', 0.0),
        )

    def __repr__(self) -> str:
        return (
            f"Vehicle({self.vehicle_type.display_name}, "
            f"{self.origin}→{self.destination}, "
            f"progress={self.progress:.1%})"
        )
