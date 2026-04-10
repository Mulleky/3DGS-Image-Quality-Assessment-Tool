"""Runtime configuration for the Phase 1 CLI."""

from __future__ import annotations

from dataclasses import dataclass

from splatscout.constants import (
    DEFAULT_BLUR_THRESHOLD,
    DEFAULT_CLIPPED_THRESHOLD,
    DEFAULT_DUPLICATE_DISTANCE,
    DEFAULT_EXPOSURE_MAX,
    DEFAULT_EXPOSURE_MIN,
    DEFAULT_MIN_IMAGE_COUNT,
    DEFAULT_NOISE_THRESHOLD,
    DEFAULT_RESOLUTION_VARIANCE_THRESHOLD,
    DEFAULT_SKY_THRESHOLD,
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
    quality: bool = False
    blur_threshold: float = DEFAULT_BLUR_THRESHOLD
    exposure_min: float = DEFAULT_EXPOSURE_MIN
    exposure_max: float = DEFAULT_EXPOSURE_MAX
    clipped_threshold: float = DEFAULT_CLIPPED_THRESHOLD
    noise_threshold: float = DEFAULT_NOISE_THRESHOLD
    sky_threshold: float = DEFAULT_SKY_THRESHOLD
