"""Background worker for RAG queries."""

from PySide6.QtCore import QThread, Signal

from deepnotevault.config import AppConfig
from deepnotevault.core.rag_engine import query_notebook


class QueryWorker(QThread):
    """Run a RAG query in a background thread."""

    finished = Signal(dict)   # {"answer": str, "sources": list}
    error = Signal(str)

    def __init__(
        self,
        notebook_id: str,
        question: str,
        config: AppConfig,
        parent=None,
    ):
        super().__init__(parent)
        self._notebook_id = notebook_id
        self._question = question
        self._config = config

    def run(self) -> None:
        try:
            result = query_notebook(self._notebook_id, self._question, self._config)
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))
