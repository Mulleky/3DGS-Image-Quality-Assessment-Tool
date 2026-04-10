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
    quality: bool,
    blur_threshold: float,
    exposure_min: float,
    exposure_max: float,
    clipped_threshold: float,
    noise_threshold: float,
    sky_threshold: float,
    flagged_only: bool,
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
        quality=quality,
        blur_threshold=blur_threshold,
        exposure_min=exposure_min,
        exposure_max=exposure_max,
        clipped_threshold=clipped_threshold,
        noise_threshold=noise_threshold,
        sky_threshold=sky_threshold,
    )
    report = analyze_path(Path(input_path), config=config, mode=mode)

    if json_output:
        if output:
            write_json_report(report, Path(output))
            sys.stdout.write(render_terminal_report(report, flagged_only=flagged_only))
        else:
            sys.stdout.write(render_json_report(report))
            sys.stdout.write("\n")
    else:
        sys.stdout.write(render_terminal_report(report, flagged_only=flagged_only))

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
        quality: bool = typer.Option(False, help="Run OpenCV-based image quality analysis."),
        blur_threshold: float = typer.Option(80.0, help="Flag images below this blur score."),
        exposure_min: float = typer.Option(0.20, help="Flag images below this normalized exposure mean."),
        exposure_max: float = typer.Option(0.80, help="Flag images above this normalized exposure mean."),
        clipped_threshold: float = typer.Option(0.03, help="Flag images above this clipped highlight ratio."),
        noise_threshold: float = typer.Option(0.12, help="Flag images above this noise proxy score."),
        sky_threshold: float = typer.Option(0.35, help="Flag images above this sky or reflective dominance ratio."),
        flagged_only: bool = typer.Option(False, help="Show only flagged images in terminal output."),
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
                quality=quality,
                blur_threshold=blur_threshold,
                exposure_min=exposure_min,
                exposure_max=exposure_max,
                clipped_threshold=clipped_threshold,
                noise_threshold=noise_threshold,
                sky_threshold=sky_threshold,
                flagged_only=flagged_only,
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
    analyze_parser.add_argument("--quality", action="store_true")
    analyze_parser.add_argument("--blur-threshold", type=float, default=80.0)
    analyze_parser.add_argument("--exposure-min", type=float, default=0.20)
    analyze_parser.add_argument("--exposure-max", type=float, default=0.80)
    analyze_parser.add_argument("--clipped-threshold", type=float, default=0.03)
    analyze_parser.add_argument("--noise-threshold", type=float, default=0.12)
    analyze_parser.add_argument("--sky-threshold", type=float, default=0.35)
    analyze_parser.add_argument("--flagged-only", action="store_true")
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
                quality=args.quality,
                blur_threshold=args.blur_threshold,
                exposure_min=args.exposure_min,
                exposure_max=args.exposure_max,
                clipped_threshold=args.clipped_threshold,
                noise_threshold=args.noise_threshold,
                sky_threshold=args.sky_threshold,
                flagged_only=args.flagged_only,
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
