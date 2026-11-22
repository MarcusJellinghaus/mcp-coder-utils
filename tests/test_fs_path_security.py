"""Tests for fs/path_security module — check_path_within, normalize_path."""

import errno
import os
from collections.abc import Callable, Iterator
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder_utils.fs.path_security import check_path_within, normalize_path

Check = Callable[[str, Path], object]

CHECKS: list[Check] = [check_path_within, normalize_path]


@pytest.fixture
def identity_resolve() -> Iterator[None]:
    """Make ``Path.resolve`` return the path unchanged."""
    with patch.object(Path, "resolve", autospec=True, side_effect=lambda self: self):
        yield


def _symlink_or_skip(link: Path, target: Path) -> None:
    try:
        os.symlink(target, link)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks not available: {exc}")


def _winerror_loop() -> OSError:
    exc = OSError("loop")
    setattr(exc, "winerror", 1921)  # noqa: B010 - typeshed declares winerror only on win32; attribute assignment fails mypy on Linux
    return exc


LOOP_ERRORS = [
    pytest.param(lambda: OSError(errno.ELOOP, "loop"), id="eloop"),
    pytest.param(_winerror_loop, id="winerror-1921"),
]


class TestNormalizePath:
    """Tests for normalize_path function."""

    def test_simple_relative_path(self, tmp_path: Path) -> None:
        result = normalize_path("file.txt", tmp_path)
        assert result == tmp_path / "file.txt"

    def test_subdirectory_path(self, tmp_path: Path) -> None:
        result = normalize_path("sub/file.txt", tmp_path)
        assert result == tmp_path / "sub" / "file.txt"

    def test_traversal_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="contains a '..' segment"):
            normalize_path("../outside.txt", tmp_path)

    def test_deep_traversal_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="contains a '..' segment"):
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


class TestCheckPathWithin:
    """Tests for check_path_within specific behaviour."""

    def test_accepts_path_object(self, tmp_path: Path) -> None:
        check_path_within(Path("sub/file.txt"), tmp_path)


@pytest.mark.parametrize("check", CHECKS)
class TestContainment:
    """Containment rules shared by check_path_within and normalize_path."""

    @pytest.mark.parametrize("path", ["../x", "sub/../file.txt"])
    def test_dotdot_segment_rejected(
        self, check: Check, path: str, tmp_path: Path
    ) -> None:
        with pytest.raises(ValueError, match="contains a '..' segment"):
            check(path, tmp_path)

    def test_nul_byte_rejected(self, check: Check, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="contains a NUL byte"):
            check("a\0b", tmp_path)

    def test_inside_relative_accepted(self, check: Check, tmp_path: Path) -> None:
        check("sub/file.txt", tmp_path)

    def test_inside_absolute_accepted(self, check: Check, tmp_path: Path) -> None:
        check(str(tmp_path / "f"), tmp_path)

    def test_absolute_outside_rejected(self, check: Check, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="outside allowed root"):
            check(str(tmp_path.parent / "out"), tmp_path)

    def test_root_with_dotdot_accepted(self, check: Check, tmp_path: Path) -> None:
        (tmp_path / "sub").mkdir()
        check("file.txt", tmp_path / "sub" / "..")

    def test_resolve_oserror_propagates(self, check: Check, tmp_path: Path) -> None:
        with patch.object(Path, "resolve", autospec=True, side_effect=OSError("boom")):
            with pytest.raises(OSError, match="boom"):
                check("sub/file.txt", tmp_path)

    def test_dotdot_checked_before_resolve(self, check: Check, tmp_path: Path) -> None:
        with patch.object(Path, "resolve", autospec=True, side_effect=OSError("boom")):
            with pytest.raises(ValueError, match="contains a '..' segment"):
                check("../x", tmp_path)

    def test_resolve_runtimeerror_becomes_oserror(
        self, check: Check, tmp_path: Path
    ) -> None:
        with patch.object(
            Path, "resolve", autospec=True, side_effect=RuntimeError("loop")
        ):
            with pytest.raises(OSError, match="cannot be resolved"):
                check("sub/file.txt", tmp_path)

    @pytest.mark.parametrize("make_error", LOOP_ERRORS)
    @pytest.mark.usefixtures("identity_resolve")
    def test_stat_loop_on_path_raises(
        self, check: Check, make_error: Callable[[], OSError], tmp_path: Path
    ) -> None:
        root = tmp_path
        real_stat = Path.stat

        def fake_stat(self: Path, **kwargs: object) -> os.stat_result:
            if self == root:
                return real_stat(self)
            raise make_error()

        with patch.object(Path, "stat", autospec=True, side_effect=fake_stat):
            with pytest.raises(OSError, match="loop"):
                check("sub/file.txt", root)

    @pytest.mark.usefixtures("identity_resolve")
    def test_stat_loop_on_root_raises(self, check: Check, tmp_path: Path) -> None:
        root = tmp_path

        def fake_stat(self: Path, **kwargs: object) -> os.stat_result:
            if self == root:
                raise OSError(errno.ELOOP, "loop")
            raise FileNotFoundError(errno.ENOENT, "missing")

        with patch.object(Path, "stat", autospec=True, side_effect=fake_stat):
            with pytest.raises(OSError, match="loop"):
                check(str(tmp_path.parent / "out"), root)

    def test_symlink_escape_rejected(self, check: Check, tmp_path: Path) -> None:
        root = tmp_path / "root"
        outside = tmp_path / "outside"
        root.mkdir()
        outside.mkdir()
        _symlink_or_skip(root / "link", outside)
        with pytest.raises(ValueError, match="outside allowed root"):
            check("link", root)

    def test_symlink_loop_raises(self, check: Check, tmp_path: Path) -> None:
        root = tmp_path / "root"
        root.mkdir()
        _symlink_or_skip(root / "a", root / "b")
        _symlink_or_skip(root / "b", root / "a")
        with pytest.raises(OSError):
            check("a", root)
