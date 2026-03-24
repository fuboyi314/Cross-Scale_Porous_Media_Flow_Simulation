from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


@dataclass(slots=True)
class CropRange:
    """ROI crop settings in pixel coordinates."""

    x_min: int
    y_min: int
    x_max: int
    y_max: int


@dataclass(slots=True)
class PreprocessConfig:
    """Preprocessing configuration for 2D porous media images."""

    threshold: int = 128
    invert_binary: bool = False
    min_component_size: int = 0
    fill_holes: bool = False
    max_hole_size: int = 0
    crop: CropRange | None = None


@dataclass(slots=True)
class PreprocessResult:
    """Preprocessing outputs for downstream LBM solver input."""

    original_rgb: np.ndarray
    grayscale: np.ndarray
    binary: np.ndarray  # 1=pore, 0=solid
    porosity: float
    width: int
    height: int
    pore_pixel_count: int
    solid_pixel_count: int


def _validate_extension(path: Path) -> None:
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported image format: {path.suffix}. Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )


def load_image(path: Path) -> np.ndarray:
    """Load image to RGB array for supported 2D image formats."""

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    _validate_extension(path)
    img = Image.open(path).convert("RGB")
    return np.asarray(img, dtype=np.uint8)


def rgb_to_grayscale(rgb: np.ndarray) -> np.ndarray:
    """Convert RGB image to grayscale uint8 image."""

    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("Expected RGB image with shape (H, W, 3).")
    gray = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]).round()
    return gray.astype(np.uint8)


def threshold_segmentation(grayscale: np.ndarray, threshold: int, invert: bool) -> np.ndarray:
    """Segment grayscale to binary image (1=pore, 0=solid)."""

    if grayscale.ndim != 2:
        raise ValueError("grayscale must be 2D")
    if not (0 <= threshold <= 255):
        raise ValueError("threshold must be in [0, 255]")

    binary = (grayscale >= threshold).astype(np.uint8)
    if invert:
        binary = 1 - binary
    return binary


def _neighbors(y: int, x: int, h: int, w: int) -> Iterable[tuple[int, int]]:
    if y > 0:
        yield y - 1, x
    if y + 1 < h:
        yield y + 1, x
    if x > 0:
        yield y, x - 1
    if x + 1 < w:
        yield y, x + 1


def _connected_components(mask: np.ndarray, target_value: int) -> list[list[tuple[int, int]]]:
    h, w = mask.shape
    visited = np.zeros((h, w), dtype=bool)
    components: list[list[tuple[int, int]]] = []

    for y0 in range(h):
        for x0 in range(w):
            if visited[y0, x0] or mask[y0, x0] != target_value:
                continue

            stack = [(y0, x0)]
            visited[y0, x0] = True
            comp: list[tuple[int, int]] = []

            while stack:
                y, x = stack.pop()
                comp.append((y, x))
                for ny, nx in _neighbors(y, x, h, w):
                    if not visited[ny, nx] and mask[ny, nx] == target_value:
                        visited[ny, nx] = True
                        stack.append((ny, nx))
            components.append(comp)
    return components


def remove_small_isolated_regions(binary: np.ndarray, min_component_size: int) -> np.ndarray:
    """Remove small pore components by converting them to solid."""

    if min_component_size <= 0:
        return binary
    out = binary.copy()
    for comp in _connected_components(out, target_value=1):
        if len(comp) < min_component_size:
            for y, x in comp:
                out[y, x] = 0
    return out


def fill_small_holes(binary: np.ndarray, max_hole_size: int) -> np.ndarray:
    """Fill small solid holes surrounded by pores."""

    if max_hole_size <= 0:
        return binary

    out = binary.copy()
    h, w = out.shape
    for comp in _connected_components(out, target_value=0):
        touches_border = any(y == 0 or y == h - 1 or x == 0 or x == w - 1 for y, x in comp)
        if (not touches_border) and len(comp) <= max_hole_size:
            for y, x in comp:
                out[y, x] = 1
    return out


def crop_roi(image: np.ndarray, crop: CropRange | None) -> np.ndarray:
    """Crop image array with ROI settings."""

    if crop is None:
        return image
    h, w = image.shape[:2]
    x_min = max(0, min(crop.x_min, w - 1))
    x_max = max(1, min(crop.x_max, w))
    y_min = max(0, min(crop.y_min, h - 1))
    y_max = max(1, min(crop.y_max, h))
    if x_max <= x_min or y_max <= y_min:
        raise ValueError("Invalid crop ROI range.")
    return image[y_min:y_max, x_min:x_max]


def compute_porosity(binary: np.ndarray) -> float:
    """Compute porosity from binary matrix where pore=1."""

    return float(np.mean(binary.astype(np.float64)))


def preprocess_image(path: Path, config: PreprocessConfig) -> PreprocessResult:
    """Full preprocessing pipeline for 2D porous media images."""

    rgb = load_image(path)
    rgb = crop_roi(rgb, config.crop)
    gray = rgb_to_grayscale(rgb)
    binary = threshold_segmentation(gray, config.threshold, config.invert_binary)
    binary = remove_small_isolated_regions(binary, config.min_component_size)
    if config.fill_holes:
        binary = fill_small_holes(binary, config.max_hole_size)

    height, width = binary.shape
    pore_count = int(np.sum(binary == 1))
    solid_count = int(np.sum(binary == 0))

    return PreprocessResult(
        original_rgb=rgb,
        grayscale=gray,
        binary=binary,
        porosity=compute_porosity(binary),
        width=width,
        height=height,
        pore_pixel_count=pore_count,
        solid_pixel_count=solid_count,
    )
