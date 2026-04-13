"""Application entry point."""

import sys

from deepnotevault.constants import DATA_DIR, CHROMA_DIR, NOTEBOOKS_DIR


def ensure_data_dirs() -> None:
    """Create application data directories if they don't exist."""
    for d in (DATA_DIR, CHROMA_DIR, NOTEBOOKS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """Launch the DeepNote Vault application."""
    ensure_data_dirs()

    from PySide6.QtWidgets import QApplication

    from deepnotevault.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("DeepNote Vault")
    app.setOrganizationName("DeepNoteVault")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
