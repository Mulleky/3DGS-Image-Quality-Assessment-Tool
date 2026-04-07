"""Runtime configuration for the Phase 1 CLI."""

from __future__ import annotations

from dataclasses import dataclass

from splatscout.constants import (
    DEFAULT_DUPLICATE_DISTANCE,
    DEFAULT_MIN_IMAGE_COUNT,
    DEFAULT_RESOLUTION_VARIANCE_THRESHOLD,
    DEFAULT_WARN_IMAGE_COUNT,
)


@dataclass(slots=True)
class Phase1Config:
    min_image_count: int = DEFAULT_MIN_IMAGE_COUNT
    warn_image_count: int = DEFAULT_WARN_IMAGE_COUNT
    duplicate_distance_threshold: int = DEFAULT_DUPLICATE_DISTANCE
    recursive: bool = False
    fps: float = 2.0
    strict: bool = False
    resolution_variance_threshold: float = DEFAULT_RESOLUTION_VARIANCE_THRESHOLD
