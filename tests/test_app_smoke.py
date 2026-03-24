from __future__ import annotations

import os

import pytest


def test_main_window_constructs() -> None:
    pyside6 = pytest.importorskip("PySide6")
    assert pyside6 is not None

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from cspmfs.core.log_manager import LogManager
    from cspmfs.core.project_manager import ProjectManager
    from cspmfs.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    log_manager = LogManager(log_dir=os.getcwd())
    window = MainWindow(ProjectManager(), log_manager.logger)
    assert window.windowTitle() != ""
    window.close()
    app.quit()
