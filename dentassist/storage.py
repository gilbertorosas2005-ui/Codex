"""Storage helpers for DentAssist data."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

DEFAULT_STORAGE_PATH = Path.home() / ".dentassist.json"


def ensure_storage_path(path: Path | None = None) -> Path:
    """Return a writable storage path, creating parent directories if needed."""
    storage_path = path or DEFAULT_STORAGE_PATH
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    return storage_path


def load_state(path: Path | None = None) -> Dict[str, Any]:
    """Load the stored state or return an empty structure when missing."""
    storage_path = ensure_storage_path(path)
    if not storage_path.exists():
        return {"appointments": [], "inventory": [], "tasks": []}

    with storage_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_state(state: Dict[str, Any], path: Path | None = None) -> None:
    """Persist the provided state as JSON."""
    storage_path = ensure_storage_path(path)
    with storage_path.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)
