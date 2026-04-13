"""Document loading, parsing, and chunking pipeline."""

from pathlib import Path

from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document as LlamaDocument

from deepnotevault.constants import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    SUPPORTED_EXTENSIONS,
)


class UnsupportedFileError(Exception):
    """Raised when a file type is not supported."""


def validate_file(file_path: str) -> Path:
    """Validate that the file exists and has a supported extension."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileError(
            f"Unsupported file type: {path.suffix}. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )
    return path


def load_documents(file_path: str) -> list[LlamaDocument]:
    """Load a file and return LlamaIndex Document objects."""
    path = validate_file(file_path)
    reader = SimpleDirectoryReader(input_files=[str(path)])
    return reader.load_data()


def chunk_documents(
    documents: list[LlamaDocument],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list:
    """Split documents into chunks (nodes) for embedding."""
    splitter = SentenceSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.get_nodes_from_documents(documents)


def process_file(
    file_path: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> tuple[list[LlamaDocument], list]:
    """Load and chunk a file. Returns (documents, nodes)."""
    documents = load_documents(file_path)
    nodes = chunk_documents(documents, chunk_size, chunk_overlap)
    return documents, nodes
