"""Unified input detection and loading for Phase 1."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, UnidentifiedImageError

from splatscout.constants import INVALID_PRETRAINING_EXTENSIONS, SUPPORTED_VIDEO_EXTENSIONS
from splatscout.io.colmap_parser import parse_colmap_summary
from splatscout.io.exif import extract_exif_data
from splatscout.io.image_normalize import discover_image_files
from splatscout.io.video_frames import extract_video_frames
from splatscout.types import ImageRecord, InputMode, LoadedInput
from splatscout.utils.paths import safe_relative


def detect_input_mode(path: Path, forced_mode: str | None = None, recursive: bool = False) -> InputMode:
    if not path.exists():
        raise ValueError(f"Input path does not exist: {path}")

    if path.is_file():
        suffix = path.suffix.lower()
        if suffix in INVALID_PRETRAINING_EXTENSIONS:
            raise ValueError("PLY files are not valid inputs for pre-training dataset analysis.")
        if suffix in SUPPORTED_VIDEO_EXTENSIONS:
            detected = InputMode.VIDEO
        else:
            raise ValueError(
                "Unsupported file input. Provide a video file or a directory containing images or COLMAP sparse outputs."
            )
    else:
        try:
            colmap_summary = parse_colmap_summary(path)
        except ValueError:
            colmap_summary = None

        if colmap_summary is not None:
            detected = InputMode(colmap_summary.model_type)
        else:
            image_paths = discover_image_files(path, recursive=recursive)
            if image_paths:
                detected = InputMode.IMAGE_FOLDER
            else:
                raise ValueError(
                    "Could not detect a supported input type. Expected images, a supported video file, or a COLMAP sparse directory."
                )

    if forced_mode is None:
        return detected

    normalized_forced = forced_mode.strip().lower()
    alias_map = {
        "images": InputMode.IMAGE_FOLDER,
        "image_folder": InputMode.IMAGE_FOLDER,
        "video": InputMode.VIDEO,
        "colmap": detected if detected in {InputMode.COLMAP_BINARY, InputMode.COLMAP_TEXT} else InputMode.COLMAP_TEXT,
        "colmap_text": InputMode.COLMAP_TEXT,
        "colmap_binary": InputMode.COLMAP_BINARY,
    }
    if normalized_forced not in alias_map:
        raise ValueError(f"Unsupported forced mode: {forced_mode}")

    forced = alias_map[normalized_forced]
    if forced == InputMode.COLMAP_TEXT and detected == InputMode.COLMAP_BINARY:
        raise ValueError("Forced mode colmap_text does not match the detected COLMAP binary sparse directory.")
    if forced == InputMode.COLMAP_BINARY and detected == InputMode.COLMAP_TEXT:
        raise ValueError("Forced mode colmap_binary does not match the detected COLMAP text sparse directory.")
    if forced in {InputMode.IMAGE_FOLDER, InputMode.VIDEO} and forced != detected:
        raise ValueError(f"Forced mode {forced.value} does not match detected input type {detected.value}.")
    return forced


def load_input(path: Path, forced_mode: str | None = None, recursive: bool = False, fps: float = 2.0) -> LoadedInput:
    resolved = path.expanduser().resolve()
    input_mode = detect_input_mode(resolved, forced_mode=forced_mode, recursive=recursive)

    metadata: dict[str, object] = {}
    if input_mode == InputMode.IMAGE_FOLDER:
        image_records = _load_image_folder(resolved, recursive=recursive)
    elif input_mode == InputMode.VIDEO:
        frame_paths, temp_dir = extract_video_frames(resolved, fps=fps)
        image_records = _load_image_paths(frame_paths, temp_dir)
        metadata["extracted_frame_dir"] = str(temp_dir)
        metadata["extracted_frame_count"] = len(frame_paths)
    else:
        summary = parse_colmap_summary(resolved)
        image_records = _load_colmap_records(summary)
        metadata["colmap_model_type"] = summary.model_type

    return LoadedInput(
        input_path=str(path),
        resolved_path=str(resolved),
        input_mode=input_mode,
        image_records=image_records,
        metadata=metadata,
        forced_mode=forced_mode,
    )


def _load_image_folder(root: Path, recursive: bool) -> list[ImageRecord]:
    image_paths = discover_image_files(root, recursive=recursive)
    return _load_image_paths(image_paths, root)


def _load_image_paths(image_paths: list[Path], base_dir: Path) -> list[ImageRecord]:
    records: list[ImageRecord] = []
    for image_path in image_paths:
        try:
            with Image.open(image_path) as image:
                width, height = image.size
                exif = extract_exif_data(image)
                records.append(
                    ImageRecord(
                        path=str(image_path),
                        width=width,
                        height=height,
                        exif=exif,
                        format=image.format,
                        readable=True,
                        source_exists=True,
                        parent_relative=safe_relative(image_path.parent, base_dir),
                    )
                )
        except (OSError, UnidentifiedImageError) as exc:
            records.append(
                ImageRecord(
                    path=str(image_path),
                    width=0,
                    height=0,
                    readable=False,
                    source_exists=True,
                    parent_relative=safe_relative(image_path.parent, base_dir),
                    notes=[f"Could not open image: {exc}"],
                )
            )
    return records


def _load_colmap_records(summary) -> list[ImageRecord]:
    records: list[ImageRecord] = []
    for image_entry in summary.images:
        camera = summary.cameras.get(image_entry.camera_id)
        width = camera.width if camera is not None else 0
        height = camera.height if camera is not None else 0
        records.append(
            ImageRecord(
                path=image_entry.name,
                width=width,
                height=height,
                readable=True,
                source_exists=None,
                notes=["Derived from COLMAP sparse model without opening source image bytes."],
            )
        )
    return records
