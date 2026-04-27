"""Chat panel with message display and input."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from deepnotevault.models.schemas import ChatMessage, MessageRole, Source
from deepnotevault.ui.widgets.message_bubble import MessageBubble


class ChatPanel(QWidget):
    """Chat interface for asking questions about documents."""

    question_submitted = Signal(str)  # user question text

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bubbles: list[MessageBubble] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header
        header = QLabel("Chat with your documents")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        # Scroll area for messages
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self._messages_container = QWidget()
        self._messages_layout = QVBoxLayout(self._messages_container)
        self._messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._messages_layout.setSpacing(8)

        # Welcome message
        self._welcome = QLabel(
            "Upload documents and ask questions about them.\n"
            "Your data stays 100% local."
        )
        self._welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._welcome.setStyleSheet("color: #6c757d; padding: 40px;")
        self._messages_layout.addWidget(self._welcome)

        self._scroll_area.setWidget(self._messages_container)
        layout.addWidget(self._scroll_area, 1)

        # Loading indicator
        self._loading = QLabel("Thinking...")
        self._loading.setStyleSheet(
            "color: #1976d2; font-style: italic; padding: 4px;"
        )
        self._loading.setVisible(False)
        layout.addWidget(self._loading)

        # Input area
        input_layout = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("Ask a question about your documents...")
        self._input.setStyleSheet(
            "QLineEdit { border: 1px solid #dee2e6; border-radius: 8px; "
            "padding: 8px 12px; font-size: 13px; }"
        )
        self._input.returnPressed.connect(self._submit)

        self._send_btn = QPushButton("Send")
        self._send_btn.setStyleSheet(
            "QPushButton { background: #1976d2; color: white; border: none; "
            "border-radius: 8px; padding: 8px 16px; font-weight: bold; }"
            "QPushButton:hover { background: #1565c0; }"
            "QPushButton:disabled { background: #90caf9; }"
        )
        self._send_btn.clicked.connect(self._submit)

        input_layout.addWidget(self._input, 1)
        input_layout.addWidget(self._send_btn)
        layout.addLayout(input_layout)

    def _submit(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self.question_submitted.emit(text)

    def _remove_welcome(self) -> None:
        if self._welcome is not None:
            self._welcome.setParent(None)
            self._welcome.deleteLater()
            self._welcome = None

    def add_user_message(self, text: str) -> None:
        """Display a user message bubble."""
        self._remove_welcome()
        msg = ChatMessage(role=MessageRole.USER, content=text)
        bubble = MessageBubble(msg)
        self._messages_layout.addWidget(bubble)
        self._bubbles.append(bubble)
        self._scroll_to_bottom()

    def add_assistant_message(self, text: str, sources: list[dict] | None = None) -> None:
        """Display an assistant message with optional sources."""
        self._remove_welcome()
        source_objs = [Source(**s) for s in (sources or [])]
        msg = ChatMessage(
            role=MessageRole.ASSISTANT, content=text, sources=source_objs
        )
        bubble = MessageBubble(msg)
        self._messages_layout.addWidget(bubble)
        self._bubbles.append(bubble)
        self._scroll_to_bottom()

    def add_error_message(self, text: str) -> None:
        """Display an error message."""
        self._remove_welcome()
        label = QLabel(f"Error: {text}")
        label.setWordWrap(True)
        label.setStyleSheet(
            "color: #d32f2f; background: #ffebee; border-radius: 8px; "
            "padding: 8px; margin: 4px;"
        )
        self._messages_layout.addWidget(label)
        self._scroll_to_bottom()

    def set_loading(self, loading: bool) -> None:
        """Show or hide the loading indicator."""
        self._loading.setVisible(loading)
        self._send_btn.setEnabled(not loading)
        self._input.setEnabled(not loading)

    def _scroll_to_bottom(self) -> None:
        scrollbar = self._scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear(self) -> None:
        """Remove all messages and restore the welcome screen."""
        while self._messages_layout.count():
            item = self._messages_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
                item.widget().deleteLater()
        self._bubbles.clear()

        self._welcome = QLabel(
            "Upload documents and ask questions about them.\n"
            "Your data stays 100% local."
        )
        self._welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._welcome.setStyleSheet("color: #6c757d; padding: 40px;")
        self._messages_layout.addWidget(self._welcome)
