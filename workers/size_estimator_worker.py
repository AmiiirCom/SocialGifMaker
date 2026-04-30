"""
Worker thread for estimating final GIF size without writing the full file.
Samples a few frames, applies the same transformations, and extrapolates.
"""

import os
import sys
import tempfile
import traceback
import cv2
from PIL import Image
from PySide6.QtCore import QThread, Signal
from core.video_processor import VideoProcessor
from core.text_overlay import add_text_to_frame
from logging_config import setup_logging

logger = setup_logging()


class SizeEstimatorWorker(QThread):
    finished = Signal(int)   # estimated size in bytes
    error = Signal(str)

    def __init__(self, video_path: str, start_sec: float, end_sec: float,
                 text_config: dict, gif_config: dict, original_fps: float):
        super().__init__()
        self.video_path = video_path
        self.start_sec = start_sec
        self.end_sec = end_sec
        self.text_config = text_config
        self.gif_config = gif_config
        self.orig_fps = original_fps

    def run(self):
        try:
            logger.info("SizeEstimatorWorker started")
            vp = VideoProcessor(self.video_path)
            resize_percent = self.gif_config["resize_percent"]
            palette = self.gif_config["palette"]
            frame_skip = self.gif_config["frame_skip"]
            target_fps = self.orig_fps * self.gif_config["fps_factor"]

            total_duration = self.end_sec - self.start_sec
            if total_duration <= 0:
                logger.warning("Total duration <= 0, estimating 0 bytes")
                self.finished.emit(0)
                return

            total_frames = max(1, int(total_duration * target_fps / frame_skip))
            num_samples = min(10, total_frames)
            if num_samples == 0:
                num_samples = 1
            logger.info(f"Total frames: {total_frames}, sampling {num_samples} frames")

            total_size = 0
            sample_count = 0

            # Create a fallback temp directory if system temp is not writable
            fallback_temp = os.path.join(os.path.dirname(sys.executable), "temp_estimator")
            os.makedirs(fallback_temp, exist_ok=True)

            for i in range(num_samples):
                t = self.start_sec + (i / num_samples) * total_duration
                frame = vp.get_frame_at_time(t)
                if frame is None:
                    logger.warning(f"Could not get frame at time {t:.2f}, skipping")
                    continue

                h, w = frame.shape[:2]
                new_w = max(1, int(w * resize_percent / 100))
                new_h = max(1, int(h * resize_percent / 100))
                resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

                if self.text_config and self.text_config.get("text"):
                    resized = add_text_to_frame(resized, self.text_config, new_w, new_h)

                pil_img = Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
                if palette != "Full":
                    try:
                        num_colors = int(palette) if palette.isdigit() else 256
                    except:
                        num_colors = 256
                    pil_img = pil_img.quantize(colors=num_colors, method=Image.MEDIANCUT, dither=Image.NONE)

                # Try to create temp file, fallback to program's directory if fails
                try:
                    fd, tmp_path = tempfile.mkstemp(suffix=".gif")
                    os.close(fd)
                    pil_img.save(tmp_path, save_all=False, optimize=True)
                    size = os.path.getsize(tmp_path)
                    os.unlink(tmp_path)
                except Exception as temp_err:
                    logger.warning(f"Tempfile error: {temp_err}, using fallback")
                    tmp_path = os.path.join(fallback_temp, f"sample_{i}.gif")
                    pil_img.save(tmp_path, save_all=False, optimize=True)
                    size = os.path.getsize(tmp_path)
                    os.unlink(tmp_path)

                total_size += size
                sample_count += 1
                logger.debug(f"Sample {i} size: {size} bytes")

            if sample_count == 0:
                logger.warning("No valid samples, estimating 0 bytes")
                self.finished.emit(0)
            else:
                avg_size = total_size / sample_count
                estimated = int(avg_size * total_frames)
                logger.info(f"Estimation completed: {estimated} bytes ({estimated/1024:.1f} KB)")
                self.finished.emit(estimated)

            vp.release()

        except Exception as e:
            error_msg = f"Size estimator failed: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            self.error.emit(error_msg)