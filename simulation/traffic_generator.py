"""
Traffic generator for SmartCity Twin.
Generates random traffic including regular vehicles,
emergency vehicles, and traffic surges.
"""

from __future__ import annotations

import random
from typing import Optional

from simulation.vehicle import Vehicle, VehicleType
from communication.queues import NODE_IDS, NEIGHBOR_MAP


class TrafficGenerator:
    """
    Generates random traffic for a junction node.
    
    Each MCU has its own TrafficGenerator instance that
    independently produces vehicles at configurable intervals.
    """

    # Vehicle count range per generation cycle
    MIN_VEHICLES: int = 0
    MAX_VEHICLES: int = 50

    # Probability weights for vehicle types (regular traffic)
    REGULAR_WEIGHTS: dict[VehicleType, float] = {
        VehicleType.CAR: 0.60,
        VehicleType.BUS: 0.20,
        VehicleType.TRUCK: 0.20,
    }

    # Emergency vehicle types
    EMERGENCY_TYPES: list[VehicleType] = [
        VehicleType.AMBULANCE,
        VehicleType.FIRE_TRUCK,
        VehicleType.POLICE,
    ]

    # Probability of emergency vehicle in regular generation
    EMERGENCY_PROBABILITY: float = 0.05

    def __init__(self, junction_id: str) -> None:
        self.junction_id = junction_id
        self._total_generated: int = 0
        self._emergency_generated: int = 0

    @property
    def total_generated(self) -> int:
        return self._total_generated

    @property
    def emergency_generated(self) -> int:
        return self._emergency_generated

    def generate_vehicles(
        self,
        count: Optional[int] = None,
    ) -> list[Vehicle]:
        """
        Generate a batch of random vehicles.
        
        Args:
            count: Number of vehicles to generate. 
                   If None, random count in [MIN, MAX] range.
        
        Returns:
            List of generated Vehicle instances.
        """
        if count is None:
            count = random.randint(self.MIN_VEHICLES, self.MAX_VEHICLES)

        vehicles: list[Vehicle] = []
        neighbors = NEIGHBOR_MAP.get(self.junction_id, [])

        for _ in range(count):
            # Determine vehicle type
            if random.random() < self.EMERGENCY_PROBABILITY:
                v_type = random.choice(self.EMERGENCY_TYPES)
                self._emergency_generated += 1
            else:
                types = list(self.REGULAR_WEIGHTS.keys())
                weights = list(self.REGULAR_WEIGHTS.values())
                v_type = random.choices(types, weights=weights, k=1)[0]

            # Assign destination (random neighbor)
            destination = random.choice(neighbors) if neighbors else self.junction_id

            vehicle = Vehicle(
                vehicle_type=v_type,
                origin=self.junction_id,
                destination=destination,
                speed=random.uniform(0.5, 2.0),
            )
            vehicles.append(vehicle)

        self._total_generated += len(vehicles)
        return vehicles

    def generate_emergency_vehicle(self) -> Vehicle:
        """Generate a single emergency vehicle."""
        neighbors = NEIGHBOR_MAP.get(self.junction_id, [])
        destination = random.choice(neighbors) if neighbors else self.junction_id

        v_type = random.choice(self.EMERGENCY_TYPES)
        self._emergency_generated += 1
        self._total_generated += 1

        return Vehicle(
            vehicle_type=v_type,
            origin=self.junction_id,
            destination=destination,
            speed=2.0,  # Emergency vehicles move faster
        )

    def generate_traffic_surge(self) -> list[Vehicle]:
        """
        Generate a traffic surge (40-50 vehicles at once).
        Used for testing congestion detection.
        """
        return self.generate_vehicles(count=random.randint(40, 50))

    def reset(self) -> None:
        """Reset generator statistics."""
        self._total_generated = 0
        self._emergency_generated = 0
