import cv2
import config


class Camera:
    def __init__(self):
        self._cap = cv2.VideoCapture(config.CAMERA_INDEX)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        self._cap.set(cv2.CAP_PROP_FPS, config.TARGET_FPS)

    def read(self):
        ok, frame = self._cap.read()
        if not ok:
            return None
        return cv2.flip(frame, 1)  # mirror so it feels natural

    def release(self):
        self._cap.release()
