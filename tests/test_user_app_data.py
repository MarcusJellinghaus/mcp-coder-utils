"""Tests for user_app_data module."""

from pathlib import Path

import pytest

from mcp_coder_utils.user_app_data import get_user_app_data_dir


@pytest.mark.parametrize("app_name", ["mcp_coder", "foo"])
def test_returns_dotdir_under_home(app_name: str) -> None:
    assert get_user_app_data_dir(app_name) == Path.home() / f".{app_name}"
