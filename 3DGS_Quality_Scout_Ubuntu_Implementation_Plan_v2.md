# 3DGS Quality Scout — Ubuntu-First Implementation Plan for AI Coding Agents

**Project:** 3DGS Quality Scout  
**Planning date:** April 2026  
**Target implementers:** Codex, Claude Code, or similar agentic coding systems operating through VS Code  
**Primary deployment target for this plan:** Ubuntu Linux only  
**Out of scope for this planning phase:** Windows packaging, macOS packaging, cross-platform GUI distribution

---

## 1. Purpose

Build a modular Python tool that analyzes a folder of images, video frames, or COLMAP sparse outputs **before** 3D Gaussian Splatting training. The tool should estimate whether the dataset is suitable for 3DGS, identify likely failure modes, provide actionable recommendations, and determine whether the dataset can be **optimized** by removing redundant images that add compute cost without materially improving reconstruction support.

This plan is written so that an AI coding agent can implement the project in a staged, low-risk way on **Ubuntu first**. The focus is on correctness, modularity, maintainability, and a clean CLI-first architecture that can later support a GUI.

---

## 2. High-level product definition

The system should:

1. Accept one of several inputs:
   - Raw image folder
   - COLMAP sparse output (`cameras.bin`, `images.bin`, `points3D.bin`)
   - COLMAP text output
   - Video file (frames extracted internally)

2. Run multiple layers of analysis:
   - Input validation and sanity checks
   - Per-image quality analysis
   - Collection-level geometry and overlap analysis
   - Scene characterization
   - Final scoring and recommendations
   - Dataset optimization analysis for redundancy reduction

3. Produce outputs in multiple formats:
   - Rich terminal report
   - JSON report
   - HTML report

4. Be able to identify redundant images and, when explicitly requested by the user, generate an **optimized dataset** with those images removed in order to reduce unnecessary 3DGS training time.

5. Be implemented first as a **Python CLI application on Ubuntu**.

---

## 3. Ubuntu-first assumptions

For the planning and implementation stage, assume:

- OS: Ubuntu 22.04 or 24.04
- Python: 3.11 preferred
- Package manager: `pip` with virtual environment
- No GPU required for analysis
- All development and testing happen on Ubuntu
- Filesystem, path handling, temp files, subprocess calls, and dependency installation should all be designed for Ubuntu first
- No platform-specific abstraction for Windows or macOS is needed yet unless it is easy and natural to keep code portable

### Ubuntu-specific implementation guidance

- Use `pathlib` everywhere for file paths
- Prefer pure Python or widely available Linux-compatible packages
- Assume `ffmpeg` may be installed via `apt`, but design code to fail gracefully if it is missing
- Use temporary directories under `/tmp` or Python `tempfile`
- Avoid any Windows-specific path logic
- Avoid PyInstaller, installer scripts, code signing, `.exe`, `.dmg`, and notarization concerns for now
- GUI packaging is out of scope in this phase

---

## 4. Implementation strategy

Implement the system in **five sequential phases**. Do not attempt to build everything at once.

### Phase 1 — Core CLI + input validation
Deliver a working command-line tool that:
- accepts an input path
- detects input mode
- loads and normalizes files
- runs fast sanity checks
- outputs terminal and JSON summaries

### Phase 2 — Per-image quality analysis
Add image-level metrics:
- blur
- exposure
- highlights
- noise proxy
- sky/reflective heuristics
- flagged image reporting

### Phase 3 — Geometry and overlap analysis
Add collection-level structure:
- feature extraction
- candidate pair estimation
- co-visibility graph
- isolated image detection
- coverage and diversity analysis
- loop-closure proxy

### Phase 4 — Scoring, recommendations, and dataset optimization
Add:
- weighted sub-scores
- overall grade
- scene-aware thresholds
- recommendation engine
- strict mode exit codes
- redundant image selection logic
- optimized dataset export at user request

### Phase 5 — HTML reporting
Add:
- static HTML report generation
- thumbnails for flagged images
- structured summary cards
- optional diagnostic plots
- optimized-dataset summary when relevant

Do **not** implement a GUI during the initial Ubuntu-first build unless all CLI phases are stable.

---

## 5. Repository structure

Use this structure:

