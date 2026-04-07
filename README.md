# SplatScout

SplatScout is an Ubuntu-first Python CLI for validating image, video, and COLMAP sparse inputs before 3D Gaussian Splatting training.

Phase 1 currently includes:

- input mode detection
- image and COLMAP sparse loading
- fast sanity checks
- EXIF extraction
- duplicate and near-duplicate heuristics
- terminal and JSON reports
- strict-mode exit handling

## Install

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
```

## Usage

```bash
splatscout analyze ./images
splatscout analyze ./images --json
splatscout analyze ./images --json --output report.json
splatscout analyze ./images --strict
splatscout analyze ./colmap_sparse --mode colmap_text
```

## Notes

- The codebase uses `pathlib` and keeps runtime logic portable so you can build on Windows and test on Ubuntu later.
- Video extraction expects `ffmpeg` to be installed when analyzing video files.
- Optional extras such as `imagehash` are not required for Phase 1.
