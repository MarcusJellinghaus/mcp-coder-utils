"""Tests for fs/path_security module — normalize_path."""

from pathlib import Path

import pytest

from mcp_coder_utils.fs.path_security import normalize_path


class TestNormalizePath:
    """Tests for normalize_path function."""

    def test_simple_relative_path(self, tmp_path: Path) -> None:
        result = normalize_path("file.txt", tmp_path)
        assert result == tmp_path / "file.txt"

    def test_subdirectory_path(self, tmp_path: Path) -> None:
        result = normalize_path("sub/file.txt", tmp_path)
        assert result == tmp_path / "sub" / "file.txt"

    def test_traversal_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="outside allowed root"):
            normalize_path("../outside.txt", tmp_path)

    def test_deep_traversal_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="outside allowed root"):
            normalize_path("a/../../outside", tmp_path)

    def test_absolute_path_within_root(self, tmp_path: Path) -> None:
        abs_path = str(tmp_path / "inside.txt")
        result = normalize_path(abs_path, tmp_path)
        assert result == tmp_path / "inside.txt"

    def test_absolute_path_outside_root(self, tmp_path: Path) -> None:
        outside = str(tmp_path.parent / "outside.txt")
        with pytest.raises(ValueError, match="outside allowed root"):
            normalize_path(outside, tmp_path)

    def test_dot_path(self, tmp_path: Path) -> None:
        result = normalize_path(".", tmp_path)
        assert result == tmp_path

    def test_returns_resolved_path(self, tmp_path: Path) -> None:
        result = normalize_path("file.txt", tmp_path)
        assert result.is_absolute()


class TestNormalizePathNonExistentPaths:
    """Tests for normalize_path with non-existent paths."""

    def test_nonexistent_path_within_root(self, tmp_path: Path) -> None:
        result = normalize_path("fake/file.txt", tmp_path)
        assert result == tmp_path / "fake" / "file.txt"
