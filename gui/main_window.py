"""
Main Window for SmartCity Twin Simulator.
Combines all dashboard widgets and handles simulation controls.
"""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QFrame, QSplitter, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QColor

from controller.central_controller import CentralController
from gui.city_map import CityMapWidget
from gui.monitoring_panel import MonitoringPanel
from gui.network_panel import NetworkPanel
from gui.analytics_panel import AnalyticsPanel
from gui.log_panel import LogPanel
from gui.traffic_chart import TrafficChartWidget

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main operations center window for the SmartCity Traffic Twin.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SmartCity Twin: Distributed Traffic Simulator")
        self.resize(1400, 900)
        self.setMinimumSize(1200, 800)

        # Initialize controller
        self.controller = CentralController()

        # State
        self._last_msg_bus_count: int = 0
        self._tick_counter: int = 0

        # Stylesheet (Modern Dark Mode)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0b0b14;
            }
            QWidget {
                color: #ffffff;
            }
            QFrame {
                border: none;
            }
            QSplitter::handle {
                background-color: #1a1a2e;
            }
        """)

        # Set up GUI
        self._init_ui()

        # Polling Timer (50ms interval for GUI updates and process queue polling)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(50)

        self._add_log_local("INFO", "Dashboard interface initialized.")

    def _init_ui(self) -> None:
        """Create and arrange window widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(6, 6, 6, 6)

        # 1. Header & Control Bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)

        # 2. Main Workspace Splitter (Vertical splitter separating Top panels from Bottom Logs)
        v_splitter = QSplitter(Qt.Orientation.Vertical)
        v_splitter.setHandleWidth(4)

        # Top half (Dashboard panels)
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(6)

        # Horizontal Splitter for Dashboard Columns
        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        h_splitter.setHandleWidth(4)

        # Column 1: City Map
        self.city_map = CityMapWidget()
        h_splitter.addWidget(self.city_map)

        # Column 2: Monitoring Panel
        self.monitoring_panel = MonitoringPanel()
        h_splitter.addWidget(self.monitoring_panel)

        # Column 3: Network + Analytics (Vertical layout inside Column 3)
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        self.network_panel = NetworkPanel()
        self.analytics_panel = AnalyticsPanel()

        right_layout.addWidget(self.network_panel, stretch=1)
        right_layout.addWidget(self.analytics_panel, stretch=1)
        h_splitter.addWidget(right_column)

        # Set stretch factors for 3 columns: Map=4, Monitoring=2, RightCol=2
        h_splitter.setSizes([700, 300, 300])
        top_layout.addWidget(h_splitter)
        v_splitter.addWidget(top_widget)

        # Bottom half (Tabs for Logs and Traffic History)
        self.bottom_tabs = QTabWidget()
        self.bottom_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #20203a; background: #0b0b14; }
            QTabBar::tab { background: #1a1a2e; color: #8888aa; padding: 6px 12px; border: 1px solid #20203a; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #2a2a4a; color: #ffffff; font-weight: bold; }
        """)
        
        self.log_panel = LogPanel()
        self.traffic_chart = TrafficChartWidget(max_history=100)
        
        self.bottom_tabs.addTab(self.log_panel, "📋 Log Console")
        self.bottom_tabs.addTab(self.traffic_chart, "📈 Traffic History")
        
        v_splitter.addWidget(self.bottom_tabs)

        # Set sizes for vertical split: Top Dashboard=650, Logs=200
        v_splitter.setSizes([650, 200])
        main_layout.addWidget(v_splitter)

        # Status Bar
        self.statusBar().showMessage("Simulator Offline")
        self.statusBar().setStyleSheet("color: #8888aa; background-color: #0d0d1a; border-top: 1px solid #20203a;")

        # Update initial button states
        self._update_control_states()

    def _create_control_bar(self) -> QWidget:
        """Create the top controls dashboard bar."""
        bar = QFrame()
        bar.setObjectName("ControlBar")
        bar.setStyleSheet("""
            QFrame#ControlBar {
                background-color: #111122;
                border: 1px solid #20203a;
                border-radius: 8px;
                padding: 6px;
            }
        """)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(10)

        # Title/Logo Area
        logo_label = QLabel("🏎️ SmartCity Twin")
        logo_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        logo_label.setStyleSheet("color: #78b8ff; background: transparent;")
        layout.addWidget(logo_label)

        # Subtitle
        sub_label = QLabel("Multi-MCU Simulation Operations")
        sub_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        sub_label.setStyleSheet("color: #666688; margin-left: -5px; background: transparent;")
        layout.addWidget(sub_label)

        layout.addSpacing(15)

        # Separator 1
        layout.addWidget(self._create_v_line())

        # Simulation Flow Controls
        self.btn_start = QPushButton("▶ Start")
        self.btn_start.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #1b4d3e;
                color: #a7f3d0;
                border: 1px solid #059669;
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #059669; }
            QPushButton:pressed { background-color: #047857; }
            QPushButton:disabled { background-color: #111122; color: #444455; border: 1px solid #20203a; }
        """)
        self.btn_start.clicked.connect(self._on_start)
        layout.addWidget(self.btn_start)

        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_pause.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.btn_pause.setStyleSheet("""
            QPushButton {
                background-color: #4c3017;
                color: #fed7aa;
                border: 1px solid #d97706;
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #d97706; }
            QPushButton:pressed { background-color: #b45309; }
            QPushButton:disabled { background-color: #111122; color: #444455; border: 1px solid #20203a; }
        """)
        self.btn_pause.clicked.connect(self._on_pause)
        layout.addWidget(self.btn_pause)

        self.btn_reset = QPushButton("🔄 Reset")
        self.btn_reset.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #3b2a2a;
                color: #fca5a5;
                border: 1px solid #dc2626;
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #dc2626; }
            QPushButton:pressed { background-color: #b91c1c; }
            QPushButton:disabled { background-color: #111122; color: #444455; border: 1px solid #20203a; }
        """)
        self.btn_reset.clicked.connect(self._on_reset)
        layout.addWidget(self.btn_reset)

        # Separator 2
        layout.addWidget(self._create_v_line())

        # Junction Target Selector (applied to events)
        target_lbl = QLabel("Target Junction:")
        target_lbl.setFont(QFont("Segoe UI", 9))
        target_lbl.setStyleSheet("color: #a0a0c0; background: transparent;")
        layout.addWidget(target_lbl)

        self.junction_combo = QComboBox()
        self.junction_combo.setFont(QFont("Segoe UI", 9))
        self.junction_combo.addItems([
            "Random Node",
            "Junction A (Top-Left)",
            "Junction B (Top-Right)",
            "Junction C (Bottom-Left)",
            "Junction D (Bottom-Right)",
        ])
        self.junction_combo.setStyleSheet("""
            QComboBox {
                background-color: #1a1a2e;
                color: #ffffff;
                border: 1px solid #2a2a4a;
                border-radius: 5px;
                padding: 4px 10px;
                min-width: 160px;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a2e;
                color: #ffffff;
                selection-background-color: #2a2a4a;
            }
        """)
        layout.addWidget(self.junction_combo)

        # Trigger Actions
        self.btn_congestion = QPushButton("⚠️ Congest")
        self.btn_congestion.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.btn_congestion.setToolTip("Inject excessive vehicle density into target junction")
        self.btn_congestion.setStyleSheet("""
            QPushButton {
                background-color: #4b3e15;
                color: #fef08a;
                border: 1px solid #ca8a04;
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #ca8a04; }
            QPushButton:pressed { background-color: #a16207; }
            QPushButton:disabled { background-color: #111122; color: #444455; border: 1px solid #20203a; }
        """)
        self.btn_congestion.clicked.connect(self._on_generate_congestion)
        layout.addWidget(self.btn_congestion)

        self.btn_emergency = QPushButton("🚨 Emergency")
        self.btn_emergency.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.btn_emergency.setToolTip("Spawn emergency vehicle to trigger green-light overrides")
        self.btn_emergency.setStyleSheet("""
            QPushButton {
                background-color: #4f1b1b;
                color: #fecaca;
                border: 1px solid #dc2626;
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #dc2626; }
            QPushButton:pressed { background-color: #b91c1c; }
            QPushButton:disabled { background-color: #111122; color: #444455; border: 1px solid #20203a; }
        """)
        self.btn_emergency.clicked.connect(self._on_generate_emergency)
        layout.addWidget(self.btn_emergency)

        self.btn_surge = QPushButton("📈 Surge")
        self.btn_surge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.btn_surge.setToolTip("Simulate sudden high traffic flow incoming to the target node")
        self.btn_surge.setStyleSheet("""
            QPushButton {
                background-color: #3b1e54;
                color: #f3e8ff;
                border: 1px solid #7c3aed;
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #7c3aed; }
            QPushButton:pressed { background-color: #6d28d9; }
            QPushButton:disabled { background-color: #111122; color: #444455; border: 1px solid #20203a; }
        """)
        self.btn_surge.clicked.connect(self._on_generate_surge)
        layout.addWidget(self.btn_surge)

        layout.addStretch()

        # Visual indicator of execution state
        self._indicator = QLabel("OFFLINE")
        self._indicator.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._indicator.setStyleSheet("""
            QLabel {
                background-color: #1a1a2e;
                color: #8888aa;
                border: 1px solid #2a2a4a;
                border-radius: 5px;
                padding: 6px 12px;
                min-width: 70px;
                alignment: center;
            }
        """)
        self._indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._indicator)

        return bar

    def _create_v_line(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setStyleSheet("background-color: #20203a; max-width: 1px; border: none;")
        return line

    def _get_selected_node_id(self) -> Optional[str]:
        """Convert selected combo box item to specific junction node ID."""
        idx = self.junction_combo.currentIndex()
        mapping = {
            0: None,            # Random Node
            1: "junction_a",
            2: "junction_b",
            3: "junction_c",
            4: "junction_d",
        }
        return mapping.get(idx)

    def _update_control_states(self) -> None:
        """Enable or disable control buttons depending on state."""
        running = self.controller.is_running
        paused = self.controller.is_paused

        self.btn_start.setEnabled(not running or paused)
        if paused:
            self.btn_start.setText("▶ Resume")
        else:
            self.btn_start.setText("▶ Start")

        self.btn_pause.setEnabled(running and not paused)
        self.btn_reset.setEnabled(running)

        # Trigger buttons are only enabled when simulation is actively running
        active_run = running and not paused
        self.btn_congestion.setEnabled(active_run)
        self.btn_emergency.setEnabled(active_run)
        self.btn_surge.setEnabled(active_run)

        # Indicator styling
        if active_run:
            self._indicator.setText("RUNNING")
            self._indicator.setStyleSheet("""
                QLabel {
                    background-color: #064e3b;
                    color: #a7f3d0;
                    border: 1px solid #059669;
                    border-radius: 5px;
                    padding: 6px 12px;
                }
            """)
            self.statusBar().showMessage("Simulator Running")
        elif running and paused:
            self._indicator.setText("PAUSED")
            self._indicator.setStyleSheet("""
                QLabel {
                    background-color: #451a03;
                    color: #ffedd5;
                    border: 1px solid #d97706;
                    border-radius: 5px;
                    padding: 6px 12px;
                }
            """)
            self.statusBar().showMessage("Simulator Paused")
        else:
            self._indicator.setText("OFFLINE")
            self._indicator.setStyleSheet("""
                QLabel {
                    background-color: #1c1917;
                    color: #e7e5e4;
                    border: 1px solid #44403c;
                    border-radius: 5px;
                    padding: 6px 12px;
                }
            """)
            self.statusBar().showMessage("Simulator Offline")

    # ─── Actions ──────────────────────────────────────────────────────

    def _on_start(self) -> None:
        if self.controller.is_paused:
            self.controller.resume()
            self._add_log_local("INFO", "Simulation execution resumed.")
        else:
            self.controller.start()
            self._last_msg_bus_count = 0
            self._add_log_local("INFO", "Distributed MCU processes starting up...")
        self._update_control_states()

    def _on_pause(self) -> None:
        self.controller.pause()
        self._add_log_local("INFO", "Simulation execution paused.")
        self._update_control_states()

    def _on_reset(self) -> None:
        self.controller.reset()
        self.city_map.reset_map()
        # Clear local state
        self._last_msg_bus_count = 0
        self._tick_counter = 0
        self.log_panel.clear_logs()
        self.traffic_chart.reset_data()
        self._add_log_local("INFO", "Simulation reset requested. All MCU processes halted.")
        self._update_control_states()

    def _on_generate_congestion(self) -> None:
        target = self._get_selected_node_id()
        self.controller.generate_congestion(target)
        self._update_control_states()

    def _on_generate_emergency(self) -> None:
        target = self._get_selected_node_id()
        self.controller.generate_emergency(target)
        self._update_control_states()

    def _on_generate_surge(self) -> None:
        target = self._get_selected_node_id()
        self.controller.generate_traffic_surge(target)
        self._update_control_states()

    def _add_log_local(self, level: str, message: str) -> None:
        """Insert a log into controller log list from GUI thread directly."""
        self.controller._add_log(level, message)

    def _on_tick(self) -> None:
        """Timer callback to fetch and display updates."""
        if not self.controller.is_running:
            return

        # Poll updates from node processes
        self.controller.poll_updates()

        # Update sub-widgets with latest statuses
        statuses = self.controller.get_all_status()
        
        # Track vehicle counts for the chart (sample every 10 ticks = 500ms)
        self._tick_counter += 1
        if self._tick_counter >= 10:
            self._tick_counter = 0
            chart_data = {
                node_id: status.vehicle_count for node_id, status in statuses.items()
            }
            self.traffic_chart.add_data(chart_data)

        for node_id, status in statuses.items():
            # 1. Update City Map
            self.city_map.update_junction(
                node_id,
                status.vehicle_count,
                status.density_level,
                status.light_state,
                status.congestion,
                status.emergency
            )

            # 2. Update Monitoring Panel Cards
            self.monitoring_panel.update_node(
                node_id,
                status.vehicle_count,
                status.density_level,
                status.light_state,
                status.green_duration,
                status.congestion,
                status.emergency,
                status.message_count,
                status.is_active
            )

            # 3. Update active state in Network Graph
            self.network_panel.set_node_active(node_id, status.is_active)

        self.network_panel.set_node_active('controller', self.controller.is_running)

        # 4. Message routing particles in Network Panel
        current_msg_count = self.controller._message_bus.message_count
        if current_msg_count > self._last_msg_bus_count:
            recent_msgs = self.controller._message_bus.recent_messages
            new_count = current_msg_count - self._last_msg_bus_count
            new_msgs = recent_msgs[-new_count:] if new_count <= len(recent_msgs) else recent_msgs

            for msg in new_msgs:
                self.network_panel.add_message_particle(msg.source, msg.target)
            self._last_msg_bus_count = current_msg_count

        # 5. Update Log Console
        logs = self.controller.get_event_log()
        self.log_panel.update_logs(logs)

        # 6. Update Analytics Panel
        metrics = self.controller.get_metrics()
        self.analytics_panel.update_metrics(metrics)

    def closeEvent(self, event) -> None:
        """Clean up child processes before shutting down the GUI."""
        logger.info("Main window closing, shutting down child processes...")
        self._timer.stop()
        try:
            self.controller.stop()
        except Exception as e:
            logger.error(f"Error stopping controller: {e}")
        event.accept()
