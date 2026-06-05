"""
Junction A - Virtual MCU for SmartCity Twin.
Top-left intersection. Neighbors: Junction B, Junction C.
"""

from __future__ import annotations

from nodes.base_junction import JunctionMCU
from communication.queues import NodeQueues


class JunctionA(JunctionMCU):
    """
    Junction A virtual MCU.
    
    Position: Top-Left of the city grid
    Neighbors: Junction B (east), Junction C (south)
    
    Runs as an independent process demonstrating
    parallel execution in the distributed system.
    """

    def __init__(self, node_queues: NodeQueues) -> None:
        super().__init__(
            node_id='junction_a',
            display_name='Junction A',
            node_queues=node_queues,
            neighbors=['junction_b', 'junction_c'],
        )
