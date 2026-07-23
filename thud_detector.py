# thud_detector.py
import sounddevice as sd
import numpy as np
import time
from typing import Callable

SAMPLERATE = 48_000          # high-res capture
WINDOW_MS  = 50              # analysis window size
THRESHOLD_FACTOR = 0.5       # multiplied by user-sensitivity

def _energy(signal: np.ndarray) -> float:
    """Root-mean-square energy of a mono signal."""
    return float(np.sqrt(np.mean(np.square(signal))))

class ThudDetector:
    """Detect isolated desk thumps within a short listening window."""
    def __init__(self, sensitivity: float = 0.4):
        self.sensitivity = np.clip(sensitivity, 0.0, 1.0)

    def listen(self, duration: float = 2.0) -> int:
        """Open the mic for `duration` seconds, return number of thumps."""
        frames = int(duration * SAMPLERATE)
        raw = sd.rec(frames, samplerate=SAMPLERATE, channels=1, dtype='float32')
        sd.wait()

        # Convert to 1-D array
        audio = raw[:, 0]

        # Simple onset detection: look for peaks that exceed a dynamic threshold
        win = int(WINDOW_MS * SAMPLERATE / 1000)
        energy_curve = np.array([
            _energy(audio[i:i+win]) for i in range(0, len(audio) - win, win)
        ])

        base_noise = np.median(energy_curve)          # background level
        # Dynamic threshold based on relative noise floor spike
        multiplier = 2.0 + (1.0 - self.sensitivity) * 8.0
        threshold = max(base_noise * multiplier, base_noise + 0.005)

        # Count peaks that cross threshold and are separated by at least 200 ms
        min_gap_frames = int(0.2 * SAMPLERATE / win)
        thumps = 0
        last_peak = -min_gap_frames
        for i, e in enumerate(energy_curve):
            if e > threshold and i - last_peak >= min_gap_frames:
                thumps += 1
                last_peak = i

        return thumps
