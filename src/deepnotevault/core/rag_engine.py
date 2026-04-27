"""RAG engine: index documents and query them using LlamaIndex + Chroma + Ollama.

Ported from vaultai-backend/app/rag/engine.py with the following changes:
- session_id -> notebook_id
- async -> sync (runs in QThread)
- chroma_persist_dir -> ~/.deepnotevault/chroma/
- Configurable via AppConfig instead of server settings
"""

import logging
from pathlib import Path

from llama_index.core import (
    Settings as LlamaSettings,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

from deepnotevault.config import AppConfig
from deepnotevault.constants import CHROMA_DIR
from deepnotevault.core.document_processor import load_documents, chunk_documents

logger = logging.getLogger(__name__)


def configure_llama(config: AppConfig) -> None:
    """Apply LlamaIndex global settings from app config."""
    LlamaSettings.llm = Ollama(
        model=config.llm_model,
        base_url=config.ollama_url,
        request_timeout=120.0,
    )
    LlamaSettings.embed_model = OllamaEmbedding(
        model_name=config.embed_model,
        base_url=config.ollama_url,
    )
    LlamaSettings.node_parser = SentenceSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )


def _get_chroma_collection(
    notebook_id: str, persist_dir: Path = CHROMA_DIR
) -> tuple[chromadb.PersistentClient, chromadb.Collection]:
    """Get or create a Chroma collection for a notebook."""
    persist_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    client = chromadb.PersistentClient(path=str(persist_dir))
    collection_name = f"notebook_{notebook_id.replace('-', '_')}"
    return client, client.get_or_create_collection(collection_name)


def index_file(notebook_id: str, file_path: str, config: AppConfig) -> int:
    """
    Parse and index a single file into the notebook's Chroma collection.
    Returns the number of chunks indexed.
    """
    configure_llama(config)
    logger.info("Indexing file '%s' into notebook %s", file_path, notebook_id)

    _client, collection = _get_chroma_collection(notebook_id)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    documents = load_documents(file_path)
    nodes = chunk_documents(documents, config.chunk_size, config.chunk_overlap)

    VectorStoreIndex(
        nodes,
        storage_context=storage_context,
        show_progress=False,
    )
    logger.info("Indexed %d chunks from '%s'", len(nodes), file_path)
    return len(nodes)


def query_notebook(notebook_id: str, question: str, config: AppConfig) -> dict:
    """
    Query a notebook's indexed documents.
    Returns {"answer": str, "sources": list[dict]}
    """
    configure_llama(config)
    logger.info("Querying notebook %s: %r", notebook_id, question)

    _client, collection = _get_chroma_collection(notebook_id)
    if collection.count() == 0:
        return {
            "answer": "No documents have been indexed for this notebook yet.",
            "sources": [],
        }

    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        storage_context=storage_context,
    )

    query_engine = index.as_query_engine(similarity_top_k=config.similarity_top_k)
    response = query_engine.query(question)

    sources = []
    for node in response.source_nodes:
        metadata = node.node.metadata or {}
        sources.append(
            {
                "text": node.node.get_content()[:300],
                "page": metadata.get("page_label"),
                "filename": metadata.get("file_name"),
                "score": round(node.score, 4) if node.score else None,
            }
        )

    return {
        "answer": str(response),
        "sources": sources,
    }


def delete_notebook_index(notebook_id: str) -> None:
    """Remove all indexed data for a notebook."""
    client, _ = _get_chroma_collection(notebook_id)
    collection_name = f"notebook_{notebook_id.replace('-', '_')}"
    try:
        client.delete_collection(collection_name)
        logger.info("Deleted Chroma collection for notebook %s", notebook_id)
    except Exception:
        logger.warning(
            "Could not delete Chroma collection for notebook %s", notebook_id, exc_info=True
        )
