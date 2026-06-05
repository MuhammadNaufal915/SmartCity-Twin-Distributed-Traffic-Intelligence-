"""
Analytics Panel for SmartCity Twin.
Displays real-time performance metrics, throughput, speedup, and efficiency.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QProgressBar,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor


class MetricCard(QFrame):
    """A individual card to display a single metric with label, value, and unit."""

    def __init__(
        self,
        title: str,
        value: str,
        color_hex: str = "#78b8ff",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            MetricCard {{
                background-color: #1a1a2e;
                border: 1px solid #2a2a4a;
                border-radius: 6px;
                padding: 6px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(8, 6, 8, 6)

        self._title_label = QLabel(title)
        self._title_label.setFont(QFont("Segoe UI", 9))
        self._title_label.setStyleSheet("color: #8888aa; background: transparent; border: none;")
        layout.addWidget(self._title_label)

        self._value_label = QLabel(value)
        self._value_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {color_hex}; background: transparent; border: none;")
        layout.addWidget(self._value_label)

    def set_value(self, value: str) -> None:
        self._value_label.setText(value)


class AnalyticsPanel(QWidget):
    """
    Panel displaying simulation performance metrics.
    Compares sequential (serial) vs parallel execution.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(280)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # Title
        title = QLabel("📊 PERFORMANCE ANALYTICS")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #78b8ff; padding: 4px; background: transparent;")
        main_layout.addWidget(title)

        # ─── System Metrics ───
        sys_group = QFrame()
        sys_group.setStyleSheet("background-color: #111122; border-radius: 8px; border: 1px solid #20203a;")
        sys_layout = QVBoxLayout(sys_group)
        sys_layout.setContentsMargins(6, 6, 6, 6)
        sys_layout.setSpacing(4)

        sys_title = QLabel("System Metrics")
        sys_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        sys_title.setStyleSheet("color: #a0a0c0; border: none; background: transparent;")
        sys_layout.addWidget(sys_title)

        self._metrics_grid = QGridLayout()
        self._metrics_grid.setSpacing(4)

        self._cards = {
            'runtime': MetricCard("Runtime", "0.0s", "#4fc3f7"),
            'messages': MetricCard("Total Messages", "0", "#ce93d8"),
            'throughput': MetricCard("Throughput", "0 veh", "#81c784"),
            'latency': MetricCard("Avg Latency", "0.0ms", "#ffb74d"),
        }

        self._metrics_grid.addWidget(self._cards['runtime'], 0, 0)
        self._metrics_grid.addWidget(self._cards['messages'], 0, 1)
        self._metrics_grid.addWidget(self._cards['throughput'], 1, 0)
        self._metrics_grid.addWidget(self._cards['latency'], 1, 1)
        sys_layout.addLayout(self._metrics_grid)
        main_layout.addWidget(sys_group)

        # ─── Parallel Computing Metrics ───
        parallel_group = QFrame()
        parallel_group.setStyleSheet("background-color: #111122; border-radius: 8px; border: 1px solid #20203a;")
        parallel_layout = QVBoxLayout(parallel_group)
        parallel_layout.setContentsMargins(6, 6, 6, 6)
        parallel_layout.setSpacing(6)

        parallel_title = QLabel("Parallel Performance (Amdahl's)")
        parallel_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        parallel_title.setStyleSheet("color: #a0a0c0; border: none; background: transparent;")
        parallel_layout.addWidget(parallel_title)

        # CPU Nodes, Tasks, Speedup, Efficiency
        grid = QGridLayout()
        grid.setSpacing(4)

        self._cards['nodes'] = MetricCard("Active CPU Cores", "4", "#81c784")
        self._cards['tasks'] = MetricCard("Parallel Tasks", "0", "#9575cd")
        self._cards['speedup'] = MetricCard("Measured Speedup", "1.00x", "#ffb74d")
        self._cards['efficiency'] = MetricCard("Core Efficiency", "0%", "#4db6ac")

        grid.addWidget(self._cards['nodes'], 0, 0)
        grid.addWidget(self._cards['tasks'], 0, 1)
        grid.addWidget(self._cards['speedup'], 1, 0)
        grid.addWidget(self._cards['efficiency'], 1, 1)
        parallel_layout.addLayout(grid)

        # Speedup visual progress bar
        speedup_bar_label = QLabel("Speedup Ratio (vs Linear)")
        speedup_bar_label.setFont(QFont("Segoe UI", 8))
        speedup_bar_label.setStyleSheet("color: #8888aa; border: none; background: transparent;")
        parallel_layout.addWidget(speedup_bar_label)

        self._speedup_bar = QProgressBar()
        self._speedup_bar.setRange(0, 100)
        self._speedup_bar.setValue(0)
        self._speedup_bar.setTextVisible(True)
        self._speedup_bar.setFormat("%p%")
        self._speedup_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #2a2a4a;
                border-radius: 4px;
                background-color: #1a1a2e;
                color: #ffffff;
                text-align: center;
                height: 16px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff8a65, stop:1 #4db6ac);
                border-radius: 3px;
            }
        """)
        parallel_layout.addWidget(self._speedup_bar)

        # Efficiency visual progress bar
        efficiency_bar_label = QLabel("Parallel Efficiency")
        efficiency_bar_label.setFont(QFont("Segoe UI", 8))
        efficiency_bar_label.setStyleSheet("color: #8888aa; border: none; background: transparent;")
        parallel_layout.addWidget(efficiency_bar_label)

        self._efficiency_bar = QProgressBar()
        self._efficiency_bar.setRange(0, 100)
        self._efficiency_bar.setValue(0)
        self._efficiency_bar.setTextVisible(True)
        self._efficiency_bar.setFormat("%p%")
        self._efficiency_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #2a2a4a;
                border-radius: 4px;
                background-color: #1a1a2e;
                color: #ffffff;
                text-align: center;
                height: 16px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9575cd, stop:1 #4fc3f7);
                border-radius: 3px;
            }
        """)
        parallel_layout.addWidget(self._efficiency_bar)

        main_layout.addWidget(parallel_group)
        main_layout.addStretch()

    def update_metrics(self, metrics: dict) -> None:
        """Update metrics values and progress bars from dictionary."""
        runtime = metrics.get('simulation_runtime', 0.0)
        self._cards['runtime'].set_value(f"{runtime:.1f}s")

        total_messages = metrics.get('total_messages', 0)
        self._cards['messages'].set_value(f"{total_messages:,}")

        throughput = metrics.get('vehicle_throughput', 0)
        self._cards['throughput'].set_value(f"{throughput} veh")

        latency = metrics.get('average_latency', 0.0) * 1000.0  # Convert to ms
        self._cards['latency'].set_value(f"{latency:.1f} ms")

        num_nodes = metrics.get('num_nodes', 4)
        self._cards['nodes'].set_value(str(num_nodes))

        tasks = metrics.get('parallel_tasks', 0)
        self._cards['tasks'].set_value(str(tasks))

        speedup = metrics.get('speedup', 1.0)
        self._cards['speedup'].set_value(f"{speedup:.2f}x")

        efficiency = metrics.get('efficiency', 0.0)
        efficiency_pct = int(efficiency * 100)
        self._cards['efficiency'].set_value(f"{efficiency_pct}%")

        # Set progress bars
        max_speedup = float(num_nodes)
        speedup_pct = int((speedup / max_speedup) * 100) if max_speedup > 0 else 0
        self._speedup_bar.setValue(min(max(speedup_pct, 0), 100))
        self._efficiency_bar.setValue(min(max(efficiency_pct, 0), 100))
