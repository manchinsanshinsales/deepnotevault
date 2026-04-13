"""Ollama HTTP client for health checks, model listing, and generation."""

from dataclasses import dataclass
from typing import Iterator

import httpx

from deepnotevault.constants import DEFAULT_OLLAMA_URL


@dataclass(frozen=True)
class OllamaModel:
    """Metadata for an installed Ollama model."""

    name: str
    size: int
    digest: str


class OllamaConnectionError(Exception):
    """Raised when Ollama is unreachable."""


class OllamaClient:
    """Synchronous HTTP client for the Ollama API."""

    def __init__(self, base_url: str = DEFAULT_OLLAMA_URL, timeout: float = 120.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self._base_url}{path}"

    def is_healthy(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            resp = httpx.get(self._url("/"), timeout=5.0)
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    def list_models(self) -> list[OllamaModel]:
        """Return all locally available models."""
        try:
            resp = httpx.get(self._url("/api/tags"), timeout=10.0)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise OllamaConnectionError(f"Cannot list models: {exc}") from exc

        models = []
        for m in resp.json().get("models", []):
            models.append(
                OllamaModel(
                    name=m.get("name", ""),
                    size=m.get("size", 0),
                    digest=m.get("digest", ""),
                )
            )
        return models

    def has_model(self, model_name: str) -> bool:
        """Check whether a specific model is installed."""
        try:
            models = self.list_models()
        except OllamaConnectionError:
            return False
        return any(m.name.startswith(model_name) for m in models)

    def generate(self, model: str, prompt: str, system: str = "") -> str:
        """Single-shot generation (non-streaming). Returns full response text."""
        payload: dict = {"model": model, "prompt": prompt, "stream": False}
        if system:
            payload["system"] = system
        try:
            resp = httpx.post(
                self._url("/api/generate"),
                json=payload,
                timeout=self._timeout,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise OllamaConnectionError(f"Generation failed: {exc}") from exc
        return resp.json().get("response", "")

    def generate_stream(
        self, model: str, prompt: str, system: str = ""
    ) -> Iterator[str]:
        """Streaming generation. Yields text chunks as they arrive."""
        payload: dict = {"model": model, "prompt": prompt, "stream": True}
        if system:
            payload["system"] = system
        try:
            with httpx.stream(
                "POST",
                self._url("/api/generate"),
                json=payload,
                timeout=self._timeout,
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    import json

                    data = json.loads(line)
                    token = data.get("response", "")
                    if token:
                        yield token
                    if data.get("done", False):
                        return
        except httpx.HTTPError as exc:
            raise OllamaConnectionError(f"Streaming failed: {exc}") from exc
