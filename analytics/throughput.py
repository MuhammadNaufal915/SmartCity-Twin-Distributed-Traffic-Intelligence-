"""
Throughput tracker for SmartCity Twin.
Tracks vehicle and message throughput metrics
for the distributed traffic simulation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from collections import deque


@dataclass
class ThroughputTracker:
    """
    Tracks throughput metrics for the simulation.
    
    Measures:
    - Vehicle throughput (vehicles processed per second)
    - Message throughput (messages exchanged per second)
    """

    _vehicle_timestamps: deque = field(
        default_factory=lambda: deque(maxlen=1000)
    )
    _message_timestamps: deque = field(
        default_factory=lambda: deque(maxlen=1000)
    )
    _total_vehicles: int = 0
    _total_messages: int = 0
    _window_seconds: float = 60.0  # Sliding window for rate calculation

    def record_vehicle(self, count: int = 1) -> None:
        """Record vehicle(s) processed."""
        now = time.time()
        for _ in range(count):
            self._vehicle_timestamps.append(now)
        self._total_vehicles += count

    def record_message(self, count: int = 1) -> None:
        """Record message(s) exchanged."""
        now = time.time()
        for _ in range(count):
            self._message_timestamps.append(now)
        self._total_messages += count

    @property
    def vehicle_rate(self) -> float:
        """Current vehicle throughput (vehicles/second) in sliding window."""
        return self._calculate_rate(self._vehicle_timestamps)

    @property
    def message_rate(self) -> float:
        """Current message throughput (messages/second) in sliding window."""
        return self._calculate_rate(self._message_timestamps)

    @property
    def total_vehicles(self) -> int:
        return self._total_vehicles

    @property
    def total_messages(self) -> int:
        return self._total_messages

    def _calculate_rate(self, timestamps: deque) -> float:
        """Calculate rate from timestamps within the sliding window."""
        if not timestamps:
            return 0.0
        now = time.time()
        cutoff = now - self._window_seconds
        # Count entries within window
        count = sum(1 for t in timestamps if t >= cutoff)
        return count / self._window_seconds if self._window_seconds > 0 else 0.0

    def reset(self) -> None:
        """Reset all tracking data."""
        self._vehicle_timestamps.clear()
        self._message_timestamps.clear()
        self._total_vehicles = 0
        self._total_messages = 0

    def get_report(self) -> dict:
        """Get throughput analysis report."""
        return {
            'total_vehicles': self._total_vehicles,
            'total_messages': self._total_messages,
            'vehicle_rate': round(self.vehicle_rate, 2),
            'message_rate': round(self.message_rate, 2),
            'window_seconds': self._window_seconds,
        }
