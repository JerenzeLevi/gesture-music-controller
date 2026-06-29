import os
import subprocess
import sys
import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
import config

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(_PROJECT_ROOT, "models", "hand_landmarker.task")
_DOWNLOAD_SCRIPT = os.path.join(_PROJECT_ROOT, "scripts", "download_model.py")


def _ensure_model():
    if not os.path.exists(MODEL_PATH):
        print(f"Model not found at {MODEL_PATH}. Running download script...")
        result = subprocess.run([sys.executable, _DOWNLOAD_SCRIPT], check=False)
        if result.returncode != 0 or not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model download failed. Please run manually:\n  python scripts/download_model.py"
            )
        print("Model downloaded successfully.")


class HandTracker:
    def __init__(self):
        _ensure_model()
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=RunningMode.IMAGE,
            num_hands=config.MAX_HANDS,
            min_hand_detection_confidence=config.DETECTION_CONFIDENCE,
            min_hand_presence_confidence=config.DETECTION_CONFIDENCE,
            min_tracking_confidence=config.TRACKING_CONFIDENCE,
        )
        self._landmarker = HandLandmarker.create_from_options(options)
        self.last_results = None  # mediapipe HandLandmarkerResult, used by visualization

    def get_landmarks(self, frame):
        """Return list of landmark lists — one per detected hand.

        Each hand is a list of 21 (x, y, z) normalized tuples.
        Returns empty list if no hands detected.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self.last_results = self._landmarker.detect(mp_image)

        if not self.last_results.hand_landmarks:
            return []

        return [
            [(lm.x, lm.y, lm.z) for lm in hand]
            for hand in self.last_results.hand_landmarks
        ]

    def close(self):
        self._landmarker.close()
