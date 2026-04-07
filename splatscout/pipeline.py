"""High-level analysis orchestration."""

from __future__ import annotations

from pathlib import Path

from splatscout.config import Phase1Config
from splatscout.io.loaders import load_input
from splatscout.types import DatasetReport
from splatscout.validation.sanity_checks import build_phase1_report


def analyze_path(
    input_path: Path,
    config: Phase1Config,
    mode: str | None = None,
) -> DatasetReport:
    loaded_input = load_input(
        input_path,
        forced_mode=mode,
        recursive=config.recursive,
        fps=config.fps,
    )
    return build_phase1_report(loaded_input, config)
