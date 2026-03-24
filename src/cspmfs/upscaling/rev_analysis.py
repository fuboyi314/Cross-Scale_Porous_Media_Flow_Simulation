from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


@dataclass(slots=True)
class REVConfig:
    """Configuration for 2D REV sampling."""

    window_sizes: list[int]
    stride_factor: float = 0.5
    min_porosity: float = 0.01
    max_samples_per_size: int | None = None
    mean_change_tol: float = 0.05
    rel_fluct_tol: float = 0.10


@dataclass(slots=True)
class REVWindowSample:
    """One sampled window and computed properties."""

    window_size: int
    x0: int
    y0: int
    porosity: float
    permeability: float


@dataclass(slots=True)
class REVSizeStats:
    """Aggregated statistics for a window size."""

    window_size: int
    mean_permeability: float
    std_permeability: float
    relative_fluctuation: float
    valid_samples: int


@dataclass(slots=True)
class REVResult:
    """REV analysis outputs."""

    samples: list[REVWindowSample]
    stats_by_size: list[REVSizeStats]
    suggested_rev_size: int | None
    criterion_note: str


def _porosity(binary: np.ndarray) -> float:
    return float(np.mean(binary.astype(np.float64)))


class REVAnalyzer:
    """REV analyzer decoupled from any specific solver implementation.

    Parameters
    ----------
    permeability_callback:
        Callable that receives a binary window array (1=pore, 0=solid)
        and returns permeability in lattice units. If it returns `None`
        or raises, the sample is treated as invalid.
    """

    def __init__(self, permeability_callback: Callable[[np.ndarray], float | None]) -> None:
        self.permeability_callback = permeability_callback

    def run(
        self,
        binary_geometry: np.ndarray,
        config: REVConfig,
        progress_callback: Callable[[str], None] | None = None,
    ) -> REVResult:
        if binary_geometry.ndim != 2:
            raise ValueError("binary_geometry must be 2D")

        h, w = binary_geometry.shape
        stats: list[REVSizeStats] = []
        samples: list[REVWindowSample] = []

        for size in sorted(config.window_sizes):
            if size < 2 or size > h or size > w:
                continue
            stride = max(1, int(size * config.stride_factor))
            if progress_callback:
                progress_callback(f"REV size={size}, stride={stride}")

            size_k: list[float] = []
            sample_count = 0
            for y0 in range(0, h - size + 1, stride):
                for x0 in range(0, w - size + 1, stride):
                    win = binary_geometry[y0 : y0 + size, x0 : x0 + size]
                    por = _porosity(win)
                    if por < config.min_porosity:
                        continue
                    try:
                        k = self.permeability_callback(win)
                    except Exception:
                        k = None
                    if k is None:
                        continue
                    sample = REVWindowSample(window_size=size, x0=x0, y0=y0, porosity=por, permeability=float(k))
                    samples.append(sample)
                    size_k.append(float(k))
                    sample_count += 1

                    if config.max_samples_per_size is not None and sample_count >= config.max_samples_per_size:
                        break
                if config.max_samples_per_size is not None and sample_count >= config.max_samples_per_size:
                    break

            if len(size_k) == 0:
                continue

            mean_k = float(np.mean(size_k))
            std_k = float(np.std(size_k))
            rel_fluct = float(std_k / (abs(mean_k) + 1e-14))
            stats.append(
                REVSizeStats(
                    window_size=size,
                    mean_permeability=mean_k,
                    std_permeability=std_k,
                    relative_fluctuation=rel_fluct,
                    valid_samples=len(size_k),
                )
            )

        suggestion, note = _suggest_rev(stats, config)
        return REVResult(samples=samples, stats_by_size=stats, suggested_rev_size=suggestion, criterion_note=note)


def _suggest_rev(stats: list[REVSizeStats], config: REVConfig) -> tuple[int | None, str]:
    if len(stats) < 2:
        return None, "Not enough window sizes for REV criterion."

    for i in range(1, len(stats)):
        prev = stats[i - 1]
        cur = stats[i]
        mean_change = abs(cur.mean_permeability - prev.mean_permeability) / (abs(prev.mean_permeability) + 1e-14)
        if mean_change <= config.mean_change_tol and cur.relative_fluctuation <= config.rel_fluct_tol:
            return cur.window_size, (
                f"REV suggested at size={cur.window_size}: mean change={mean_change:.3f}, "
                f"relative fluctuation={cur.relative_fluctuation:.3f}"
            )
    return None, "No REV size met stabilization thresholds."
