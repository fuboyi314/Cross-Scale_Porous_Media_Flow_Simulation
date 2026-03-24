from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")

from cspmfs.upscaling.rev_analysis import REVAnalyzer, REVConfig


def test_rev_stats_and_suggestion() -> None:
    geom = np.ones((32, 32), dtype=np.uint8)

    def permeability_cb(win: np.ndarray) -> float:
        # deterministic mock permeability linked to porosity and size
        return float(np.mean(win)) * float(win.shape[0])

    analyzer = REVAnalyzer(permeability_cb)
    result = analyzer.run(
        geom,
        REVConfig(
            window_sizes=[8, 12, 16],
            stride_factor=0.5,
            max_samples_per_size=20,
            mean_change_tol=0.6,
            rel_fluct_tol=0.2,
        ),
    )

    assert len(result.stats_by_size) >= 2
    assert all(s.valid_samples > 0 for s in result.stats_by_size)
    assert result.stats_by_size[0].mean_permeability > 0
