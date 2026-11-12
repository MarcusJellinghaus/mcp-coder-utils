"""Tests for tool_verify module."""

import pytest

from mcp_coder_utils.tool_verify import VerifyItem, VerifyStatus


class TestVerifyItem:
    """Tests for the VerifyItem dataclass."""

    def test_defaults(self) -> None:
        """Test default message and hint."""
        item = VerifyItem(name="n", status="ok")
        assert item.message == ""
        assert item.hint is None

    @pytest.mark.parametrize("status", ["ok", "warning", "error"])
    def test_valid_status(self, status: VerifyStatus) -> None:
        """Test that each allowed status is accepted."""
        assert VerifyItem(name="n", status=status).status == status

    def test_unknown_status_raises(self) -> None:
        """Test that an unknown status is rejected."""
        with pytest.raises(ValueError, match="bogus"):
            VerifyItem(name="n", status="bogus")  # type: ignore[arg-type]