```text
splatscout/
  pyproject.toml
  README.md
  .gitignore

  splatscout/
    __init__.py
    cli.py
    config.py
    constants.py
    types.py

    io/
      __init__.py
      loaders.py
      image_normalize.py
      exif.py
      colmap_parser.py
      video_frames.py

    validation/
      __init__.py
      sanity_checks.py
      duplicates.py
      scene_consistency.py

    optimization/
      __init__.py
      redundancy.py
      subset_selector.py
      export.py

    image_quality/
      __init__.py
      blur.py
      exposure.py
      highlights.py
      noise.py
      reflective_sky.py

    geometry/
      __init__.py
      features.py
      pair_estimation.py
      covisibility.py
      coverage.py
      view_diversity.py
      baseline_depth.py
      loop_closure.py

    scene/
      __init__.py
      classifier.py
      resource_estimator.py

    scoring/
      __init__.py
      score_engine.py
      thresholds.py
      recommendations.py

    reports/
      __init__.py
      terminal_report.py
      json_report.py
      html_report.py
      templates/

    utils/
      __init__.py
      logging.py
      paths.py
      parallel.py
      image_ops.py

  tests/
    test_io.py
    test_validation.py
    test_image_quality.py
    test_geometry.py
    test_scoring.py
    test_optimization.py
    test_reports.py

  sample_data/
    README.md
```

---

## 6. Development environment on Ubuntu

The AI coding agent should set up the project like this:

### Recommended system packages
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip ffmpeg libgl1
```

### Recommended Python environment
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

### Initial Python dependencies
```bash
pip install typer rich pillow numpy scipy opencv-python networkx jinja2 pydantic
```

### Optional dependencies
```bash
pip install pillow-heif rawpy matplotlib imagehash
```

Notes:
- `opencv-python` is sufficient for Ubuntu development unless system OpenCV conflicts arise
- `pillow-heif` and `rawpy` should be optional extras, not hard requirements
- keep optional dependencies isolated so base installs remain simple

---

## 7. Core architectural principles

The coding agent must follow these rules:

1. **CLI-first architecture**
   - All analysis logic belongs in reusable modules, not in CLI command bodies.

2. **Single internal report model**
   - Terminal, JSON, and HTML reports must all be generated from the same structured internal data model.

3. **Separation of concerns**
   - Input parsing, metric computation, scoring, and reporting must remain separate.

4. **Deterministic behavior**
   - Given the same input and config, the tool should return reproducible outputs.

5. **Fast enough for laptop use**
   - Analysis should remain practical for approximately 100–200 images on a normal Ubuntu laptop.

6. **Graceful degradation**
   - If EXIF or COLMAP data is absent, the tool should continue with weaker heuristics rather than crashing.

7. **Ubuntu-first reliability over cleverness**
   - Prefer simpler, robust implementations over fragile, ambitious ones.

8. **Optimization must be conservative**
   - The tool may recommend and export a reduced dataset, but it must avoid aggressive pruning that risks removing useful geometric support.

---

## 8. Data model

The coding agent should create strongly typed internal models. Use `dataclasses` or `pydantic`. Example structure:

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ImageRecord:
    path: str
    width: int
    height: int
    exif: dict[str, Any] = field(default_factory=dict)
    converted_path: str | None = None
    format: str | None = None

@dataclass
class ImageQualityMetrics:
    blur_score: float | None = None
    blur_type: str | None = None
    exposure_mean: float | None = None
    exposure_std: float | None = None
    clipped_ratio: float | None = None
    noise_score: float | None = None
    sky_reflective_ratio: float | None = None
    flags: list[str] = field(default_factory=list)

@dataclass
class GeometryMetrics:
    keypoint_count: int | None = None
    estimated_neighbors: int | None = None
    isolated: bool = False
    baseline_proxy: float | None = None
    view_direction: list[float] | None = None
    flags: list[str] = field(default_factory=list)

@dataclass
class DatasetSubscores:
    input_quality: float
    feature_richness: float
    geometry_coverage: float
    scene_difficulty: float

@dataclass
class OptimizationReport:
    redundant_images: list[str] = field(default_factory=list)
    candidate_removals: list[str] = field(default_factory=list)
    retained_images: list[str] = field(default_factory=list)
    estimated_reduction_count: int = 0
    estimated_reduction_percent: float = 0.0
    optimization_notes: list[str] = field(default_factory=list)

@dataclass
class DatasetReport:
    image_count: int
    scene_type: str
    input_mode: str
    subscores: DatasetSubscores
    overall_score: float
    grade: str
    issues: list[str]
    recommendations: list[str]
    optimization: OptimizationReport | None = None
```

