"""
Main entry point for the Social GIF Maker application.
Handles single-instance locking, high-DPI scaling, and application bootstrap.
"""

import sys
import os
import ctypes
from typing import Optional
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtNetwork import QLocalServer
from PySide6.QtGui import QIcon

from ui.main_window import MainWindow
from logging_config import setup_logging
import resources_rc

APP_ID = "AE.SOCIALGIFMAKER.1.0.0"
SERVER_NAME = "SocialGifMaker"


def setup_single_instance() -> Optional[QLocalServer]:
    """
    Ensure only one instance of the application runs.
    Returns a QLocalServer if this is the first instance, otherwise None.
    """
    server = QLocalServer()
    if not server.listen(SERVER_NAME):
        return None
    return server


def set_windows_app_id() -> None:
    """Set Windows AppUserModelID for correct taskbar icon grouping."""
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except (AttributeError, OSError):
        pass


if __name__ == "__main__":
    # Single-instance check
    server = setup_single_instance()
    if server is None:
        QMessageBox.critical(None, "Already Running", "Another instance is already running.")
        sys.exit(0)

    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    setup_logging()

    # Create application
    app = QApplication(sys.argv)
    app._single_instance_server = server

    # Set AppUserModelID before and after app creation (ensures taskbar icon registers)
    set_windows_app_id()
    # Also set icon on the application itself
    app.setWindowIcon(QIcon(":/resource/icon.ico"))

    window = MainWindow()

    # Slight delay to allow Windows to register the AppUserModelID before showing
    QTimer.singleShot(50, window.show)

    sys.exit(app.exec())