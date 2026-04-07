"""Filesystem helpers."""

from __future__ import annotations

from pathlib import Path


def resolve_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def safe_relative(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return path.name
