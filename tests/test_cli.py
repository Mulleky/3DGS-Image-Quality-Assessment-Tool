from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from splatscout.cli import main

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class CliTests(unittest.TestCase):
    def test_json_stdout_mode(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["analyze", str(FIXTURES / "images_basic"), "--json"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["input_summary"]["image_count"], 3)

    def test_strict_mode_returns_non_zero_on_blocking_issue(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["analyze", str(FIXTURES / "images_basic"), "--strict"])

        self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()
