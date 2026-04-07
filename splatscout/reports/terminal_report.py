"""Terminal report rendering with a plain-text fallback."""

from __future__ import annotations

from splatscout.types import DatasetReport


def render_terminal_report(report: DatasetReport) -> str:
    summary = report.input_summary
    issue_counts = report.issue_counts
    lines = [
        "SplatScout Phase 1 Report",
        f"Input: {summary.resolved_path}",
        f"Mode: {summary.input_mode.value}",
        f"Images: {summary.image_count}",
        f"Issues: {issue_counts['error']} errors, {issue_counts['warning']} warnings, {issue_counts['info']} info",
        "",
    ]

    if report.issues:
        lines.append("Issues")
        for issue in report.issues:
            lines.append(f"- [{issue.severity.value}] {issue.message}")
        lines.append("")

    lines.append("Validation")
    lines.append(
        f"- Unique resolutions: {', '.join(report.resolution_stats.unique_resolutions) or 'n/a'}"
    )
    orientation_text = ", ".join(
        f"{label}={count}" for label, count in sorted(report.resolution_stats.orientation_counts.items())
    ) or "n/a"
    lines.append(f"- Orientation mix: {orientation_text}")
    lines.append(
        f"- Images with EXIF: {report.exif_stats.images_with_exif}/{report.image_count}"
    )
    lines.append(
        f"- Duplicate groups: {len(report.validation_stats.duplicate_clusters)}"
    )
    if report.validation_stats.skipped_checks:
        for skipped in report.validation_stats.skipped_checks:
            lines.append(f"- Skipped: {skipped}")
    lines.append("")

    if report.recommendations:
        lines.append("Recommendations")
        for recommendation in report.recommendations:
            lines.append(f"- {recommendation}")

    return "\n".join(lines).rstrip() + "\n"
