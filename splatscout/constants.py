"""Project constants."""

from __future__ import annotations

APP_NAME = "splatscout"
APP_VERSION = "0.1.0"

SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
    ".ppm",
}

SUPPORTED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".m4v",
}

INVALID_PRETRAINING_EXTENSIONS = {".ply"}

COLMAP_BINARY_FILES = {"cameras.bin", "images.bin", "points3D.bin"}
COLMAP_TEXT_FILES = {"cameras.txt", "images.txt", "points3D.txt"}

DEFAULT_MIN_IMAGE_COUNT = 10
DEFAULT_WARN_IMAGE_COUNT = 30
DEFAULT_DUPLICATE_DISTANCE = 6
DEFAULT_RESOLUTION_VARIANCE_THRESHOLD = 0.25
DEFAULT_BLUR_THRESHOLD = 80.0
DEFAULT_EXPOSURE_MIN = 0.20
DEFAULT_EXPOSURE_MAX = 0.80
DEFAULT_CLIPPED_THRESHOLD = 0.03
DEFAULT_NOISE_THRESHOLD = 0.12
DEFAULT_SKY_THRESHOLD = 0.35
QUALITY_ENABLE_WARNING_COUNT = 3
