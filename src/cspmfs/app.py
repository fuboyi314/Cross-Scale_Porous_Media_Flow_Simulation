from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from cspmfs.core.log_manager import LogManager
from cspmfs.core.project_manager import ProjectManager
from cspmfs.ui.main_window import MainWindow


def run() -> int:
    """Run Phase 1 desktop app."""

    qt_app = QApplication(sys.argv)

    log_manager = LogManager(log_dir=Path.cwd() / "logs")
    project_manager = ProjectManager()

    window = MainWindow(project_manager=project_manager, logger=log_manager.logger)
    log_manager.attach_gui_sink(window.append_gui_log)

    window.show()
    log_manager.logger.info("Application started")
    return qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
