"""Main application window."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from deepnotevault.constants import APP_NAME, SIDEBAR_WIDTH, WINDOW_MIN_HEIGHT, WINDOW_MIN_WIDTH


class MainWindow(QMainWindow):
    """Main application window with sidebar and central panel."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self._setup_ui()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Sidebar placeholder
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.addWidget(QLabel("Notebooks"))
        sidebar_layout.addStretch()
        sidebar.setMaximumWidth(SIDEBAR_WIDTH)

        # Main content placeholder
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.addWidget(
            QLabel("Welcome to DeepNote Vault\n\nDrag & drop documents to get started.")
        )
        content_layout.addStretch()

        splitter.addWidget(sidebar)
        splitter.addWidget(content)

        layout = QHBoxLayout(central)
        layout.addWidget(splitter)
