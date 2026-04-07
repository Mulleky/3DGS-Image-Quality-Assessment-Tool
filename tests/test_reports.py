from __future__ import annotations

import json
import unittest
from pathlib import Path

from splatscout.config import Phase1Config
from splatscout.pipeline import analyze_path
from splatscout.reports.json_report import render_json_report
from splatscout.reports.terminal_report import render_terminal_report

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class ReportTests(unittest.TestCase):
    def test_json_report_serializes(self) -> None:
        report = analyze_path(FIXTURES / "images_basic", Phase1Config())
        payload = json.loads(render_json_report(report))
        self.assertEqual(payload["input_summary"]["input_mode"], "image_folder")
        self.assertEqual(payload["input_summary"]["image_count"], 3)

    def test_terminal_report_contains_headings(self) -> None:
        report = analyze_path(FIXTURES / "images_basic", Phase1Config())
        rendered = render_terminal_report(report)
        self.assertIn("SplatScout Phase 1 Report", rendered)
        self.assertIn("Validation", rendered)


if __name__ == "__main__":
    unittest.main()
