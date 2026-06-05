"""
Unit tests for the inter-process messaging system.
"""

from __future__ import annotations

import time

from communication.messaging import Message, MessageType, MessagePriority


def test_message_serialization() -> None:
    """Verify converting Message instances to/from dictionaries and JSON."""
    msg = Message(
        msg_type=MessageType.STATUS_UPDATE,
        source="junction_a",
        target="controller",
        payload={"vehicle_count": 12, "congestion": False},
        priority=MessagePriority.HIGH,
    )

    # Dictionary serialization
    serialized = msg.to_dict()
    assert serialized["msg_type"] == "STATUS_UPDATE"
    assert serialized["source"] == "junction_a"
    assert serialized["target"] == "controller"
    assert serialized["payload"]["vehicle_count"] == 12
    assert serialized["priority"] == MessagePriority.HIGH.value

    # Deserialization
    deserialized = Message.from_dict(serialized)
    assert deserialized.msg_id == msg.msg_id
    assert deserialized.msg_type == MessageType.STATUS_UPDATE
    assert deserialized.source == "junction_a"
    assert deserialized.target == "controller"
    assert deserialized.payload["vehicle_count"] == 12
    assert deserialized.priority == MessagePriority.HIGH


def test_json_serialization() -> None:
    """Verify JSON string serialization compatibility."""
    msg = Message(
        msg_type=MessageType.EMERGENCY_ALERT,
        source="junction_b",
        target="junction_d",
        payload={"vehicle_type": "AMBULANCE"},
        priority=MessagePriority.EMERGENCY,
    )

    json_str = msg.to_json()
    assert "EMERGENCY_ALERT" in json_str
    assert "junction_b" in json_str

    deserialized = Message.from_json(json_str)
    assert deserialized.msg_type == MessageType.EMERGENCY_ALERT
    assert deserialized.source == "junction_b"
    assert deserialized.target == "junction_d"
    assert deserialized.payload["vehicle_type"] == "AMBULANCE"
    assert deserialized.priority == MessagePriority.EMERGENCY
