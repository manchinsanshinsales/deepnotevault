"""Document panel with drag-and-drop upload and document list."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from deepnotevault.constants import SUPPORTED_EXTENSIONS
from deepnotevault.models.schemas import Document


class DropZone(QLabel):
    """A label that accepts file drops."""

    files_dropped = Signal(list)  # list of file paths

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(80)
        self.setText("Drop files here\n(PDF, TXT, MD)")
        self._set_default_style()

    def _set_default_style(self) -> None:
        self.setStyleSheet(
            "QLabel { border: 2px dashed #adb5bd; border-radius: 8px; "
            "color: #6c757d; padding: 16px; background: #f8f9fa; }"
        )

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(
                "QLabel { border: 2px dashed #1976d2; border-radius: 8px; "
                "color: #1976d2; padding: 16px; background: #e3f2fd; }"
            )

    def dragLeaveEvent(self, event) -> None:
        self._set_default_style()

    def dropEvent(self, event) -> None:
        self._set_default_style()
        paths = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                paths.append(str(path))
        if paths:
            self.files_dropped.emit(paths)


class DocumentPanel(QWidget):
    """Panel for managing documents in a notebook."""

    file_selected = Signal(str)      # file path for indexing
    summarize_requested = Signal(str)  # file path for summarization

    def __init__(self, parent=None):
        super().__init__(parent)
        self._documents: list[Document] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header
        header = QLabel("Documents")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        # Drop zone
        self._drop_zone = DropZone()
        self._drop_zone.files_dropped.connect(self._on_files_dropped)
        layout.addWidget(self._drop_zone)

        # Browse button
        browse_btn = QPushButton("Browse Files...")
        browse_btn.clicked.connect(self._browse_files)
        layout.addWidget(browse_btn)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setTextVisible(True)
        layout.addWidget(self._progress)

        # Document list
        self._doc_list = QListWidget()
        self._doc_list.setStyleSheet("QListWidget { border: 1px solid #dee2e6; border-radius: 4px; }")
        layout.addWidget(self._doc_list)

        # Action buttons
        btn_layout = QHBoxLayout()
        self._summarize_btn = QPushButton("Summarize")
        self._summarize_btn.clicked.connect(self._on_summarize)
        self._summarize_btn.setEnabled(False)
        self._delete_btn = QPushButton("Remove")
        self._delete_btn.clicked.connect(self._on_delete)
        self._delete_btn.setEnabled(False)
        btn_layout.addWidget(self._summarize_btn)
        btn_layout.addWidget(self._delete_btn)
        layout.addLayout(btn_layout)

        # Selection tracking
        self._doc_list.currentRowChanged.connect(self._on_selection_changed)

    def _browse_files(self) -> None:
        extensions = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS))
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Documents", "", f"Documents ({extensions})"
        )
        if files:
            self._on_files_dropped(files)

    def _on_files_dropped(self, paths: list[str]) -> None:
        for path in paths:
            self.file_selected.emit(path)

    def _on_selection_changed(self, row: int) -> None:
        has_selection = row >= 0
        self._summarize_btn.setEnabled(has_selection)
        self._delete_btn.setEnabled(has_selection)

    def _on_summarize(self) -> None:
        row = self._doc_list.currentRow()
        if 0 <= row < len(self._documents):
            self.summarize_requested.emit(self._documents[row].file_path)

    def _on_delete(self) -> None:
        row = self._doc_list.currentRow()
        if 0 <= row < len(self._documents):
            self._documents.pop(row)
            self._doc_list.takeItem(row)

    def add_document(self, doc: Document) -> None:
        """Add an indexed document to the list."""
        self._documents.append(doc)
        item = QListWidgetItem(f"{doc.filename} ({doc.chunk_count} chunks)")
        self._doc_list.addItem(item)

    def show_progress(self, message: str) -> None:
        """Show indexing progress."""
        self._progress.setVisible(True)
        self._progress.setFormat(message)
        self._progress.setRange(0, 0)  # indeterminate

    def hide_progress(self) -> None:
        """Hide progress bar."""
        self._progress.setVisible(False)
        self._progress.setRange(0, 100)

    def get_documents(self) -> list[Document]:
        """Return all documents in this panel."""
        return list(self._documents)
