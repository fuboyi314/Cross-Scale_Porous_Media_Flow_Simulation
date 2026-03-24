# Software Requirements Specification (Draft)

## 1. Project Background

**Project name:** Cross-Scale Porous Media Flow Simulation Platform Based on LBM.

This software is a desktop scientific application for porous media flow analysis. It supports the workflow from pore-scale image-based structure processing to REV-scale cross-scale statistical analysis. The current version scope focuses on 2D single-phase steady incompressible flow with D2Q9 LBM.

## 2. Project Goals

1. Provide a modular, maintainable Python desktop software platform.
2. Enable reproducible porous media image preprocessing and simulation workflows.
3. Compute flow fields, effective permeability, and REV convergence indicators.
4. Generate documentation-ready outputs (figures, tables, logs, reports) for engineering and registration materials.

## 3. Intended Users

- Researchers in porous media, geoscience, energy, and multiphysics modeling.
- Engineering users requiring image-based permeability and REV studies.
- Academic users performing method demonstrations and software validation exercises.

## 4. Functional Requirements

### 4.1 Project Management
- FR-01: Create/open/save simulation projects.
- FR-02: Persist project metadata and selected input paths.

### 4.2 Geometry Input and Preprocessing
- FR-03: Import 2D images (`png`, `jpg/jpeg`, `bmp`, `tif/tiff`).
- FR-04: Convert RGB image to grayscale.
- FR-05: Perform threshold segmentation.
- FR-06: Support optional binary inversion.
- FR-07: Remove small isolated regions.
- FR-08: Fill small enclosed holes if configured.
- FR-09: Crop ROI by user-defined bounds.
- FR-10: Output binary matrix with convention `1 = pore`, `0 = solid`.
- FR-11: Compute porosity and pixel statistics.

### 4.3 LBM Simulation
- FR-12: Run 2D D2Q9 BGK/SRT simulation.
- FR-13: Support solid bounce-back boundary treatment.
- FR-14: Support left-to-right density-driven flow setup.
- FR-15: Output density, `ux`, `uy`, velocity magnitude, average velocity.
- FR-16: Track residual history and convergence status.

### 4.4 Permeability and REV Analysis
- FR-17: Compute effective permeability from simulation outputs.
- FR-18: Produce lattice-unit permeability and optional physical-unit permeability when scaling is supplied.
- FR-19: Run REV window sampling across multiple sizes.
- FR-20: Compute per-window porosity and permeability via callback-based interface.
- FR-21: Aggregate size-wise REV statistics (mean/std/fluctuation/sample count).
- FR-22: Provide rule-based REV size suggestion.

### 4.5 Visualization and Export
- FR-23: Visualize original and binary geometry.
- FR-24: Visualize velocity fields and streamlines.
- FR-25: Visualize REV convergence curves.
- FR-26: Export PNG figures, CSV tables, JSON summaries, runtime logs, and Markdown summary report.

## 5. Non-Functional Requirements

- NFR-01: Modular architecture with clear separation of UI, solver, geometry, upscaling, and I/O.
- NFR-02: Readable code with type hints and docstrings.
- NFR-03: Explicit error handling; no silent failure handling in core workflow.
- NFR-04: Deterministic file naming and export folder organization with timestamps.
- NFR-05: Extensible structure for future 3D and advanced physics modules.

## 6. Operating Environment

- Programming language: Python (>=3.10)
- GUI framework: PySide6
- Scientific stack: NumPy
- Plotting: Matplotlib
- Image I/O: Pillow
- Typical OS target: Windows desktop (primary), with Linux/macOS compatibility where dependencies permit.

## 7. Scope Statement (Current Version)

- Included: 2D, single-phase, steady incompressible approximation.
- Not included in current version: full 3D analysis, multiphase models, advanced boundary model library, distributed computing runtime.
