"""Sky and reflective-surface heuristics."""

from __future__ import annotations

import cv2
import numpy as np


def compute_sky_reflective_ratio(image_bgr: np.ndarray) -> float:
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    bright_low_sat = cv2.inRange(hsv, (0, 0, 170), (180, 70, 255))
    pale_blue = cv2.inRange(hsv, (85, 10, 120), (130, 160, 255))
    combined = cv2.bitwise_or(bright_low_sat, pale_blue)
    kernel = np.ones((3, 3), dtype=np.uint8)
    cleaned = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)
    return float(np.count_nonzero(cleaned)) / float(cleaned.size)
