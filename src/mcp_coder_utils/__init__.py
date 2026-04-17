"""Shared low-level Python helpers for the mcp-coder family of repos."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mcp-coder-utils")
except PackageNotFoundError:
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
