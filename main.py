# main.py
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from logging_config import setup_logging

if __name__ == "__main__":
    setup_logging()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())