"""Main application window with integrated panels."""

from uuid import uuid4

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QMenuBar,
    QMenu,
    QMessageBox,
)

from deepnotevault.config import load_config, save_config, update_config
from deepnotevault.constants import (
    APP_NAME,
    CHROMA_DIR,
    NOTEBOOKS_DIR,
    SIDEBAR_WIDTH,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)
from deepnotevault.core.ollama_client import OllamaClient
from deepnotevault.models.schemas import Document, Notebook
from deepnotevault.ui.chat_panel import ChatPanel
from deepnotevault.ui.document_panel import DocumentPanel
from deepnotevault.ui.settings_dialog import SettingsDialog
from deepnotevault.ui.widgets.status_bar import StatusBar
from deepnotevault.workers.indexing_worker import IndexingWorker
from deepnotevault.workers.query_worker import QueryWorker
from deepnotevault.workers.summary_worker import SummaryWorker


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        # Application state
        self._config = load_config()
        self._client = OllamaClient(base_url=self._config.ollama_url)
        self._current_notebook = Notebook(name="Default Notebook")
        self._current_notebook.id = str(uuid4())

        # Active workers
        self._indexing_worker: IndexingWorker | None = None
        self._query_worker: QueryWorker | None = None
        self._summary_worker: SummaryWorker | None = None

        self._setup_menu()
        self._setup_ui()

    def _setup_menu(self) -> None:
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        settings_action = file_menu.addAction("Settings")
        settings_action.triggered.connect(self._open_settings)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        # Notebook menu
        nb_menu = menubar.addMenu("Notebook")
        new_nb_action = nb_menu.addAction("New Notebook")
        new_nb_action.triggered.connect(self._new_notebook)

        # Help menu
        help_menu = menubar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self._show_about)

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Document panel
        self._doc_panel = DocumentPanel()
        self._doc_panel.file_selected.connect(self._on_file_selected)
        self._doc_panel.summarize_requested.connect(self._on_summarize_requested)
        self._doc_panel.setMaximumWidth(SIDEBAR_WIDTH)
        splitter.addWidget(self._doc_panel)

        # Right: Chat panel
        self._chat_panel = ChatPanel()
        self._chat_panel.question_submitted.connect(self._on_question_submitted)
        splitter.addWidget(self._chat_panel)

        # Layout
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter, 1)

        # Status bar
        self._status_bar = StatusBar(self._client)
        self.setStatusBar(self._status_bar)

    def _on_file_selected(self, file_path: str) -> None:
        """Handle file selection for indexing."""
        if not self._client.is_healthy():
            QMessageBox.warning(
                self, "Error", "Ollama is not running. Please start Ollama."
            )
            return

        self._doc_panel.show_progress("Indexing...")
        self._indexing_worker = IndexingWorker(
            self._current_notebook.id, file_path, self._config
        )
        self._indexing_worker.finished.connect(
            lambda chunks: self._on_indexing_finished(file_path, chunks)
        )
        self._indexing_worker.error.connect(
            lambda err: self._on_indexing_error(err)
        )
        self._indexing_worker.start()

    def _on_indexing_finished(self, file_path: str, chunk_count: int) -> None:
        """Handle successful file indexing."""
        from pathlib import Path

        path = Path(file_path)
        doc = Document(filename=path.name, file_path=file_path, chunk_count=chunk_count)
        self._current_notebook.documents.append(doc)
        self._doc_panel.add_document(doc)
        self._doc_panel.hide_progress()
        self._chat_panel.add_assistant_message(
            f"✅ Indexed {path.name} ({chunk_count} chunks)"
        )

    def _on_indexing_error(self, error: str) -> None:
        """Handle indexing error."""
        self._doc_panel.hide_progress()
        self._chat_panel.add_error_message(f"Indexing failed: {error}")

    def _on_question_submitted(self, question: str) -> None:
        """Handle user question."""
        if not self._current_notebook.documents:
            self._chat_panel.add_assistant_message(
                "Please index some documents first before asking questions."
            )
            return

        self._chat_panel.add_user_message(question)
        self._chat_panel.set_loading(True)

        self._query_worker = QueryWorker(
            self._current_notebook.id, question, self._config
        )
        self._query_worker.finished.connect(self._on_query_finished)
        self._query_worker.error.connect(self._on_query_error)
        self._query_worker.start()

    def _on_query_finished(self, result: dict) -> None:
        """Handle query result."""
        self._chat_panel.set_loading(False)
        self._chat_panel.add_assistant_message(result["answer"], result["sources"])

    def _on_query_error(self, error: str) -> None:
        """Handle query error."""
        self._chat_panel.set_loading(False)
        self._chat_panel.add_error_message(f"Query failed: {error}")

    def _on_summarize_requested(self, file_path: str) -> None:
        """Handle summarization request."""
        self._chat_panel.set_loading(True)
        self._summary_worker = SummaryWorker(file_path, self._config)
        self._summary_worker.finished.connect(self._on_summarize_finished)
        self._summary_worker.error.connect(self._on_summarize_error)
        self._summary_worker.start()

    def _on_summarize_finished(self, summary: str) -> None:
        """Handle summarization result."""
        self._chat_panel.set_loading(False)
        self._chat_panel.add_assistant_message(f"**Summary:**\n\n{summary}")

    def _on_summarize_error(self, error: str) -> None:
        """Handle summarization error."""
        self._chat_panel.set_loading(False)
        self._chat_panel.add_error_message(f"Summarization failed: {error}")

    def _open_settings(self) -> None:
        """Open settings dialog."""
        dialog = SettingsDialog(self._config, self)
        if dialog.exec():
            self._config = dialog.get_config()
            save_config(self._config)
            self._client = OllamaClient(base_url=self._config.ollama_url)
            self._status_bar = StatusBar(self._client)
            self.setStatusBar(self._status_bar)

    def _new_notebook(self) -> None:
        """Create a new notebook."""
        self._current_notebook = Notebook(name="Untitled Notebook")
        self._current_notebook.id = str(uuid4())
        self._doc_panel._documents.clear()
        self._doc_panel._doc_list.clear()
        self._chat_panel._bubbles.clear()
        self._chat_panel._messages_layout.removeWidget(self._chat_panel._welcome)
        self._chat_panel._welcome = None

    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About DeepNote Vault",
            "DeepNote Vault v0.1.0\n\n"
            "Privacy-first local NotebookLM alternative.\n"
            "100% offline. Your data stays on your machine.\n\n"
            "Powered by Ollama, LlamaIndex, and ChromaDB.",
        )
