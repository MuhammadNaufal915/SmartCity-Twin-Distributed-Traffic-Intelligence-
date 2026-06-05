"""
Messaging system for SmartCity Twin.
Defines message types, message dataclass, and message bus
for inter-process communication between virtual MCUs.
"""

from __future__ import annotations

import time
import json
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import Any, Optional


class MessageType(Enum):
    """Types of messages exchanged between nodes and controller."""
    VEHICLE_COUNT = auto()
    CONGESTION_ALERT = auto()
    EMERGENCY_ALERT = auto()
    TRAFFIC_PREDICTION = auto()
    STATUS_UPDATE = auto()
    CONTROL_COMMAND = auto()
    HEARTBEAT = auto()
    VEHICLE_TRANSFER = auto()
    GREEN_TIME_UPDATE = auto()
    EMERGENCY_CLEAR = auto()
    TRAFFIC_SURGE = auto()
    GENERATE_CONGESTION = auto()
    GENERATE_EMERGENCY = auto()
    SHUTDOWN = auto()
    PAUSE = auto()
    RESUME = auto()


class MessagePriority(Enum):
    """Priority levels for message processing."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3
    EMERGENCY = 4


@dataclass
class Message:
    """
    A message exchanged between nodes in the distributed system.
    
    All inter-process communication uses this standardized format.
    Messages are serializable for queue-based transport.
    """
    msg_type: MessageType
    source: str
    target: str
    payload: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    priority: MessagePriority = MessagePriority.NORMAL
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        """Serialize message to dictionary for queue transport."""
        return {
            'msg_type': self.msg_type.name,
            'source': self.source,
            'target': self.target,
            'payload': self.payload,
            'timestamp': self.timestamp,
            'priority': self.priority.value,
            'msg_id': self.msg_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Message:
        """Deserialize message from dictionary."""
        return cls(
            msg_type=MessageType[data['msg_type']],
            source=data['source'],
            target=data['target'],
            payload=data.get('payload', {}),
            timestamp=data.get('timestamp', time.time()),
            priority=MessagePriority(data.get('priority', 1)),
            msg_id=data.get('msg_id', str(uuid.uuid4())[:8]),
        )

    def to_json(self) -> str:
        """Serialize message to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> Message:
        """Deserialize message from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def __repr__(self) -> str:
        return (
            f"Message(type={self.msg_type.name}, "
            f"src={self.source}, dst={self.target}, "
            f"priority={self.priority.name}, id={self.msg_id})"
        )


class MessageBus:
    """
    Central message routing system.
    
    Routes messages between nodes based on target field.
    Used by the Central Controller to manage message flow.
    """

    def __init__(self) -> None:
        self._message_count: int = 0
        self._message_log: list[Message] = []
        self._max_log_size: int = 1000

    @property
    def message_count(self) -> int:
        """Total number of messages routed."""
        return self._message_count

    @property
    def recent_messages(self) -> list[Message]:
        """Recent message log."""
        return list(self._message_log)

    def record_message(self, message: Message) -> None:
        """Record a message in the bus log."""
        self._message_count += 1
        self._message_log.append(message)
        if len(self._message_log) > self._max_log_size:
            self._message_log = self._message_log[-self._max_log_size:]

    def get_stats(self) -> dict:
        """Get message bus statistics."""
        type_counts: dict[str, int] = {}
        for msg in self._message_log:
            name = msg.msg_type.name
            type_counts[name] = type_counts.get(name, 0) + 1

        return {
            'total_messages': self._message_count,
            'log_size': len(self._message_log),
            'type_distribution': type_counts,
        }

    def reset(self) -> None:
        """Reset message bus state."""
        self._message_count = 0
        self._message_log.clear()
