from __future__ import annotations

from pathlib import Path

import pytest

np = pytest.importorskip("numpy")

from cspmfs.io.exporter import export_array_csv, export_json, export_rev_stats_csv, make_export_root
from cspmfs.upscaling.rev_analysis import REVSizeStats


def test_make_export_root_and_write_files(tmp_path: Path) -> None:
    root = make_export_root(tmp_path, "proj")
    assert root.exists()
    assert (root / "figures").exists()
    assert (root / "tables").exists()
    assert (root / "reports").exists()
    assert (root / "logs").exists()

    csv_path = export_array_csv(root / "tables" / "a.csv", np.array([[1, 2], [3, 4]], dtype=float))
    assert csv_path.exists()

    json_path = export_json(root / "reports" / "a.json", {"x": 1})
    assert json_path.exists()

    rev_csv = export_rev_stats_csv(
        root / "tables" / "rev.csv",
        [REVSizeStats(window_size=10, mean_permeability=1.0, std_permeability=0.1, relative_fluctuation=0.1, valid_samples=5)],
    )
    assert rev_csv.exists()
