from __future__ import annotations

import csv
import json
import shutil
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from cspmfs.upscaling.rev_analysis import REVResult, REVSizeStats


def _normalize(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Path):
        return str(value)
    return value


def make_export_root(project_root: Path, project_name: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = project_root / "exports" / f"{project_name}_{ts}"
    root.mkdir(parents=True, exist_ok=True)
    (root / "figures").mkdir(exist_ok=True)
    (root / "tables").mkdir(exist_ok=True)
    (root / "reports").mkdir(exist_ok=True)
    (root / "logs").mkdir(exist_ok=True)
    return root


def export_json(path: Path, payload: dict[str, Any]) -> Path:
    serializable = {k: _normalize(v) for k, v in payload.items()}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
    return path


def export_array_csv(path: Path, array: np.ndarray) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(path, array, delimiter=",")
    return path


def export_rev_stats_csv(path: Path, stats: list[REVSizeStats]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["window_size", "mean_permeability", "std_permeability", "relative_fluctuation", "valid_samples"])
        for s in stats:
            writer.writerow([s.window_size, s.mean_permeability, s.std_permeability, s.relative_fluctuation, s.valid_samples])
    return path


def copy_runtime_log(source_log: Path, target_path: Path) -> Path | None:
    if not source_log.exists():
        return None
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_log, target_path)
    return target_path


def write_summary_report(path: Path, lines: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_summary_lines(
    project_name: str,
    input_file: str | None,
    preprocess_params: dict[str, Any],
    porosity: float | None,
    simulation_params: dict[str, Any],
    average_velocity: float | None,
    permeability_lu: float | None,
    permeability_m2: float | None,
    rev_result: REVResult | None,
    output_paths: list[Path],
) -> list[str]:
    lines = [
        f"# Simulation Summary Report",
        f"Project name: {project_name}",
        f"Input file: {input_file or 'N/A'}",
        "",
        "## Preprocessing Parameters",
        json.dumps(preprocess_params, indent=2),
        f"Porosity: {porosity if porosity is not None else 'N/A'}",
        "",
        "## Simulation Parameters",
        json.dumps(simulation_params, indent=2),
        f"Average velocity: {average_velocity if average_velocity is not None else 'N/A'}",
        "",
        "## Permeability",
        f"Permeability (lattice): {permeability_lu if permeability_lu is not None else 'N/A'}",
        f"Permeability (m^2): {permeability_m2 if permeability_m2 is not None else 'N/A'}",
        "",
        "## REV Summary",
    ]

    if rev_result is None:
        lines.append("No REV results available.")
    else:
        lines.extend([
            f"Suggested REV size: {rev_result.suggested_rev_size}",
            f"Criterion note: {rev_result.criterion_note}",
            f"Window sizes analyzed: {[s.window_size for s in rev_result.stats_by_size]}",
        ])

    lines.extend(["", "## Output Files"]) 
    for p in output_paths:
        lines.append(f"- {p}")
    return lines
