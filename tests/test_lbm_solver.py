from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")

from cspmfs.lbm.d2q9_solver import D2Q9LBMSolver, SimulationConfig


def test_channel_flow_runs_and_moves_right() -> None:
    ny, nx = 24, 60
    geom = np.ones((ny, nx), dtype=np.uint8)
    geom[0, :] = 0
    geom[-1, :] = 0

    cfg = SimulationConfig(
        tau=0.8,
        rho_in=1.01,
        rho_out=1.0,
        max_iterations=1200,
        convergence_tol=1e-5,
        report_interval=200,
    )
    solver = D2Q9LBMSolver(cfg)
    result = solver.solve(geom)

    assert result.ux.shape == geom.shape
    assert result.uy.shape == geom.shape
    assert result.density.shape == geom.shape
    assert result.velocity_magnitude.shape == geom.shape
    assert len(result.residual_history) >= 1
    assert result.average_velocity > 0.0
    assert float(np.mean(result.ux[1:-1, 1:-1])) > 0.0
