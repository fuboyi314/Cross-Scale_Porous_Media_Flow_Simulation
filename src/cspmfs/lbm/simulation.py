from __future__ import annotations

import numpy as np

from cspmfs.lbm.d2q9_solver import D2Q9LBMSolver, SimulationConfig, SimulationResult


def run_simulation(binary_geometry: np.ndarray, config: SimulationConfig, progress_callback: callable | None = None) -> SimulationResult:
    """Run 2D D2Q9 BGK/SRT simulation using configured parameters."""

    solver = D2Q9LBMSolver(config=config)
    return solver.solve(binary_geometry, progress_callback=progress_callback)
