"""Rule-based gesture detection using MediaPipe 21-point hand landmarks.

Landmark index reference (MediaPipe):
    0  = WRIST
    1  = THUMB_CMC,  2  = THUMB_MCP,  3  = THUMB_IP,   4  = THUMB_TIP
    5  = INDEX_MCP,  6  = INDEX_PIP,  7  = INDEX_DIP,  8  = INDEX_TIP
    9  = MIDDLE_MCP, 10 = MIDDLE_PIP, 11 = MIDDLE_DIP, 12 = MIDDLE_TIP
    13 = RING_MCP,   14 = RING_PIP,   15 = RING_DIP,   16 = RING_TIP
    17 = PINKY_MCP,  18 = PINKY_PIP,  19 = PINKY_DIP,  20 = PINKY_TIP

Each landmark is a (x, y, z) tuple with values normalized 0–1.
Y increases downward, so a raised fingertip has a smaller y than its MCP.
"""

import math


# ── helpers ──────────────────────────────────────────────────────────────────

def _dist(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def _finger_extended(lm, tip, pip):
    """True when fingertip is above (smaller y than) its PIP joint."""
    return lm[tip][1] < lm[pip][1]


def _palm_center(lm):
    """Approximate palm center as midpoint of wrist and middle MCP."""
    return (
        (lm[0][0] + lm[9][0]) / 2,
        (lm[0][1] + lm[9][1]) / 2,
    )


# ── single-hand gestures ──────────────────────────────────────────────────────

def is_open_palm(lm):
    """All four fingers extended (thumb excluded to avoid false positives)."""
    return (
        _finger_extended(lm, 8, 6)   # index
        and _finger_extended(lm, 12, 10)  # middle
        and _finger_extended(lm, 16, 14)  # ring
        and _finger_extended(lm, 20, 18)  # pinky
    )


def is_ok_gesture(lm, threshold=0.07):
    """Thumb tip and index tip form a small circle; other fingers extended."""
    thumb_index_close = _dist(lm[4], lm[8]) < threshold
    others_extended = (
        _finger_extended(lm, 12, 10)
        and _finger_extended(lm, 16, 14)
        and _finger_extended(lm, 20, 18)
    )
    return thumb_index_close and others_extended


def is_ily(lm, thumb_threshold=0.10, cross_threshold=0.07):
    """Index + thumb + pinky extended; middle and ring crossed over each other.

    Crossing is detected by the middle and ring fingertips being close together —
    the physical signature of overlapping fingers regardless of how extended they are.
    """
    index_up       = _finger_extended(lm, 8, 6)
    pinky_up       = _finger_extended(lm, 20, 18)
    thumb_out      = _dist(lm[4], lm[5]) > thumb_threshold
    fingers_crossed = _dist(lm[12], lm[16]) < cross_threshold  # tips overlap when crossed
    return index_up and pinky_up and thumb_out and fingers_crossed


def is_fist(lm):
    """All fingers curled — none of the four finger tips are extended."""
    return not any([
        _finger_extended(lm, 8, 6),
        _finger_extended(lm, 12, 10),
        _finger_extended(lm, 16, 14),
        _finger_extended(lm, 20, 18),
    ])


def is_pointing_up(lm):
    """Only index finger extended upward, others curled."""
    return (
        _finger_extended(lm, 8, 6)
        and not _finger_extended(lm, 12, 10)
        and not _finger_extended(lm, 16, 14)
        and not _finger_extended(lm, 20, 18)
    )


def is_pointing_down(lm, extension_threshold=0.12):
    """Index finger extended downward, others curled.

    Distinguishes from a fist by checking the index tip-to-MCP distance:
    an extended (pointing) finger is long; a curled (fist) finger is short.
    """
    index_tip_below_pip = lm[8][1] > lm[6][1]          # tip y > pip y → pointing down
    index_extended = _dist(lm[8], lm[5]) > extension_threshold  # tip far from MCP → not curled
    return (
        index_tip_below_pip
        and index_extended
        and not _finger_extended(lm, 12, 10)
        and not _finger_extended(lm, 16, 14)
        and not _finger_extended(lm, 20, 18)
    )


def is_peace(lm, thumb_threshold=0.07):
    """Index and middle fingers extended, ring and pinky curled; thumb not touching index (distinguish from ok)."""
    index_up    = _finger_extended(lm, 8, 6)
    middle_up   = _finger_extended(lm, 12, 10)
    ring_down   = not _finger_extended(lm, 16, 14)
    pinky_down  = not _finger_extended(lm, 20, 18)
    thumb_clear = _dist(lm[4], lm[8]) > thumb_threshold
    return index_up and middle_up and ring_down and pinky_down and thumb_clear


# ── two-hand gestures ─────────────────────────────────────────────────────────

def is_clap(lm1, lm2, threshold=0.15):
    """Both palms close together — distance between palm centers is small."""
    c1 = _palm_center(lm1)
    c2 = _palm_center(lm2)
    return _dist(c1, c2) < threshold


# ── dispatcher ────────────────────────────────────────────────────────────────

# Gesture priority order for single-hand detection.
# More specific gestures (ok, pointing) are checked before broad ones (open_palm).
SINGLE_HAND_GESTURES = [
    ("ok",            is_ok_gesture),
    ("pointing_up",   is_pointing_up),
    ("pointing_down", is_pointing_down),
    ("peace",         is_peace),
    ("ily",           is_ily),        # index + thumb + pinky; checked before open_palm
    ("open_palm",     is_open_palm),
    ("fist",          is_fist),
]


def detect_gesture(hands):
    """Return the detected gesture name string, or 'none'.

    Args:
        hands: list of landmark lists from HandTracker.get_landmarks()
                Each item is a list of 21 (x, y, z) tuples.
    """
    if not hands:
        return "none"

    # Two-hand gestures take priority
    if len(hands) >= 2 and is_clap(hands[0], hands[1]):
        return "clap"

    # Single-hand detection on the first hand
    lm = hands[0]
    for name, fn in SINGLE_HAND_GESTURES:
        if fn(lm):
            return name

    return "none"
