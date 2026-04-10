"""Blur scoring helpers."""

from __future__ import annotations

import cv2
import numpy as np


def compute_blur_score(image_bgr: np.ndarray) -> tuple[float, str]:
    grayscale = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blur_score = float(cv2.Laplacian(grayscale, cv2.CV_64F).var())
    return blur_score, "laplacian_variance"
