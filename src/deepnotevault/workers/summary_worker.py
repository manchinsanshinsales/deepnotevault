"""Background worker for document summarization."""

from PySide6.QtCore import QThread, Signal

from deepnotevault.config import AppConfig
from deepnotevault.core.summarizer import summarize_file


class SummaryWorker(QThread):
    """Summarize a document in a background thread."""

    finished = Signal(str)    # summary text
    error = Signal(str)

    def __init__(
        self,
        file_path: str,
        config: AppConfig,
        parent=None,
    ):
        super().__init__(parent)
        self._file_path = file_path
        self._config = config

    def run(self) -> None:
        try:
            summary = summarize_file(self._file_path, self._config)
            self.finished.emit(summary)
        except Exception as exc:
            self.error.emit(str(exc))
