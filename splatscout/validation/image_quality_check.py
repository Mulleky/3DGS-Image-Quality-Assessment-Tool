"""Phase 2 image quality analysis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from splatscout.config import Phase1Config
from splatscout.constants import QUALITY_ENABLE_WARNING_COUNT
from splatscout.image_quality.blur import compute_blur_score
from splatscout.image_quality.exposure import compute_exposure_metrics
from splatscout.image_quality.highlights import compute_clipped_highlights
from splatscout.image_quality.noise import estimate_noise_score
from splatscout.image_quality.reflective_sky import compute_sky_reflective_ratio
from splatscout.types import ImageQualityMetrics, ImageRecord, Severity, ValidationIssue

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None


@dataclass(slots=True)
class ImageQualityCheckResult:
    issues: list[ValidationIssue]
    recommendations: list[str]
    skipped_checks: list[str]
    analyzed_images: int
    flagged_images: int


def run_image_quality_checks(records: list[ImageRecord], config: Phase1Config) -> ImageQualityCheckResult:
    if cv2 is None:
        return ImageQualityCheckResult(
            issues=[],
            recommendations=[],
            skipped_checks=["Image quality checks were skipped because OpenCV is not available."],
            analyzed_images=0,
            flagged_images=0,
        )

    issues: list[ValidationIssue] = []
    recommendations: list[str] = []
    skipped_checks: list[str] = []
    analyzed_images = 0
    flagged_records: list[ImageRecord] = []

    for record in records:
        if not record.readable:
            skipped_checks.append(f"Skipped quality analysis for unreadable image: {record.path}")
            continue
        if not record.source_exists:
            skipped_checks.append(f"Skipped quality analysis without source pixels: {record.path}")
            continue

        try:
            image = cv2.imread(str(Path(record.path)), cv2.IMREAD_COLOR)
            if image is None:
                raise OSError("OpenCV could not decode the image.")

            blur_score, blur_type = compute_blur_score(image)
            exposure_mean, exposure_std = compute_exposure_metrics(image)
            clipped_ratio = compute_clipped_highlights(image)
            noise_score = estimate_noise_score(image)
            sky_reflective_ratio = compute_sky_reflective_ratio(image)

            flags: list[str] = []
            if blur_score < config.blur_threshold:
                flags.append("blurry")
            if exposure_mean < config.exposure_min:
                flags.append("underexposed")
            elif exposure_mean > config.exposure_max:
                flags.append("overexposed")
            if clipped_ratio > config.clipped_threshold:
                flags.append("clipped_highlights")
            if noise_score > config.noise_threshold:
                flags.append("high_noise")
            if sky_reflective_ratio > config.sky_threshold:
                flags.append("sky_or_reflective_dominance")

            record.quality_metrics = ImageQualityMetrics(
                blur_score=round(blur_score, 4),
                blur_type=blur_type,
                exposure_mean=round(exposure_mean, 4),
                exposure_std=round(exposure_std, 4),
                clipped_ratio=round(clipped_ratio, 4),
                noise_score=round(noise_score, 4),
                sky_reflective_ratio=round(sky_reflective_ratio, 4),
                flags=flags,
            )
            analyzed_images += 1
            if flags:
                flagged_records.append(record)
        except Exception as exc:  # pragma: no cover - defensive
            record.notes.append(f"Quality analysis failed: {exc}")
            record.quality_metrics = None
            skipped_checks.append(f"Quality analysis partially skipped for {record.path}: {exc}")

    if flagged_records:
        issues.append(
            ValidationIssue(
                severity=Severity.WARNING,
                code="flagged_image_quality",
                message=f"Flagged {len(flagged_records)} images with potential quality issues.",
            )
        )
        recommendations.append("Review flagged images before 3DGS training and retake or exclude severe outliers.")
        if len(flagged_records) >= QUALITY_ENABLE_WARNING_COUNT:
            recommendations.append("Consider cleaning the dataset before training to avoid low-quality views dominating reconstruction.")

    return ImageQualityCheckResult(
        issues=issues,
        recommendations=recommendations,
        skipped_checks=_deduplicate_keep_order(skipped_checks),
        analyzed_images=analyzed_images,
        flagged_images=len(flagged_records),
    )


def _deduplicate_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered
