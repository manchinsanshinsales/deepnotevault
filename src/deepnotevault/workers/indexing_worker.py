"""Background worker for document indexing."""

from PySide6.QtCore import QThread, Signal

from deepnotevault.config import AppConfig
from deepnotevault.core.rag_engine import index_file


class IndexingWorker(QThread):
    """Index a document in a background thread."""

    progress = Signal(str)        # status message
    finished = Signal(int)        # chunk count
    error = Signal(str)           # error message

    def __init__(
        self,
        notebook_id: str,
        file_path: str,
        config: AppConfig,
        parent=None,
    ):
        super().__init__(parent)
        self._notebook_id = notebook_id
        self._file_path = file_path
        self._config = config

    def run(self) -> None:
        try:
            self.progress.emit(f"Indexing: {self._file_path}")
            chunk_count = index_file(self._notebook_id, self._file_path, self._config)
            self.finished.emit(chunk_count)
        except Exception as exc:
            self.error.emit(str(exc))
