"""Path security utilities — containment checks."""

import errno
from pathlib import Path

__all__ = ["check_path_within", "normalize_path"]

_WINERROR_CANT_RESOLVE_FILENAME = 1921


def _resolve_within(path: str | Path, root: Path) -> Path:
    """Resolve *path* against *root* and verify it stays within *root*.

    Args:
        path: The path to validate (relative to *root*, or absolute).
        root: The directory that the path must stay within.

    Returns:
        The resolved absolute path.

    Raises:
        ValueError: If *path* contains a ``..`` segment or a NUL byte, or
            resolves outside *root*.
        OSError: If *path* or *root* cannot be resolved, or is a symlink
            loop the OS reports.
    """
    if ".." in Path(path).parts:
        raise ValueError(f"Path '{path}' contains a '..' segment")
    if "\0" in str(path):
        raise ValueError(f"Path '{path}' contains a NUL byte")

    try:
        resolved_root = root.resolve()
        resolved = (resolved_root / path).resolve()
    except RuntimeError as exc:  # Python 3.11/3.12 raise on a symlink loop
        raise OSError(f"Path '{path}' cannot be resolved: {exc}") from exc

    # Python 3.13+ resolve() returns a partial resolution of a loop silently
    for candidate in (resolved_root, resolved):
        try:
            candidate.stat()
        except OSError as exc:
            if (
                exc.errno == errno.ELOOP
                or getattr(exc, "winerror", None) == _WINERROR_CANT_RESOLVE_FILENAME
            ):
                raise

    if not resolved.is_relative_to(resolved_root):
        raise ValueError(f"Path {path} is outside allowed root {resolved_root}")

    return resolved


def check_path_within(path: str | Path, root: Path) -> None:
    """Verify that *path* stays within *root*, without returning it.

    Use when the caller keeps its own form of the path (e.g. a joined path)
    and only needs the containment check. A relative *path* is anchored to
    *root*. ``OSError`` and symlink loops reach the caller on purpose — what
    to do with them (e.g. a lexical fallback) is the caller's policy.

    A symlink loop the OS reports raises ``OSError`` on every Python version.
    On Windows a loop is reported only as the last component — below a
    looping junction the partial resolution is checked for containment like
    any path.

    Args:
        path: The path to validate (relative to *root*, or absolute).
        root: The directory that the path must stay within.

    Raises:
        ValueError: If *path* contains a ``..`` segment or a NUL byte, or
            resolves outside *root*.
        OSError: If *path* or *root* cannot be resolved, or is a symlink
            loop the OS reports.
    """  # noqa: DOC502 - raised by _resolve_within
    _resolve_within(path, root)


def normalize_path(requested_path: str, allowed_root: Path) -> Path:
    """Resolve a requested path and verify it falls within an allowed root.

    Same rules as :func:`check_path_within`, but returns the resolved path.

    Behaviour change: a ``..`` segment now raises even when the path stays
    inside the root (``"sub/../file.txt"``); a NUL byte raises the same
    ``ValueError`` on every OS; a symlink loop the OS reports raises
    ``OSError`` (Python 3.11/3.12 raised ``RuntimeError``, 3.13+ returned a
    partial path).

    Args:
        requested_path: The path to validate (relative or absolute).
        allowed_root: The directory that the path must stay within.

    Returns:
        The resolved, validated absolute path.

    Raises:
        ValueError: If *requested_path* contains a ``..`` segment or a NUL
            byte, or resolves outside *allowed_root*.
        OSError: If *requested_path* or *allowed_root* cannot be resolved,
            or is a symlink loop the OS reports.
    """  # noqa: DOC502 - raised by _resolve_within
    return _resolve_within(requested_path, allowed_root)
