"""
Entry point for the SmartCity Twin Simulator.
Initializes the application, launches the main window, and cleans up on exit.
"""

from __future__ import annotations

import sys
import logging
from multiprocessing import freeze_support

from PyQt6.QtWidgets import QApplication

from gui.main_window import MainWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Main application setup and execution."""
    logger.info("Initializing SmartCity Twin Simulator...")

    # Create PyQt6 application
    app = QApplication(sys.argv)
    
    # Establish modern styling accents
    app.setStyle("Fusion")

    # Launch GUI
    window = MainWindow()
    window.show()

    # Run event loop and exit cleanly
    sys.exit(app.exec())


if __name__ == '__main__':
    # freeze_support is mandatory on Windows for multiprocessing
    freeze_support()
    main()
