from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ProjectModel:
    """Serializable project model for Phase 1."""

    name: str = "Untitled"
    image_path: str | None = None
    geometry_preprocessed: bool = False
    simulation_ran: bool = False
    rev_ran: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProjectSession:
    """Runtime project state."""

    root: Path
    model: ProjectModel


class ProjectManager:
    """Create/open/save project sessions."""

    PROJECT_FILE = "project.json"

    def __init__(self) -> None:
        self.current: ProjectSession | None = None

    def new_project(self, directory: Path, name: str) -> ProjectSession:
        directory.mkdir(parents=True, exist_ok=True)
        if any(directory.iterdir()):
            raise FileExistsError(f"Project directory is not empty: {directory}")
        session = ProjectSession(root=directory, model=ProjectModel(name=name.strip() or "Untitled"))
        self.current = session
        self.save_project(session)
        return session

    def open_project(self, directory: Path) -> ProjectSession:
        project_file = directory / self.PROJECT_FILE
        if not project_file.exists():
            raise FileNotFoundError(f"Project file does not exist: {project_file}")
        payload = json.loads(project_file.read_text(encoding="utf-8"))
        model = ProjectModel(**payload)
        session = ProjectSession(root=directory, model=model)
        self.current = session
        return session

    def save_project(self, session: ProjectSession | None = None) -> Path:
        active = session or self.current
        if active is None:
            raise RuntimeError("No active project session to save.")
        active.root.mkdir(parents=True, exist_ok=True)
        path = active.root / self.PROJECT_FILE
        path.write_text(json.dumps(active.model.__dict__, indent=2), encoding="utf-8")
        return path
