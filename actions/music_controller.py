"""Local music controller powered by pygame.mixer.

Usage:
    controller = MusicController(
        "path/to/songs",
        on_play=fn, on_pause=fn, on_track=fn
    )
    controller.execute("ok")           # toggle play/pause
    controller.execute("open_palm")    # pause
    controller.execute("pointing_up")  # next track
"""

import os
import time
import logging
import pygame


SUPPORTED_EXTENSIONS = (".mp3", ".wav", ".ogg", ".flac")

logging.basicConfig(
    filename="music_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)

# Maps stable gesture names → controller method names
GESTURE_ACTION_MAP = {
    "ok":            "toggle_play",
    "open_palm":     "toggle_play",   # play if stopped, pause if playing
    "pointing_up":   "next_track",
    "pointing_down": "prev_track",
    "peace":         "toggle_loop",
    "clap":          None,
    "fist":          None,            # handled in app.py — disables detection
    "ily":           None,            # handled in app.py — enables detection
    "none":          None,
}


class MusicController:
    def __init__(self, music_dir="music", on_play=None, on_pause=None, on_track=None):
        pygame.mixer.init()
        self._tracks         = self._load_tracks(music_dir)
        self._index          = 0
        self._playing        = False
        self._loop           = False
        self._on_play        = on_play
        self._on_pause       = on_pause
        self._on_track       = on_track
        self._last_play_time = 0.0   # guards tick() from firing before audio starts

        if self._tracks:
            self._load_current()

    # ── public API ────────────────────────────────────────────────────────────

    def execute(self, gesture):
        """Dispatch a stable gesture name to the appropriate action."""
        action = GESTURE_ACTION_MAP.get(gesture)
        if action:
            getattr(self, action)()

    def play(self):
        if not self._tracks:
            return
        if not self._playing:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.play(-1 if self._loop else 0)
            self._playing = True
            self._last_play_time = time.time()
            print("[Music] Playing")
            if self._on_play:
                self._on_play(self._current_name())

    def pause(self):
        if self._playing:
            pygame.mixer.music.pause()
            self._playing = False
            print("[Music] Paused")
            if self._on_pause:
                self._on_pause()

    def toggle_play(self):
        if self._playing:
            self.pause()
        else:
            self.play()

    def next_track(self):
        if not self._tracks:
            return
        self._index = (self._index + 1) % len(self._tracks)
        self._load_current()
        self._play_from_start()
        name = self._current_name()
        print(f"[Music] Next → {name}")
        if self._on_track:
            self._on_track(name)

    def prev_track(self):
        if not self._tracks:
            return
        self._index = (self._index - 1) % len(self._tracks)
        self._load_current()
        self._play_from_start()
        name = self._current_name()
        print(f"[Music] Prev → {name}")
        if self._on_track:
            self._on_track(name)

    def toggle_loop(self):
        self._loop = not self._loop
        print(f"[Music] Loop {'ON' if self._loop else 'OFF'}")
        if self._playing:
            pygame.mixer.music.play(-1 if self._loop else 0)

    def tick(self):
        """Call once per frame to handle end-of-track auto-advance."""
        # Skip check for 1 s after play() so the audio driver has time to register
        if time.time() - self._last_play_time < 1.0:
            return
        if self._playing and not self._loop and not pygame.mixer.music.get_busy():
            self._playing = False
            self.next_track()

    # ── internals ─────────────────────────────────────────────────────────────

    def _load_tracks(self, music_dir):
        if not os.path.isdir(music_dir):
            print(f"[Music] Directory '{music_dir}' not found — no tracks loaded.")
            return []
        tracks = sorted(
            os.path.join(music_dir, f)
            for f in os.listdir(music_dir)
            if f.lower().endswith(SUPPORTED_EXTENSIONS)
        )
        print(f"[Music] Loaded {len(tracks)} track(s) from '{music_dir}'")
        return tracks

    def _load_current(self):
        pygame.mixer.music.load(self._tracks[self._index])

    def _play_from_start(self):
        pygame.mixer.music.play(-1 if self._loop else 0)
        self._playing = True
        self._last_play_time = time.time()

    def _current_name(self):
        return os.path.basename(self._tracks[self._index]) if self._tracks else "—"
