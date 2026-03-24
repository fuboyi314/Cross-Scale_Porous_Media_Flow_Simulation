# Test Report (Draft Template)

## 1. Test Environment

- OS: [PLACEHOLDER: specify OS and version]
- Python: [PLACEHOLDER: specify version]
- Key libraries: PySide6, NumPy, Matplotlib, Pillow, pytest
- Execution mode: local desktop and/or CI

## 2. Test Items

1. Image preprocessing
2. LBM solver execution and output fields
3. Permeability calculation
4. REV analysis and suggestion logic
5. Export generation (PNG/CSV/JSON/LOG/MD)
6. GUI startup smoke test

## 3. Test Cases

### TC-01 Preprocessing basic segmentation
- Input: known grayscale/threshold sample
- Expected: binary output contains only {0,1}; porosity calculation correct
- Actual: [PLACEHOLDER]
- Status: [PLACEHOLDER]

### TC-02 LBM channel flow sanity check
- Input: simple channel mask with top/bottom solid walls
- Expected: positive mean streamwise flow, valid field shapes, residual history generated
- Actual: [PLACEHOLDER]
- Status: [PLACEHOLDER]

### TC-03 Permeability known-value check
- Input: synthetic parameter set with analytically checked Darcy relation
- Expected: computed lattice permeability matches expected value within tolerance
- Actual: [PLACEHOLDER]
- Status: [PLACEHOLDER]

### TC-04 REV statistics generation
- Input: synthetic porous mask and deterministic callback
- Expected: multiple window-size stats generated; valid sample counts > 0
- Actual: [PLACEHOLDER]
- Status: [PLACEHOLDER]

### TC-05 Export artifact generation
- Input: project run with preprocess/simulation/REV results
- Expected: timestamped output folder with required subfolders and files
- Actual: [PLACEHOLDER]
- Status: [PLACEHOLDER]

### TC-06 GUI startup smoke
- Input: headless/offscreen startup
- Expected: main window constructs without crash
- Actual: [PLACEHOLDER]
- Status: [PLACEHOLDER]

## 4. Defect and Risk Notes

- [PLACEHOLDER: list known issues if any]
- [PLACEHOLDER: list unresolved risks and mitigation plans]

## 5. Conclusion

- Overall result: [PLACEHOLDER: Pass / Conditional Pass / Fail]
- Notes for next test cycle: [PLACEHOLDER]

> This document is a draft template. Actual measured values, logs, and pass/fail evidence must be filled in after formal test execution.
