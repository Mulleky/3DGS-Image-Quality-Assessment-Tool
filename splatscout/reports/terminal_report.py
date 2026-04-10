"""Terminal report rendering with a plain-text fallback."""

from __future__ import annotations

from splatscout.types import DatasetReport


def render_terminal_report(report: DatasetReport, flagged_only: bool = False) -> str:
    summary = report.input_summary
    issue_counts = report.issue_counts
    quality_enabled = bool(report.metadata.get("quality", {}).get("enabled"))
    visible_records = report.flagged_image_records if flagged_only else report.image_records
    lines = [
        "SplatScout Phase 2 Report" if quality_enabled else "SplatScout Phase 1 Report",
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

    if quality_enabled:
        quality_metadata = report.metadata.get("quality", {})
        lines.append("Quality")
        lines.append(f"- Analyzed images: {quality_metadata.get('analyzed_images', 0)}")
        lines.append(f"- Flagged images: {quality_metadata.get('flagged_images', 0)}")
        if flagged_only:
            lines.append("- Terminal filter: flagged images only")
        if report.flagged_image_records:
            for record in visible_records:
                if record.quality_metrics is None or not record.quality_metrics.flags:
                    continue
                flag_text = ", ".join(record.quality_metrics.flags)
                lines.append(f"- {record.path}: {flag_text}")
        elif flagged_only:
            lines.append("- No flagged images to display.")
        lines.append("")

    if report.recommendations:
        lines.append("Recommendations")
        for recommendation in report.recommendations:
            lines.append(f"- {recommendation}")

    return "\n".join(lines).rstrip() + "\n"
