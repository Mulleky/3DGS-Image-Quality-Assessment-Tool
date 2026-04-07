"""Image discovery helpers used by the Phase 1 loaders."""

from __future__ import annotations

from pathlib import Path

from splatscout.constants import SUPPORTED_IMAGE_EXTENSIONS


def is_supported_image_file(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS


def discover_image_files(root: Path, recursive: bool = False) -> list[Path]:
    iterator = root.rglob("*") if recursive else root.glob("*")
    image_paths = [path for path in iterator if path.is_file() and is_supported_image_file(path)]
    return sorted(path.resolve() for path in image_paths)
