# Gesture-Controlled Music System

A real-time, computer vision–powered music player for Windows. Control your local music library using hand gestures detected via webcam — no buttons, no keyboard.

---

## Demo

> Point up to skip, flash your palm to pause, make an OK to play. Your hand is the remote.

---

## Features

- Real-time hand tracking via [MediaPipe](https://mediapipe.dev/)
- Gesture-to-action mapping (play, pause, next/previous track, loop toggle)
- Smoothed gesture detection (rolling majority-vote window — no accidental triggers)
- Runs silently in the Windows system tray — no console window
- Windows toast notifications for track changes and playback state
- Toggle the camera overlay on/off from the tray icon

---

## Gesture Reference

| Gesture | Action |
|---|---|
| OK (thumb + index tip together) | Toggle play / pause |
| Open palm (all fingers extended) | Toggle play / pause |
| Pointing up (index up) | Next track |
| Pointing down (index down) | Previous track |
| Peace sign (index + middle up) | Toggle loop |
| Fist (all fingers curled) | Disable gesture detection |
| ILY (index + pinky + thumb out) | Re-enable gesture detection |

---

## Requirements

- Windows 10/11
- Python 3.9+
- A webcam

---

## Setup

**1. Clone the repo**

```bash
git clone https://github.com/your-username/gesture-controlled-music-system.git
cd gesture-controlled-music-system
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Download the MediaPipe hand landmark model**

```bash
python scripts/download_model.py
```

**4. Add your music**

Drop `.mp3`, `.wav`, `.ogg`, or `.flac` files into the `music/` folder.

**5. Run**

```bash
python app.py
```

The app starts in the background. Look for the tray icon in the system tray (bottom-right corner). Right-click it to show/hide the camera window or exit.

---

## Project Structure

```
app.py                    Main loop
config.py                 All thresholds and settings

core/
  camera.py               Webcam capture
  tracker.py              MediaPipe hand landmark detection

gestures/
  rules.py                Gesture detector functions
  smoothing.py            Rolling majority-vote stabilizer

actions/
  music_controller.py     pygame.mixer playback controller

background/
  tray.py                 System tray icon
  notifications.py        Windows toast notifications

utils/
  visualization.py        Landmark overlay and FPS display

models/
  hand_landmarker.task    MediaPipe model (downloaded by setup script)

music/                    Your local tracks go here
scripts/
  download_model.py       One-time model download
datasets/                 Gesture training images (optional)
```

---

## Architecture

```
Camera → HandTracker → detect_gesture → GestureSmoother → MusicController
```

Each layer is isolated. Actions only fire when the stable gesture *changes*, preventing repeated triggers on a held pose.

See [ARCHITECTURE.md](ARCHITECTURE,md) for the full design breakdown.

---

## License

MIT
