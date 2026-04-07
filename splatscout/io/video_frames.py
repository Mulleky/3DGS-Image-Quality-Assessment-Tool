"""Video frame extraction helpers."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


def extract_video_frames(video_path: Path, fps: float) -> tuple[list[Path], Path]:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        raise ValueError(
            "Could not analyze video input because ffmpeg is not installed or not on PATH."
        )

    temp_dir = Path(tempfile.mkdtemp(prefix="splatscout_"))
    output_pattern = temp_dir / "frame_%06d.png"
    command = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        f"fps={fps}",
        str(output_pattern),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise ValueError(f"ffmpeg failed while extracting frames: {result.stderr.strip() or 'unknown error'}")

    frames = sorted(temp_dir.glob("frame_*.png"))
    if not frames:
        raise ValueError("Video extraction completed but no frames were generated.")
    return frames, temp_dir
