from __future__ import annotations

import unittest
from pathlib import Path

from splatscout.config import Phase1Config
from splatscout.pipeline import analyze_path

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class ValidationTests(unittest.TestCase):
    def test_warns_when_dataset_is_small(self) -> None:
        report = analyze_path(
            FIXTURES / "images_basic",
            Phase1Config(min_image_count=2, warn_image_count=5),
        )
        issue_codes = {issue.code for issue in report.issues}
        self.assertIn("low_image_count", issue_codes)

    def test_detects_duplicate_group(self) -> None:
        report = analyze_path(FIXTURES / "images_duplicates", Phase1Config())
        issue_codes = {issue.code for issue in report.issues}
        self.assertIn("duplicate_images", issue_codes)

    def test_detects_mixed_orientations(self) -> None:
        report = analyze_path(FIXTURES / "images_mixed_orientation", Phase1Config())
        issue_codes = {issue.code for issue in report.issues}
        self.assertIn("mixed_orientations", issue_codes)

    def test_quality_mode_populates_metrics(self) -> None:
        report = analyze_path(
            FIXTURES / "images_basic",
            Phase1Config(
                quality=True,
                min_image_count=1,
                warn_image_count=1,
                blur_threshold=0.0,
                exposure_min=0.0,
                exposure_max=1.0,
                clipped_threshold=1.0,
                noise_threshold=1.0,
                sky_threshold=1.0,
            ),
        )
        self.assertTrue(all(record.quality_metrics is not None for record in report.image_records))
        self.assertEqual(report.metadata["quality"]["analyzed_images"], 3)

    def test_quality_mode_skips_colmap_without_crashing(self) -> None:
        report = analyze_path(
            FIXTURES / "colmap_text",
            Phase1Config(quality=True),
        )
        skipped = "\n".join(report.validation_stats.skipped_checks)
        self.assertIn("Image quality checks are unavailable for COLMAP-only inputs", skipped)

    def test_quality_mode_emits_flagged_issue(self) -> None:
        report = analyze_path(
            FIXTURES / "images_basic",
            Phase1Config(
                quality=True,
                min_image_count=1,
                warn_image_count=1,
                blur_threshold=10_000_000.0,
            ),
        )
        self.assertIn("flagged_image_quality", {issue.code for issue in report.issues})


if __name__ == "__main__":
    unittest.main()
