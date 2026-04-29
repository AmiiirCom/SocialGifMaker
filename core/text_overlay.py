import cv2
import numpy as np
from PySide6.QtGui import QImage, QPainter, QColor, QFont
from PySide6.QtCore import Qt, QPoint

def add_text_to_frame(frame, text_config, img_width, img_height):
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

    # تقسیم متن به خطوط
    lines = text.split('\n')
    if not lines:
        return frame

    # محاسبه ارتفاع هر خط و ارتفاع کل بلوک متن
    line_height = fm.lineSpacing()
    total_text_height = len(lines) * line_height

    # یافتن پهنای حداکثر خط برای تعیین موقعیت‌های افقی
    max_line_width = max(fm.horizontalAdvance(line) for line in lines)

    # تعیین نقطه شروع (x, y) برای اولین خط بر اساس موقعیت و حاشیه
    if position == "top":
        start_y = margin
        # تراز افقی وسط
        start_x = (w - max_line_width) // 2
        align_left = False  # وسط‌چین
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

    # رسم هر خط
    current_y = start_y
    for line in lines:
        # محاسبه x بر اساس تراز افقی
        if align_left:
            x = start_x
        else:
            # وسط‌چین: محاسبه عرض واقعی این خط
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

    rgb_bytes = qimage.bits()
    rgb_array = np.array(rgb_bytes).reshape(h, w, 3)
    bgr_frame = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
    return bgr_frame