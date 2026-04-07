from __future__ import annotations

import unittest
from pathlib import Path

from splatscout.io.loaders import detect_input_mode, load_input
from splatscout.types import InputMode

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class InputLoaderTests(unittest.TestCase):
    def test_detects_image_folder(self) -> None:
        root = FIXTURES / "images_basic"
        self.assertEqual(detect_input_mode(root), InputMode.IMAGE_FOLDER)

    def test_rejects_ply_input(self) -> None:
        ply_path = FIXTURES / "invalid" / "model.ply"
        with self.assertRaisesRegex(ValueError, "PLY files"):
            detect_input_mode(ply_path)

    def test_loads_colmap_text_summary(self) -> None:
        root = FIXTURES / "colmap_text"
        loaded = load_input(root)
        self.assertEqual(loaded.input_mode, InputMode.COLMAP_TEXT)
        self.assertEqual(len(loaded.image_records), 1)
        self.assertEqual(loaded.image_records[0].width, 640)


if __name__ == "__main__":
    unittest.main()
