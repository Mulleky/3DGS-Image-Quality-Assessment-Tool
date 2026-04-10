"""Exposure metrics backed by OpenCV."""

from __future__ import annotations

import cv2
import numpy as np


def compute_exposure_metrics(image_bgr: np.ndarray) -> tuple[float, float]:
    grayscale = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    return float(grayscale.mean()), float(grayscale.std())
