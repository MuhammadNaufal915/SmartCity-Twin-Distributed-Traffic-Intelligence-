"""
Junction C - Virtual MCU for SmartCity Twin.
Bottom-left intersection. Neighbors: Junction A, Junction D.
"""

from __future__ import annotations

from nodes.base_junction import JunctionMCU
from communication.queues import NodeQueues


class JunctionC(JunctionMCU):
    """
    Junction C virtual MCU.
    
    Position: Bottom-Left of the city grid
    Neighbors: Junction A (north), Junction D (east)
    
    Runs as an independent process demonstrating
    parallel execution in the distributed system.
    """

    def __init__(self, node_queues: NodeQueues) -> None:
        super().__init__(
            node_id='junction_c',
            display_name='Junction C',
            node_queues=node_queues,
            neighbors=['junction_a', 'junction_d'],
        )