The exact schema may evolve, but the agent must preserve a stable internal report object.

---

## 9. CLI design

Use `typer` for the command-line interface.

### Initial command surface
```bash
splatscout analyze ./images/
splatscout analyze ./colmap_sparse/ --mode colmap
splatscout analyze footage.mp4 --fps 2
splatscout analyze ./images/ --json
splatscout analyze ./images/ --html --output report.html
splatscout analyze ./images/ --strict
splatscout analyze ./images/ --flagged-only
splatscout analyze ./images/ --scene-type outdoor-object
splatscout analyze ./images/ --blur-threshold 80
splatscout optimize ./images/ --output-dir ./optimized_dataset
splatscout optimize ./images/ --dry-run
splatscout optimize ./images/ --include-report
```

### CLI requirements
- clear help text
- human-readable validation errors
- exit code `0` on success
- nonzero exit code on hard failure
- strict mode should return nonzero exit code if data quality is below threshold
- optimization mode must never modify the original dataset in place

---

## 10. Phase 1 details — input validation and sanity checks

### Goals
Implement a fast validation layer that runs before heavy analysis.

### Required checks
1. Minimum image count
   - warn below 30
   - hard reject below 10

2. File readability
   - verify all image files can be opened

3. Input mode detection
   - image folder
   - video
   - COLMAP sparse binary
   - COLMAP sparse text

4. Resolution consistency
   - flag mixed portrait and landscape
   - flag high variance in resolution

5. EXIF extraction
   - focal length
   - sensor metadata if available
   - GPS if available
   - warn when EXIF is absent or broken

6. Duplicate detection
   - perceptual hash (`pHash`) for near-duplicate images
   - cluster redundant frames into duplicate or near-duplicate groups

7. Redundancy analysis for optimization
   - identify images that are likely redundant for 3DGS preprocessing and likely add compute cost more than reconstruction benefit
   - separate true duplicates from merely similar but potentially useful views

7. Wrong input type detection
   - reject `.ply` as invalid for pre-training analysis

8. Multiple-scene suspicion
   - initial heuristic only
   - stronger graph-based logic can come later

### Implementation notes
- Use Pillow for opening files
- Use `imagehash` or custom pHash logic
- Resolve symlinks
- Handle Unicode paths correctly
- Normalize all internal paths with `pathlib.Path`

---

## 11. Phase 2 details — per-image quality analysis

### Goals
Compute per-image diagnostic metrics and attach flags.

### Required metrics

#### Blur
- Start with Laplacian variance
- Rank blur relative to the image set
- Add basic blur thresholding
- Optional second-stage heuristic for motion blur vs defocus blur

#### Exposure
- Luminance mean
- Luminance standard deviation
- Flag strongly underexposed and overexposed images

#### Clipped highlights
- Measure fraction of saturated bright pixels
- Warn when highlight clipping is severe

#### Noise proxy
- Estimate sensor noise using local texture-poor regions or wavelet/high-frequency residual proxies

#### Sky / reflective surface ratio
- Use a simple heuristic segmentation approach
- Keep this conservative in MVP
- Label as a heuristic in reporting

### Output behavior
For each image:
- store computed metrics
- assign flags with severity
- support “flagged only” CLI output later

---

## 12. Phase 3 details — geometry and overlap analysis

This is the core technical module.

### 12.1 Feature extraction
Implement:
- SIFT if available in OpenCV build
- ORB fallback if needed

For each image:
- keypoint count
- descriptor extraction
- optional spatial spread statistic

### 12.2 Candidate pair estimation
Do not begin with exhaustive all-pairs matching if avoidable.

Recommended approach:
1. Compute per-image descriptors
2. Build a lightweight similarity shortlist
3. Run descriptor matching only on shortlisted pairs

Possible approaches:
- bag-of-visual-words proxy
- descriptor centroid similarity
- global image embedding proxy if simple and CPU-safe
- temporal adjacency heuristic for video-derived frames

### 12.3 Co-visibility graph
Create a graph:
- nodes = images
- weighted edges = estimated overlap or strong matching likelihood

From this graph compute:
- degree per node
- isolated images
- connected components
- weak overlap clusters
- global overlap strength

This graph should become the backbone of collection-level diagnostics.

### 12.4 Coverage analysis
Two modes:

#### A. If actual camera poses are available from COLMAP
- use camera centers directly
- identify sparse regions
- detect spatial gaps
- produce stronger diagnostics

