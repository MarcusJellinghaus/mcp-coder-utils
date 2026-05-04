"""Per-user app-data directory helper."""

from pathlib import Path

__all__ = ["get_user_app_data_dir"]


def get_user_app_data_dir(app_name: str) -> Path:
    """Return the per-user data directory for ``app_name``.

    Uses the dotfile-in-home convention on every platform:
    ``~/.<app_name>/``.

    Args:
        app_name: Application name (e.g. ``"mcp_coder"``).

    Returns:
        Absolute path under the user's home directory.

    Raises:
        RuntimeError: If ``Path.home()`` cannot be resolved (mirrors stdlib).
    """
    return Path.home() / f".{app_name}"
