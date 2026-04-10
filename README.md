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

Phase 2 adds an opt-in OpenCV quality pass for:

- blur
- exposure
- clipped highlights
- noise proxy
- sky and reflective heuristics
- flagged image reporting

## Install

```bash
cd /home/dreamslab/3DGS-Image-Quality-Assessment-Tool
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
```

Run `splatscout` while both of these are true:

- the virtual environment is active
- your shell is inside the project directory: `/home/dreamslab/3DGS-Image-Quality-Assessment-Tool`

Typical startup flow:

```bash
cd /home/dreamslab/3DGS-Image-Quality-Assessment-Tool
source .venv/bin/activate
```

If your active virtual environment was created before dependency changes, or the CLI fails with missing-package errors, reinstall the project into that environment:

```bash
pip install -e /home/dreamslab/3DGS-Image-Quality-Assessment-Tool
```

Use that reinstall command when:

- a new dependency was added, such as `opencv-python`
- you already had the `venv` active, but the package was not reinstalled after updates
- you see an import error such as `ModuleNotFoundError: No module named 'cv2'`

## Usage

Phase 1 commands:

```bash
splatscout analyze ./images
splatscout analyze ./images --json
splatscout analyze ./images --json --output report.json
splatscout analyze ./images --strict
splatscout analyze ./colmap_sparse --mode colmap_text
```

Phase 2 commands:

```bash
splatscout analyze ./images --quality
splatscout analyze ./images --quality --json
splatscout analyze ./images --quality --json --output phase2_report.json
splatscout analyze ./images --quality --flagged-only
splatscout analyze ./images --quality --strict
```

Phase 2 quality flags:

- `--quality` enables the OpenCV-based image quality pass
- `--blur-threshold` changes the blur flag threshold
- `--exposure-min` changes the underexposure threshold
- `--exposure-max` changes the overexposure threshold
- `--clipped-threshold` changes the clipped-highlight threshold
- `--noise-threshold` changes the noise proxy threshold
- `--sky-threshold` changes the sky/reflective heuristic threshold
- `--flagged-only` limits terminal output to flagged images

Example using your dataset and output folder:

```bash
splatscout analyze /home/dreamslab/Yellow_Boat/images/boat_5_fps --quality --json --output /home/dreamslab/Yellow_Boat/image_checker/phase2_report.json
```

## Notes

- The codebase uses `pathlib` and keeps runtime logic portable so you can build on Windows and test on Ubuntu later.
- Video extraction expects `ffmpeg` to be installed when analyzing video files.
- Optional extras such as `imagehash` are not required for Phase 1.
- Phase 2 requires OpenCV to be installed in the active virtual environment.
