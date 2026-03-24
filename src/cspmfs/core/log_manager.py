from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable


class GuiLogHandler(logging.Handler):
    """Forward logs to a GUI callback."""

    def __init__(self, callback: Callable[[str], None]) -> None:
        super().__init__()
        self.callback = callback

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        self.callback(msg)


class LogManager:
    """Owns app logger configuration for file + GUI output."""

    def __init__(self, log_dir: Path) -> None:
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("cspmfs")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()
        self.logger.propagate = False

        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

        file_handler = RotatingFileHandler(
            filename=self.log_dir / "application.log",
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(stream_handler)

    def attach_gui_sink(self, callback: Callable[[str], None]) -> None:
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        gui_handler = GuiLogHandler(callback)
        gui_handler.setFormatter(formatter)
        self.logger.addHandler(gui_handler)
