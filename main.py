# main.py
import sys, os, ctypes
from datetime import datetime
from typing import Optional
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import QApplication, QMainWindow
from ui.main_window import MainWindow
from logging_config import setup_logging

from PySide6.QtNetwork import QLocalServer

from PySide6.QtGui import QFontDatabase, QIcon
import resources_rc

APP_ID = "AE.SOCIALGIFMAKER.0.1.0"
SERVER_NAME = "SocialGifMaker"
ICON_RESOURCE_PATH = ":/resource/icon.ico"

def resource_path(relative_path: str) -> str:
    """بازگرداندن مسیر فایل در حالت اجرای عادی یا打包 (PyInstaller)"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def setup_single_instance() -> Optional[QLocalServer]:
    """اطمینان از تک‌نمونه بودن برنامه. در صورت موفقیت، سرور محلی را برمی‌گرداند."""
    server = QLocalServer()
    if not server.listen(SERVER_NAME):
        return None
    return server

def set_windows_app_id() -> None:
    """تنظیم AppUserModelID در ویندوز برای گروه‌بندی صحیح آیکن تسکبار"""
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except (AttributeError, OSError):
        pass

if __name__ == "__main__":
    server = setup_single_instance()
    if server is None:
        QMessageBox.critical(None, "در حال اجرا", "نسخه دیگری از برنامه در حال اجراست.")
        sys.exit(0)

    set_windows_app_id()

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    setup_logging()
    app = QApplication(sys.argv)
    app._single_instance_server = server
    app.setWindowIcon(QIcon(":/resource/icon.ico"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())