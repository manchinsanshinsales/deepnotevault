"""Source citation card widget."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class SourceCard(QFrame):
    """Displays a single source citation from a RAG query result."""

    def __init__(self, source: dict, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet(
            "SourceCard { background: #f8f9fa; border: 1px solid #dee2e6; "
            "border-radius: 6px; padding: 8px; }"
        )
        self._setup_ui(source)

    def _setup_ui(self, source: dict) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        # Header: filename + page
        header_parts = []
        if source.get("filename"):
            header_parts.append(source["filename"])
        if source.get("page"):
            header_parts.append(f"p.{source['page']}")
        if source.get("score") is not None:
            header_parts.append(f"({source['score']:.2f})")

        header = QLabel(" | ".join(header_parts) if header_parts else "Source")
        header.setStyleSheet("font-weight: bold; font-size: 11px; color: #495057;")
        layout.addWidget(header)

        # Preview text
        text = source.get("text", "")
        preview = QLabel(text[:200] + "..." if len(text) > 200 else text)
        preview.setWordWrap(True)
        preview.setStyleSheet("font-size: 12px; color: #6c757d;")
        layout.addWidget(preview)
