# Cross-Scale Porous Media Flow Simulation Platform Based on LBM

A modular desktop scientific application for **2D porous-media flow simulation** and **cross-scale REV analysis**.

## Project Overview

This software targets image-based porous media studies with a complete workflow:

1. Project creation and management
2. 2D image import and preprocessing
3. D2Q9 LBM flow simulation (BGK/SRT)
4. Effective permeability calculation
5. REV-based cross-scale analysis
6. Visualization and structured export for documentation

Current release scope is V1.0 (2D, single-phase, steady incompressible approximation).

## Folder Structure

```text
.
├─ app.py
├─ pyproject.toml
├─ README.md
├─ docs/
│  ├─ requirements_spec.md
│  ├─ design_spec.md
│  ├─ user_manual.md
│  ├─ test_report.md
│  └─ phase1_overview.md
├─ src/
│  └─ cspmfs/
│     ├─ app.py
│     ├─ core/
│     ├─ geometry/
│     ├─ io/
│     ├─ lbm/
│     ├─ ui/
│     ├─ upscaling/
│     └─ visualization/
└─ tests/
```

## Installation

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
# source .venv/bin/activate
pip install -e .
```

## Run

```bash
python app.py
```

## Test

```bash
pytest -q
```

## Export Outputs

Each export creates a timestamped folder:

```text
<project_root>/exports/<project_name>_YYYYMMDD_HHMMSS/
├─ figures/   # PNG
├─ tables/    # CSV
├─ reports/   # JSON + Markdown report
└─ logs/      # runtime.log copy
```

## Known Limitations (V1.0)

- 2D only (no 3D yet)
- Single-phase only
- Steady incompressible approximation only
- Density-driven boundary setup implemented; broader BC library not yet included
- REV evaluation can be computationally heavy for large windows because each sample triggers a local simulation

## Completed Feature Set

- Project create/open/save
- Image import and preprocessing (threshold, inversion, denoise filters, ROI)
- Porosity and geometry statistics
- D2Q9 BGK/SRT solver with convergence monitoring
- Permeability postprocessing (lattice and optional physical conversion)
- REV statistics and suggestion
- Visualization and structured export package
- Unit/smoke tests for key modules

## Recommended V1.1 Roadmap

1. Parallelized REV sampling (multi-process/thread worker queue)
2. Additional boundary condition options and validation cases
3. Embedded in-GUI plotting panels (instead of popup figures)
4. Batch project runner and CLI automation mode
5. Benchmark dataset pack + formal verification report templates
