# User Manual (Draft)

## 1. Installation

1. Install Python 3.10+.
2. Create virtual environment.
3. Install project dependencies.

Example:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -e .
```

## 2. Startup

Run desktop GUI:

```bash
python app.py
```

## 3. Typical Workflow

### 3.1 Create/Open Project
- Use **File → New Project** to select an empty project folder.
- Use **File → Open Project** to load an existing project.
- Use **File → Save Project** to persist current metadata.

### 3.2 Import Image
- Use **File → Import 2D Image**.
- Supported: png, jpg/jpeg, bmp, tif/tiff.

### 3.3 Preprocess Geometry
- Set threshold, inversion, component/hole filters, and ROI parameters.
- Run **Simulation → Preprocess Geometry**.
- Review original and binary previews and porosity in summary panel.

### 3.4 Run Simulation
- Set LBM parameters (`tau`, `rho_in`, `rho_out`, iteration/tolerance settings).
- Run **Simulation → Run Simulation**.
- Monitor progress in runtime log panel.
- Review velocity/convergence/permeability outputs in summary panel.

### 3.5 Run REV Analysis
- Set REV parameters (minimum size, number of sizes, stride factor, sample cap).
- Run **Simulation → Run REV Analysis**.
- Review REV suggestion and convergence behavior.

### 3.6 Export Results
- Use **Export → Export Full Package** for complete artifacts.
- Use **Export → Export Figures Only** for PNG figure bundle.
- Exported files are written to timestamped directories under project `exports/`.

## 4. Troubleshooting

### 4.1 "Create or open a project first"
Create a project before running import/preprocess/simulation/export actions.

### 4.2 "Import an image first"
Image-dependent actions require a valid imported image path.

### 4.3 No physical permeability value
Set `dx [m/lu]` to a positive value to enable `k (m^2)` conversion.

### 4.4 REV cannot suggest size
This may occur when stabilization thresholds are not met with current sampling parameters. Increase sizes/samples or adjust thresholds.

## 5. Notes

- Current version scope is 2D, single-phase, steady incompressible approximation.
- Physical-unit interpretation requires user-provided scaling assumptions.
