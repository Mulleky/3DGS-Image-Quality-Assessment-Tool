"""JSON report rendering."""

from __future__ import annotations

import json
from pathlib import Path

from splatscout.types import DatasetReport, model_to_dict


def render_json_report(report: DatasetReport, pretty: bool = True) -> str:
    indent = 2 if pretty else None
    return json.dumps(model_to_dict(report), indent=indent, sort_keys=False)


def write_json_report(report: DatasetReport, output_path: Path) -> None:
    output_path.write_text(render_json_report(report, pretty=True), encoding="utf-8")
