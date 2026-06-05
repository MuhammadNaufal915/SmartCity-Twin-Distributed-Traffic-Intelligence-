"""
Emergency event handling for SmartCity Twin.
Manages emergency vehicle detection, priority routing,
and emergency lifecycle in the traffic simulation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from simulation.vehicle import Vehicle, VehicleType


@dataclass
class EmergencyEvent:
    """
    Represents an emergency event in the simulation.
    
    Created when an emergency vehicle is detected at a junction.
    Tracks the emergency lifecycle and priority routing.
    """
    event_id: str
    event_type: str  # 'AMBULANCE', 'FIRE_TRUCK', 'POLICE'
    junction: str
    vehicle: Vehicle
    timestamp: float = field(default_factory=time.time)
    priority_route: list[str] = field(default_factory=list)
    is_active: bool = True
    resolved_time: Optional[float] = None

    @property
    def duration(self) -> float:
        """Duration of the emergency event in seconds."""
        end = self.resolved_time or time.time()
        return end - self.timestamp

    def resolve(self) -> None:
        """Mark the emergency as resolved."""
        self.is_active = False
        self.resolved_time = time.time()

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'junction': self.junction,
            'vehicle_id': self.vehicle.vehicle_id,
            'vehicle_type': self.vehicle.vehicle_type.name,
            'timestamp': self.timestamp,
            'priority_route': self.priority_route,
            'is_active': self.is_active,
            'duration': self.duration,
        }


class EmergencyManager:
    """
    Manages emergency events for a junction node.
    
    Handles emergency detection, priority route calculation,
    and emergency lifecycle management.
    """

    # Emergency duration before auto-resolve (seconds)
    EMERGENCY_DURATION: float = 15.0

    def __init__(self, junction_id: str) -> None:
        self.junction_id = junction_id
        self._active_emergencies: list[EmergencyEvent] = []
        self._resolved_emergencies: list[EmergencyEvent] = []
        self._event_counter: int = 0

    @property
    def has_active_emergency(self) -> bool:
        """Check if there are any active emergencies."""
        return len(self._active_emergencies) > 0

    @property
    def active_count(self) -> int:
        return len(self._active_emergencies)

    @property
    def total_events(self) -> int:
        return self._event_counter

    def detect_and_create(
        self,
        vehicle: Vehicle,
        neighbors: list[str],
    ) -> Optional[EmergencyEvent]:
        """
        Detect emergency vehicle and create emergency event.
        
        Args:
            vehicle: The emergency vehicle detected
            neighbors: List of neighboring junction IDs for route
            
        Returns:
            EmergencyEvent if vehicle is emergency, None otherwise
        """
        if not vehicle.is_emergency:
            return None

        self._event_counter += 1
        event_id = f"EMG-{self.junction_id[-1].upper()}-{self._event_counter:04d}"

        # Calculate priority route through neighbors
        priority_route = [self.junction_id] + neighbors

        event = EmergencyEvent(
            event_id=event_id,
            event_type=vehicle.vehicle_type.name,
            junction=self.junction_id,
            vehicle=vehicle,
            priority_route=priority_route,
        )

        self._active_emergencies.append(event)
        return event

    def update(self) -> list[EmergencyEvent]:
        """
        Update emergency states, auto-resolve expired emergencies.
        
        Returns:
            List of newly resolved emergencies.
        """
        resolved: list[EmergencyEvent] = []
        still_active: list[EmergencyEvent] = []

        for event in self._active_emergencies:
            if event.duration >= self.EMERGENCY_DURATION:
                event.resolve()
                self._resolved_emergencies.append(event)
                resolved.append(event)
            else:
                still_active.append(event)

        self._active_emergencies = still_active
        return resolved

    def get_active_emergencies(self) -> list[EmergencyEvent]:
        """Get all currently active emergencies."""
        return list(self._active_emergencies)

    def get_emergency_stats(self) -> dict:
        """Get emergency statistics."""
        return {
            'active_count': len(self._active_emergencies),
            'resolved_count': len(self._resolved_emergencies),
            'total_events': self._event_counter,
        }

    def reset(self) -> None:
        """Reset emergency manager state."""
        self._active_emergencies.clear()
        self._resolved_emergencies.clear()
        self._event_counter = 0
