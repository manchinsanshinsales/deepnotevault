"""Application-wide constants."""

from pathlib import Path

APP_NAME = "DeepNote Vault"
APP_VERSION = "0.1.0"
APP_ID = "com.deepnotevault.app"

# Default paths
DATA_DIR = Path.home() / ".deepnotevault"
CHROMA_DIR = DATA_DIR / "chroma"
CONFIG_FILE = DATA_DIR / "config.json"
NOTEBOOKS_DIR = DATA_DIR / "notebooks"

# Ollama defaults
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_LLM_MODEL = "llama3.2"
DEFAULT_EMBED_MODEL = "nomic-embed-text"

# RAG defaults
DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 64
DEFAULT_SIMILARITY_TOP_K = 4

# Supported file types
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}

# UI constants
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 700
SIDEBAR_WIDTH = 250
