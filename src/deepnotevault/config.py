"""Application configuration with JSON persistence."""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

from deepnotevault.constants import (
    CONFIG_FILE,
    DATA_DIR,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_EMBED_MODEL,
    DEFAULT_LLM_MODEL,
    DEFAULT_OLLAMA_URL,
    DEFAULT_SIMILARITY_TOP_K,
)


@dataclass(frozen=True)
class AppConfig:
    """Immutable application configuration."""

    ollama_url: str = DEFAULT_OLLAMA_URL
    llm_model: str = DEFAULT_LLM_MODEL
    embed_model: str = DEFAULT_EMBED_MODEL
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    similarity_top_k: int = DEFAULT_SIMILARITY_TOP_K


def load_config(path: Path = CONFIG_FILE) -> AppConfig:
    """Load config from JSON file. Returns defaults if file doesn't exist."""
    if not path.exists():
        return AppConfig()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        known_fields = {f.name for f in AppConfig.__dataclass_fields__.values()}
        filtered = {k: v for k, v in raw.items() if k in known_fields}
        return AppConfig(**filtered)
    except (json.JSONDecodeError, TypeError):
        return AppConfig()


def save_config(config: AppConfig, path: Path = CONFIG_FILE) -> None:
    """Persist config to JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(config), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def update_config(config: AppConfig, **changes: object) -> AppConfig:
    """Return a new AppConfig with the specified fields changed (immutable update)."""
    current = asdict(config)
    current.update(changes)
    return AppConfig(**current)
