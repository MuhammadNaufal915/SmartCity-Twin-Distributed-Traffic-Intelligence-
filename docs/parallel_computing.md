# Parallel Computing Concepts

This document details the parallel computing concepts demonstrated in the **SmartCity Twin** simulation, explaining how concurrency is achieved and measured.

## Concurrency Model: Process-Level Parallelism

Python has a Global Interpreter Lock (GIL) that prevents multiple threads from executing Python bytecodes in parallel on multiple CPU cores. To overcome this limitation and demonstrate true parallel computing, this project uses process-level parallelism:

- **Independent Processes**: Each junction node runs in its own operating system process (`multiprocessing.Process`).
- **Hardware Mapping**: The OS schedules the processes across different CPU cores, enabling simultaneous execution.
- **Asymmetric Workload**: The main process runs the GUI application and Central Controller, while the four virtual MCUs run their simulation loops in parallel.

---

## Parallel Performance Metrics

To evaluate parallel efficiency, the system measures execution metrics in real-time, displaying them in the **Performance Analytics** panel.

### 1. Speedup ($S$)
Speedup measures how much faster a parallel execution is compared to serial execution:

$$Speedup (S) = \frac{T_{serial}}{T_{parallel}}$$

In our simulation, we measure:
- $T_{parallel}$: Wall-clock elapsed runtime of the parallel system.
- $T_{serial}$: Estimated serial runtime, calculated by multiplying the parallel runtime by the number of active nodes ($T_{parallel} \times N$). This models a single-threaded system running each MCU's computation sequentially.

### 2. Efficiency ($E$)
Efficiency measures the utilization of the allocated processors:

$$Efficiency (E) = \frac{Speedup (S)}{N} = \frac{T_{serial}}{N \times T_{parallel}}$$

- An efficiency of **1.0 (100%)** represents ideal linear speedup, where adding processors results in a proportional decrease in runtime.
- In real distributed systems, efficiency is less than 1.0 due to IPC latency, process scheduling, and synchronization overhead.

---

## Task Parallelism vs. Data Parallelism

| Dimension | Task Parallelism (Used Here) | Data Parallelism |
| :--- | :--- | :--- |
| **Definition** | Distributing different computational tasks across processors. | Distributing partitions of the same dataset across processors. |
| **Logic** | Nodes execute unique routines based on local states and positions. | All nodes execute the exact same instruction on different data slices. |
| **Application** | Junction A runs eastern traffic logic while Junction B monitors northern queues. | Splitting a massive traffic coordinate grid to calculate positions. |

## Amdahl's Law

Amdahl's law calculates the theoretical limit of speedup given a sequential fraction $s$ of the program:

$$Speedup_{Theoretical} = \frac{1}{s + \frac{1 - s}{N}}$$

- In this simulation, the GUI thread represents a sequential execution component ($s > 0$).
- By delegating the heavy simulation logic (traffic generators, event monitors, and light timing) to child processes, we keep $s$ low, achieving high parallel speedup ratios.
