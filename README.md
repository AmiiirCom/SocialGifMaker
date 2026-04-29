# 🎬 Social Gif Maker (SGM)

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.6%2B-green)](https://doc.qt.io/qtforpython/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-red)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![AI-Assisted](https://img.shields.io/badge/AI--Assisted-blue?logo=openai&logoColor=white)](https://deepseek.com/)

![AppIcon](https://github.com/AmiiirCom/SocialGifMaker/blob/master/resource/icon.png)

A **professional desktop application** to convert video clips into **lightweight, social‑media‑ready GIFs** with full control over quality, trimming, and text overlays.

![Screenshot](screenshot.png) *(add a screenshot of your app here)*

---

## ✨ Features

- **Trim any video** – Sliders with real‑time preview (linked start/end).
- **Text overlay** – Supports multiline (Persian, English, any language) with:
  - Custom font, size, color, shadow
  - 5 positions (top, bottom, left, right, center)
  - Adjustable margin from edges
- **Master Quality slider** – One‑touch control over all compression parameters:
  - Resolution percentage
  - Frame rate reduction
  - Frame skip (float values 1.0–2.0)
  - Color palette (32 – Full)
- **Live size estimation** – See estimated file size while you adjust settings.
- **Preview playback** – Loop the trimmed section to check result before exporting.
- **Multithreaded** – No UI freezes during heavy operations (loading, processing, GIF generation).
- **Logging** – All actions and errors saved to `logs/app.log`.
- **Modern UI** – Dark theme, scrollable settings, responsive layout.

---

## 🖥️ How It Works

1. **Load a video** (MP4, AVI, MOV, MKV, WebM).
2. **Trim** the desired segment using the start/end sliders.
3. **Add text** (optional) – type multiple lines, choose font/color/position.
4. **Adjust overall quality** with the master slider (0 = lowest file size, 100 = original quality).
5. **Preview** the result (use Play button to loop).
6. **Generate GIF** – the app creates a highly optimized `.gif` file.

All processing is done in background threads, so you can keep interacting with the UI.

---

## 🔧 Installation

### Requirements
- Python 3.8+
- pip

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/AmiiirCom/SocialGifMaker.git
   cd SocialGifMaker