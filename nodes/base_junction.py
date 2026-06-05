"""
Base Junction MCU for SmartCity Twin.
Abstract base class simulating a virtual microcontroller (MCU)
that runs as an independent process. Each junction inherits
from this class and operates concurrently without shared memory.
"""

from __future__ import annotations

import time
import random
import logging
from multiprocessing import Process
from typing import Optional, Any

from communication.messaging import Message, MessageType, MessagePriority
from communication.protocols import NodeToControllerProtocol, NodeToNodeProtocol
from communication.queues import NodeQueues, NEIGHBOR_MAP
from simulation.vehicle import Vehicle, VehicleType
from simulation.traffic_logic import TrafficLogic, TrafficDensityLevel
from simulation.traffic_generator import TrafficGenerator
from simulation.emergency_events import EmergencyManager, EmergencyEvent


class JunctionMCU(Process):
    """
    Virtual Microcontroller Unit (MCU) simulating a traffic junction.
    
    Each instance runs as a separate OS process, demonstrating:
    - Task Parallelism: concurrent execution with other MCUs
    - Distributed Communication: message passing via queues
    - Independent Node Processing: no shared memory
    - Multi-MCU Architecture: each MCU maintains its own state
    
    Main Loop (executed every cycle):
    1. Vehicle Generation
    2. Vehicle Movement  
    3. Traffic Density Calculation
    4. Green Time Calculation
    5. Congestion Detection
    6. Emergency Detection
    7. Status Reporting
    """

    # Simulation timing
    CYCLE_INTERVAL: float = 1.0        # Main loop interval (seconds)
    GENERATION_INTERVAL: float = 3.0    # Vehicle generation interval
    REPORT_INTERVAL: float = 0.5        # Status report interval

    def __init__(
        self,
        node_id: str,
        display_name: str,
        node_queues: NodeQueues,
        neighbors: list[str],
    ) -> None:
        super().__init__(daemon=True, name=f"MCU-{display_name}")
        
        self.node_id = node_id
        self.display_name = display_name
        self._node_queues = node_queues
        self._neighbors = neighbors

        # MCU State (local to this process — no shared memory)
        self._vehicle_count: int = 0
        self._vehicles: list[Vehicle] = []
        self._incoming_vehicles: list[Vehicle] = []
        self._outgoing_vehicles: list[Vehicle] = []
        self._traffic_density: TrafficDensityLevel = TrafficDensityLevel.LOW
        self._light_state: str = "RED"
        self._green_duration: int = TrafficLogic.BASE_GREEN_TIME
        self._congestion_status: bool = False
        self._emergency_status: bool = False
        self._message_count: int = 0
        self._neighbor_predictions: dict[str, bool] = {}
        self._tasks_executed: int = 0

        # Internal components
        self._traffic_generator = TrafficGenerator(node_id)
        self._emergency_manager = EmergencyManager(node_id)
        self._node_protocol = NodeToControllerProtocol(node_id)
        self._peer_protocol = NodeToNodeProtocol(node_id)

        # Timing
        self._last_generation_time: float = 0.0
        self._last_report_time: float = 0.0
        self._cycle_start_time: float = 0.0
        self._light_cycle_start: float = 0.0

        # Control flags
        self._running: bool = True
        self._paused: bool = False

    def run(self) -> None:
        """
        Main MCU execution loop (runs in separate process).
        
        Continuously performs all MCU tasks in parallel with
        other junction processes.
        """
        logging.basicConfig(
            level=logging.INFO,
            format=f'[{self.display_name}] %(message)s'
        )
        
        self._cycle_start_time = time.time()
        # Berikan offset awal acak agar siklus lampu tidak sinkron bersamaan (lebih realistis)
        self._light_cycle_start = time.time() - random.uniform(0, 15)
        self._last_generation_time = time.time()
        self._last_report_time = time.time()

        while self._running:
            try:
                if self._paused:
                    time.sleep(0.1)
                    self._process_incoming_messages()
                    continue

                cycle_start = time.time()

                # 1. Process incoming messages
                self._process_incoming_messages()
                self._tasks_executed += 1

                # 2. Generate vehicles (periodic)
                if time.time() - self._last_generation_time >= self.GENERATION_INTERVAL:
                    self._generate_traffic()
                    self._last_generation_time = time.time()
                    self._tasks_executed += 1

                # 3. Move vehicles
                self._move_vehicles()
                self._tasks_executed += 1

                # 4. Calculate traffic density
                self._calculate_density()
                self._tasks_executed += 1

                # 5. Calculate green time
                self._calculate_green_time()
                self._tasks_executed += 1

                # 6. Update traffic light state
                self._update_light_state()
                self._tasks_executed += 1

                # 7. Detect congestion
                self._detect_congestion()
                self._tasks_executed += 1

                # 8. Detect emergencies
                self._detect_emergencies()
                self._tasks_executed += 1

                # 9. Update emergency manager
                self._emergency_manager.update()
                self._emergency_status = self._emergency_manager.has_active_emergency
                self._tasks_executed += 1

                # 10. Send traffic predictions to neighbors
                self._send_predictions()
                self._tasks_executed += 1

                # 11. Report status to controller
                if time.time() - self._last_report_time >= self.REPORT_INTERVAL:
                    self._report_status()
                    self._last_report_time = time.time()
                    self._tasks_executed += 1

                # Sleep to maintain cycle interval
                elapsed = time.time() - cycle_start
                sleep_time = max(0.05, self.CYCLE_INTERVAL - elapsed)
                time.sleep(sleep_time)

            except Exception as e:
                logging.error(f"MCU Error: {e}")
                time.sleep(0.5)

    def _process_incoming_messages(self) -> None:
        """Process all incoming messages from controller and neighbors."""
        # Messages from controller
        while True:
            msg = self._node_protocol.receive(self._node_queues.from_controller)
            if msg is None:
                break
            self._handle_controller_message(msg)
            self._message_count += 1

        # Messages from neighbors
        for neighbor_id, queue in self._node_queues.from_neighbors.items():
            while True:
                msg = self._peer_protocol.receive(queue)
                if msg is None:
                    break
                self._handle_neighbor_message(msg, neighbor_id)
                self._message_count += 1

    def _handle_controller_message(self, msg: Message) -> None:
        """Handle a message from the central controller."""
        if msg.msg_type == MessageType.SHUTDOWN:
            self._running = False
        elif msg.msg_type == MessageType.PAUSE:
            self._paused = True
        elif msg.msg_type == MessageType.RESUME:
            self._paused = False
        elif msg.msg_type == MessageType.GENERATE_CONGESTION:
            # Force congestion by generating 45+ vehicles
            surge = self._traffic_generator.generate_vehicles(count=45)
            self._vehicles.extend(surge)
            self._vehicle_count = len(self._vehicles)
        elif msg.msg_type == MessageType.GENERATE_EMERGENCY:
            # Generate emergency vehicle
            emg = self._traffic_generator.generate_emergency_vehicle()
            self._vehicles.append(emg)
            self._vehicle_count = len(self._vehicles)
        elif msg.msg_type == MessageType.TRAFFIC_SURGE:
            surge = self._traffic_generator.generate_traffic_surge()
            self._vehicles.extend(surge)
            self._vehicle_count = len(self._vehicles)
        elif msg.msg_type == MessageType.GREEN_TIME_UPDATE:
            override = msg.payload.get('green_time')
            if override is not None:
                self._green_duration = int(override)

    def _handle_neighbor_message(self, msg: Message, neighbor_id: str) -> None:
        """Handle a message from a neighboring junction."""
        if msg.msg_type == MessageType.TRAFFIC_PREDICTION:
            predicted = msg.payload.get('predicted_count', 0)
            self._neighbor_predictions[neighbor_id] = predicted > 5
        elif msg.msg_type == MessageType.VEHICLE_TRANSFER:
            incoming_count = msg.payload.get('vehicle_count', 0)
            # Create incoming vehicles
            for _ in range(min(incoming_count, 10)):
                v = Vehicle(
                    vehicle_type=random.choice([VehicleType.CAR, VehicleType.BUS, VehicleType.TRUCK]),
                    origin=neighbor_id,
                    destination=self.node_id,
                    speed=random.uniform(0.5, 1.5),
                )
                self._incoming_vehicles.append(v)
        elif msg.msg_type == MessageType.CONGESTION_ALERT:
            # Neighbor is congested — adjust predictions
            self._neighbor_predictions[neighbor_id] = True
        elif msg.msg_type == MessageType.EMERGENCY_ALERT:
            # Emergency approaching from neighbor — prepare
            self._neighbor_predictions[neighbor_id] = True

    def _generate_traffic(self) -> None:
        """Generate random traffic vehicles."""
        # Random count between 1-15 per cycle for realistic flow
        count = random.randint(1, 15)
        new_vehicles = self._traffic_generator.generate_vehicles(count=count)
        self._vehicles.extend(new_vehicles)
        self._vehicle_count = len(self._vehicles)

    def _move_vehicles(self) -> None:
        """
        Move vehicles through the junction.
        Vehicles progress toward their destination and are
        transferred to neighbors when they complete.
        """
        # Process incoming vehicles
        self._vehicles.extend(self._incoming_vehicles)
        self._incoming_vehicles.clear()

        remaining: list[Vehicle] = []
        outgoing_by_dest: dict[str, int] = {}

        for vehicle in self._vehicles:
            # Progress the vehicle
            vehicle.progress += vehicle.speed * 0.1

            if vehicle.progress >= 1.0:
                # Vehicle has passed through — transfer to destination
                dest = vehicle.destination
                outgoing_by_dest[dest] = outgoing_by_dest.get(dest, 0) + 1
                self._outgoing_vehicles.append(vehicle)
            else:
                remaining.append(vehicle)

        self._vehicles = remaining
        self._vehicle_count = len(self._vehicles)

        # Send outgoing vehicles to neighbors
        for dest_id, count in outgoing_by_dest.items():
            if dest_id in self._node_queues.to_neighbors:
                self._peer_protocol.send_vehicle_transfer(
                    self._node_queues.to_neighbors[dest_id],
                    dest_id,
                    count,
                )

        # Clear outgoing list periodically
        if len(self._outgoing_vehicles) > 100:
            self._outgoing_vehicles = self._outgoing_vehicles[-20:]

    def _calculate_density(self) -> None:
        """Calculate current traffic density level."""
        self._traffic_density = TrafficLogic.calculate_density_level(
            self._vehicle_count
        )

    def _calculate_green_time(self) -> None:
        """Calculate optimal green light duration."""
        has_prediction = any(self._neighbor_predictions.values())
        self._green_duration = TrafficLogic.calculate_green_time(
            self._traffic_density,
            neighbor_prediction=has_prediction,
        )

    def _update_light_state(self) -> None:
        """Update traffic light state based on cycle timing."""
        if self._emergency_status:
            self._light_state = "GREEN"  # Emergency override
        else:
            elapsed = time.time() - self._light_cycle_start
            self._light_state = TrafficLogic.get_light_cycle_state(
                elapsed,
                self._green_duration,
            )
            # Reset cycle if complete
            cycle_len = self._green_duration + 3 + 5  # green + yellow + red
            if elapsed >= cycle_len:
                self._light_cycle_start = time.time()

    def _detect_congestion(self) -> None:
        """Detect and handle congestion condition."""
        was_congested = self._congestion_status
        self._congestion_status = TrafficLogic.detect_congestion(self._vehicle_count)

        if self._congestion_status and not was_congested:
            # New congestion detected — alert controller and neighbors
            self._node_protocol.send_congestion_alert(
                self._node_queues.to_controller,
                self._vehicle_count,
            )
            # Notify neighbors
            for neighbor_id, queue in self._node_queues.to_neighbors.items():
                self._peer_protocol.send_congestion_warning(
                    queue,
                    neighbor_id,
                    self._vehicle_count,
                )

    def _detect_emergencies(self) -> None:
        """Detect emergency vehicles and trigger emergency protocol."""
        emergency_vehicles = TrafficLogic.detect_emergency(self._vehicles)

        for vehicle in emergency_vehicles:
            event = self._emergency_manager.detect_and_create(
                vehicle,
                self._neighbors,
            )
            if event is not None:
                # Alert controller
                self._node_protocol.send_emergency_alert(
                    self._node_queues.to_controller,
                    vehicle.vehicle_type.name,
                    event.to_dict(),
                )
                # Alert neighbors
                for neighbor_id, queue in self._node_queues.to_neighbors.items():
                    self._peer_protocol.send_emergency_notification(
                        queue,
                        neighbor_id,
                        vehicle.vehicle_type.name,
                    )
                # Remove emergency vehicle from regular traffic after detection
                if vehicle in self._vehicles:
                    self._vehicles.remove(vehicle)
                    self._vehicle_count = len(self._vehicles)

    def _send_predictions(self) -> None:
        """Send traffic predictions to neighboring junctions."""
        for neighbor_id, queue in self._node_queues.to_neighbors.items():
            # Predict vehicles heading toward this neighbor
            predicted = sum(
                1 for v in self._vehicles
                if v.destination == neighbor_id
            )
            self._peer_protocol.send_traffic_prediction(
                queue,
                neighbor_id,
                predicted,
            )

    def _report_status(self) -> None:
        """Report current MCU status to central controller."""
        self._node_protocol.send_status_update(
            self._node_queues.to_controller,
            vehicle_count=self._vehicle_count,
            density_level=self._traffic_density.value,
            light_state=self._light_state,
            green_duration=self._green_duration,
            congestion=self._congestion_status,
            emergency=self._emergency_status,
            message_count=self._message_count,
        )

    def get_state_snapshot(self) -> dict:
        """Get a snapshot of current MCU state (for serialization)."""
        return {
            'node_id': self.node_id,
            'display_name': self.display_name,
            'vehicle_count': self._vehicle_count,
            'traffic_density': self._traffic_density.value,
            'light_state': self._light_state,
            'green_duration': self._green_duration,
            'congestion_status': self._congestion_status,
            'emergency_status': self._emergency_status,
            'message_count': self._message_count,
            'tasks_executed': self._tasks_executed,
            'timestamp': time.time(),
        }
