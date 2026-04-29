# workers/gif_worker.py
import os
import traceback
from PySide6.QtCore import QThread, Signal
from core.video_processor import VideoProcessor
from core.gif_generator import GifGenerator

class GifWorker(QThread):
    progress = Signal(int)
    finished = Signal(int)
    error = Signal(str)

    def __init__(self, video_path, start_sec, end_sec, output_path, text_config, gif_config):
        super().__init__()
        self.video_path = video_path
        self.start_sec = start_sec
        self.end_sec = end_sec
        self.output_path = output_path
        self.text_config = text_config
        self.gif_config = gif_config

    def run(self):
        try:
            # ایجاد یک VideoProcessor مستقل در این نخ
            vp = VideoProcessor(self.video_path)
            orig_fps = vp.fps
            target_fps = orig_fps * self.gif_config["fps_factor"]
            frame_skip = self.gif_config["frame_skip"]

            frame_gen = vp.extract_frames(
                self.start_sec, self.end_sec, target_fps, frame_skip
            )
            total_frames = max(1, int((self.end_sec - self.start_sec) * target_fps / frame_skip))
            generator = GifGenerator.create_gif(
                frame_gen, self.output_path,
                self.gif_config["resize_percent"],
                self.gif_config["palette"],
                total_frames,
                self.text_config,
                target_fps
            )
            last_pct = 0
            for pct in generator:
                if int(pct) > last_pct:
                    last_pct = int(pct)
                    self.progress.emit(last_pct)
            self.progress.emit(100)
            size = os.path.getsize(self.output_path)
            self.finished.emit(size)
            vp.release()
        except Exception as e:
            self.error.emit(str(e) + "\n" + traceback.format_exc())