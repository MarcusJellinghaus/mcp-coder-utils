"""File reading utilities with encoding fallback."""

from pathlib import Path

__all__ = ["read_file"]


def read_file(file_path: str | Path, encoding: str = "utf-8") -> str:
    """Read a file with encoding fallback.

    Tries the specified encoding first, falls back to latin-1
    on UnicodeDecodeError.

    Args:
        file_path: Path to the file to read.
        encoding: Primary encoding to try. Defaults to utf-8.

    Returns:
        File contents as a string.
    """
    path = Path(file_path)
    try:
        return path.read_text(encoding=encoding)
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")
