"""Text processing utilities for filesystem operations."""

__all__ = ["normalize_line_endings"]


def normalize_line_endings(text: str) -> str:
    """Normalize CRLF and CR line endings to LF.

    Replaces Windows (CRLF) and old Mac (CR) line endings with Unix (LF).
    CRLF is replaced first to avoid double conversion.

    Args:
        text: Text with any line ending style.

    Returns:
        Text with only LF line endings.
    """
    return text.replace("\r\n", "\n").replace("\r", "\n")
