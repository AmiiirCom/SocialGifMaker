from PySide6.QtCore import QThread, Signal
from core.video_processor import VideoProcessor
import traceback

class VideoLoaderWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path

    def run(self):
        try:
            proc = VideoProcessor(self.video_path)
            info = {
                "processor": proc,
                "duration": proc.duration,
                "width": proc.width,
                "height": proc.height,
                "fps": proc.fps
            }
            self.finished.emit(info)
        except Exception as e:
            self.error.emit(str(e) + "\n" + traceback.format_exc())