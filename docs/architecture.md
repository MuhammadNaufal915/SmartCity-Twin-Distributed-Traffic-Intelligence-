# System Architecture: SmartCity Twin

This document details the software architecture of the **SmartCity Twin: Distributed Traffic Intelligence Simulator**. The system is built as a multi-process Python desktop application simulating a real-time digital twin of a four-intersection traffic system.

## Process Model & Architectural Overview

The simulation avoids shared memory completely, modeling each intersection as an independent physical microcontroller (MCU) board. 

```mermaid
graph TD
    subgraph Main Process
        GUI[PyQt6 GUI Dashboard]
        CC[Central Controller]
        GUI <--> |Direct Method Calls| CC
    end

    subgraph Child Processes (Virtual MCUs)
        JA[Junction A Process]
        JB[Junction B Process]
        JC[Junction C Process]
        JD[Junction D Process]
    end

    %% Controller - Node messaging
    CC <--> |multiprocessing.Queue| JA
    CC <--> |multiprocessing.Queue| JB
    CC <--> |multiprocessing.Queue| JC
    CC <--> |multiprocessing.Queue| JD

    %% Node - Node messaging
    JA <--> |multiprocessing.Queue| JB
    JA <--> |multiprocessing.Queue| JC
    JB <--> |multiprocessing.Queue| JD
    JC <--> |multiprocessing.Queue| JD
```

### 1. Main Process (GUI & Central Controller)
- **GUI Thread**: Runs the PyQt6 application loop, renders the Digital Twin map, manages the charts, updates monitoring panels, and logs. It stays responsive by using non-blocking calls.
- **Central Controller**: Aggregates telemetry from all four junctions and coordinates global events (e.g., emergencies, surges). It runs in the main process thread.
- **Polling Loop**: A QTimer fires every 50ms in the main process to poll the receive queues for updates from child MCUs, keeping UI overhead low while ensuring real-time responsiveness.

### 2. Junction Node Processes (Virtual MCUs)
- Each of the four junctions (**Junction A, B, C, D**) runs in its own dedicated operating system process via Python's `multiprocessing` library.
- Each junction operates an independent main loop simulating the behavior of a physical MCU:
  1. **Traffic Generation**: Spawns and moves local vehicles.
  2. **Telemetry Calculation**: Computes local vehicle counts, congestion thresholds, and density levels.
  3. **Traffic Light Logic**: Runs adaptive signal timing using density calculations and incoming predictions.
  4. **Inter-MCU Communication**: Exchanges traffic prediction messages with immediate neighbors.
  5. **Status Reporting**: Packages local telemetry and transmits it to the Central Controller.

---

## Inter-Process Communication (IPC) Topology

IPC is constructed using unidirectional `multiprocessing.Queue` objects. The network contains 16 total queues to support full bi-directional communication:

1. **Junction-to-Controller Queues (4 queues)**: Each node has a dedicated queue to send status reports to the controller.
2. **Controller-to-Junction Queues (4 queues)**: The controller has a dedicated queue for each node to transmit override commands, surges, or shutdown signals.
3. **Inter-Junction Queues (8 queues)**: Bi-directional connections between connected neighbors:
   - Junction A $\leftrightarrow$ Junction B (2 queues)
   - Junction A $\leftrightarrow$ Junction C (2 queues)
   - Junction B $\leftrightarrow$ Junction D (2 queues)
   - Junction C $\leftrightarrow$ Junction D (2 queues)

No node can inspect or modify the memory of any other node, ensuring strict adherence to distributed computing constraints.
