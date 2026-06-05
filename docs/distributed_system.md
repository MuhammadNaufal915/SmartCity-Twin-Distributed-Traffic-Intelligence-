# Distributed System Design & Communication Protocols

This document details how the **SmartCity Twin** simulation models a distributed system. The system achieves decentralized traffic control and coordination by using message-passing communication protocols over independent OS process boundaries.

## Shared-Nothing Architecture

The simulator conforms to a **shared-nothing architecture**:
- Node processes have **no shared variables, global states, or lock-based memory protection** between them.
- All inter-process sync and data replication are performed by passing serialized data frames.
- This models physical embedded MCUs connected via serial buses (such as UART, CAN, or SPI).

---

## Message Packet Structure

All messages are modeled using the `Message` dataclass. The message is serialized into JSON strings or key-value structures before being injected into communication queues:

| Field | Type | Description |
| :--- | :--- | :--- |
| `msg_id` | `str` | Unique 8-character identifier generated using UUIDv4 for tracing. |
| `msg_type` | `str` | Type of message from the `MessageType` enum. |
| `source` | `str` | Node ID of the sending process (e.g. `'junction_a'`, `'controller'`). |
| `target` | `str` | Node ID of the target recipient process. |
| `payload` | `dict` | Key-value dictionary containing the actual content data. |
| `timestamp` | `float` | Epoch timestamp of message creation. |
| `priority` | `int` | Priority level (0-4) mapping to processing ordering. |

### Message Types
- `STATUS_UPDATE`: Telemetry reports sent from junction nodes to the Central Controller.
- `CONGESTION_ALERT`: Broadcast warning from a congested node to neighbors and controller.
- `EMERGENCY_ALERT`: Alert triggered by emergency vehicles requiring priority overrides.
- `TRAFFIC_PREDICTION`: Incoming vehicle count estimates passed between neighboring nodes.
- `CONTROL_COMMAND`: Command frames (e.g. pause, resume, reset) sent from the controller.
- `SHUTDOWN`: Signal to gracefully stop child loops and close resources.

---

## Communication Protocols

Three main protocols govern node interactions:

```
                  ┌──────────────────────┐
                  │  Central Controller  │
                  └──────────┬───────────┘
                             │
            ControllerToNode │ NodeToController
            Command Protocol │ Status Protocol
                             │
                             ▼
┌──────────────┐      NodeToNode      ┌──────────────┐
│  Junction A  │◄────────────────────►│  Junction B  │
│ (Virtual MCU)│   Neighbor Protocol  │ (Virtual MCU)│
└──────────────┘                      └──────────────┘
```

### 1. Node-to-Controller Protocol (`NodeToControllerProtocol`)
Nodes report status to the controller periodically (every 200ms). The packet payload includes:
- `vehicle_count`: Current count of active vehicles.
- `density_level`: Mapped density string (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- `light_state`: Current signal color (`RED`, `YELLOW`, `GREEN`).
- `green_duration`: Active timer configuration.
- `congestion`: Boolean flag indicating if count exceeds threshold (>40).
- `emergency`: Boolean flag indicating emergency vehicle presence.

### 2. Node-to-Node Neighbor Protocol (`NodeToNodeProtocol`)
Nodes coordinate locally without controller intervention:
- **Traffic Forecasting**: When vehicle count exceeds 15, a node calculates how many vehicles will head toward its neighbors and sends a `TRAFFIC_PREDICTION` message.
- **Adaptive Adjustments**: Receiving nodes extract the prediction value and use it to dynamically extend their upcoming green light phases, reducing delay before the queue arrives.

### 3. Controller-to-Node Command Protocol (`ControllerToNodeProtocol`)
Sent from the controller to override local MCU states:
- `PAUSE` / `RESUME`: Standardizes state machines across independent processes.
- `SHUTDOWN`: Triggers safety cleanup routines on virtual hardware.
- Event injection (`TRAFFIC_SURGE`, `GENERATE_CONGESTION`, `GENERATE_EMERGENCY`) for simulation testing.
