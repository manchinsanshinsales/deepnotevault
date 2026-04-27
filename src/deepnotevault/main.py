"""Application entry point."""

import logging
import sys
from pathlib import Path

from deepnotevault.constants import DATA_DIR, CHROMA_DIR, NOTEBOOKS_DIR

LOG_FILE = DATA_DIR / "app.log"


def _setup_logging() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ],
    )


def ensure_data_dirs() -> None:
    """Create application data directories with restricted permissions."""
    for d in (DATA_DIR, CHROMA_DIR, NOTEBOOKS_DIR):
        d.mkdir(parents=True, exist_ok=True, mode=0o700)


def main() -> None:
    """Launch the DeepNote Vault application."""
    _setup_logging()
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
