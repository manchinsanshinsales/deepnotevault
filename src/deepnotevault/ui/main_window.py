"""Main application window with integrated panels."""

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from deepnotevault.config import load_config, save_config
from deepnotevault.constants import (
    APP_NAME,
    NOTEBOOKS_DIR,
    SIDEBAR_WIDTH,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)
from deepnotevault.core.ollama_client import OllamaClient
from deepnotevault.core.rag_engine import delete_notebook_index
from deepnotevault.models.schemas import ChatMessage, Document, MessageRole, Notebook, Source
from deepnotevault.notebook_manager import NotebookManager
from deepnotevault.ui.chat_panel import ChatPanel
from deepnotevault.ui.document_panel import DocumentPanel
from deepnotevault.ui.settings_dialog import SettingsDialog
from deepnotevault.ui.widgets.status_bar import StatusBar
from deepnotevault.workers.indexing_worker import IndexingWorker
from deepnotevault.workers.query_worker import QueryWorker
from deepnotevault.workers.summary_worker import SummaryWorker

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        self._config = load_config()
        self._client = OllamaClient(base_url=self._config.ollama_url)
        self._nb_mgr = NotebookManager(NOTEBOOKS_DIR)
        self._current_notebook = self._nb_mgr.load_or_create_active()

        self._indexing_worker: IndexingWorker | None = None
        self._query_worker: QueryWorker | None = None
        self._summary_worker: SummaryWorker | None = None

        self._setup_menu()
        self._setup_ui()
        self._restore_notebook_ui()
        self._update_title()
        logger.info("Application started with notebook '%s'", self._current_notebook.name)

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        settings_action = file_menu.addAction("Settings")
        settings_action.triggered.connect(self._open_settings)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        self._nb_menu = menubar.addMenu("Notebook")
        new_nb_action = self._nb_menu.addAction("New Notebook")
        new_nb_action.triggered.connect(self._new_notebook)
        rename_action = self._nb_menu.addAction("Rename Notebook")
        rename_action.triggered.connect(self._rename_notebook)
        delete_action = self._nb_menu.addAction("Delete Notebook")
        delete_action.triggered.connect(self._delete_notebook)
        self._nb_menu.addSeparator()
        self._nb_menu.aboutToShow.connect(self._populate_notebook_list)

        help_menu = menubar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self._show_about)

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._doc_panel = DocumentPanel()
        self._doc_panel.file_selected.connect(self._on_file_selected)
        self._doc_panel.summarize_requested.connect(self._on_summarize_requested)
        self._doc_panel.setMaximumWidth(SIDEBAR_WIDTH)
        splitter.addWidget(self._doc_panel)

        self._chat_panel = ChatPanel()
        self._chat_panel.question_submitted.connect(self._on_question_submitted)
        splitter.addWidget(self._chat_panel)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter, 1)

        self._status_bar = StatusBar(self._client)
        self.setStatusBar(self._status_bar)

    # ------------------------------------------------------------------
    # Notebook UI restore
    # ------------------------------------------------------------------

    def _restore_notebook_ui(self) -> None:
        """Populate panels from the current notebook's persisted data."""
        for doc in self._current_notebook.documents:
            self._doc_panel.add_document(doc)
        for msg in self._current_notebook.messages:
            if msg.role == MessageRole.USER:
                self._chat_panel.add_user_message(msg.content)
            elif msg.role == MessageRole.ASSISTANT:
                source_dicts = [s.model_dump() for s in msg.sources]
                self._chat_panel.add_assistant_message(msg.content, source_dicts)

    def _update_title(self) -> None:
        self.setWindowTitle(f"{APP_NAME} — {self._current_notebook.name}")

    # ------------------------------------------------------------------
    # File indexing
    # ------------------------------------------------------------------

    def _on_file_selected(self, file_path: str) -> None:
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
        self._indexing_worker.error.connect(self._on_indexing_error)
        self._indexing_worker.start()

    def _on_indexing_finished(self, file_path: str, chunk_count: int) -> None:
        from pathlib import Path

        path = Path(file_path)
        doc = Document(filename=path.name, file_path=file_path, chunk_count=chunk_count)
        self._current_notebook.documents.append(doc)
        self._nb_mgr.save(self._current_notebook)

        self._doc_panel.add_document(doc)
        self._doc_panel.hide_progress()
        self._chat_panel.add_assistant_message(
            f"Indexed {path.name} ({chunk_count} chunks)"
        )
        logger.info("Indexed '%s' (%d chunks)", path.name, chunk_count)

    def _on_indexing_error(self, error: str) -> None:
        self._doc_panel.hide_progress()
        self._chat_panel.add_error_message(f"Indexing failed: {error}")
        logger.error("Indexing error: %s", error)

    # ------------------------------------------------------------------
    # RAG query
    # ------------------------------------------------------------------

    def _on_question_submitted(self, question: str) -> None:
        if not self._current_notebook.documents:
            self._chat_panel.add_assistant_message(
                "Please index some documents first before asking questions."
            )
            return

        user_msg = ChatMessage(role=MessageRole.USER, content=question)
        self._current_notebook.messages.append(user_msg)
        self._chat_panel.add_user_message(question)
        self._chat_panel.set_loading(True)

        self._query_worker = QueryWorker(
            self._current_notebook.id, question, self._config
        )
        self._query_worker.finished.connect(self._on_query_finished)
        self._query_worker.error.connect(self._on_query_error)
        self._query_worker.start()

    def _on_query_finished(self, result: dict) -> None:
        self._chat_panel.set_loading(False)
        answer = result["answer"]
        sources = result["sources"]

        source_objs = [Source(**s) for s in sources]
        assistant_msg = ChatMessage(
            role=MessageRole.ASSISTANT, content=answer, sources=source_objs
        )
        self._current_notebook.messages.append(assistant_msg)
        self._nb_mgr.save(self._current_notebook)

        self._chat_panel.add_assistant_message(answer, sources)

    def _on_query_error(self, error: str) -> None:
        self._chat_panel.set_loading(False)
        self._chat_panel.add_error_message(f"Query failed: {error}")
        logger.error("Query error: %s", error)

    # ------------------------------------------------------------------
    # Summarization
    # ------------------------------------------------------------------

    def _on_summarize_requested(self, file_path: str) -> None:
        self._chat_panel.set_loading(True)
        self._summary_worker = SummaryWorker(file_path, self._config)
        self._summary_worker.finished.connect(self._on_summarize_finished)
        self._summary_worker.error.connect(self._on_summarize_error)
        self._summary_worker.start()

    def _on_summarize_finished(self, summary: str) -> None:
        self._chat_panel.set_loading(False)
        self._chat_panel.add_assistant_message(f"**Summary:**\n\n{summary}")

    def _on_summarize_error(self, error: str) -> None:
        self._chat_panel.set_loading(False)
        self._chat_panel.add_error_message(f"Summarization failed: {error}")
        logger.error("Summarization error: %s", error)

    # ------------------------------------------------------------------
    # Notebook management
    # ------------------------------------------------------------------

    def _populate_notebook_list(self) -> None:
        """Rebuild the 'switch to' submenu each time the menu opens."""
        # Remove old switch entries (everything after the separator)
        actions = self._nb_menu.actions()
        sep_idx = next(
            (i for i, a in enumerate(actions) if a.isSeparator()), len(actions)
        )
        for action in actions[sep_idx + 1 :]:
            self._nb_menu.removeAction(action)

        for nb in self._nb_mgr.list_notebooks():
            label = f"{'→ ' if nb.id == self._current_notebook.id else ''}{nb.name}"
            action = self._nb_menu.addAction(label)
            action.setEnabled(nb.id != self._current_notebook.id)
            action.triggered.connect(lambda checked=False, nid=nb.id: self._switch_notebook(nid))

    def _new_notebook(self) -> None:
        name, ok = QInputDialog.getText(self, "New Notebook", "Notebook name:")
        if not ok or not name.strip():
            return
        self._nb_mgr.save(self._current_notebook)
        self._current_notebook = Notebook(name=name.strip())
        self._nb_mgr.save(self._current_notebook)
        self._nb_mgr.set_active(self._current_notebook.id)
        self._doc_panel.clear()
        self._chat_panel.clear()
        self._update_title()
        logger.info("Created new notebook '%s'", self._current_notebook.name)

    def _rename_notebook(self) -> None:
        name, ok = QInputDialog.getText(
            self,
            "Rename Notebook",
            "New name:",
            text=self._current_notebook.name,
        )
        if not ok or not name.strip():
            return
        self._current_notebook.name = name.strip()
        self._nb_mgr.save(self._current_notebook)
        self._update_title()

    def _delete_notebook(self) -> None:
        reply = QMessageBox.question(
            self,
            "Delete Notebook",
            f"Delete '{self._current_notebook.name}' and all its indexed data?\n"
            "This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        old_id = self._current_notebook.id
        delete_notebook_index(old_id)
        self._nb_mgr.delete(old_id)

        remaining = self._nb_mgr.list_notebooks()
        if remaining:
            self._current_notebook = remaining[0]
        else:
            self._current_notebook = Notebook(name="Default Notebook")
            self._nb_mgr.save(self._current_notebook)

        self._nb_mgr.set_active(self._current_notebook.id)
        self._doc_panel.clear()
        self._chat_panel.clear()
        self._restore_notebook_ui()
        self._update_title()
        logger.info("Deleted notebook %s", old_id)

    def _switch_notebook(self, notebook_id: str) -> None:
        self._nb_mgr.save(self._current_notebook)
        nb = self._nb_mgr.load(notebook_id)
        if nb is None:
            QMessageBox.warning(self, "Error", "Could not load the selected notebook.")
            return
        self._current_notebook = nb
        self._nb_mgr.set_active(nb.id)
        self._doc_panel.clear()
        self._chat_panel.clear()
        self._restore_notebook_ui()
        self._update_title()
        logger.info("Switched to notebook '%s'", nb.name)

    # ------------------------------------------------------------------
    # Settings / About
    # ------------------------------------------------------------------

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self._config, self)
        if dialog.exec():
            try:
                new_config = dialog.get_config()
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid Settings", str(exc))
                return
            self._config = new_config
            save_config(self._config)
            self._client = OllamaClient(base_url=self._config.ollama_url)
            self._status_bar = StatusBar(self._client)
            self.setStatusBar(self._status_bar)

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About DeepNote Vault",
            "DeepNote Vault v0.1.0\n\n"
            "Privacy-first local NotebookLM alternative.\n"
            "100% offline. Your data stays on your machine.\n\n"
            "Powered by Ollama, LlamaIndex, and ChromaDB.",
        )

    def closeEvent(self, event) -> None:
        """Save current notebook before closing."""
        self._nb_mgr.save(self._current_notebook)
        logger.info("Application closing, notebook saved.")
        super().closeEvent(event)
