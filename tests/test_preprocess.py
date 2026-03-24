from __future__ import annotations

from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
Image = pytest.importorskip("PIL.Image").Image

from cspmfs.geometry.preprocess import (
    PreprocessConfig,
    compute_porosity,
    preprocess_image,
    threshold_segmentation,
)


def test_threshold_segmentation() -> None:
    gray = np.array([[50, 120, 200]], dtype=np.uint8)
    binary = threshold_segmentation(gray, threshold=120, invert=False)
    assert binary.tolist() == [[0, 1, 1]]


def test_porosity_calculation() -> None:
    binary = np.array([[1, 0], [1, 1]], dtype=np.uint8)
    assert compute_porosity(binary) == 0.75


def test_binary_output_validity(tmp_path: Path) -> None:
    rgb = np.array(
        [
            [[0, 0, 0], [255, 255, 255]],
            [[200, 200, 200], [10, 10, 10]],
        ],
        dtype=np.uint8,
    )
    path = tmp_path / "sample.png"
    from PIL import Image as PILImage

    PILImage.fromarray(rgb).save(path)

    result = preprocess_image(path, PreprocessConfig(threshold=128))
    assert result.binary.shape == (2, 2)
    unique = set(np.unique(result.binary).tolist())
    assert unique.issubset({0, 1})
    assert result.pore_pixel_count + result.solid_pixel_count == 4
