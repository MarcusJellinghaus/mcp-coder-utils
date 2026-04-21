"""Path security utilities — traversal prevention."""

import os
from pathlib import Path

__all__ = ["normalize_path"]


def normalize_path(requested_path: str, allowed_root: Path) -> Path:
    """Resolve a requested path and verify it falls within an allowed root.

    Prevents path traversal attacks (e.g. ``../../etc/passwd``).

    Args:
        requested_path: The path to validate (relative or absolute).
        allowed_root: The directory that the path must stay within.

    Returns:
        The resolved, validated absolute path.

    Raises:
        ValueError: If the resolved path is outside *allowed_root*.
    """
    resolved_root = allowed_root.resolve()

    if os.path.isabs(requested_path):
        resolved = Path(requested_path).resolve()
    else:
        resolved = (resolved_root / requested_path).resolve()

    if not resolved.is_relative_to(resolved_root):
        raise ValueError(
            f"Path {requested_path} is outside allowed root {resolved_root}"
        )

    return resolved
