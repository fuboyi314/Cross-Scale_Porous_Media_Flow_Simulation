"""Upscaling and post-processing package."""

from cspmfs.upscaling.permeability import (
    PermeabilityInput,
    PermeabilityResult,
    compute_effective_permeability,
)

__all__ = [
    "PermeabilityInput",
    "PermeabilityResult",
    "compute_effective_permeability",
]
