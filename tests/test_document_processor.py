"""Tests for document processor."""

from pathlib import Path

import pytest

from deepnotevault.core.document_processor import (
    UnsupportedFileError,
    validate_file,
)


class TestValidateFile:
    def test_valid_txt_file(self, tmp_path: Path):
        f = tmp_path / "test.txt"
        f.write_text("hello world", encoding="utf-8")
        result = validate_file(str(f))
        assert result == f

    def test_valid_md_file(self, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("# Heading", encoding="utf-8")
        result = validate_file(str(f))
        assert result == f

    def test_valid_pdf_extension(self, tmp_path: Path):
        f = tmp_path / "test.pdf"
        f.write_bytes(b"%PDF-1.4 fake")
        result = validate_file(str(f))
        assert result == f

    def test_unsupported_extension(self, tmp_path: Path):
        f = tmp_path / "test.docx"
        f.write_text("content", encoding="utf-8")
        with pytest.raises(UnsupportedFileError, match="Unsupported file type"):
            validate_file(str(f))

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            validate_file("/nonexistent/path/file.txt")

    def test_case_insensitive_extension(self, tmp_path: Path):
        f = tmp_path / "test.PDF"
        f.write_bytes(b"%PDF-1.4 fake")
        result = validate_file(str(f))
        assert result == f
