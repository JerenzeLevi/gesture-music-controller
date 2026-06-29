from collections import deque, Counter


class GestureSmoother:
    """Stabilizes gesture predictions by returning the most common result
    over a rolling window of recent frames.

    "none" participates in the vote so that brief spurious detections during
    hand transitions cannot win over the dominant resting state. A gesture
    must appear in the majority of the window to be considered stable.
    """

    def __init__(self, window=10):
        self._history = deque(maxlen=window)

    def update(self, gesture):
        """Feed the latest raw gesture and return the stable gesture."""
        self._history.append(gesture)
        return self.current()

    def current(self):
        """Return the most common gesture in the current window."""
        if not self._history:
            return "none"
        return Counter(self._history).most_common(1)[0][0]

    def reset(self):
        self._history.clear()
