"""
Central Controller for SmartCity Twin.
Aggregates status from all junction nodes, issues commands,
and provides data to the GUI for real-time monitoring.
"""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Optional, Any
from multiprocessing import Queue

from communication.messaging import Message, MessageType, MessageBus
from communication.protocols import ControllerToNodeProtocol
from communication.queues import QueueManager, NODE_IDS
from nodes.junction_a import JunctionA
from nodes.junction_b import JunctionB
from nodes.junction_c import JunctionC
from nodes.junction_d import JunctionD

logger = logging.getLogger(__name__)


@dataclass
class NodeStatus:
    """Status snapshot for a single junction node."""
    node_id: str = ""
    display_name: str = ""
    vehicle_count: int = 0
    density_level: str = "LOW"
    light_state: str = "RED"
    green_duration: int = 10
    congestion: bool = False
    emergency: bool = False
    message_count: int = 0
    last_update: float = 0.0
    is_active: bool = False


class CentralController:
    """
    Central Controller for the distributed traffic system.
    
    Runs in the main process alongside the GUI.
    Responsibilities:
    - Collect status updates from all junction MCUs
    - Issue control commands to nodes
    - Maintain global system state for GUI consumption
    - Track message flow and performance metrics
    """

    DISPLAY_NAMES = {
        'junction_a': 'Junction A',
        'junction_b': 'Junction B',
        'junction_c': 'Junction C',
        'junction_d': 'Junction D',
    }

    def __init__(self) -> None:
        self._queue_manager = QueueManager()
        self._message_bus = MessageBus()
        self._protocol = ControllerToNodeProtocol('controller')
        
        # Node processes
        self._processes: dict[str, Any] = {}
        
        # Node status
        self._node_status: dict[str, NodeStatus] = {}
        for node_id in NODE_IDS:
            self._node_status[node_id] = NodeStatus(
                node_id=node_id,
                display_name=self.DISPLAY_NAMES[node_id],
            )

        # Event log
        self._event_log: list[dict] = []
        self._max_log_size: int = 500

        # Metrics
        self._start_time: float = 0.0
        self._total_messages: int = 0
        self._node_updates: int = 0
        self._is_running: bool = False
        self._is_paused: bool = False

        # Receive queues (node → controller)
        self._receive_queues: dict[str, Queue] = {}
        # Send queues (controller → node)
        self._send_queues: dict[str, Queue] = {}

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    @property
    def runtime(self) -> float:
        """Simulation runtime in seconds."""
        if self._start_time == 0:
            return 0.0
        return time.time() - self._start_time

    @property
    def total_messages(self) -> int:
        return self._total_messages

    @property
    def node_updates(self) -> int:
        return self._node_updates

    def start(self) -> None:
        """Start all junction processes and begin simulation."""
        if self._is_running:
            return

        logger.info("Starting Central Controller...")

        # Initialize queues
        self._queue_manager.initialize()
        self._receive_queues = self._queue_manager.get_controller_receive_queues()
        self._send_queues = self._queue_manager.get_controller_send_queues()

        # Create and start junction processes
        junction_classes = {
            'junction_a': JunctionA,
            'junction_b': JunctionB,
            'junction_c': JunctionC,
            'junction_d': JunctionD,
        }

        for node_id, cls in junction_classes.items():
            node_queues = self._queue_manager.get_node_queues(node_id)
            process = cls(node_queues)
            process.start()
            self._processes[node_id] = process
            self._node_status[node_id].is_active = True
            self._add_log('INFO', f'{self.DISPLAY_NAMES[node_id]} MCU started (PID: {process.pid})')

        self._start_time = time.time()
        self._is_running = True
        self._is_paused = False
        self._add_log('INFO', 'Central Controller started — all nodes online')

    def stop(self) -> None:
        """Stop all junction processes and shut down."""
        if not self._is_running:
            return

        logger.info("Stopping Central Controller...")

        # Send shutdown to all nodes
        for node_id in NODE_IDS:
            if node_id in self._send_queues:
                self._protocol.send_shutdown(
                    self._send_queues[node_id],
                    node_id,
                )

        # Wait for processes to finish
        for node_id, process in self._processes.items():
            try:
                process.join(timeout=3)
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=1)
            except Exception:
                pass
            self._node_status[node_id].is_active = False

        self._processes.clear()
        self._queue_manager.cleanup()
        self._is_running = False
        self._is_paused = False
        self._add_log('INFO', 'Central Controller stopped — all nodes offline')

    def pause(self) -> None:
        """Pause simulation on all nodes."""
        if not self._is_running or self._is_paused:
            return
        for node_id in NODE_IDS:
            self._protocol.send_pause(self._send_queues[node_id], node_id)
        self._is_paused = True
        self._add_log('INFO', 'Simulation paused')

    def resume(self) -> None:
        """Resume simulation on all nodes."""
        if not self._is_running or not self._is_paused:
            return
        for node_id in NODE_IDS:
            self._protocol.send_resume(self._send_queues[node_id], node_id)
        self._is_paused = False
        self._add_log('INFO', 'Simulation resumed')

    def reset(self) -> None:
        """Reset simulation — stop and restart all nodes."""
        self.stop()
        # Reset metrics
        self._total_messages = 0
        self._node_updates = 0
        self._event_log.clear()
        self._message_bus.reset()
        for ns in self._node_status.values():
            ns.vehicle_count = 0
            ns.density_level = "LOW"
            ns.light_state = "RED"
            ns.green_duration = 10
            ns.congestion = False
            ns.emergency = False
            ns.message_count = 0
            ns.is_active = False
        self._add_log('INFO', 'Simulation reset')

    def generate_congestion(self, node_id: Optional[str] = None) -> None:
        """Generate congestion at a specific or random node."""
        if not self._is_running:
            return
        import random
        target = node_id or random.choice(NODE_IDS)
        self._protocol.send_generate_congestion(self._send_queues[target], target)
        self._add_log('WARNING', f'Congestion generated at {self.DISPLAY_NAMES[target]}')

    def generate_emergency(self, node_id: Optional[str] = None) -> None:
        """Generate emergency vehicle at a specific or random node."""
        if not self._is_running:
            return
        import random
        target = node_id or random.choice(NODE_IDS)
        self._protocol.send_generate_emergency(self._send_queues[target], target)
        self._add_log('EMERGENCY', f'Emergency vehicle generated at {self.DISPLAY_NAMES[target]}')

    def generate_traffic_surge(self, node_id: Optional[str] = None) -> None:
        """Generate traffic surge at a specific or random node."""
        if not self._is_running:
            return
        import random
        target = node_id or random.choice(NODE_IDS)
        self._protocol.send_traffic_surge(self._send_queues[target], target)
        self._add_log('WARNING', f'Traffic surge at {self.DISPLAY_NAMES[target]}')

    def poll_updates(self) -> None:
        """
        Poll all node queues for status updates.
        
        Called periodically by the GUI timer to collect
        the latest data from all junction processes.
        """
        if not self._is_running:
            return

        for node_id, queue in self._receive_queues.items():
            messages_processed = 0
            while messages_processed < 50:  # Limit per poll
                try:
                    if queue.empty():
                        break
                    data = queue.get_nowait()
                    msg = Message.from_dict(data)
                    self._message_bus.record_message(msg)
                    self._total_messages += 1
                    self._handle_node_message(node_id, msg)
                    messages_processed += 1
                except Exception:
                    break

    def _handle_node_message(self, node_id: str, msg: Message) -> None:
        """Handle a message received from a junction node."""
        status = self._node_status[node_id]
        name = self.DISPLAY_NAMES[node_id]

        if msg.msg_type == MessageType.STATUS_UPDATE:
            status.vehicle_count = msg.payload.get('vehicle_count', 0)
            status.density_level = msg.payload.get('density_level', 'LOW')
            status.light_state = msg.payload.get('light_state', 'RED')
            status.green_duration = msg.payload.get('green_duration', 10)
            status.congestion = msg.payload.get('congestion', False)
            status.emergency = msg.payload.get('emergency', False)
            status.message_count = msg.payload.get('message_count', 0)
            status.last_update = msg.timestamp
            status.is_active = True
            self._node_updates += 1

        elif msg.msg_type == MessageType.CONGESTION_ALERT:
            count = msg.payload.get('vehicle_count', 0)
            self._add_log(
                'WARNING',
                f'{name} detected congestion ({count} vehicles)'
            )

        elif msg.msg_type == MessageType.EMERGENCY_ALERT:
            v_type = msg.payload.get('vehicle_type', 'Unknown')
            self._add_log(
                'EMERGENCY',
                f'{v_type} detected at {name} — priority route enabled'
            )

        elif msg.msg_type == MessageType.TRAFFIC_PREDICTION:
            predicted = msg.payload.get('predicted_count', 0)
            if predicted > 10:
                self._add_log(
                    'INFO',
                    f'{name} sent traffic prediction: {predicted} vehicles incoming'
                )

    def get_node_status(self, node_id: str) -> NodeStatus:
        """Get current status for a specific node."""
        return self._node_status.get(node_id, NodeStatus())

    def get_all_status(self) -> dict[str, NodeStatus]:
        """Get status for all nodes."""
        return dict(self._node_status)

    def get_event_log(self) -> list[dict]:
        """Get the event log."""
        return list(self._event_log)

    def get_metrics(self) -> dict:
        """Get performance metrics."""
        runtime = self.runtime
        total_vehicles = sum(
            ns.vehicle_count for ns in self._node_status.values()
        )

        # Calculate parallel computing metrics
        num_nodes = len(NODE_IDS)
        # Simulated serial time (what it would take without parallelism)
        serial_time = runtime * num_nodes if runtime > 0 else 0
        parallel_time = runtime if runtime > 0 else 1
        speedup = serial_time / parallel_time if parallel_time > 0 else 0
        efficiency = speedup / num_nodes if num_nodes > 0 else 0

        # Task count from message count as proxy
        total_tasks = self._node_updates * 11  # Each update cycle = ~11 tasks

        return {
            'total_messages': self._total_messages,
            'node_updates': self._node_updates,
            'average_latency': self._calculate_avg_latency(),
            'simulation_runtime': runtime,
            'vehicle_throughput': total_vehicles,
            'parallel_tasks': total_tasks,
            'speedup': round(speedup, 2),
            'efficiency': round(efficiency, 2),
            'num_nodes': num_nodes,
        }

    def _calculate_avg_latency(self) -> float:
        """Calculate average message latency."""
        recent = self._message_bus.recent_messages[-100:]
        if not recent:
            return 0.0
        now = time.time()
        latencies = [now - m.timestamp for m in recent]
        return sum(latencies) / len(latencies) if latencies else 0.0

    def _add_log(self, level: str, message: str) -> None:
        """Add an entry to the event log."""
        entry = {
            'timestamp': time.time(),
            'level': level,
            'message': message,
        }
        self._event_log.append(entry)
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size:]
