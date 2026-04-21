"""Tests for fs/read_file module — read_file with encoding fallback."""

from pathlib import Path

import pytest

from mcp_coder_utils.fs.read_file import read_file


class TestReadFile:
    """Tests for read_file function."""

    def test_read_utf8_file(self, tmp_path: Path) -> None:
        f = tmp_path / "utf8.txt"
        f.write_text("hello café", encoding="utf-8")
        assert read_file(str(f)) == "hello café"

    def test_read_latin1_fallback(self, tmp_path: Path) -> None:
        f = tmp_path / "latin1.bin"
        f.write_bytes(b"caf\xe9")
        assert read_file(str(f)) == "café"

    def test_read_with_explicit_encoding(self, tmp_path: Path) -> None:
        f = tmp_path / "latin1.txt"
        f.write_bytes(b"caf\xe9")
        assert read_file(str(f), encoding="latin-1") == "café"

    def test_file_not_found_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            read_file(str(tmp_path / "missing.txt"))

    def test_accepts_path_object(self, tmp_path: Path) -> None:
        f = tmp_path / "path_obj.txt"
        f.write_text("content", encoding="utf-8")
        assert read_file(f) == "content"

    def test_empty_file(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        assert read_file(str(f)) == ""
