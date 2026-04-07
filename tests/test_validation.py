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


if __name__ == "__main__":
    unittest.main()
