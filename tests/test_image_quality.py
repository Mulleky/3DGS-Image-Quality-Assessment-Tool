from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from splatscout.config import Phase1Config
from splatscout.image_quality.blur import compute_blur_score
from splatscout.image_quality.exposure import compute_exposure_metrics
from splatscout.image_quality.highlights import compute_clipped_highlights
from splatscout.image_quality.noise import estimate_noise_score
from splatscout.image_quality.reflective_sky import compute_sky_reflective_ratio
from splatscout.pipeline import analyze_path


def _write_ppm(path: Path, pixels: np.ndarray) -> None:
    height, width, _ = pixels.shape
    rows = [" ".join(f"{r} {g} {b}" for r, g, b in row) for row in pixels]
    ppm = f"P3\n{width} {height}\n255\n" + "\n".join(rows) + "\n"
    path.write_text(ppm, encoding="ascii")


class ImageQualityMetricTests(unittest.TestCase):
    def test_blur_score_is_lower_after_gaussian_blur(self) -> None:
        sharp = np.zeros((32, 32, 3), dtype=np.uint8)
        sharp[:, :16] = 255
        blurred = cv2.GaussianBlur(sharp, (9, 9), 0)

        sharp_score, _ = compute_blur_score(sharp)
        blurred_score, _ = compute_blur_score(blurred)

        self.assertGreater(sharp_score, blurred_score)

    def test_exposure_metrics_distinguish_dark_and_bright_images(self) -> None:
        dark = np.full((16, 16, 3), 20, dtype=np.uint8)
        bright = np.full((16, 16, 3), 230, dtype=np.uint8)

        dark_mean, _ = compute_exposure_metrics(dark)
        bright_mean, _ = compute_exposure_metrics(bright)

        self.assertLess(dark_mean, 0.2)
        self.assertGreater(bright_mean, 0.8)

    def test_clipped_highlights_detect_saturated_regions(self) -> None:
        image = np.zeros((20, 20, 3), dtype=np.uint8)
        image[:10, :10] = 255

        clipped_ratio = compute_clipped_highlights(image)

        self.assertGreater(clipped_ratio, 0.2)

    def test_noise_proxy_rises_for_noisy_input(self) -> None:
        smooth = np.full((32, 32, 3), 127, dtype=np.uint8)
        rng = np.random.default_rng(42)
        noise = rng.integers(0, 256, size=(32, 32, 3), dtype=np.uint8)

        self.assertLess(estimate_noise_score(smooth), estimate_noise_score(noise))

    def test_sky_reflective_ratio_detects_bright_low_saturation_regions(self) -> None:
        image = np.zeros((20, 20, 3), dtype=np.uint8)
        image[:12, :] = (220, 220, 220)

        ratio = compute_sky_reflective_ratio(image)

        self.assertGreater(ratio, 0.35)


class ImageQualityIntegrationTests(unittest.TestCase):
    def test_analyze_quality_populates_metrics_and_flags(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sharp = np.zeros((32, 32, 3), dtype=np.uint8)
            sharp[:, :16] = 255
            blurred = cv2.GaussianBlur(sharp, (11, 11), 0)
            _write_ppm(root / "sharp.ppm", sharp)
            _write_ppm(root / "blurred.ppm", blurred)

            report = analyze_path(
                root,
                Phase1Config(
                    quality=True,
                    min_image_count=1,
                    warn_image_count=1,
                    blur_threshold=500.0,
                ),
            )

        self.assertTrue(all(record.quality_metrics is not None for record in report.image_records))
        flagged_paths = {record.path for record in report.flagged_image_records}
        self.assertIn(str(root / "blurred.ppm"), flagged_paths)
        self.assertIn("flagged_image_quality", {issue.code for issue in report.issues})
