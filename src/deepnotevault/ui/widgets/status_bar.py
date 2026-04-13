"""Ollama connection status bar widget."""

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from deepnotevault.core.ollama_client import OllamaClient


class StatusBar(QWidget):
    """Displays Ollama connection status and current model info."""

    def __init__(self, ollama_client: OllamaClient, parent=None):
        super().__init__(parent)
        self._client = ollama_client
        self._setup_ui()
        self._start_polling()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self._indicator = QLabel()
        self._indicator.setFixedSize(10, 10)
        self._status_label = QLabel("Checking Ollama...")
        self._model_label = QLabel("")

        layout.addWidget(self._indicator)
        layout.addWidget(self._status_label)
        layout.addStretch()
        layout.addWidget(self._model_label)

        self._set_disconnected()

    def _start_polling(self) -> None:
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_status)
        self._timer.start(5000)
        self._check_status()

    def _check_status(self) -> None:
        if self._client.is_healthy():
            self._set_connected()
        else:
            self._set_disconnected()

    def _set_connected(self) -> None:
        self._indicator.setStyleSheet(
            "background-color: #22c55e; border-radius: 5px;"
        )
        self._status_label.setText("Ollama Connected")
        try:
            models = self._client.list_models()
            names = [m.name for m in models[:3]]
            self._model_label.setText(f"Models: {', '.join(names)}")
        except Exception:
            self._model_label.setText("")

    def _set_disconnected(self) -> None:
        self._indicator.setStyleSheet(
            "background-color: #ef4444; border-radius: 5px;"
        )
        self._status_label.setText("Ollama Disconnected")
        self._model_label.setText("Start Ollama to begin")
