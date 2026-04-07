"""Typed internal models used by the CLI, validation layer, and reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class InputMode(str, Enum):
    IMAGE_FOLDER = "image_folder"
    VIDEO = "video"
    COLMAP_TEXT = "colmap_text"
    COLMAP_BINARY = "colmap_binary"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(slots=True)
class ImageRecord:
    path: str
    width: int
    height: int
    exif: dict[str, Any] = field(default_factory=dict)
    converted_path: str | None = None
    format: str | None = None
    readable: bool = True
    source_exists: bool | None = True
    parent_relative: str | None = None
    perceptual_hash: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ValidationIssue:
    severity: Severity
    code: str
    message: str


@dataclass(slots=True)
class DuplicateCluster:
    representative: str
    members: list[str]
    average_distance: float
    exact: bool


@dataclass(slots=True)
class ResolutionStats:
    unique_resolutions: list[str] = field(default_factory=list)
    orientation_counts: dict[str, int] = field(default_factory=dict)
    pixel_count_variation: float = 0.0


@dataclass(slots=True)
class ExifStats:
    images_with_exif: int = 0
    images_with_focal_length: int = 0
    images_with_gps: int = 0
    images_without_exif: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ValidationStats:
    unreadable_images: list[str] = field(default_factory=list)
    duplicate_clusters: list[DuplicateCluster] = field(default_factory=list)
    duplicate_image_count: int = 0
    skipped_checks: list[str] = field(default_factory=list)


@dataclass(slots=True)
class InputSummary:
    input_path: str
    resolved_path: str
    input_mode: InputMode
    forced_mode: str | None
    recursive: bool
    image_count: int
    extracted_frame_count: int | None = None


@dataclass(slots=True)
class DatasetReport:
    generated_at: str
    input_summary: InputSummary
    image_records: list[ImageRecord]
    issues: list[ValidationIssue]
    recommendations: list[str]
    resolution_stats: ResolutionStats
    exif_stats: ExifStats
    validation_stats: ValidationStats
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def image_count(self) -> int:
        return self.input_summary.image_count

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == Severity.ERROR for issue in self.issues)

    @property
    def issue_counts(self) -> dict[str, int]:
        counts = {severity.value: 0 for severity in Severity}
        for issue in self.issues:
            counts[issue.severity.value] += 1
        return counts


@dataclass(slots=True)
class LoadedInput:
    input_path: str
    resolved_path: str
    input_mode: InputMode
    image_records: list[ImageRecord]
    metadata: dict[str, Any] = field(default_factory=dict)
    forced_mode: str | None = None


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def model_to_dict(value: Any) -> Any:
    if is_dataclass(value):
        return {key: model_to_dict(val) for key, val in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: model_to_dict(val) for key, val in value.items()}
    if isinstance(value, list):
        return [model_to_dict(item) for item in value]
    return value
