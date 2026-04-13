"""Chat message bubble widget with markdown rendering."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from deepnotevault.models.schemas import ChatMessage, MessageRole
from deepnotevault.ui.widgets.source_card import SourceCard


USER_STYLE = (
    "background: #e3f2fd; border-radius: 12px; padding: 10px; "
    "margin-left: 60px; margin-right: 4px;"
)
ASSISTANT_STYLE = (
    "background: #ffffff; border: 1px solid #e0e0e0; border-radius: 12px; "
    "padding: 10px; margin-left: 4px; margin-right: 60px;"
)


class MessageBubble(QFrame):
    """A single chat message bubble with optional source citations."""

    def __init__(self, message: ChatMessage, parent=None):
        super().__init__(parent)
        is_user = message.role == MessageRole.USER
        self.setStyleSheet(USER_STYLE if is_user else ASSISTANT_STYLE)
        self._setup_ui(message, is_user)

    def _setup_ui(self, message: ChatMessage, is_user: bool) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # Role label
        role_text = "You" if is_user else "DeepNote"
        role_label = QLabel(role_text)
        role_label.setStyleSheet(
            f"font-weight: bold; font-size: 11px; "
            f"color: {'#1976d2' if is_user else '#388e3c'};"
        )
        layout.addWidget(role_label)

        # Content
        content_label = QLabel(message.content)
        content_label.setWordWrap(True)
        content_label.setTextFormat(Qt.TextFormat.RichText)
        content_label.setStyleSheet("font-size: 13px;")
        content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(content_label)

        # Source citations
        if message.sources:
            sources_label = QLabel("Sources:")
            sources_label.setStyleSheet(
                "font-weight: bold; font-size: 11px; color: #666; margin-top: 4px;"
            )
            layout.addWidget(sources_label)
            for src in message.sources:
                card = SourceCard(src.model_dump())
                layout.addWidget(card)

    def append_text(self, text: str) -> None:
        """Append text to the content label (for streaming)."""
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QLabel) and widget.styleSheet().startswith("font-size: 13px"):
                current = widget.text()
                widget.setText(current + text)
                break