#### B. If only raw images are available
- use GPS EXIF if present
- otherwise use graph-based approximation only
- clearly indicate reduced confidence

### 12.5 Viewing angle diversity
- Use camera pose information if available
- Otherwise estimate only weakly
- Penalize datasets captured from nearly identical viewpoints

### 12.6 Baseline-to-depth proxy
- Stronger implementation in COLMAP mode
- Heuristic proxy in raw-image mode
- Store confidence level

### 12.7 Loop closure potential
Implement as:
- graph cycle / return-to-start heuristic
- stronger spatial version when poses exist
- useful especially in larger scenes or video-derived captures

---

## 13. Phase 4 details — scoring, recommendations, and optimization

### 13.1 Sub-score categories
Use the following initial weights:

- Input Quality: 25%
- Feature Richness: 25%
- Geometry Coverage: 30%
- Scene Difficulty: 20%

### 13.2 Score bands
- A = 80–100
- B = 60–79
- C = 40–59
- F = 0–39

### 13.3 Scoring logic
Each raw metric must be normalized to a 0–100 score before aggregation.

Examples:
- duplicate penalty
- blur penalty
- EXIF completeness
- mean keypoint sufficiency
- graph connectivity quality
- coverage continuity
- angle diversity
- reflection/sky difficulty

### 13.4 Recommendations engine
Implement as a rule-based system, not ML.

Examples:
- low co-visibility → add overlapping views
- too many isolated images → remove or retake poor viewpoints
- low angle diversity → capture from varied heights and oblique angles
- high duplicate count → reduce frame extraction density
- severe blur → retake with slower motion or faster shutter
- missing EXIF → use original images instead of stripped exports

### 13.5 Strict mode
- if overall grade is below threshold, return failure exit code
- optionally fail on any blocking issue

---

## 14. Phase 5 details — HTML reporting

### Goals
Generate a shareable static report.

### Requirements
- summary score card
- grade
- sub-score visualization
- top issues
- recommendations
- flagged image gallery
- optional diagnostic plots
- optimization summary when redundant images are detected
- retained vs removed image counts when optimization is run
- self-contained or minimally dependent HTML

### Suggested implementation
- `jinja2` template
- CSS embedded locally
- thumbnail generation stored in temp or output directory
- optional matplotlib figures saved as PNG

Keep the HTML report simple and reliable.

---

## 15. Input handling design

### Supported input modes
1. Raw image folder
2. Video file
3. COLMAP sparse binary output
4. COLMAP text output

### Normalization pipeline
All modes should feed a common internal interface.

#### Raw images
- scan recursively or non-recursively according to config
- detect supported formats
- convert unsupported but recoverable formats to internal PNG
- keep originals untouched

#### Video
- extract frames using `ffmpeg` if available
- fallback to OpenCV video decode if needed
- allow user-set FPS
- save extracted frames in temp workspace

#### COLMAP
- parse sparse model
- expose:
  - camera intrinsics
  - image entries
  - camera centers / poses if derivable
  - sparse point stats

### Important design rule
COLMAP mode should not rely on the same weak geometry proxies as raw-image mode if stronger information is available.

---

## 16. Dependency policy

### Core dependencies
These should remain small and stable:
- typer
- rich
- pillow
- numpy
- scipy
- opencv-python
- networkx
- jinja2

### Optional dependencies
- pillow-heif
- rawpy
- imagehash
- matplotlib

### Dependency rules
- optional features must fail gracefully with informative messages
- avoid obscure or poorly maintained packages
- document Ubuntu installation clearly
- keep the base CLI install lightweight

---

## 17. Performance constraints

Target runtime:
- approximately 30–90 seconds for around 150 images on a normal Ubuntu laptop

### Performance rules
- downsample images for analysis where possible
- cache intermediate normalized images
- parallelize per-image analysis
- avoid exhaustive pair matching for large sets
- reuse descriptors between modules
- reuse redundancy-analysis artifacts during optimization export
- expose config knobs for speed/quality tradeoff

### Parallelism
Use either:
- `concurrent.futures`
- joblib if needed later

Keep parallel code simple and Linux-safe.

---

## 18. Testing strategy

The AI coding agent must create tests early.

### Test types
1. Unit tests
2. Small integration tests
3. Regression tests on miniature example datasets

