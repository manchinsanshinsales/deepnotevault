"""Tests for Ollama client (unit tests with mocked HTTP)."""

from unittest.mock import patch, MagicMock

import httpx
import pytest

from deepnotevault.core.ollama_client import (
    OllamaClient,
    OllamaConnectionError,
    OllamaModel,
)


@pytest.fixture
def client():
    return OllamaClient(base_url="http://localhost:11434")


class TestHealthCheck:
    def test_healthy(self, client: OllamaClient):
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            assert client.is_healthy() is True

    def test_unhealthy_status(self, client: OllamaClient):
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=500)
            assert client.is_healthy() is False

    def test_connection_refused(self, client: OllamaClient):
        with patch("httpx.get", side_effect=httpx.ConnectError("refused")):
            assert client.is_healthy() is False


class TestListModels:
    def test_returns_models(self, client: OllamaClient):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3.2:latest", "size": 2000000000, "digest": "abc123"},
                {"name": "nomic-embed-text:latest", "size": 500000000, "digest": "def456"},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        with patch("httpx.get", return_value=mock_response):
            models = client.list_models()
            assert len(models) == 2
            assert models[0].name == "llama3.2:latest"
            assert isinstance(models[0], OllamaModel)

    def test_connection_error(self, client: OllamaClient):
        with patch("httpx.get", side_effect=httpx.ConnectError("refused")):
            with pytest.raises(OllamaConnectionError):
                client.list_models()


class TestHasModel:
    def test_model_exists(self, client: OllamaClient):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [{"name": "llama3.2:latest", "size": 0, "digest": ""}]
        }
        mock_response.raise_for_status = MagicMock()
        with patch("httpx.get", return_value=mock_response):
            assert client.has_model("llama3.2") is True

    def test_model_missing(self, client: OllamaClient):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [{"name": "mistral:latest", "size": 0, "digest": ""}]
        }
        mock_response.raise_for_status = MagicMock()
        with patch("httpx.get", return_value=mock_response):
            assert client.has_model("llama3.2") is False


class TestGenerate:
    def test_successful_generation(self, client: OllamaClient):
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Hello world!"}
        mock_response.raise_for_status = MagicMock()
        with patch("httpx.post", return_value=mock_response):
            result = client.generate("llama3.2", "Say hello")
            assert result == "Hello world!"

    def test_generation_error(self, client: OllamaClient):
        with patch("httpx.post", side_effect=httpx.ConnectError("refused")):
            with pytest.raises(OllamaConnectionError):
                client.generate("llama3.2", "Say hello")
