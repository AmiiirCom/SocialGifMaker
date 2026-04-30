"""
OpenCV-based video reader with frame extraction and seeking capabilities.
"""

import cv2
from logging_config import setup_logging

logger = setup_logging()


class VideoProcessor:
    """Handles video loading, frame extraction, and seeking."""

    def __init__(self, video_path: str):
        """
        Initialize the video processor.

        Args:
            video_path: Path to the video file.

        Raises:
            Exception: If the video cannot be opened.
        """
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise Exception(f"Failed to open video: {video_path}")

        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.fps
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        logger.info(f"Video loaded: {self.width}x{self.height}, fps={self.fps:.2f}, frames={self.total_frames}")

    def get_frame_at_time(self, time_sec: float):
        """
        Retrieve a single frame at a given time (seconds).

        Args:
            time_sec: Timestamp in seconds.

        Returns:
            Frame as numpy array (BGR) or None if error.
        """
        frame_no = int(time_sec * self.fps)
        frame_no = max(0, min(frame_no, self.total_frames - 1))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ret, frame = self.cap.read()
        return frame if ret else None

    def extract_frames(self, start_sec: float, end_sec: float,
                       target_fps: float = None, frame_skip: float = 1.0):
        """
        Generator yielding frames from start to end with subsampling.

        Args:
            start_sec: Start time (seconds).
            end_sec: End time (seconds).
            target_fps: Desired output FPS (if None, use original).
            frame_skip: Skip every N frames (float allows fractional skipping).

        Yields:
            Frame (numpy array, BGR).
        """
        start_frame = int(start_sec * self.fps)
        end_frame = int(end_sec * self.fps)
        if target_fps is None:
            target_fps = self.fps

        # Step = (original_fps / target_fps) * frame_skip
        step = max(1, int(round((self.fps / target_fps) * frame_skip)))

        current = start_frame
        while current <= end_frame:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, current)
            ret, frame = self.cap.read()
            if not ret:
                break
            yield frame
            current += step

    def release(self):
        """Release the underlying VideoCapture object."""
        self.cap.release()