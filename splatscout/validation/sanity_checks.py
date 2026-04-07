"""Phase 1 sanity checks and report assembly."""

from __future__ import annotations

from collections import Counter

from splatscout.config import Phase1Config
from splatscout.types import (
    DatasetReport,
    ExifStats,
    ImageRecord,
    InputSummary,
    LoadedInput,
    ResolutionStats,
    Severity,
    ValidationIssue,
    ValidationStats,
    utc_timestamp,
)
from splatscout.validation.duplicates import detect_duplicate_clusters
from splatscout.validation.scene_consistency import detect_multiple_scene_suspicion


def build_phase1_report(loaded_input: LoadedInput, config: Phase1Config) -> DatasetReport:
    records = loaded_input.image_records
    issues: list[ValidationIssue] = []
    recommendations: list[str] = []

    image_count = len(records)
    if image_count < config.min_image_count:
        issues.append(
            ValidationIssue(
                severity=Severity.ERROR,
                code="too_few_images",
                message=f"Dataset has {image_count} images, below the hard minimum of {config.min_image_count}.",
            )
        )
        recommendations.append("Capture or provide more views before 3DGS training.")
    elif image_count < config.warn_image_count:
        issues.append(
            ValidationIssue(
                severity=Severity.WARNING,
                code="low_image_count",
                message=f"Dataset has {image_count} images, below the recommended minimum of {config.warn_image_count}.",
            )
        )
        recommendations.append("Add more overlapping views to improve reconstruction support.")

    unreadable_images = [record.path for record in records if not record.readable]
    if unreadable_images:
        issues.append(
            ValidationIssue(
                severity=Severity.ERROR,
                code="unreadable_images",
                message=f"{len(unreadable_images)} image files could not be opened.",
            )
        )
        recommendations.append("Remove or re-export unreadable image files.")

    resolution_stats = _build_resolution_stats(records)
    if resolution_stats.orientation_counts.get("portrait", 0) and resolution_stats.orientation_counts.get("landscape", 0):
        issues.append(
            ValidationIssue(
                severity=Severity.WARNING,
                code="mixed_orientations",
                message="Dataset mixes portrait and landscape images.",
            )
        )
        recommendations.append("Keep capture orientation consistent unless the variation is intentional.")

    if resolution_stats.pixel_count_variation > config.resolution_variance_threshold:
        issues.append(
            ValidationIssue(
                severity=Severity.WARNING,
                code="resolution_variance",
                message="Image resolutions vary significantly across the dataset.",
            )
        )
        recommendations.append("Normalize resolution or remove mismatched exports before training.")

    exif_stats = _build_exif_stats(records)
    input_mode_value = loaded_input.input_mode.value
    if input_mode_value in {"colmap_text", "colmap_binary"}:
        skipped_checks = [
            "EXIF completeness is limited in COLMAP-only mode.",
            "Duplicate analysis is skipped when raw image bytes are not available.",
        ]
    else:
        skipped_checks = []
        if exif_stats.images_with_exif == 0:
            issues.append(
                ValidationIssue(
                    severity=Severity.WARNING,
                    code="missing_exif",
                    message="No EXIF metadata was found in the readable images.",
                )
            )
            recommendations.append("Use original images instead of stripped exports when possible.")

    duplicate_clusters = []
    duplicate_image_count = 0
    if input_mode_value not in {"colmap_text", "colmap_binary"}:
        duplicate_clusters = detect_duplicate_clusters(
            records,
            distance_threshold=config.duplicate_distance_threshold,
        )
        duplicate_image_count = sum(max(0, len(cluster.members) - 1) for cluster in duplicate_clusters)
        if duplicate_clusters:
            issues.append(
                ValidationIssue(
                    severity=Severity.WARNING,
                    code="duplicate_images",
                    message=f"Detected {len(duplicate_clusters)} duplicate or near-duplicate image groups.",
                )
            )
            recommendations.append("Reduce redundant frames to save 3DGS training time without losing coverage.")

    issues.extend(detect_multiple_scene_suspicion(records))
    _extend_recommendations_from_issue_codes(issues, recommendations)

    validation_stats = ValidationStats(
        unreadable_images=unreadable_images,
        duplicate_clusters=duplicate_clusters,
        duplicate_image_count=duplicate_image_count,
        skipped_checks=skipped_checks,
    )

    input_summary = InputSummary(
        input_path=loaded_input.input_path,
        resolved_path=loaded_input.resolved_path,
        input_mode=loaded_input.input_mode,
        forced_mode=loaded_input.forced_mode,
        recursive=config.recursive,
        image_count=image_count,
        extracted_frame_count=loaded_input.metadata.get("extracted_frame_count"),
    )

    metadata = dict(loaded_input.metadata)
    metadata["issue_counts"] = {
        "info": sum(issue.severity == Severity.INFO for issue in issues),
        "warning": sum(issue.severity == Severity.WARNING for issue in issues),
        "error": sum(issue.severity == Severity.ERROR for issue in issues),
    }

    return DatasetReport(
        generated_at=utc_timestamp(),
        input_summary=input_summary,
        image_records=records,
        issues=issues,
        recommendations=_deduplicate_keep_order(recommendations),
        resolution_stats=resolution_stats,
        exif_stats=exif_stats,
        validation_stats=validation_stats,
        metadata=metadata,
    )


def _build_resolution_stats(records: list[ImageRecord]) -> ResolutionStats:
    readable_records = [record for record in records if record.readable and record.width > 0 and record.height > 0]
    resolution_counts = Counter(f"{record.width}x{record.height}" for record in readable_records)
    orientation_counts = Counter(_classify_orientation(record) for record in readable_records)
    if not readable_records:
        return ResolutionStats()

    pixel_counts = [record.width * record.height for record in readable_records]
    mean_pixels = sum(pixel_counts) / len(pixel_counts)
    variance = sum((count - mean_pixels) ** 2 for count in pixel_counts) / len(pixel_counts)
    coeff_variation = (variance ** 0.5) / mean_pixels if mean_pixels else 0.0

    return ResolutionStats(
        unique_resolutions=sorted(resolution_counts),
        orientation_counts=dict(orientation_counts),
        pixel_count_variation=round(coeff_variation, 4),
    )


def _build_exif_stats(records: list[ImageRecord]) -> ExifStats:
    readable_records = [record for record in records if record.readable]
    without_exif = [record.path for record in readable_records if not record.exif]
    with_focal = sum(1 for record in readable_records if record.exif.get("focal_length_mm") is not None)
    with_gps = sum(
        1
        for record in readable_records
        if record.exif.get("gps_latitude") is not None and record.exif.get("gps_longitude") is not None
    )
    with_exif = sum(1 for record in readable_records if record.exif)
    return ExifStats(
        images_with_exif=with_exif,
        images_with_focal_length=with_focal,
        images_with_gps=with_gps,
        images_without_exif=without_exif,
    )


def _classify_orientation(record: ImageRecord) -> str:
    if record.width == record.height:
        return "square"
    if record.width > record.height:
        return "landscape"
    return "portrait"


def _extend_recommendations_from_issue_codes(
    issues: list[ValidationIssue], recommendations: list[str]
) -> None:
    issue_codes = {issue.code for issue in issues}
    mapping = {
        "mixed_focal_lengths": "Verify that the folder contains one coherent capture session before training.",
        "multiple_parent_groups": "Split unrelated scenes into separate datasets before running 3DGS.",
    }
    for code, recommendation in mapping.items():
        if code in issue_codes:
            recommendations.append(recommendation)


def _deduplicate_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered
