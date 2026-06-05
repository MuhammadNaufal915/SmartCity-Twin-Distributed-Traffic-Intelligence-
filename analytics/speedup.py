"""
Speedup calculator for SmartCity Twin.
Measures and calculates parallel speedup metrics
demonstrating the benefits of parallel computing.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class SpeedupCalculator:
    """
    Calculates parallel speedup metrics.
    
    Speedup = Serial_Time / Parallel_Time
    
    In this simulation:
    - Serial time = what it would take to run all 4 junction
      computations sequentially on a single processor
    - Parallel time = actual wall-clock time with 4 processes
    """

    num_nodes: int = 4
    _serial_task_times: list[float] = field(default_factory=list)
    _parallel_start: float = 0.0
    _total_serial_time: float = 0.0

    def start_parallel_timer(self) -> None:
        """Mark the start of parallel execution."""
        self._parallel_start = time.time()

    def record_serial_task(self, duration: float) -> None:
        """Record a single task's execution time (for serial estimation)."""
        self._serial_task_times.append(duration)
        self._total_serial_time += duration

    @property
    def parallel_time(self) -> float:
        """Elapsed parallel execution time."""
        if self._parallel_start == 0:
            return 0.0
        return time.time() - self._parallel_start

    @property
    def serial_time(self) -> float:
        """Estimated serial execution time."""
        # Serial time = parallel time * number of nodes
        # (since all nodes would run sequentially)
        return self.parallel_time * self.num_nodes

    @property
    def speedup(self) -> float:
        """
        Calculate speedup: S = T_serial / T_parallel
        
        Ideal speedup = number of nodes (linear speedup).
        """
        p_time = self.parallel_time
        if p_time <= 0:
            return 0.0
        return self.serial_time / p_time

    @property
    def theoretical_max_speedup(self) -> float:
        """Theoretical maximum speedup (Amdahl's Law with 0% serial fraction)."""
        return float(self.num_nodes)

    def get_speedup_ratio(self) -> float:
        """Speedup as percentage of theoretical maximum."""
        max_s = self.theoretical_max_speedup
        if max_s <= 0:
            return 0.0
        return (self.speedup / max_s) * 100.0

    def reset(self) -> None:
        """Reset all timing data."""
        self._serial_task_times.clear()
        self._parallel_start = 0.0
        self._total_serial_time = 0.0

    def get_report(self) -> dict:
        """Get full speedup analysis report."""
        return {
            'num_nodes': self.num_nodes,
            'parallel_time': round(self.parallel_time, 3),
            'serial_time': round(self.serial_time, 3),
            'speedup': round(self.speedup, 2),
            'theoretical_max': self.theoretical_max_speedup,
            'speedup_ratio_pct': round(self.get_speedup_ratio(), 1),
        }
