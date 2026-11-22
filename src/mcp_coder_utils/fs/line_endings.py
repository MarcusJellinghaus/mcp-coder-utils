"""Line-ending counting, choice and writing."""

from pathlib import Path

__all__ = [
    "count_line_endings",
    "dominant_newline",
    "normalize_line_endings",
    "write_text",
]

_NEWLINES = ("\n", "\r\n", "\r")


def normalize_line_endings(text: str) -> str:
    """Normalize CRLF and CR line endings to LF.

    Replaces Windows (CRLF) and old Mac (CR) line endings with Unix (LF).
    CRLF is replaced first to avoid double conversion. Works on text in
    memory; use ``write_text`` to write text to disk with a chosen newline.

    Args:
        text: Text with any line ending style.

    Returns:
        Text with only LF line endings.
    """
    return text.replace("\r\n", "\n").replace("\r", "\n")


def count_line_endings(data: bytes) -> tuple[int, int, int]:
    """Count each line-ending style in raw bytes.

    Returns raw counts only; ``dominant_newline`` makes the decision.

    Args:
        data: Raw file content.

    Returns:
        ``(crlf, lone_lf, lone_cr)`` counts. A CRLF pair counts once, as CRLF.
    """
    crlf = data.count(b"\r\n")
    return crlf, data.count(b"\n") - crlf, data.count(b"\r") - crlf


def dominant_newline(data: bytes) -> str | None:
    r"""Return the most common line ending in raw bytes.

    ``None`` covers both a tie (including a three-way tie) and data with no
    line breaks. Callers fall back to their own default with
    ``dominant_newline(existing or b"") or default``; the argument is bytes
    only, so a missing file passes ``b""``. Choosing ``default`` is the
    caller's policy.

    Args:
        data: Raw file content.

    Returns:
        ``"\r\n"``, ``"\n"`` or ``"\r"``, or ``None`` on a tie or when
        there are no line breaks.
    """
    crlf, lf, cr = count_line_endings(data)
    top = max(crlf, lf, cr)
    winners = [nl for n, nl in ((crlf, "\r\n"), (lf, "\n"), (cr, "\r")) if n == top]
    return winners[0] if top and len(winners) == 1 else None


def write_text(
    path: Path, text: str, *, newline: str = "\n", append: bool = False
) -> None:
    r"""Write text as UTF-8 with every line break set to ``newline``.

    Unlike ``Path.write_text``, line endings are normalised first, so
    ``newline="\r\n"`` cannot produce CR CR LF, and a lone CR becomes a
    line break. The text is encoded before the file is opened, so an encode
    error leaves an existing file untouched. An invalid ``newline`` raises
    before any file access. Parent directories are not created.
    ``append=True`` on a missing file creates it. Choosing ``newline`` is
    the caller's policy.

    Args:
        path: File to write.
        text: Text with any line ending style.
        newline: Line ending to write: ``"\n"``, ``"\r\n"`` or ``"\r"``.
        append: Append to the file instead of overwriting it.

    Raises:
        ValueError: If ``newline`` is not one of the three line endings.
    """
    if newline not in _NEWLINES:
        raise ValueError(f"newline must be one of {_NEWLINES!r}, got {newline!r}")
    data = normalize_line_endings(text).replace("\n", newline).encode("utf-8")
    with path.open("ab" if append else "wb") as handle:
        handle.write(data)
