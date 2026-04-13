"""Settings dialog for app configuration."""

from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QSpinBox,
)

from deepnotevault.config import AppConfig, save_config
from deepnotevault.core.ollama_client import OllamaClient


class SettingsDialog(QDialog):
    """Dialog for configuring app settings."""

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Ollama URL
        layout.addWidget(QLabel("Ollama Base URL"))
        self._url_input = QLineEdit()
        self._url_input.setText(self._config.ollama_url)
        layout.addWidget(self._url_input)

        # LLM Model
        layout.addWidget(QLabel("LLM Model"))
        self._llm_input = QLineEdit()
        self._llm_input.setText(self._config.llm_model)
        layout.addWidget(self._llm_input)

        # Embedding Model
        layout.addWidget(QLabel("Embedding Model"))
        self._embed_input = QLineEdit()
        self._embed_input.setText(self._config.embed_model)
        layout.addWidget(self._embed_input)

        # Chunk Size
        layout.addWidget(QLabel("Chunk Size"))
        self._chunk_size = QSpinBox()
        self._chunk_size.setMinimum(256)
        self._chunk_size.setMaximum(2048)
        self._chunk_size.setValue(self._config.chunk_size)
        layout.addWidget(self._chunk_size)

        # Chunk Overlap
        layout.addWidget(QLabel("Chunk Overlap"))
        self._chunk_overlap = QSpinBox()
        self._chunk_overlap.setMinimum(0)
        self._chunk_overlap.setMaximum(512)
        self._chunk_overlap.setValue(self._config.chunk_overlap)
        layout.addWidget(self._chunk_overlap)

        # Similarity Top K
        layout.addWidget(QLabel("Similarity Top K"))
        self._top_k = QSpinBox()
        self._top_k.setMinimum(1)
        self._top_k.setMaximum(20)
        self._top_k.setValue(self._config.similarity_top_k)
        layout.addWidget(self._top_k)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self._test_connection)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(test_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _test_connection(self) -> None:
        client = OllamaClient(base_url=self._url_input.text())
        if client.is_healthy():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Success", "Connected to Ollama!")
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Cannot connect to Ollama")

    def get_config(self) -> AppConfig:
        """Return the updated config."""
        return AppConfig(
            ollama_url=self._url_input.text(),
            llm_model=self._llm_input.text(),
            embed_model=self._embed_input.text(),
            chunk_size=self._chunk_size.value(),
            chunk_overlap=self._chunk_overlap.value(),
            similarity_top_k=self._top_k.value(),
        )
