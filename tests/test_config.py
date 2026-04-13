"""Tests for config module."""

import json
from pathlib import Path

from deepnotevault.config import AppConfig, load_config, save_config, update_config
from deepnotevault.constants import DEFAULT_LLM_MODEL, DEFAULT_OLLAMA_URL


class TestAppConfig:
    def test_defaults(self):
        config = AppConfig()
        assert config.ollama_url == DEFAULT_OLLAMA_URL
        assert config.llm_model == DEFAULT_LLM_MODEL
        assert config.chunk_size == 512
        assert config.chunk_overlap == 64
        assert config.similarity_top_k == 4

    def test_immutability(self):
        config = AppConfig()
        try:
            config.llm_model = "other"  # type: ignore[misc]
            assert False, "Should raise FrozenInstanceError"
        except AttributeError:
            pass


class TestLoadSaveConfig:
    def test_load_missing_file(self, tmp_path: Path):
        config = load_config(tmp_path / "nonexistent.json")
        assert config == AppConfig()

    def test_roundtrip(self, tmp_path: Path):
        path = tmp_path / "config.json"
        original = AppConfig(llm_model="mistral", chunk_size=1024)
        save_config(original, path)

        loaded = load_config(path)
        assert loaded.llm_model == "mistral"
        assert loaded.chunk_size == 1024
        assert loaded.ollama_url == DEFAULT_OLLAMA_URL

    def test_load_corrupt_json(self, tmp_path: Path):
        path = tmp_path / "config.json"
        path.write_text("not json at all", encoding="utf-8")
        config = load_config(path)
        assert config == AppConfig()

    def test_load_ignores_unknown_fields(self, tmp_path: Path):
        path = tmp_path / "config.json"
        data = {"llm_model": "phi3", "unknown_field": 42}
        path.write_text(json.dumps(data), encoding="utf-8")
        config = load_config(path)
        assert config.llm_model == "phi3"


class TestUpdateConfig:
    def test_update_single_field(self):
        config = AppConfig()
        updated = update_config(config, llm_model="mistral")
        assert updated.llm_model == "mistral"
        assert config.llm_model == DEFAULT_LLM_MODEL  # original unchanged

    def test_update_multiple_fields(self):
        config = AppConfig()
        updated = update_config(config, llm_model="phi3", chunk_size=256)
        assert updated.llm_model == "phi3"
        assert updated.chunk_size == 256
