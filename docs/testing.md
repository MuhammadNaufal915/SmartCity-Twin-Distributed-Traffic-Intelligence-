# Testing & Verification Guide

This document describes how to test and verify the components of the **SmartCity Twin** traffic simulator.

## Pre-requisites

Make sure PyQt6 is installed in your Python environment:

```bash
pip install -r requirements.txt
```

---

## Unit Testing

The project is structured to support testing with `pytest`. Run tests to verify the correctness of the traffic algorithms and messaging layers:

```bash
pytest tests/ -v
```

### Test Case Coverage
1. **Traffic Logic Tests (`tests/test_traffic_logic.py`)**:
   - Mappings from vehicle counts to density levels (`LOW` to `CRITICAL`).
   - Adaptive signal green-time updates based on local density and neighbor predictions.
   - Threshold triggers for congestion alerts.
   - Emergency vehicle presence detection.
2. **Message Serialization Tests (`tests/test_messaging.py`)**:
   - Serializing `Message` objects into dictionaries.
   - Deserializing dictionaries back into valid `Message` structures.
   - Validating correct data types and priorities.
3. **Queue Communication Tests (`tests/test_queues.py`)**:
   - Creating, writing to, and reading from process communication queues.

---

## Manual Verification Checklist

Follow these steps to manually verify the simulator's operations:

### 1. Launch & Dashboard Verification
- Run the entry point script:
  ```bash
  python main.py
  ```
- Verify the following window behaviors:
  - The dark dashboard theme loads with a high-contrast layout.
  - The default state displays as **OFFLINE** on the top right.
  - All trigger buttons (**Congest**, **Emergency**, **Surge**) are disabled.
  - The map displays the four junctions (A, B, C, D) connected by roads.

### 2. Simulation Execution
- Click the **▶ Start** button on the control bar.
- Verify that:
  - The status indicator shifts to **RUNNING** (green).
  - The event console displays startup messages from the Central Controller and child processes.
  - Traffic lights begin cycling through states.
  - Vehicle items spawn and animate smoothly along the roads.
  - Telemetry cards update every 200ms with changing vehicle counts.
  - The **Distributed Network** panel displays animated communication particles.

### 3. Injecting Congestion Events
- Select **Junction A** from the **Target Junction** combo box.
- Click the **⚠️ Congest** button.
- Verify that:
  - A warning message appears in the event log.
  - The vehicle count badge on Junction A jumps above 40.
  - The Junction A card shows a **CRITICAL** warning state (red background/text).
  - Junction A flashes red on the map, and connecting road segments show congestion colors (orange/red).

### 4. Injecting Emergency Events
- Select **Junction B** from the target combo box.
- Click the **🚨 Emergency** button.
- Verify that:
  - An emergency vehicle spawns (represented as a flashing red circle).
  - The traffic light at Junction B overrides immediately to **GREEN** to clear the intersection.
  - An emergency alert log displays in the event console.
  - Once the emergency vehicle exits the junction, Junction B restores normal cycling.

### 5. Pausing and Resetting
- Click **⏸ Pause** and verify that:
  - The status indicator changes to **PAUSED** (orange).
  - All vehicle animations freeze.
  - The child processes halt their logic updates.
- Click **🔄 Reset** and verify that:
  - The status indicator reverts to **OFFLINE**.
  - All vehicles disappear from the map.
  - The console and analytics metrics are cleared.
