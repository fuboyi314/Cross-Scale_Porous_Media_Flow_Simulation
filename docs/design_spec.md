# Software Design Specification (Draft)

## 1. Architectural Overview

The system adopts a layered modular architecture:

- **UI layer (`ui`)**: User interactions and workflow orchestration.
- **Core layer (`core`)**: Project management and logging services.
- **Geometry layer (`geometry`)**: Image loading and preprocessing pipeline.
- **LBM layer (`lbm`)**: Numerical solver and simulation interfaces.
- **Upscaling layer (`upscaling`)**: Permeability and REV analytics.
- **Visualization layer (`visualization`)**: Plot generation and image previews.
- **I/O layer (`io`)**: Structured export and report generation.

## 2. Module Design

### 2.1 `core`
- `ProjectManager`: create/open/save project metadata.
- `LogManager`: rotating file logging and GUI sink integration.

### 2.2 `geometry`
- `preprocess_image(...)`: orchestrates image preprocessing.
- `PreprocessConfig`: parameter object for segmentation and morphology.
- `PreprocessResult`: structured output used by solver and UI.

### 2.3 `lbm`
- `D2Q9LBMSolver`: BGK/SRT simulation engine.
- `SimulationConfig`: runtime parameters (tau, densities, iterations, tolerance).
- `SimulationResult`: flow field and convergence outputs.

### 2.4 `upscaling`
- `compute_effective_permeability(...)`: Darcy-based postprocessing utility.
- `REVAnalyzer`: callback-based multi-window REV statistics engine.
- `REVConfig`, `REVResult`, `REVSizeStats`: REV data contracts.

### 2.5 `visualization`
- Figure builders for geometry, fields, streamlines, and REV curves.
- Unified figure save helper for reproducible output assets.

### 2.6 `io`
- Export root builder with timestamp naming.
- CSV/JSON/log/report writers.
- Summary report line builder for reproducible documentation artifacts.

## 3. Data Flow

1. User imports image in UI.
2. Geometry preprocessing generates binary matrix and porosity stats.
3. LBM solver consumes binary matrix and simulation config.
4. Permeability module consumes average velocity, density gradient, viscosity, and length.
5. REV module samples windows, invokes permeability callback, aggregates statistics.
6. Visualization and export modules generate figures/tables/reports.

## 4. Key Classes and Interfaces

- `PreprocessConfig`, `PreprocessResult`
- `SimulationConfig`, `SimulationResult`
- `PermeabilityInput`, `PermeabilityResult`
- `REVConfig`, `REVWindowSample`, `REVSizeStats`, `REVResult`
- `REVAnalyzer(permeability_callback)`

The callback-based REV interface is intentionally decoupled from solver implementation to enable future alternate solvers and 3D extensions.

## 5. Storage and Export Design

### 5.1 Project Storage
- Per-project JSON metadata file in project root.

### 5.2 Export Storage
Timestamped export root:

```text
<project_root>/exports/<project_name>_YYYYMMDD_HHMMSS/
├─ figures/
├─ tables/
├─ reports/
└─ logs/
```

### 5.3 Export Artifacts
- Figures: PNG
- Tables: CSV
- Summaries: JSON + Markdown report
- Runtime trace: copied LOG/TXT

## 6. Extensibility Notes

- 3D extension can reuse interface contracts while replacing 2D operators.
- REV callback abstraction allows plugging different permeability evaluators.
- Export schema can be versioned in future for traceability.
