import os
import tempfile
import cv2
from PIL import Image
from PySide6.QtCore import QThread, Signal
from core.video_processor import VideoProcessor
from core.text_overlay import add_text_to_frame

class SizeEstimatorWorker(QThread):
    finished = Signal(int)
    error = Signal(str)

    def __init__(self, video_path, start_sec, end_sec, text_config, gif_config, original_fps):
        super().__init__()
        self.video_path = video_path
        self.start_sec = start_sec
        self.end_sec = end_sec
        self.text_config = text_config
        self.gif_config = gif_config
        self.orig_fps = original_fps

    def run(self):
        try:
            vp = VideoProcessor(self.video_path)
            resize_percent = self.gif_config["resize_percent"]
            palette = self.gif_config["palette"]
            frame_skip = self.gif_config["frame_skip"]
            target_fps = self.orig_fps * self.gif_config["fps_factor"]
            total_duration = self.end_sec - self.start_sec
            if total_duration <= 0:
                self.finished.emit(0)
                return
            total_frames = max(1, int(total_duration * target_fps / frame_skip))
            num_samples = min(15, total_frames)
            if num_samples == 0:
                num_samples = 1

            total_size = 0
            sample_count = 0
            for i in range(num_samples):
                t = self.start_sec + (i / num_samples) * total_duration
                frame = vp.get_frame_at_time(t)
                if frame is None:
                    continue
                h, w = frame.shape[:2]
                new_w = max(1, int(w * resize_percent / 100))
                new_h = max(1, int(h * resize_percent / 100))
                resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
                if self.text_config and self.text_config.get("text"):
                    resized = add_text_to_frame(resized, self.text_config, new_w, new_h)
                pil_img = Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
                if palette != "Full":
                    num_colors = int(palette)
                    pil_img = pil_img.quantize(colors=num_colors, method=Image.MEDIANCUT, dither=Image.NONE)
                with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
                    tmp_path = tmp.name
                pil_img.save(tmp_path, save_all=False, optimize=True)
                size = os.path.getsize(tmp_path)
                os.unlink(tmp_path)
                total_size += size
                sample_count += 1

            if sample_count == 0:
                self.finished.emit(0)
            else:
                avg_size = total_size / sample_count
                estimated = int(avg_size * total_frames)
                self.finished.emit(estimated)
            vp.release()
        except Exception as e:
            self.error.emit(str(e))