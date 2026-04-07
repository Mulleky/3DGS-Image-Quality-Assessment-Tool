"""Minimal COLMAP sparse parsers for Phase 1 detection and summary extraction."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from splatscout.constants import COLMAP_BINARY_FILES, COLMAP_TEXT_FILES

CAMERA_MODEL_PARAM_COUNTS = {
    0: 3,
    1: 4,
    2: 4,
    3: 5,
    4: 8,
    5: 8,
    6: 12,
    7: 5,
    8: 4,
    9: 5,
    10: 12,
}


@dataclass(slots=True)
class ColmapCamera:
    camera_id: int
    width: int
    height: int


@dataclass(slots=True)
class ColmapImage:
    image_id: int
    camera_id: int
    name: str


@dataclass(slots=True)
class ColmapSummary:
    model_type: str
    images: list[ColmapImage]
    cameras: dict[int, ColmapCamera]


def detect_colmap_model(path: Path) -> str | None:
    names = {child.name for child in path.iterdir()} if path.is_dir() else set()
    if COLMAP_BINARY_FILES.issubset(names):
        return "colmap_binary"
    if COLMAP_TEXT_FILES.issubset(names):
        return "colmap_text"
    return None


def parse_colmap_summary(path: Path) -> ColmapSummary:
    model_type = detect_colmap_model(path)
    if model_type == "colmap_text":
        cameras = _parse_cameras_text(path / "cameras.txt")
        images = _parse_images_text(path / "images.txt")
        return ColmapSummary(model_type=model_type, images=images, cameras=cameras)
    if model_type == "colmap_binary":
        cameras = _parse_cameras_bin(path / "cameras.bin")
        images = _parse_images_bin(path / "images.bin")
        return ColmapSummary(model_type=model_type, images=images, cameras=cameras)
    raise ValueError(f"Could not parse COLMAP sparse directory: expected {sorted(COLMAP_BINARY_FILES | COLMAP_TEXT_FILES)}")


def _parse_cameras_text(path: Path) -> dict[int, ColmapCamera]:
    cameras: dict[int, ColmapCamera] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        camera_id = int(parts[0])
        width = int(parts[2])
        height = int(parts[3])
        cameras[camera_id] = ColmapCamera(camera_id=camera_id, width=width, height=height)
    return cameras


def _parse_images_text(path: Path) -> list[ColmapImage]:
    images: list[ColmapImage] = []
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
    for index in range(0, len(lines), 2):
        header = lines[index].split()
        image_id = int(header[0])
        camera_id = int(header[8])
        name = header[9]
        images.append(ColmapImage(image_id=image_id, camera_id=camera_id, name=name))
    return images


def _read_struct(handle, fmt: str) -> tuple:
    size = struct.calcsize(fmt)
    data = handle.read(size)
    if len(data) != size:
        raise ValueError("Unexpected end of COLMAP binary file.")
    return struct.unpack(fmt, data)


def _read_c_string(handle) -> str:
    name_bytes = bytearray()
    while True:
        char = handle.read(1)
        if not char:
            raise ValueError("Unexpected end of COLMAP binary while reading image name.")
        if char == b"\x00":
            return name_bytes.decode("utf-8")
        name_bytes.extend(char)


def _parse_cameras_bin(path: Path) -> dict[int, ColmapCamera]:
    cameras: dict[int, ColmapCamera] = {}
    with path.open("rb") as handle:
        (camera_count,) = _read_struct(handle, "<Q")
        for _ in range(camera_count):
            camera_id, model_id, width, height = _read_struct(handle, "<iiQQ")
            param_count = CAMERA_MODEL_PARAM_COUNTS.get(model_id)
            if param_count is None:
                raise ValueError(f"Unsupported COLMAP camera model id: {model_id}")
            handle.seek(struct.calcsize(f"<{param_count}d"), 1)
            cameras[camera_id] = ColmapCamera(camera_id=camera_id, width=width, height=height)
    return cameras


def _parse_images_bin(path: Path) -> list[ColmapImage]:
    images: list[ColmapImage] = []
    with path.open("rb") as handle:
        (image_count,) = _read_struct(handle, "<Q")
        for _ in range(image_count):
            image_id = _read_struct(handle, "<i")[0]
            handle.seek(struct.calcsize("<4d3d"), 1)
            camera_id = _read_struct(handle, "<i")[0]
            name = _read_c_string(handle)
            (point_count,) = _read_struct(handle, "<Q")
            handle.seek(point_count * struct.calcsize("<ddq"), 1)
            images.append(ColmapImage(image_id=image_id, camera_id=camera_id, name=name))
    return images
