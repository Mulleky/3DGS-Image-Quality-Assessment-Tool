"""Simple scene consistency heuristics for Phase 1."""

from __future__ import annotations

from collections import Counter

from splatscout.types import ImageRecord, Severity, ValidationIssue


def detect_multiple_scene_suspicion(records: list[ImageRecord]) -> list[ValidationIssue]:
    readable_records = [record for record in records if record.readable]
    if len(readable_records) < 10:
        return []

    issues: list[ValidationIssue] = []
    parents = Counter(record.parent_relative for record in readable_records if record.parent_relative)
    dominant_parents = [parent for parent, count in parents.items() if parent and count >= 3]
    if len(dominant_parents) >= 3:
        issues.append(
            ValidationIssue(
                severity=Severity.WARNING,
                code="multiple_parent_groups",
                message="Images appear to come from several different subfolders. Verify that the dataset is a single scene.",
            )
        )

    focal_lengths = [
        float(record.exif["focal_length_mm"])
        for record in readable_records
        if record.exif.get("focal_length_mm") is not None
    ]
    if focal_lengths:
        min_focal = min(focal_lengths)
        max_focal = max(focal_lengths)
        if min_focal > 0 and (max_focal / min_focal) >= 2.0:
            issues.append(
                ValidationIssue(
                    severity=Severity.WARNING,
                    code="mixed_focal_lengths",
                    message="Large focal-length variation may indicate mixed capture conditions or multiple scenes.",
                )
            )
        return issues

    return issues
