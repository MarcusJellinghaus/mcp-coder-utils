"""Tests for fs/text module — normalize_line_endings."""

from mcp_coder_utils.fs.text import normalize_line_endings


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
