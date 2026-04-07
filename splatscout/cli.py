"""CLI entry point for SplatScout."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from splatscout.config import Phase1Config
from splatscout.pipeline import analyze_path
from splatscout.reports.json_report import render_json_report, write_json_report
from splatscout.reports.terminal_report import render_terminal_report
from splatscout.utils.logging import configure_logging

try:
    import typer
except ImportError:  # pragma: no cover
    typer = None


def _run_analyze(
    input_path: str,
    mode: str | None,
    recursive: bool,
    fps: float,
    json_output: bool,
    output: str | None,
    strict: bool,
    debug: bool,
) -> int:
    configure_logging(debug)
    config = Phase1Config(
        recursive=recursive,
        fps=fps,
        strict=strict,
    )
    report = analyze_path(Path(input_path), config=config, mode=mode)

    if json_output:
        if output:
            write_json_report(report, Path(output))
            sys.stdout.write(render_terminal_report(report))
        else:
            sys.stdout.write(render_json_report(report))
            sys.stdout.write("\n")
    else:
        sys.stdout.write(render_terminal_report(report))

    if strict and report.has_errors:
        return 2
    return 0


def _run_optimize() -> int:
    raise ValueError("The optimize command is planned for Phase 4 and is not implemented yet.")


if typer is not None:
    app = typer.Typer(help="Validate 3DGS datasets before training.")

    @app.command()
    def analyze(
        input_path: str,
        mode: str | None = typer.Option(None, help="Force the input mode."),
        recursive: bool = typer.Option(False, help="Scan subdirectories for images."),
        fps: float = typer.Option(2.0, help="Video frame extraction rate."),
        json_output: bool = typer.Option(False, "--json", help="Emit JSON to stdout or --output."),
        output: str | None = typer.Option(None, help="Write JSON report to this path when --json is set."),
        strict: bool = typer.Option(False, help="Return a non-zero exit code when blocking issues are found."),
        debug: bool = typer.Option(False, help="Enable debug logging."),
    ) -> None:
        try:
            exit_code = _run_analyze(
                input_path=input_path,
                mode=mode,
                recursive=recursive,
                fps=fps,
                json_output=json_output,
                output=output,
                strict=strict,
                debug=debug,
            )
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
        raise typer.Exit(code=exit_code)

    @app.command()
    def optimize() -> None:
        raise typer.BadParameter("The optimize command is planned for Phase 4 and is not implemented yet.")


def _build_argparse_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="splatscout", description="Validate 3DGS datasets before training.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Analyze an input path.")
    analyze_parser.add_argument("input_path")
    analyze_parser.add_argument("--mode")
    analyze_parser.add_argument("--recursive", action="store_true")
    analyze_parser.add_argument("--fps", type=float, default=2.0)
    analyze_parser.add_argument("--json", dest="json_output", action="store_true")
    analyze_parser.add_argument("--output")
    analyze_parser.add_argument("--strict", action="store_true")
    analyze_parser.add_argument("--debug", action="store_true")

    subparsers.add_parser("optimize", help="Reserved for Phase 4.")
    return parser


def main(argv: list[str] | None = None) -> int:
    if typer is not None and argv is None:
        app()
        return 0

    parser = _build_argparse_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "analyze":
            return _run_analyze(
                input_path=args.input_path,
                mode=args.mode,
                recursive=args.recursive,
                fps=args.fps,
                json_output=args.json_output,
                output=args.output,
                strict=args.strict,
                debug=args.debug,
            )
        if args.command == "optimize":
            return _run_optimize()
    except ValueError as exc:
        parser.error(str(exc))
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
