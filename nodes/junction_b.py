"""
Junction B - Virtual MCU for SmartCity Twin.
Top-right intersection. Neighbors: Junction A, Junction D.
"""

from __future__ import annotations

from nodes.base_junction import JunctionMCU
from communication.queues import NodeQueues


class JunctionB(JunctionMCU):
    """
    Junction B virtual MCU.
    
    Position: Top-Right of the city grid
    Neighbors: Junction A (west), Junction D (south)
    
    Runs as an independent process demonstrating
    parallel execution in the distributed system.
    """

    def __init__(self, node_queues: NodeQueues) -> None:
        super().__init__(
            node_id='junction_b',
            display_name='Junction B',
            node_queues=node_queues,
            neighbors=['junction_a', 'junction_d'],
        )
