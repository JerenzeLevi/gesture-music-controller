import sys
import os
import ctypes
import time
import cv2

# Ensure CWD is the project root so relative paths (music/, models/) always resolve
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Hide the console window so the app doesn't appear in the taskbar
if sys.platform == "win32":
    _hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if _hwnd:
        ctypes.windll.user32.ShowWindow(_hwnd, 0)  # SW_HIDE
from core.camera import Camera
from core.tracker import HandTracker
from gestures.rules import detect_gesture
from gestures.smoothing import GestureSmoother
from actions.music_controller import MusicController
from background.tray import TrayIcon
from background.notifications import (
    notify_startup,
    notify_detection_off,
    notify_detection_on,
    notify_track,
    notify_play,
    notify_pause,
)
from utils.visualization import draw_landmarks, draw_fps


GESTURE_LABEL_COLOR = (0, 255, 255)
GESTURE_LABEL_POS   = (10, 120)
DETECTION_OFF_COLOR = (0, 0, 200)
WINDOW_NAME         = "Gesture Controller"


def draw_gesture(frame, gesture):
    cv2.putText(frame, f"Gesture: {gesture}", GESTURE_LABEL_POS,
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, GESTURE_LABEL_COLOR, 2)


def draw_detection_off_banner(frame):
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h // 2 - 40), (w, h // 2 + 40), DETECTION_OFF_COLOR, -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
    cv2.putText(frame, "DETECTION OFF", (w // 2 - 160, h // 2 + 15),
                cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3)


def main():
    # ── mutable flags accessed by tray callbacks ──────────────────────────────
    state = {
        "show_camera":        False,
        "running":            True,
        "detection_enabled":  True,
    }

    # ── tray callbacks ────────────────────────────────────────────────────────
    def _toggle_camera():
        visible = not state["show_camera"]
        state["show_camera"] = visible
        tray.set_camera_visible(visible)
        # cv2.destroyAllWindows() is NOT called here — tray runs on a background
        # thread and OpenCV window ops must happen on the main thread.
        # The main loop detects the state change and destroys the window itself.

    def _exit():
        state["running"] = False

    def _show_camera_from_notification():
        state["show_camera"] = True
        tray.set_camera_visible(True)

    # ── init ──────────────────────────────────────────────────────────────────
    camera   = Camera()
    tracker  = HandTracker()
    smoother = GestureSmoother(window=10)
    music    = MusicController(
        music_dir="music",
        on_play=lambda name: notify_play(name, on_click=_show_camera_from_notification),
        on_pause=lambda: notify_pause(on_click=_show_camera_from_notification),
        on_track=lambda name: notify_track(name, on_click=_show_camera_from_notification),
    )

    tray = TrayIcon(on_toggle_camera=_toggle_camera, on_exit=_exit)
    tray.start()

    # Startup notification — body click opens camera, Exit button stops the app
    notify_startup(on_exit=_exit, on_show_camera=_show_camera_from_notification)

    prev_time         = time.time()
    last_gesture      = "none"
    camera_was_shown  = False   # tracks previous frame's show_camera so we can
                                # destroy the window on the main thread when it flips

    print("Starting in background — right-click the tray icon to show camera or exit.")
    print("Gestures: ok/open_palm=play▶pause | pointing_up=next | pointing_down=prev")
    print("          peace=loop | fist=DISABLE detection | ily=ENABLE detection")

    # ── main loop ─────────────────────────────────────────────────────────────
    while state["running"]:
        frame = camera.read()
        if frame is None:
            print("Camera read failed.")
            break

        hands  = tracker.get_landmarks(frame)
        raw    = detect_gesture(hands)
        stable = smoother.update(raw)

        detection_enabled = state["detection_enabled"]

        # Disable fires on raw frame to prevent transition gestures from sneaking through
        if raw == "fist" and detection_enabled:
            state["detection_enabled"] = False
            last_gesture = "none"
            smoother.reset()
            tray.set_detection(False)
            notify_detection_off(on_click=_show_camera_from_notification)
            print("[Detection] DISABLED")

        elif stable != last_gesture:
            if stable == "ily" and not detection_enabled:
                state["detection_enabled"] = True
                smoother.reset()
                # Set last_gesture to "ily" so the *next* gesture change fires cleanly
                # instead of trapping on intermediate shapes during hand transition
                last_gesture = "ily"
                tray.set_detection(True)
                notify_detection_on(on_click=_show_camera_from_notification)
                print("[Detection] ENABLED")
            elif detection_enabled:
                music.execute(stable)
                last_gesture = stable
            else:
                last_gesture = stable

        music.tick()

        # ── display (only when camera window is requested) ────────────────────
        if state["show_camera"]:
            now       = time.time()
            fps       = 1.0 / (now - prev_time) if (now - prev_time) > 0 else 0
            prev_time = now

            draw_landmarks(frame, tracker)
            draw_fps(frame, fps)

            cv2.putText(frame, f"Hands: {len(hands)}", (10, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            draw_gesture(frame, stable)

            if not state["detection_enabled"]:
                draw_detection_off_banner(frame)

            cv2.imshow(WINDOW_NAME, frame)
            key = cv2.waitKey(1) & 0xFF

            # q key OR user closing the window with X both hide the feed
            window_closed = cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1
            if key == ord("q") or window_closed:
                state["show_camera"] = False
                tray.set_camera_visible(False)
                cv2.destroyAllWindows()
                camera_was_shown = False
            else:
                camera_was_shown = True

        else:
            # Destroy from main thread if tray hid the camera between frames
            if camera_was_shown:
                cv2.destroyAllWindows()
                camera_was_shown = False
            prev_time = time.time()
            cv2.waitKey(1)        # keep OpenCV event pump alive

    # ── cleanup ───────────────────────────────────────────────────────────────
    tray.stop()
    tracker.close()
    camera.release()
    cv2.destroyAllWindows()
    print("Stopped.")


if __name__ == "__main__":
    main()