### Minimum sample datasets to prepare
- good indoor object dataset
- blur-heavy dataset
- duplicate-heavy dataset
- redundancy-heavy video-frame dataset
- low-texture dataset
- multi-scene mistaken folder
- aerial/nadir-style dataset
- small COLMAP sparse example

### What to test
- input mode detection
- file normalization
- duplicate detection
- blur ranking consistency
- graph construction behavior
- score stability
- optimization selection stability
- optimized export directory correctness
- JSON schema validity
- CLI exit codes

### Ubuntu CI recommendation
Use GitHub Actions on Ubuntu with:
- Python 3.11
- dependency install
- pytest
- linting

---

## 19. Logging and error handling

### Logging
Implement structured logging with levels:
- INFO
- WARNING
- ERROR
- DEBUG

### Error handling rules
- no raw stack traces to end users in normal CLI mode
- provide actionable messages
- preserve full debug info in logs when `--debug` is enabled

### Example style
Bad:
- “IndexError in module X”

Good:
- “Could not parse COLMAP sparse directory: `points3D.bin` missing or invalid.”

---

## 20. Configuration system

Create a config layer that supports:
- default thresholds
- scene-type overrides
- CLI parameter overrides

Possible options:
- blur threshold
- duplicate pHash threshold
- min image count
- scene type override
- frame extraction FPS
- downsample size
- strict mode thresholds

Use either:
- a simple YAML config file
- or internal defaults plus CLI overrides for MVP

For Ubuntu-first MVP, internal defaults plus CLI options are sufficient.

---

## 21. Recommended implementation order inside the codebase

### Step 1
Set up package, CLI skeleton, type models, and report schema.

### Step 2
Implement loaders and input mode detection.

### Step 3
Implement sanity checks and duplicate detection.

### Step 4
Implement per-image quality metrics.

### Step 5
Implement feature extraction and image-level feature counts.

### Step 6
Implement candidate pair estimation and co-visibility graph.

### Step 7
Implement scoring engine, recommendation rules, and conservative redundancy-selection logic.

### Step 8
Implement terminal and JSON reports.

### Step 9
Implement optimization export (`optimize` command and `--dry-run` behavior).

### Step 10
Implement HTML report.

### Step 11
Polish tests, docs, and packaging.

---

## 22. What not to do in the initial Ubuntu phase

Do not spend time yet on:
- Windows installers
- macOS packaging or notarization
- Tauri
- Electron
- system tray behavior
- auto-update systems
- mobile apps
- neural classifiers for scene type
- overengineered learned-image-quality models
- GPU acceleration for analysis
- direct training integration with nerfstudio or gsplat

These are future concerns and should not block the core Ubuntu CLI.

---

## 23. Deliverables for the first usable release

A successful Ubuntu MVP should provide:

1. Installable Python package
2. `splatscout analyze ...` CLI command
3. Input handling for image folders and basic COLMAP parsing
4. Validation and duplicate detection
5. Blur and exposure analysis
6. Feature richness and co-visibility diagnostics
7. Overall dataset grade
8. Top issues and actionable recommendations
9. Redundant-image detection and optimization recommendation
10. JSON report export
11. Optional optimized dataset export into a separate directory
12. Optional HTML report

That is already enough to validate the product concept and support future publication or broader tooling.

---

## 24. Acceptance criteria for AI coding agent

The implementation should be considered successful when all of the following are true:

- runs on Ubuntu in a fresh virtual environment
- installs without platform-specific hacks
- handles normal image folders robustly
- does not crash on missing EXIF
- does not crash when optional dependencies are absent
- produces interpretable CLI output
- exports machine-readable JSON
- detects obvious duplicates and blur cases
- identifies candidate redundant images conservatively
- can export an optimized dataset without touching originals
- produces at least a basic geometry overlap assessment
- has automated tests that pass on Ubuntu CI

---

## 25. Final instruction to coding agent

Implement this project as a **modular, Ubuntu-first Python CLI tool**, emphasizing correctness, maintainability, and practical usefulness. Avoid premature cross-platform concerns. Build the reusable analysis engine first, then layer reporting and optimization features on top of it. Keep every module narrowly scoped, testable, and documented.

A core requirement is that the tool must not only analyze dataset quality, but also determine whether a smaller optimized dataset can be derived by removing redundant images that mainly increase 3DGS compute cost. This optimization must be conservative, explainable, and never destructive to the original dataset.

The Ubuntu-first CLI is the product for now. Windows and macOS can be addressed later after the core engine is stable.
