# ui/main_window.py
"""
Main window of the Social GIF Maker.
Provides UI for video loading, trimming, text overlay, quality control, and GIF generation.
"""

import os
import cv2
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QGroupBox,
    QFileDialog, QProgressBar, QScrollArea, QFrame, QColorDialog, QFontDialog,
    QMessageBox, QLineEdit, QTextEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont, QColor, QIcon

from core.video_processor import VideoProcessor
from core.text_overlay import add_text_to_frame
from workers.video_loader_worker import VideoLoaderWorker
from workers.gif_worker import GifWorker
from workers.size_estimator_worker import SizeEstimatorWorker
from logging_config import setup_logging

import resources_rc

logger = setup_logging()


class MainWindow(QMainWindow):
    """Main application window containing preview and all controls."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Social GIF Maker")
        self.setWindowIcon(QIcon(":/resource/icon.ico"))
        self.setMinimumSize(1200, 700)

        # Video state
        self.video_processor = None
        self.current_video_path = None
        self.start_time = 0.0
        self.end_time = 1.0
        self.total_duration = 1.0

        # Text overlay state
        self.selected_position = "center"
        self.font = QFont("Arial", 24)
        self.text_color = QColor(255, 255, 255)

        # Playback preview
        self.is_playing = False
        self.play_timer = QTimer()
        self.play_timer.timeout.connect(self.play_next_frame)
        self.current_play_time = 0.0
        self.play_interval = 50  # milliseconds (20 fps)

        # Delayed preview update (800ms debounce)
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.do_update_preview_and_estimate)

        self.estimator_worker = None

        self.init_ui()
        self.apply_stylesheet()
        self._connect_all_signals()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---------- Left panel: preview ----------
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.NoFrame)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)

        self.preview_label = QLabel("Video Preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #1e1e1e; border: 1px solid #555;")
        self.preview_label.setScaledContents(False)
        left_layout.addWidget(self.preview_label)

        play_layout = QHBoxLayout()
        self.btn_play = QPushButton("▶ Play")
        self.btn_play.clicked.connect(self.toggle_play)
        play_layout.addWidget(self.btn_play)
        play_layout.addStretch()
        left_layout.addLayout(play_layout)

        main_layout.addWidget(left_panel, 3)

        # ---------- Right panel: settings (scrollable) ----------
        right_panel = QScrollArea()
        right_panel.setWidgetResizable(True)
        right_panel.setStyleSheet("QScrollArea { border: none; }")
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)

        # --- Video group ---
        video_group = QGroupBox("📹 Video")
        video_layout = QVBoxLayout()
        self.btn_load = QPushButton("Load Video")
        self.btn_load.clicked.connect(self.load_video)
        self.video_label = QLabel("No video selected")
        video_layout.addWidget(self.btn_load)
        video_layout.addWidget(self.video_label)
        video_group.setLayout(video_layout)
        settings_layout.addWidget(video_group)

        # --- Trim group ---
        trim_group = QGroupBox("✂️ Trim")
        trim_layout = QVBoxLayout()
        self.start_slider = QSlider(Qt.Horizontal)
        self.start_slider.setRange(0, 1000)
        self.start_slider.valueChanged.connect(self.on_start_slider)
        self.end_slider = QSlider(Qt.Horizontal)
        self.end_slider.setRange(0, 1000)
        self.end_slider.setValue(1000)
        self.end_slider.valueChanged.connect(self.on_end_slider)
        self.start_label = QLabel("Start: 0.0 s")
        self.end_label = QLabel("End: 0.0 s")
        trim_layout.addWidget(QLabel("Start"))
        trim_layout.addWidget(self.start_slider)
        trim_layout.addWidget(self.start_label)
        trim_layout.addWidget(QLabel("End"))
        trim_layout.addWidget(self.end_slider)
        trim_layout.addWidget(self.end_label)
        trim_group.setLayout(trim_layout)
        settings_layout.addWidget(trim_group)

        # --- Text overlay group ---
        text_group = QGroupBox("✍️ Text Overlay")
        text_layout = QVBoxLayout()
        self.enable_text_cb = QCheckBox("Enable Text")
        self.enable_text_cb.setChecked(False)
        text_layout.addWidget(self.enable_text_cb)

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Enter your text...\n(Press Enter for new line)")
        self.text_input.setPlainText("My GIF")
        self.text_input.setMaximumHeight(100)
        self.text_input.setMinimumHeight(60)
        text_layout.addWidget(self.text_input)

        pos_layout = QHBoxLayout()
        self.btn_top = QPushButton("Top")
        self.btn_bottom = QPushButton("Bottom")
        self.btn_left = QPushButton("Left")
        self.btn_right = QPushButton("Right")
        self.btn_center = QPushButton("Center")
        for btn in (self.btn_top, self.btn_bottom, self.btn_left, self.btn_right, self.btn_center):
            btn.setCheckable(True)
            btn.clicked.connect(self.on_position_clicked)
        self.btn_center.setChecked(True)
        pos_layout.addWidget(self.btn_top)
        pos_layout.addWidget(self.btn_bottom)
        pos_layout.addWidget(self.btn_left)
        pos_layout.addWidget(self.btn_right)
        pos_layout.addWidget(self.btn_center)
        text_layout.addLayout(pos_layout)

        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(0, 200)
        self.margin_spin.setValue(20)
        self.margin_spin.setSuffix(" px")
        text_layout.addWidget(QLabel("Margin from edge:"))
        text_layout.addWidget(self.margin_spin)

        self.btn_font = QPushButton("Select Font")
        self.btn_font.clicked.connect(self.choose_font)
        self.btn_color = QPushButton("Text Color")
        self.btn_color.clicked.connect(self.choose_text_color)
        self.shadow_cb = QCheckBox("Shadow")
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 200)
        self.font_size_spin.setValue(28)
        self.font_size_spin.valueChanged.connect(lambda v: self.font.setPointSize(v))
        text_layout.addWidget(self.btn_font)
        text_layout.addWidget(self.btn_color)
        text_layout.addWidget(self.shadow_cb)
        text_layout.addWidget(QLabel("Font size:"))
        text_layout.addWidget(self.font_size_spin)

        text_group.setLayout(text_layout)
        settings_layout.addWidget(text_group)

        # --- Output settings group (with master quality) ---
        output_group = QGroupBox("🎬 GIF Output")
        output_layout = QVBoxLayout()

        self.quality_master = QSlider(Qt.Horizontal)
        self.quality_master.setRange(0, 100)
        self.quality_master.setValue(100)
        self.quality_master.valueChanged.connect(self.on_quality_master_changed)
        output_layout.addWidget(QLabel("🎚️ Master Quality (0–100):"))
        output_layout.addWidget(self.quality_master)

        self.resize_percent = QDoubleSpinBox()
        self.resize_percent.setRange(10, 100)
        self.resize_percent.setValue(50)
        self.resize_percent.setSuffix(" %")
        output_layout.addWidget(QLabel("Size percentage:"))
        output_layout.addWidget(self.resize_percent)

        self.fps_factor = QDoubleSpinBox()
        self.fps_factor.setRange(0.1, 1.0)
        self.fps_factor.setSingleStep(0.05)
        self.fps_factor.setValue(0.5)
        self.fps_factor.setSuffix(" of original")
        output_layout.addWidget(QLabel("Frame rate reduction:"))
        output_layout.addWidget(self.fps_factor)

        self.frame_skip = QDoubleSpinBox()
        self.frame_skip.setRange(1.0, 2.0)
        self.frame_skip.setSingleStep(0.1)
        self.frame_skip.setDecimals(1)
        self.frame_skip.setValue(1.0)
        output_layout.addWidget(QLabel("Frame skip (1.0 = none, 2.0 = max):"))
        output_layout.addWidget(self.frame_skip)

        self.palette_combo = QComboBox()
        self.palette_combo.addItems(["32", "64", "96", "128", "256", "Full"])
        output_layout.addWidget(QLabel("Color palette:"))
        output_layout.addWidget(self.palette_combo)

        self.size_label = QLabel("📦 Estimated size: unknown")
        output_layout.addWidget(self.size_label)

        output_group.setLayout(output_layout)
        settings_layout.addWidget(output_group)

        self.btn_generate = QPushButton("⚡ Generate Low-Size GIF")
        self.btn_generate.clicked.connect(self.generate_gif)
        self.btn_generate.setEnabled(False)
        settings_layout.addWidget(self.btn_generate)

        self.progress_bar = QProgressBar()
        settings_layout.addWidget(self.progress_bar)

        settings_layout.addStretch()
        right_panel.setWidget(settings_widget)
        main_layout.addWidget(right_panel, 2)

    def apply_stylesheet(self):
        style = """
        QGroupBox { font-weight: bold; border: 1px solid #aaa; border-radius: 5px; margin-top: 10px; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        QPushButton { background-color: #4CAF50; color: white; border-radius: 4px; padding: 6px; min-height: 25px; }
        QPushButton:hover { background-color: #45a049; }
        QSlider::groove:horizontal { height: 6px; background: #ddd; }
        QSlider::handle:horizontal { background: #4CAF50; width: 14px; border-radius: 7px; }
        QLabel { color: #f0f0f0; }
        QLineEdit, QTextEdit { padding: 4px; border: 1px solid #555; border-radius: 3px; background: #2a2a2a; color: white; }
        """
        self.setStyleSheet(style)

    def _connect_all_signals(self):
        # Video trimming
        self.start_slider.valueChanged.connect(self.request_update_preview)
        self.end_slider.valueChanged.connect(self.request_update_preview)
        # Text changes
        self.enable_text_cb.toggled.connect(self.request_update_preview)
        self.text_input.textChanged.connect(self.request_update_preview)
        self.btn_top.clicked.connect(self.request_update_preview)
        self.btn_bottom.clicked.connect(self.request_update_preview)
        self.btn_left.clicked.connect(self.request_update_preview)
        self.btn_right.clicked.connect(self.request_update_preview)
        self.btn_center.clicked.connect(self.request_update_preview)
        self.margin_spin.valueChanged.connect(self.request_update_preview)
        self.btn_font.clicked.connect(self.request_update_preview)
        self.btn_color.clicked.connect(self.request_update_preview)
        self.shadow_cb.toggled.connect(self.request_update_preview)
        self.font_size_spin.valueChanged.connect(self.request_update_preview)
        # Output controls
        self.resize_percent.valueChanged.connect(self.request_update_preview)
        self.fps_factor.valueChanged.connect(self.request_update_preview)
        self.frame_skip.valueChanged.connect(self.request_update_preview)
        self.palette_combo.currentTextChanged.connect(self.request_update_preview)

    def request_update_preview(self):
        """Debounced request to refresh preview and estimate size."""
        if self.video_processor and not self.is_playing:
            self.update_timer.start(800)

    def do_update_preview_and_estimate(self):
        self.update_preview_at_time(self.start_time)
        self.estimate_gif_size()

    def update_preview_at_time(self, time_sec: float):
        """Update the preview label with the frame at given time (with current settings)."""
        if not self.video_processor:
            return
        frame = self.video_processor.get_frame_at_time(time_sec)
        if frame is None:
            return
        resize_pct = self.resize_percent.value()
        h, w = frame.shape[:2]
        new_w = max(1, int(w * resize_pct / 100))
        new_h = max(1, int(h * resize_pct / 100))
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        if self.enable_text_cb.isChecked():
            text_cfg = {
                "text": self.text_input.toPlainText(),
                "position": self.selected_position,
                "margin": self.margin_spin.value(),
                "font": self.font,
                "color": self.text_color,
                "shadow": self.shadow_cb.isChecked()
            }
            resized = add_text_to_frame(resized, text_cfg, new_w, new_h)
        pixmap = self._cv_to_pixmap(resized)
        label_w = self.preview_label.width()
        label_h = self.preview_label.height()
        if label_w <= 0 or label_h <= 0:
            label_w, label_h = 400, 300
        scaled = pixmap.scaled(label_w, label_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview_label.setPixmap(scaled)

    def _cv_to_pixmap(self, cv_img):
        """Convert OpenCV BGR image to QPixmap."""
        from PySide6.QtGui import QImage
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(qimg)

    def estimate_gif_size(self):
        """Start a background worker to estimate final GIF size."""
        if not self.video_processor:
            return
        if self.estimator_worker and self.estimator_worker.isRunning():
            self.estimator_worker.terminate()
            self.estimator_worker.wait()

        text_cfg = None
        if self.enable_text_cb.isChecked():
            text_cfg = {
                "text": self.text_input.toPlainText(),
                "position": self.selected_position,
                "margin": self.margin_spin.value(),
                "font": self.font,
                "color": self.text_color,
                "shadow": self.shadow_cb.isChecked()
            }
        gif_cfg = {
            "resize_percent": self.resize_percent.value(),
            "fps_factor": self.fps_factor.value(),
            "frame_skip": self.frame_skip.value(),
            "palette": self.palette_combo.currentText()
        }
        self.estimator_worker = SizeEstimatorWorker(
            self.video_processor.video_path,
            self.start_time, self.end_time,
            text_cfg, gif_cfg,
            self.video_processor.fps
        )
        self.estimator_worker.finished.connect(self._on_estimate_finished)
        self.estimator_worker.error.connect(self._on_estimate_error)
        self.estimator_worker.start()

    def _on_estimate_finished(self, size_bytes: int):
        size_kb = size_bytes / 1024
        if size_kb > 1024:
            size_mb = size_kb / 1024
            self.size_label.setText(f"📦 Estimated size: {size_mb:.1f} MB")
        else:
            self.size_label.setText(f"📦 Estimated size: {size_kb:.0f} KB")

    def _on_estimate_error(self, err: str):
        logger.error(f"Size estimation error: {err}")
        self.size_label.setText("📦 Estimated size: error")

    def on_quality_master_changed(self, value: int):
        """Automatically adjust other controls based on master quality slider."""
        factor = value / 100.0
        new_resize = int(10 + factor * 90)
        self.resize_percent.blockSignals(True)
        self.resize_percent.setValue(new_resize)
        self.resize_percent.blockSignals(False)

        new_fps = round(0.1 + factor * 0.9, 2)
        self.fps_factor.blockSignals(True)
        self.fps_factor.setValue(new_fps)
        self.fps_factor.blockSignals(False)

        new_skip = round(2.0 - factor, 1)
        self.frame_skip.blockSignals(True)
        self.frame_skip.setValue(new_skip)
        self.frame_skip.blockSignals(False)

        if value >= 90:
            pal = "Full"
        elif value >= 70:
            pal = "256"
        elif value >= 50:
            pal = "128"
        elif value >= 30:
            pal = "96"
        elif value >= 15:
            pal = "64"
        else:
            pal = "32"
        self.palette_combo.blockSignals(True)
        self.palette_combo.setCurrentText(pal)
        self.palette_combo.blockSignals(False)

        self.request_update_preview()

    # ---------- Video loading ----------
    def load_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video", "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.webm)"
        )
        if not file_path:
            return
        self.current_video_path = file_path
        self.video_label.setText(os.path.basename(file_path))
        self.btn_generate.setEnabled(False)
        self.worker = VideoLoaderWorker(file_path)
        self.worker.finished.connect(self._on_video_loaded)
        self.worker.error.connect(self._on_video_error)
        self.worker.start()

    def _on_video_loaded(self, video_info):
        self.video_processor = video_info["processor"]
        self.total_duration = video_info["duration"]
        self.start_time = 0.0
        self.end_time = self.total_duration
        self._update_sliders()
        self._update_time_labels()
        self.update_preview_at_time(self.start_time)
        self.btn_generate.setEnabled(True)
        logger.info(f"Video loaded: {self.current_video_path}")

    def _on_video_error(self, error_msg):
        logger.error(error_msg)
        self.video_label.setText(f"Error: {error_msg}")
        QMessageBox.critical(self, "Error", f"Failed to load video:\n{error_msg}")

    def _update_sliders(self):
        self.start_slider.blockSignals(True)
        self.end_slider.blockSignals(True)
        self.start_slider.setValue(0)
        self.end_slider.setValue(1000)
        self.start_slider.blockSignals(False)
        self.end_slider.blockSignals(False)

    # ---------- Trim sliders ----------
    def on_start_slider(self, value: int):
        self.start_time = (value / 1000.0) * self.total_duration
        if self.start_time >= self.end_time:
            self.start_time = max(0, self.end_time - 0.05)
            self.start_slider.blockSignals(True)
            self.start_slider.setValue(int((self.start_time / self.total_duration) * 1000))
            self.start_slider.blockSignals(False)
        self._update_time_labels()
        if not self.is_playing:
            self.update_preview_at_time(self.start_time)
            self.request_update_preview()

    def on_end_slider(self, value: int):
        self.end_time = (value / 1000.0) * self.total_duration
        if self.end_time <= self.start_time:
            self.end_time = min(self.total_duration, self.start_time + 0.05)
            self.end_slider.blockSignals(True)
            self.end_slider.setValue(int((self.end_time / self.total_duration) * 1000))
            self.end_slider.blockSignals(False)
        self._update_time_labels()
        if not self.is_playing:
            self.update_preview_at_time(self.end_time)
            self.request_update_preview()

    def _update_time_labels(self):
        self.start_label.setText(f"Start: {self.start_time:.2f} s")
        self.end_label.setText(f"End: {self.end_time:.2f} s")

    # ---------- Text position ----------
    def on_position_clicked(self):
        btn = self.sender()
        if btn == self.btn_top:
            self.selected_position = "top"
        elif btn == self.btn_bottom:
            self.selected_position = "bottom"
        elif btn == self.btn_left:
            self.selected_position = "left"
        elif btn == self.btn_right:
            self.selected_position = "right"
        else:
            self.selected_position = "center"
        for b in (self.btn_top, self.btn_bottom, self.btn_left, self.btn_right, self.btn_center):
            b.setChecked(b == btn)
        self.request_update_preview()

    def choose_font(self):
        ok, font = QFontDialog.getFont(self.font, self)
        if ok:
            self.font = font
            self.request_update_preview()

    def choose_text_color(self):
        color = QColorDialog.getColor(self.text_color, self)
        if color.isValid():
            self.text_color = color
            self.request_update_preview()

    # ---------- Playback ----------
    def toggle_play(self):
        if not self.video_processor:
            return
        if self.is_playing:
            self._stop_playback()
        else:
            self._start_playback()

    def _start_playback(self):
        self.is_playing = True
        self.btn_play.setText("⏸ Stop")
        self.current_play_time = self.start_time
        self.play_timer.start(self.play_interval)

    def _stop_playback(self):
        self.is_playing = False
        self.btn_play.setText("▶ Play")
        self.play_timer.stop()
        self.update_preview_at_time(self.start_time)

    def play_next_frame(self):
        if not self.video_processor:
            self._stop_playback()
            return
        frame = self.video_processor.get_frame_at_time(self.current_play_time)
        if frame is None:
            self._stop_playback()
            return
        resize_pct = self.resize_percent.value()
        h, w = frame.shape[:2]
        new_w = max(1, int(w * resize_pct / 100))
        new_h = max(1, int(h * resize_pct / 100))
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        if self.enable_text_cb.isChecked():
            text_cfg = {
                "text": self.text_input.toPlainText(),
                "position": self.selected_position,
                "margin": self.margin_spin.value(),
                "font": self.font,
                "color": self.text_color,
                "shadow": self.shadow_cb.isChecked()
            }
            resized = add_text_to_frame(resized, text_cfg, new_w, new_h)
        pixmap = self._cv_to_pixmap(resized)
        label_w = self.preview_label.width()
        label_h = self.preview_label.height()
        if label_w <= 0 or label_h <= 0:
            label_w, label_h = 400, 300
        scaled = pixmap.scaled(label_w, label_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview_label.setPixmap(scaled)

        self.current_play_time += (self.play_interval / 1000.0)
        if self.current_play_time >= self.end_time:
            self.current_play_time = self.start_time

    # ---------- GIF generation ----------
    def generate_gif(self):
        if not self.video_processor:
            return
        save_path, _ = QFileDialog.getSaveFileName(self, "Save GIF", "", "GIF Files (*.gif)")
        if not save_path:
            return

        text_cfg = None
        if self.enable_text_cb.isChecked():
            text_cfg = {
                "text": self.text_input.toPlainText(),
                "position": self.selected_position,
                "margin": self.margin_spin.value(),
                "font": self.font,
                "color": self.text_color,
                "shadow": self.shadow_cb.isChecked()
            }
        gif_cfg = {
            "resize_percent": self.resize_percent.value(),
            "fps_factor": self.fps_factor.value(),
            "frame_skip": self.frame_skip.value(),
            "palette": self.palette_combo.currentText()
        }

        self.btn_generate.setEnabled(False)
        self.progress_bar.setValue(0)

        self.gif_worker = GifWorker(
            self.video_processor.video_path,
            self.start_time, self.end_time,
            save_path, text_cfg, gif_cfg
        )
        self.gif_worker.progress.connect(self.progress_bar.setValue)
        self.gif_worker.finished.connect(self._on_gif_finished)
        self.gif_worker.error.connect(self._on_gif_error)
        self.gif_worker.start()

    def _on_gif_finished(self, output_size_bytes: int):
        self.btn_generate.setEnabled(True)
        size_mb = output_size_bytes / (1024 * 1024)
        self.size_label.setText(f"📦 Final size: {size_mb:.2f} MB")
        logger.info(f"GIF created, size: {size_mb:.2f} MB")
        QMessageBox.information(self, "Success",
                                f"GIF generation completed.\nFinal size: {size_mb:.2f} MB")

    def _on_gif_error(self, err: str):
        self.btn_generate.setEnabled(True)
        logger.error(f"GIF generation error: {err}")
        QMessageBox.critical(self, "Error", f"GIF generation failed:\n{err}")