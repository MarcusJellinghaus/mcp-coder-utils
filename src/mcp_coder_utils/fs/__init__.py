"""Filesystem helpers — encoding, line-endings, path security."""

from mcp_coder_utils.fs.line_endings import (
    count_line_endings,
    dominant_newline,
    normalize_line_endings,
    write_text,
)
from mcp_coder_utils.fs.path_security import normalize_path
from mcp_coder_utils.fs.read_file import read_file

__all__ = [
    "count_line_endings",
    "dominant_newline",
    "normalize_line_endings",
    "normalize_path",
    "read_file",
    "write_text",
]
