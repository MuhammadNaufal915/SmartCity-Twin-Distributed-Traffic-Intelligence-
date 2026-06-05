"""
Junction D - Virtual MCU for SmartCity Twin.
Bottom-right intersection. Neighbors: Junction B, Junction C.
"""

from __future__ import annotations

from nodes.base_junction import JunctionMCU
from communication.queues import NodeQueues


class JunctionD(JunctionMCU):
    """
    Junction D virtual MCU.
    
    Position: Bottom-Right of the city grid
    Neighbors: Junction B (north), Junction C (west)
    
    Runs as an independent process demonstrating
    parallel execution in the distributed system.
    """

    def __init__(self, node_queues: NodeQueues) -> None:
        super().__init__(
            node_id='junction_d',
            display_name='Junction D',
            node_queues=node_queues,
            neighbors=['junction_b', 'junction_c'],
        )
