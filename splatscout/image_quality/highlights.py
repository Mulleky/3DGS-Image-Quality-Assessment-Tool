"""Highlight clipping heuristics."""

from __future__ import annotations

import numpy as np


def compute_clipped_highlights(image_bgr: np.ndarray, clip_value: int = 250) -> float:
    clipped_mask = np.any(image_bgr >= clip_value, axis=2)
    return float(clipped_mask.mean())
