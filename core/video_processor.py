# core/video_processor.py
import cv2
import numpy as np
from logging_config import setup_logging
logger = setup_logging()

class VideoProcessor:
    def __init__(self, video_path):
        self.video_path = video_path  # ذخیره مسیر برای استفاده مجدد
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise Exception("نمی‌توان ویدیو را باز کرد")
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.fps
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logger.info(f"Video loaded: {self.width}x{self.height}, fps={self.fps}, frames={self.total_frames}")

    def get_frame_at_time(self, time_sec):
        frame_no = int(time_sec * self.fps)
        if frame_no < 0:
            frame_no = 0
        if frame_no >= self.total_frames:
            frame_no = self.total_frames - 1
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ret, frame = self.cap.read()
        if ret:
            return frame
        return None

    def extract_frames(self, start_sec, end_sec, target_fps=None, frame_skip=1):
        start_frame = int(start_sec * self.fps)
        end_frame = int(end_sec * self.fps)
        if target_fps is None:
            target_fps = self.fps
        skip_ratio = self.fps / target_fps
        step = max(1, int(round(skip_ratio * frame_skip)))
        current_frame = start_frame
        while current_frame <= end_frame:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = self.cap.read()
            if not ret:
                break
            yield frame
            current_frame += step

    def release(self):
        self.cap.release()