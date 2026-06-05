"""
Queue management for SmartCity Twin.
Manages multiprocessing.Queue instances for all inter-process
communication channels in the distributed system.
"""

from __future__ import annotations

from multiprocessing import Queue
from dataclasses import dataclass, field
from typing import Optional


# Node identifiers
NODE_IDS = ['junction_a', 'junction_b', 'junction_c', 'junction_d']
CONTROLLER_ID = 'controller'

# Neighbor topology: each junction and its connected neighbors
NEIGHBOR_MAP: dict[str, list[str]] = {
    'junction_a': ['junction_b', 'junction_c'],
    'junction_b': ['junction_a', 'junction_d'],
    'junction_c': ['junction_a', 'junction_d'],
    'junction_d': ['junction_b', 'junction_c'],
}


@dataclass
class NodeQueues:
    """
    Queue set for a single junction node.
    
    Each node has:
    - to_controller: sends status/alerts to central controller
    - from_controller: receives commands from central controller
    - to_neighbors: dict of queues to send to each neighbor
    - from_neighbors: dict of queues to receive from each neighbor
    """
    node_id: str
    to_controller: Queue = field(default_factory=Queue)
    from_controller: Queue = field(default_factory=Queue)
    to_neighbors: dict[str, Queue] = field(default_factory=dict)
    from_neighbors: dict[str, Queue] = field(default_factory=dict)


class QueueManager:
    """
    Manages all communication queues in the distributed system.
    
    Creates and provides access to queues for:
    - Node → Controller communication
    - Controller → Node communication
    - Node → Node (neighbor) communication
    
    All queues are multiprocessing.Queue instances that are safe
    for cross-process communication without shared memory.
    """

    def __init__(self) -> None:
        self._node_queues: dict[str, NodeQueues] = {}
        self._initialized: bool = False

    def initialize(self) -> None:
        """
        Create all queues for the distributed system.
        
        Queue topology:
        - 4 node→controller queues
        - 4 controller→node queues
        - Inter-node queues based on neighbor map
        """
        if self._initialized:
            return

        # Create node queue sets
        for node_id in NODE_IDS:
            self._node_queues[node_id] = NodeQueues(
                node_id=node_id,
                to_controller=Queue(),
                from_controller=Queue(),
            )

        # Create inter-node queues based on neighbor topology
        # For each pair of neighbors, create a shared queue in each direction
        created_pairs: set[tuple[str, str]] = set()
        for node_id, neighbors in NEIGHBOR_MAP.items():
            for neighbor_id in neighbors:
                pair = tuple(sorted([node_id, neighbor_id]))
                if pair not in created_pairs:
                    # Create bidirectional queues
                    q_forward = Queue()  # node -> neighbor
                    q_backward = Queue()  # neighbor -> node

                    self._node_queues[node_id].to_neighbors[neighbor_id] = q_forward
                    self._node_queues[neighbor_id].from_neighbors[node_id] = q_forward

                    self._node_queues[neighbor_id].to_neighbors[node_id] = q_backward
                    self._node_queues[node_id].from_neighbors[neighbor_id] = q_backward

                    created_pairs.add(pair)

        self._initialized = True

    def get_node_queues(self, node_id: str) -> NodeQueues:
        """Get the complete queue set for a node."""
        if not self._initialized:
            raise RuntimeError("QueueManager not initialized. Call initialize() first.")
        if node_id not in self._node_queues:
            raise ValueError(f"Unknown node ID: {node_id}")
        return self._node_queues[node_id]

    def get_controller_receive_queues(self) -> dict[str, Queue]:
        """Get all node→controller queues (for controller to receive from)."""
        return {
            node_id: nq.to_controller
            for node_id, nq in self._node_queues.items()
        }

    def get_controller_send_queues(self) -> dict[str, Queue]:
        """Get all controller→node queues (for controller to send to)."""
        return {
            node_id: nq.from_controller
            for node_id, nq in self._node_queues.items()
        }

    def get_all_node_ids(self) -> list[str]:
        """Get list of all node IDs."""
        return list(NODE_IDS)

    def get_neighbors(self, node_id: str) -> list[str]:
        """Get neighbor IDs for a given node."""
        return NEIGHBOR_MAP.get(node_id, [])

    def cleanup(self) -> None:
        """Close all queues and clean up resources."""
        for nq in self._node_queues.values():
            try:
                nq.to_controller.close()
                nq.from_controller.close()
                for q in nq.to_neighbors.values():
                    q.close()
                for q in nq.from_neighbors.values():
                    q.close()
            except Exception:
                pass
        self._node_queues.clear()
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def get_queue_stats(self) -> dict:
        """Get approximate sizes of all queues for monitoring."""
        stats: dict[str, dict] = {}
        for node_id, nq in self._node_queues.items():
            try:
                stats[node_id] = {
                    'to_controller': nq.to_controller.qsize(),
                    'from_controller': nq.from_controller.qsize(),
                    'to_neighbors': {
                        n: q.qsize()
                        for n, q in nq.to_neighbors.items()
                    },
                    'from_neighbors': {
                        n: q.qsize()
                        for n, q in nq.from_neighbors.items()
                    },
                }
            except NotImplementedError:
                # qsize() not reliable on all platforms
                stats[node_id] = {'note': 'qsize not available'}
        return stats
