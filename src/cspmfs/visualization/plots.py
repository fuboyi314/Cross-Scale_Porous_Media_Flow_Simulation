from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from cspmfs.upscaling.rev_analysis import REVResult


def _save_figure(fig: plt.Figure, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path


def plot_original_geometry(rgb: np.ndarray) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.imshow(rgb)
    ax.set_title("Original Geometry")
    ax.set_axis_off()
    return fig


def plot_binary_geometry(binary: np.ndarray) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.imshow(binary, cmap="gray")
    ax.set_title("Binary Geometry (1=pore)")
    ax.set_axis_off()
    return fig


def plot_velocity_magnitude(vel_mag: np.ndarray) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(vel_mag, cmap="viridis")
    ax.set_title("Velocity Magnitude")
    fig.colorbar(im, ax=ax)
    return fig


def plot_velocity_components(ux: np.ndarray, uy: np.ndarray) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    im0 = axes[0].imshow(ux, cmap="coolwarm")
    axes[0].set_title("ux")
    fig.colorbar(im0, ax=axes[0])

    im1 = axes[1].imshow(uy, cmap="coolwarm")
    axes[1].set_title("uy")
    fig.colorbar(im1, ax=axes[1])
    return fig


def plot_streamlines(ux: np.ndarray, uy: np.ndarray, step: int = 3) -> plt.Figure:
    h, w = ux.shape
    y, x = np.mgrid[0:h, 0:w]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.streamplot(x[::step, ::step], y[::step, ::step], ux[::step, ::step], uy[::step, ::step], density=1.0)
    ax.set_title("Streamlines")
    ax.invert_yaxis()
    return fig


def plot_rev_curves(rev: REVResult) -> plt.Figure:
    sizes = [s.window_size for s in rev.stats_by_size]
    means = [s.mean_permeability for s in rev.stats_by_size]
    rel = [s.relative_fluctuation for s in rev.stats_by_size]

    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].plot(sizes, means, marker="o")
    ax[0].set_title("Mean permeability vs window size")
    ax[0].set_xlabel("Window size")
    ax[0].set_ylabel("Mean permeability (lattice)")

    ax[1].plot(sizes, rel, marker="o", color="orange")
    ax[1].set_title("Relative fluctuation vs window size")
    ax[1].set_xlabel("Window size")
    ax[1].set_ylabel("std/mean")
    return fig


def save_all_figures(
    out_dir: Path,
    original_rgb: np.ndarray | None,
    binary: np.ndarray | None,
    ux: np.ndarray | None,
    uy: np.ndarray | None,
    vel_mag: np.ndarray | None,
    rev_result: REVResult | None,
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    if original_rgb is not None:
        paths.append(_save_figure(plot_original_geometry(original_rgb), out_dir / "geometry_original.png"))
    if binary is not None:
        paths.append(_save_figure(plot_binary_geometry(binary), out_dir / "geometry_binary.png"))
    if vel_mag is not None:
        paths.append(_save_figure(plot_velocity_magnitude(vel_mag), out_dir / "velocity_magnitude.png"))
    if ux is not None and uy is not None:
        paths.append(_save_figure(plot_velocity_components(ux, uy), out_dir / "velocity_components.png"))
        paths.append(_save_figure(plot_streamlines(ux, uy), out_dir / "streamlines.png"))
    if rev_result is not None and rev_result.stats_by_size:
        paths.append(_save_figure(plot_rev_curves(rev_result), out_dir / "rev_curves.png"))
    return paths
