from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class SimulationConfig:
    """Configuration for 2D D2Q9 BGK/SRT LBM simulation."""

    tau: float = 0.8
    rho_in: float = 1.01
    rho_out: float = 1.0
    max_iterations: int = 5000
    convergence_tol: float = 1e-6
    report_interval: int = 100


@dataclass(slots=True)
class SimulationResult:
    """Simulation outputs for porous-media flow."""

    density: np.ndarray
    ux: np.ndarray
    uy: np.ndarray
    velocity_magnitude: np.ndarray
    average_velocity: float
    residual_history: list[float]
    iterations: int
    converged: bool


class D2Q9LBMSolver:
    """D2Q9 BGK/SRT solver for 2D single-phase steady flow in porous media."""

    c = np.array(
        [[0, 0], [1, 0], [0, 1], [-1, 0], [0, -1], [1, 1], [-1, 1], [-1, -1], [1, -1]],
        dtype=np.int32,
    )
    w = np.array([4 / 9, 1 / 9, 1 / 9, 1 / 9, 1 / 9, 1 / 36, 1 / 36, 1 / 36, 1 / 36], dtype=np.float64)
    opp = np.array([0, 3, 4, 1, 2, 7, 8, 5, 6], dtype=np.int32)

    def __init__(self, config: SimulationConfig) -> None:
        if config.tau <= 0.5:
            raise ValueError("tau must be > 0.5 for stable positive viscosity")
        if config.rho_in <= config.rho_out:
            raise ValueError("rho_in must be greater than rho_out for left-to-right density-driven flow")
        self.config = config

    def _equilibrium(self, rho: np.ndarray, ux: np.ndarray, uy: np.ndarray) -> np.ndarray:
        uu = ux**2 + uy**2
        feq = np.zeros((9, *rho.shape), dtype=np.float64)
        for i, (cx, cy) in enumerate(self.c):
            cu = 3.0 * (cx * ux + cy * uy)
            feq[i] = self.w[i] * rho * (1 + cu + 0.5 * cu**2 - 1.5 * uu)
        return feq

    def _compute_macroscopic(self, f: np.ndarray, solid_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        rho = np.sum(f, axis=0)
        rho[rho <= 1e-14] = 1e-14
        ux = np.sum(f * self.c[:, 0][:, None, None], axis=0) / rho
        uy = np.sum(f * self.c[:, 1][:, None, None], axis=0) / rho
        ux[solid_mask] = 0.0
        uy[solid_mask] = 0.0
        return rho, ux, uy

    def _apply_density_boundary(self, f: np.ndarray, solid_mask: np.ndarray) -> None:
        """Apply Zou/He density boundaries at left and right open boundaries."""

        rho_in = self.config.rho_in
        rho_out = self.config.rho_out

        # Left boundary (x=0): unknowns f1, f5, f8
        x0 = 0
        fluid_left = ~solid_mask[:, x0]
        if np.any(fluid_left):
            row_idx = np.where(fluid_left)[0]
            f0 = f[0, row_idx, x0]
            f2 = f[2, row_idx, x0]
            f4 = f[4, row_idx, x0]
            f3 = f[3, row_idx, x0]
            f6 = f[6, row_idx, x0]
            f7 = f[7, row_idx, x0]

            ux = 1.0 - (f0 + f2 + f4 + 2.0 * (f3 + f6 + f7)) / rho_in
            f[1, row_idx, x0] = f3 + (2.0 / 3.0) * rho_in * ux
            f[5, row_idx, x0] = f7 + 0.5 * (f4 - f2) + (1.0 / 6.0) * rho_in * ux
            f[8, row_idx, x0] = f6 + 0.5 * (f2 - f4) + (1.0 / 6.0) * rho_in * ux

        # Right boundary (x=nx-1): unknowns f3, f6, f7
        x1 = f.shape[2] - 1
        fluid_right = ~solid_mask[:, x1]
        if np.any(fluid_right):
            row_idx = np.where(fluid_right)[0]
            f0 = f[0, row_idx, x1]
            f1 = f[1, row_idx, x1]
            f2 = f[2, row_idx, x1]
            f4 = f[4, row_idx, x1]
            f5 = f[5, row_idx, x1]
            f8 = f[8, row_idx, x1]

            ux = -1.0 + (f0 + f2 + f4 + 2.0 * (f1 + f5 + f8)) / rho_out
            f[3, row_idx, x1] = f1 - (2.0 / 3.0) * rho_out * ux
            f[6, row_idx, x1] = f8 + 0.5 * (f4 - f2) - (1.0 / 6.0) * rho_out * ux
            f[7, row_idx, x1] = f5 + 0.5 * (f2 - f4) - (1.0 / 6.0) * rho_out * ux

    def solve(self, geometry_binary: np.ndarray, progress_callback: callable | None = None) -> SimulationResult:
        """Run LBM simulation on binary geometry where 1=pore and 0=solid."""

        if geometry_binary.ndim != 2:
            raise ValueError("geometry_binary must be 2D")

        pore_mask = geometry_binary.astype(bool)
        solid_mask = ~pore_mask
        ny, nx = geometry_binary.shape

        rho = np.ones((ny, nx), dtype=np.float64)
        ux = np.zeros((ny, nx), dtype=np.float64)
        uy = np.zeros((ny, nx), dtype=np.float64)

        f = self._equilibrium(rho, ux, uy)
        omega = 1.0 / self.config.tau

        residual_history: list[float] = []
        converged = False

        for it in range(1, self.config.max_iterations + 1):
            feq = self._equilibrium(rho, ux, uy)
            f = f - omega * (f - feq)

            for i, (cx, cy) in enumerate(self.c):
                f[i] = np.roll(f[i], shift=(cy, cx), axis=(0, 1))

            # Bounce-back on solids.
            for i in range(9):
                f[i, solid_mask] = f[self.opp[i], solid_mask]

            self._apply_density_boundary(f, solid_mask)

            rho_new, ux_new, uy_new = self._compute_macroscopic(f, solid_mask)
            residual = float(np.linalg.norm(ux_new - ux) / (np.linalg.norm(ux_new) + 1e-14))
            residual_history.append(residual)

            rho, ux, uy = rho_new, ux_new, uy_new

            if progress_callback and (it % self.config.report_interval == 0):
                progress_callback(it, residual)

            if residual < self.config.convergence_tol:
                converged = True
                break

        vel_mag = np.sqrt(ux**2 + uy**2)
        avg_u = float(np.mean(vel_mag[pore_mask])) if np.any(pore_mask) else 0.0

        return SimulationResult(
            density=rho,
            ux=ux,
            uy=uy,
            velocity_magnitude=vel_mag,
            average_velocity=avg_u,
            residual_history=residual_history,
            iterations=it,
            converged=converged,
        )
