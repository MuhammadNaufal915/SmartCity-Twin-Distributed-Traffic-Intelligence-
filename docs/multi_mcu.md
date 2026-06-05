# Embedded Multi-MCU Architecture Simulation

This document explains how **SmartCity Twin** simulates a distributed network of microcontrollers (MCUs) controlling urban traffic signals.

## Microcontroller Emulation Design

Each junction node represents an independent physical MCU board (such as an STM32 or ESP32) deployed at an intersection. Rather than running real microcontrollers, the simulator emulates their behaviors and constraints inside Python processes:

```
┌────────────────────────────────────────────────────────┐
│                   Virtual MCU Process                  │
│                                                        │
│   ┌───────────────┐     ┌──────────────┐               │
│   │ Vehicle Spawn │────&gt;│ Local Sensor │               │
│   └───────────────┘     └──────┬───────┘               │
│                                │                       │
│                                ▼                       │
│   ┌───────────────┐     ┌──────────────┐               │
│   │ State Machine │&lt;────│ Density Calc │               │
│   └──────┬────────┘     └──────────────┘               │
│          │                                             │
│          ▼                                             │
│   ┌───────────────┐     ┌──────────────┐               │
│   │ Light Control │────&gt;│ Output GPIO  │               │
│   └───────────────┘     └──────────────┘               │
└────────────────────────────────────────────────────────┘
```

### 1. Loop-Based Execution (Superloop Pattern)
Embedded systems often execute a continuous `while(1)` loop, also known as a superloop. Each virtual MCU implements this pattern:
- The process loops continuously with a delay (`time.sleep(0.2)`), modeling a 5Hz CPU update frequency.
- The iteration consists of sequential steps: read sensors $\rightarrow$ execute controller logic $\rightarrow$ update outputs $\rightarrow$ communicate.

### 2. Isolated Address Space
- The nodes run in separate OS processes, meaning **physical memory addresses are isolated**.
- Nodes cannot share reference variables or mutate each other's parameters.
- If Junction A needs to coordinate with Junction B, it must format a packet and queue it, modeling a serial communication bus (e.g., UART or CAN).

---

## Local "Hardware" Interfaces

### 1. Virtual Sensors
Each node has private helper libraries that simulate hardware sensor inputs:
- **Loop Detector Sensors**: Simulates physical inductive loops under the pavement to measure current vehicles in the lanes. Mapped to `vehicle_count`.
- **Emergency Sirens (Sound Sensor)**: Detects emergency sirens. Mapped to `is_emergency`.

### 2. Actuators
- **Traffic Light GPIOs**: The local MCU dictates the traffic light output state (`GREEN`, `YELLOW`, `RED`).
- The light transitions are handled entirely by the local process loop.

### 3. Local Non-Volatile Registry
Each MCU maintains its own configuration parameters (such as minimum green time, maximum green time, and threshold limits) in local process memory, representing variables stored in EEPROM or Flash.

---

## Adaptive Light Cycle Logic

Each virtual MCU runs an independent adaptive traffic signal control algorithm:

```
                  ┌──────────────────────┐
                  │ Read Vehicle Sensors │
                  └──────────┬───────────┘
                             │
                             ▼
              (Is an emergency vehicle detected?)
                             ├───[Yes]───► Trigger Emergency Mode
                             │             (Override light to GREEN)
                             └───[No]────┐
                                         ▼
                        Calculate Density Level
                       (LOW / MEDIUM / HIGH / CRITICAL)
                                         │
                                         ▼
                            Retrieve Neighbor Forecasts
                        (Traverse inter-node queues)
                                         │
                                         ▼
                         Compute Extended Green Time
                        (Dynamically adapt light phase)
```

1. **Static Stage**: If traffic is `LOW`, lights maintain a baseline timer configuration (10 seconds).
2. **Dynamic Stage**: When traffic increases to `MEDIUM` or `HIGH`, the MCU dynamically increases the green phase duration to clear the queue, preventing bottlenecks.
3. **Cooperative Stage**: If Junction A predicts that a surge of vehicles is heading toward Junction B, it sends a message to Junction B. Junction B then extends its green phase in advance to accommodate the incoming traffic.
