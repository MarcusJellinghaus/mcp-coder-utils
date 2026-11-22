"""Tests for fs/line_endings module — counting, dominant newline, writing."""

from pathlib import Path

import pytest

from mcp_coder_utils.fs.line_endings import (
    count_line_endings,
    dominant_newline,
    normalize_line_endings,
    write_text,
)


class TestNormalizeLineEndings:
    """Tests for normalize_line_endings function."""

    def test_crlf_converted_to_lf(self) -> None:
        assert normalize_line_endings("a\r\nb") == "a\nb"

    def test_cr_converted_to_lf(self) -> None:
        assert normalize_line_endings("a\rb") == "a\nb"

    def test_lf_unchanged(self) -> None:
        assert normalize_line_endings("a\nb") == "a\nb"

    def test_mixed_endings_normalized(self) -> None:
        assert normalize_line_endings("a\r\nb\rc\nd") == "a\nb\nc\nd"

    def test_empty_string(self) -> None:
        assert normalize_line_endings("") == ""

    def test_no_line_endings(self) -> None:
        assert normalize_line_endings("abc") == "abc"

    def test_only_line_endings(self) -> None:
        assert normalize_line_endings("\r\n\r\n") == "\n\n"


class TestCountLineEndings:
    """Tests for count_line_endings function."""

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (b"a\r\nb\nc\rd", (1, 1, 1)),
            (b"\r\n\r\n", (2, 0, 0)),
            (b"\n\r", (0, 1, 1)),
            (b"", (0, 0, 0)),
        ],
    )
    def test_counts(self, data: bytes, expected: tuple[int, int, int]) -> None:
        assert count_line_endings(data) == expected


class TestDominantNewline:
    """Tests for dominant_newline function."""

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (b"a\r\nb\r\n", "\r\n"),
            (b"a\nb\n", "\n"),
            (b"a\rb\r", "\r"),
            (b"a\r\nb\nc\n", "\n"),
            (b"a\r\nb\n", None),
            (b"a\r\nb\nc\r", None),
            (b"abc", None),
            (b"", None),
        ],
    )
    def test_dominant(self, data: bytes, expected: str | None) -> None:
        assert dominant_newline(data) == expected


class TestWriteText:
    """Tests for write_text function."""

    @pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
    def test_newline_styles(self, tmp_path: Path, newline: str) -> None:
        path = tmp_path / "f.txt"
        write_text(path, "a\nb\n", newline=newline)
        nl = newline.encode()
        assert path.read_bytes() == b"a" + nl + b"b" + nl

    def test_embedded_crlf_and_cr_normalised_default(self, tmp_path: Path) -> None:
        path = tmp_path / "f.txt"
        write_text(path, "a\r\nb\rc\n")
        assert path.read_bytes() == b"a\nb\nc\n"

    def test_embedded_crlf_and_cr_normalised_crlf(self, tmp_path: Path) -> None:
        path = tmp_path / "f.txt"
        write_text(path, "a\r\nb\rc\n", newline="\r\n")
        assert path.read_bytes() == b"a\r\nb\r\nc\r\n"

    def test_append(self, tmp_path: Path) -> None:
        path = tmp_path / "f.txt"
        path.write_bytes(b"x\r\n")
        write_text(path, "y\n", newline="\r\n", append=True)
        assert path.read_bytes() == b"x\r\ny\r\n"

    def test_append_creates_missing_file(self, tmp_path: Path) -> None:
        path = tmp_path / "f.txt"
        write_text(path, "y\n", append=True)
        assert path.read_bytes() == b"y\n"

    def test_overwrite_replaces_content(self, tmp_path: Path) -> None:
        path = tmp_path / "f.txt"
        path.write_bytes(b"old content\n")
        write_text(path, "new\n")
        assert path.read_bytes() == b"new\n"

    @pytest.mark.parametrize("newline", ["", None])
    def test_invalid_newline_leaves_file_untouched(
        self, tmp_path: Path, newline: str | None
    ) -> None:
        path = tmp_path / "f.txt"
        path.write_bytes(b"old")
        with pytest.raises(ValueError):
            write_text(path, "new\n", newline=newline)  # type: ignore[arg-type]
        assert path.read_bytes() == b"old"

    @pytest.mark.parametrize("newline", ["", None])
    def test_invalid_newline_does_not_create_file(
        self, tmp_path: Path, newline: str | None
    ) -> None:
        path = tmp_path / "f.txt"
        with pytest.raises(ValueError):
            write_text(path, "new\n", newline=newline)  # type: ignore[arg-type]
        assert not path.exists()

    def test_encode_error_leaves_file_untouched(self, tmp_path: Path) -> None:
        path = tmp_path / "f.txt"
        path.write_bytes(b"old")
        with pytest.raises(UnicodeEncodeError):
            write_text(path, "\ud800")
        assert path.read_bytes() == b"old"

    def test_parent_directory_not_created(self, tmp_path: Path) -> None:
        path = tmp_path / "missing" / "f.txt"
        with pytest.raises(FileNotFoundError):
            write_text(path, "a\n")
        assert not (tmp_path / "missing").exists()
