"""
Efficiency calculator for SmartCity Twin.
Calculates parallel computing efficiency metrics
for the distributed simulation system.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EfficiencyCalculator:
    """
    Calculates parallel efficiency metrics.
    
    Efficiency = Speedup / Number_of_Nodes
    
    Perfect efficiency = 1.0 (100%)
    This means each processor is fully utilized.
    
    In practice, efficiency < 1.0 due to:
    - Communication overhead
    - Synchronization costs
    - Load imbalance
    """

    num_nodes: int = 4

    def calculate_efficiency(self, speedup: float) -> float:
        """
        Calculate parallel efficiency.
        
        Efficiency = Speedup / P
        where P = number of processing nodes
        
        Returns value between 0.0 and 1.0 (ideally)
        """
        if self.num_nodes <= 0:
            return 0.0
        return speedup / self.num_nodes

    def calculate_utilization(
        self,
        active_time: float,
        total_time: float,
    ) -> float:
        """
        Calculate resource utilization.
        
        Utilization = Active_Time / Total_Time
        """
        if total_time <= 0:
            return 0.0
        return min(active_time / total_time, 1.0)

    def calculate_overhead(
        self,
        speedup: float,
    ) -> float:
        """
        Calculate communication/synchronization overhead.
        
        Overhead = 1.0 - Efficiency
        """
        efficiency = self.calculate_efficiency(speedup)
        return max(0.0, 1.0 - efficiency)

    def calculate_scalability(
        self,
        speedup: float,
    ) -> str:
        """
        Assess scalability based on efficiency.
        
        Returns qualitative assessment.
        """
        efficiency = self.calculate_efficiency(speedup)
        if efficiency >= 0.9:
            return "Excellent"
        elif efficiency >= 0.7:
            return "Good"
        elif efficiency >= 0.5:
            return "Moderate"
        elif efficiency >= 0.3:
            return "Fair"
        else:
            return "Poor"

    def get_report(self, speedup: float, runtime: float = 0.0) -> dict:
        """Get full efficiency analysis report."""
        efficiency = self.calculate_efficiency(speedup)
        return {
            'num_nodes': self.num_nodes,
            'speedup': round(speedup, 2),
            'efficiency': round(efficiency, 4),
            'efficiency_pct': round(efficiency * 100, 1),
            'overhead': round(self.calculate_overhead(speedup), 4),
            'overhead_pct': round(self.calculate_overhead(speedup) * 100, 1),
            'scalability': self.calculate_scalability(speedup),
            'runtime': round(runtime, 2),
        }
