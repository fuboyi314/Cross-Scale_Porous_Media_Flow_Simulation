from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QWidget


def _to_qpixmap(image: np.ndarray) -> QPixmap:
    if image.ndim == 2:
        h, w = image.shape
        data = np.ascontiguousarray(image)
        qimg = QImage(data.data, w, h, w, QImage.Format.Format_Grayscale8)
        return QPixmap.fromImage(qimg.copy())

    if image.ndim == 3 and image.shape[2] == 3:
        h, w, _ = image.shape
        data = np.ascontiguousarray(image)
        qimg = QImage(data.data, w, h, 3 * w, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qimg.copy())

    raise ValueError("Unsupported image shape for preview.")


class VisualizationArea(QWidget):
    """Central visualization container with original/binary previews."""

    def __init__(self) -> None:
        super().__init__()
        root = QHBoxLayout(self)

        self.original_label = QLabel("Original Image")
        self.original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_label.setStyleSheet("border: 1px solid #888; padding: 8px;")

        self.binary_label = QLabel("Processed Binary")
        self.binary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.binary_label.setStyleSheet("border: 1px solid #888; padding: 8px;")

        left = QVBoxLayout()
        left.addWidget(QLabel("Original"))
        left.addWidget(self.original_label)

        right = QVBoxLayout()
        right.addWidget(QLabel("Binary (1=pore, 0=solid)"))
        right.addWidget(self.binary_label)

        left_widget = QWidget()
        left_widget.setLayout(left)
        right_widget = QWidget()
        right_widget.setLayout(right)

        root.addWidget(left_widget)
        root.addWidget(right_widget)

    def set_original_image(self, rgb: np.ndarray) -> None:
        pix = _to_qpixmap(rgb).scaled(480, 480, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.original_label.setPixmap(pix)

    def set_binary_image(self, binary: np.ndarray) -> None:
        vis = (binary * 255).astype(np.uint8)
        pix = _to_qpixmap(vis).scaled(480, 480, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.binary_label.setPixmap(pix)
