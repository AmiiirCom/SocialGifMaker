import cv2
import os
from PIL import Image
from core.text_overlay import add_text_to_frame
from logging_config import setup_logging

logger = setup_logging()

class GifGenerator:
    @staticmethod
    def create_gif(frame_generator, output_path, resize_percent, palette_colors,
                   total_frames, text_config, target_fps):
        frames_pil = []
        processed = 0
        target_size = None

        for frame in frame_generator:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)

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

            if text_config and text_config.get("text"):
                frame_resized = cv2.resize(frame, target_size, interpolation=cv2.INTER_LANCZOS4)
                frame_with_text = add_text_to_frame(frame_resized, text_config, target_size[0], target_size[1])
                pil_img = Image.fromarray(cv2.cvtColor(frame_with_text, cv2.COLOR_BGR2RGB))

            frames_pil.append(pil_img)
            processed += 1
            yield (processed / total_frames) * 100

        if palette_colors != "Full":
            num_colors = int(palette_colors)
            quantized_frames = []
            for im in frames_pil:
                q = im.quantize(colors=num_colors, method=Image.MEDIANCUT, dither=Image.NONE)
                quantized_frames.append(q)
            frames_pil = quantized_frames

        if frames_pil:
            duration_ms = max(10, int(1000 / target_fps))
            frames_pil[0].save(
                output_path,
                save_all=True,
                append_images=frames_pil[1:],
                optimize=True,
                loop=0,
                duration=duration_ms
            )
        else:
            raise Exception("هیچ فریمی استخراج نشد")