"""
Worker thread for loading a video file asynchronously.
"""

import traceback
from PySide6.QtCore import QThread, Signal
from core.video_processor import VideoProcessor


class VideoLoaderWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, video_path: str):
        super().__init__()
        self.video_path = video_path

    def run(self):
        try:
            processor = VideoProcessor(self.video_path)
            info = {
                "processor": processor,
                "duration": processor.duration,
                "width": processor.width,
                "height": processor.height,
                "fps": processor.fps
            }
            self.finished.emit(info)
        except Exception as e:
            self.error.emit(str(e) + "\n" + traceback.format_exc())