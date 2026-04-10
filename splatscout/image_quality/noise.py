"""Noise proxy estimation."""

from __future__ import annotations

import cv2
import numpy as np


def estimate_noise_score(image_bgr: np.ndarray) -> float:
    grayscale = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    blurred = cv2.GaussianBlur(grayscale, (5, 5), 0)
    residual = np.abs(grayscale - blurred)
    return float(residual.mean())
