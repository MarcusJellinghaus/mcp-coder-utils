"""Filesystem helpers — encoding, line-endings, path security."""

from mcp_coder_utils.fs.path_security import normalize_path
from mcp_coder_utils.fs.read_file import read_file
from mcp_coder_utils.fs.text import normalize_line_endings

__all__ = [
    "normalize_line_endings",
    "normalize_path",
    "read_file",
]
