"""Notebook persistence: save, load, list, and track the active notebook."""

import logging
from datetime import datetime
from pathlib import Path

from deepnotevault.models.schemas import Notebook

logger = logging.getLogger(__name__)

_ACTIVE_FILE = "active.txt"


class NotebookManager:
    """Persist notebooks as JSON files under a given directory."""

    def __init__(self, notebooks_dir: Path) -> None:
        self._dir = notebooks_dir
        self._dir.mkdir(parents=True, exist_ok=True, mode=0o700)

    def load_or_create_active(self) -> Notebook:
        """Return the last active notebook, creating a default one if none exists."""
        active_id = self._read_active_id()
        if active_id:
            nb = self.load(active_id)
            if nb is not None:
                return nb
        nb = Notebook(name="Default Notebook")
        self.save(nb)
        self.set_active(nb.id)
        return nb

    def save(self, notebook: Notebook) -> None:
        """Persist a notebook to disk, updating its timestamp."""
        notebook.updated_at = datetime.now()
        path = self._dir / f"{notebook.id}.json"
        path.write_text(notebook.model_dump_json(indent=2), encoding="utf-8")
        logger.debug("Saved notebook '%s' (%s)", notebook.name, notebook.id)

    def load(self, notebook_id: str) -> Notebook | None:
        """Load a notebook by ID. Returns None if not found or corrupt."""
        path = self._dir / f"{notebook_id}.json"
        if not path.exists():
            return None
        try:
            return Notebook.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:
            logger.warning("Failed to load notebook %s; file may be corrupt", notebook_id)
            return None

    def list_notebooks(self) -> list[Notebook]:
        """Return all saved notebooks sorted by most recently updated."""
        notebooks: list[Notebook] = []
        for p in self._dir.glob("*.json"):
            try:
                notebooks.append(
                    Notebook.model_validate_json(p.read_text(encoding="utf-8"))
                )
            except Exception:
                logger.warning("Skipping corrupt notebook file: %s", p.name)
        return sorted(notebooks, key=lambda n: n.updated_at, reverse=True)

    def delete(self, notebook_id: str) -> None:
        """Delete a notebook's JSON file."""
        (self._dir / f"{notebook_id}.json").unlink(missing_ok=True)
        logger.debug("Deleted notebook %s", notebook_id)

    def set_active(self, notebook_id: str) -> None:
        """Remember which notebook was last active."""
        (self._dir / _ACTIVE_FILE).write_text(notebook_id, encoding="utf-8")

    def _read_active_id(self) -> str | None:
        p = self._dir / _ACTIVE_FILE
        return p.read_text(encoding="utf-8").strip() if p.exists() else None
