"""Document summarization using LlamaIndex SummaryIndex."""

from llama_index.core import SummaryIndex

from deepnotevault.config import AppConfig
from deepnotevault.core.document_processor import load_documents
from deepnotevault.core.rag_engine import configure_llama


def summarize_file(file_path: str, config: AppConfig) -> str:
    """Generate a summary of a single document file.

    Uses LlamaIndex's SummaryIndex which processes all chunks
    through the LLM to create a comprehensive summary.
    """
    configure_llama(config)
    documents = load_documents(file_path)
    index = SummaryIndex.from_documents(documents, show_progress=False)
    query_engine = index.as_query_engine()
    response = query_engine.query(
        "Provide a comprehensive summary of this document. "
        "Include the key points, main arguments, and important details."
    )
    return str(response)


def summarize_notebook(
    file_paths: list[str],
    config: AppConfig,
) -> str:
    """Generate a summary across multiple documents in a notebook."""
    configure_llama(config)
    all_documents = []
    for fp in file_paths:
        all_documents.extend(load_documents(fp))

    if not all_documents:
        return "No documents to summarize."

    index = SummaryIndex.from_documents(all_documents, show_progress=False)
    query_engine = index.as_query_engine()
    response = query_engine.query(
        "Provide a comprehensive overview of all these documents. "
        "Identify common themes, key differences, and important takeaways."
    )
    return str(response)
