"""
Text overlay rendering using QPainter (supports multiline, shadows, alignment).
"""

import cv2
import numpy as np
from PySide6.QtGui import QImage, QPainter, QColor, QFont
from PySide6.QtCore import Qt, QPoint


def add_text_to_frame(frame, text_config, img_width: int, img_height: int):
    """
    Draw multi-line text onto a video frame using Qt's text rendering.

    Args:
        frame: Input frame (numpy array, BGR).
        text_config: Dictionary with keys:
            - text: str (multi-line, '\\n' separated)
            - font: QFont
            - color: QColor
            - shadow: bool
            - position: 'top'|'bottom'|'left'|'right'|'center'
            - margin: int (distance from edge)
        img_width, img_height: Dimensions of the frame (used for positioning).

    Returns:
        Frame with text overlay (numpy array, BGR).
    """
    if not text_config or not text_config.get("text"):
        return frame

    h, w, ch = frame.shape
    bytes_per_line = ch * w
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    qimage = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

    painter = QPainter(qimage)
    painter.setRenderHint(QPainter.Antialiasing)

    text = text_config["text"]
    font: QFont = text_config["font"]
    color: QColor = text_config["color"]
    shadow = text_config.get("shadow", False)
    position = text_config["position"]
    margin = text_config["margin"]

    painter.setFont(font)
    fm = painter.fontMetrics()
    lines = text.split('\n')

    if not lines:
        return frame

    line_height = fm.lineSpacing()
    total_text_height = len(lines) * line_height
    max_line_width = max(fm.horizontalAdvance(line) for line in lines)

    # Determine starting X and Y based on position
    if position == "top":
        start_y = margin
        start_x = (w - max_line_width) // 2
        align_left = False
    elif position == "bottom":
        start_y = h - margin - total_text_height
        start_x = (w - max_line_width) // 2
        align_left = False
    elif position == "left":
        start_y = (h - total_text_height) // 2
        start_x = margin
        align_left = True
    elif position == "right":
        start_y = (h - total_text_height) // 2
        start_x = w - margin - max_line_width
        align_left = True
    else:  # center
        start_y = (h - total_text_height) // 2
        start_x = (w - max_line_width) // 2
        align_left = False

    current_y = start_y
    for line in lines:
        if align_left:
            x = start_x
        else:
            line_width = fm.horizontalAdvance(line)
            x = (w - line_width) // 2
        point = QPoint(x, current_y + fm.ascent())

        if shadow:
            shadow_color = QColor(0, 0, 0, 180)
            painter.setPen(shadow_color)
            painter.drawText(point + QPoint(2, 2), line)

        painter.setPen(color)
        painter.drawText(point, line)

        current_y += line_height

    painter.end()

    # Convert back to BGR
    rgb_bytes = qimage.bits()
    rgb_array = np.array(rgb_bytes).reshape(h, w, 3)
    return cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)