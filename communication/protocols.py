"""
Communication protocols for SmartCity Twin.
Defines standardized protocols for node-to-controller,
node-to-node, and controller-to-node communication.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional
from multiprocessing import Queue

from communication.messaging import Message, MessageType, MessagePriority


class Protocol:
    """
    Base protocol class defining communication interface.
    
    All protocols follow the message-passing paradigm
    where no shared memory is used between processes.
    """

    def __init__(self, source_id: str) -> None:
        self.source_id = source_id
        self._sent_count: int = 0
        self._received_count: int = 0

    @property
    def sent_count(self) -> int:
        return self._sent_count

    @property
    def received_count(self) -> int:
        return self._received_count

    def create_message(
        self,
        msg_type: MessageType,
        target: str,
        payload: dict,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> Message:
        """Create a standardized message."""
        return Message(
            msg_type=msg_type,
            source=self.source_id,
            target=target,
            payload=payload,
            priority=priority,
        )

    def send(self, queue: Queue, message: Message) -> bool:
        """Send a message through a queue."""
        try:
            queue.put_nowait(message.to_dict())
            self._sent_count += 1
            return True
        except Exception:
            return False

    def receive(self, queue: Queue) -> Optional[Message]:
        """Receive a message from a queue (non-blocking)."""
        try:
            if not queue.empty():
                data = queue.get_nowait()
                self._received_count += 1
                return Message.from_dict(data)
        except Exception:
            pass
        return None

    def receive_all(self, queue: Queue) -> list[Message]:
        """Receive all available messages from a queue."""
        messages: list[Message] = []
        while True:
            msg = self.receive(queue)
            if msg is None:
                break
            messages.append(msg)
        return messages


class NodeToControllerProtocol(Protocol):
    """
    Protocol for junction nodes reporting to the central controller.
    
    Messages sent:
    - STATUS_UPDATE: Periodic status with all MCU state
    - CONGESTION_ALERT: When vehicle count exceeds threshold
    - EMERGENCY_ALERT: When emergency vehicle is detected
    """

    def send_status_update(
        self,
        queue: Queue,
        vehicle_count: int,
        density_level: str,
        light_state: str,
        green_duration: int,
        congestion: bool,
        emergency: bool,
        message_count: int,
    ) -> bool:
        """Send periodic status update to controller."""
        payload = {
            'vehicle_count': vehicle_count,
            'density_level': density_level,
            'light_state': light_state,
            'green_duration': green_duration,
            'congestion': congestion,
            'emergency': emergency,
            'message_count': message_count,
            'timestamp': time.time(),
        }
        msg = self.create_message(
            MessageType.STATUS_UPDATE,
            'controller',
            payload,
        )
        return self.send(queue, msg)

    def send_congestion_alert(self, queue: Queue, vehicle_count: int) -> bool:
        """Send congestion alert to controller."""
        payload = {
            'vehicle_count': vehicle_count,
            'alert_time': time.time(),
        }
        msg = self.create_message(
            MessageType.CONGESTION_ALERT,
            'controller',
            payload,
            priority=MessagePriority.HIGH,
        )
        return self.send(queue, msg)

    def send_emergency_alert(
        self,
        queue: Queue,
        vehicle_type: str,
        details: dict,
    ) -> bool:
        """Send emergency vehicle alert to controller."""
        payload = {
            'vehicle_type': vehicle_type,
            'details': details,
            'alert_time': time.time(),
        }
        msg = self.create_message(
            MessageType.EMERGENCY_ALERT,
            'controller',
            payload,
            priority=MessagePriority.EMERGENCY,
        )
        return self.send(queue, msg)


class NodeToNodeProtocol(Protocol):
    """
    Protocol for inter-junction communication.
    
    Messages sent:
    - TRAFFIC_PREDICTION: Expected incoming vehicles
    - VEHICLE_TRANSFER: Vehicles moving to neighbor
    - CONGESTION_ALERT: Warning neighbors about congestion
    - EMERGENCY_ALERT: Emergency vehicle approaching
    """

    def send_traffic_prediction(
        self,
        queue: Queue,
        target: str,
        predicted_count: int,
    ) -> bool:
        """Send traffic prediction to neighboring junction."""
        payload = {
            'predicted_count': predicted_count,
            'prediction_time': time.time(),
        }
        msg = self.create_message(
            MessageType.TRAFFIC_PREDICTION,
            target,
            payload,
        )
        return self.send(queue, msg)

    def send_vehicle_transfer(
        self,
        queue: Queue,
        target: str,
        vehicle_count: int,
    ) -> bool:
        """Notify neighbor about incoming vehicles."""
        payload = {
            'vehicle_count': vehicle_count,
            'transfer_time': time.time(),
        }
        msg = self.create_message(
            MessageType.VEHICLE_TRANSFER,
            target,
            payload,
        )
        return self.send(queue, msg)

    def send_congestion_warning(
        self,
        queue: Queue,
        target: str,
        vehicle_count: int,
    ) -> bool:
        """Warn neighbor about congestion."""
        payload = {
            'vehicle_count': vehicle_count,
            'warning_time': time.time(),
        }
        msg = self.create_message(
            MessageType.CONGESTION_ALERT,
            target,
            payload,
            priority=MessagePriority.HIGH,
        )
        return self.send(queue, msg)

    def send_emergency_notification(
        self,
        queue: Queue,
        target: str,
        vehicle_type: str,
    ) -> bool:
        """Notify neighbor about approaching emergency vehicle."""
        payload = {
            'vehicle_type': vehicle_type,
            'notification_time': time.time(),
        }
        msg = self.create_message(
            MessageType.EMERGENCY_ALERT,
            target,
            payload,
            priority=MessagePriority.EMERGENCY,
        )
        return self.send(queue, msg)


class ControllerToNodeProtocol(Protocol):
    """
    Protocol for central controller issuing commands to nodes.
    
    Messages sent:
    - CONTROL_COMMAND: Direct commands to nodes
    - GREEN_TIME_UPDATE: Override green time
    - SHUTDOWN: Graceful shutdown command
    """

    def send_control_command(
        self,
        queue: Queue,
        target: str,
        command: str,
        params: dict,
    ) -> bool:
        """Send control command to a junction node."""
        payload = {
            'command': command,
            'params': params,
            'command_time': time.time(),
        }
        msg = self.create_message(
            MessageType.CONTROL_COMMAND,
            target,
            payload,
            priority=MessagePriority.HIGH,
        )
        return self.send(queue, msg)

    def send_shutdown(self, queue: Queue, target: str) -> bool:
        """Send shutdown command to a junction node."""
        msg = self.create_message(
            MessageType.SHUTDOWN,
            target,
            {'reason': 'system_shutdown'},
            priority=MessagePriority.CRITICAL,
        )
        return self.send(queue, msg)

    def send_pause(self, queue: Queue, target: str) -> bool:
        """Send pause command to a junction node."""
        msg = self.create_message(
            MessageType.PAUSE,
            target,
            {},
            priority=MessagePriority.HIGH,
        )
        return self.send(queue, msg)

    def send_resume(self, queue: Queue, target: str) -> bool:
        """Send resume command to a junction node."""
        msg = self.create_message(
            MessageType.RESUME,
            target,
            {},
            priority=MessagePriority.HIGH,
        )
        return self.send(queue, msg)

    def send_generate_congestion(self, queue: Queue, target: str) -> bool:
        """Command a node to generate congestion."""
        msg = self.create_message(
            MessageType.GENERATE_CONGESTION,
            target,
            {},
            priority=MessagePriority.HIGH,
        )
        return self.send(queue, msg)

    def send_generate_emergency(self, queue: Queue, target: str) -> bool:
        """Command a node to generate emergency vehicle."""
        msg = self.create_message(
            MessageType.GENERATE_EMERGENCY,
            target,
            {},
            priority=MessagePriority.HIGH,
        )
        return self.send(queue, msg)

    def send_traffic_surge(self, queue: Queue, target: str) -> bool:
        """Command a node to generate traffic surge."""
        msg = self.create_message(
            MessageType.TRAFFIC_SURGE,
            target,
            {},
            priority=MessagePriority.HIGH,
        )
        return self.send(queue, msg)
