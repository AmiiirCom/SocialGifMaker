"""
GIF generation using PIL with resizing, palette quantization, and frame timing.
"""

import cv2
from PIL import Image
from core.text_overlay import add_text_to_frame
from logging_config import setup_logging

logger = setup_logging()


class GifGenerator:
    """Utility class for creating optimized GIFs from frame generators."""

    @staticmethod
    def create_gif(frame_generator, output_path: str, resize_percent: float,
                   palette_colors: str, total_frames: int,
                   text_config: dict, target_fps: float):
        """
        Generate a GIF from a frame generator.

        Args:
            frame_generator: Yields frames (numpy arrays, BGR).
            output_path: Destination file path.
            resize_percent: Percentage of original size (10-100).
            palette_colors: "Full" or number of colors (e.g., "128").
            total_frames: Total number of frames expected (for progress).
            text_config: Text overlay configuration (or None).
            target_fps: Output GIF frame rate.

        Yields:
            Progress percentage (0-100) after each frame.
        """
        frames_pil = []
        processed = 0
        target_size = None

        for frame in frame_generator:
            # Convert BGR to RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)

            # Resize if needed
            if resize_percent != 100:
                w, h = pil_img.size
                new_w = max(1, int(w * resize_percent / 100))
                new_h = max(1, int(h * resize_percent / 100))
                pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
                if target_size is None:
                    target_size = (new_w, new_h)
            else:
                if target_size is None:
                    target_size = pil_img.size

            # Add text overlay if configured
            if text_config and text_config.get("text"):
                frame_resized = cv2.resize(frame, target_size, interpolation=cv2.INTER_LANCZOS4)
                frame_with_text = add_text_to_frame(frame_resized, text_config,
                                                    target_size[0], target_size[1])
                pil_img = Image.fromarray(cv2.cvtColor(frame_with_text, cv2.COLOR_BGR2RGB))

            frames_pil.append(pil_img)
            processed += 1
            yield (processed / total_frames) * 100

        # Apply color palette quantization
        if palette_colors != "Full":
            try:
                num_colors = int(palette_colors)
                if num_colors <= 0:
                    num_colors = 256
            except (ValueError, TypeError):
                num_colors = 256

            quantized_frames = []
            for im in frames_pil:
                q = im.quantize(colors=num_colors, method=Image.MEDIANCUT, dither=Image.NONE)
                quantized_frames.append(q)
            frames_pil = quantized_frames

        if not frames_pil:
            raise RuntimeError("No frames were extracted for GIF generation.")

        duration_ms = max(10, int(1000 / target_fps))
        frames_pil[0].save(
            output_path,
            save_all=True,
            append_images=frames_pil[1:],
            optimize=True,
            loop=0,
            duration=duration_ms
        )