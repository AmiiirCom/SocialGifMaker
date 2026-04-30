"""
Application-wide configuration constants.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "logs", "app.log")
SUPPORTED_VIDEO_EXT = (".mp4", ".avi", ".mov", ".mkv", ".webm")
PREVIEW_WIDTH = 640
PREVIEW_HEIGHT = 480
TEMP_DIR = os.path.join(BASE_DIR, "temp")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)