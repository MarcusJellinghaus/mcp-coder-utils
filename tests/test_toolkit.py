"""Tests for toolkit module."""

import dataclasses
from pathlib import Path

import pytest

from mcp_coder_utils.toolkit import (
    ActionRequest,
    ActionResult,
    ActionStatus,
    Finding,
    VerifyItem,
    VerifyStatus,
)


class TestFinding:
    """Tests for the Finding dataclass."""

    def test_is_frozen(self) -> None:
        """Test that fields cannot be reassigned."""
        finding = Finding(key="k", message="m")
        with pytest.raises(dataclasses.FrozenInstanceError):
            finding.key = "x"  # type: ignore[misc]


class TestActionRequest:
    """Tests for the ActionRequest dataclass."""

    def test_is_frozen(self) -> None:
        """Test that fields cannot be reassigned."""
        request = ActionRequest(
            action="check", depth="quick", project_dir=Path("."), params={}
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            request.action = "x"  # type: ignore[misc]


class TestActionResult:
    """Tests for the ActionResult dataclass."""

    def test_defaults(self) -> None:
        """Test that only status and summary are required."""
        result = ActionResult(status="ok", summary="all good")
        assert result.findings == []
        assert result.fix_text == ""
        assert result.raw == ""

    def test_unknown_status_raises(self) -> None:
        """Test that an unknown status is rejected."""
        with pytest.raises(ValueError, match="bogus"):
            ActionResult(status="bogus", summary="s")  # type: ignore[arg-type]

    def test_findings_status_without_findings_raises(self) -> None:
        """Test that status 'findings' requires at least one finding."""
        with pytest.raises(ValueError, match="findings"):
            ActionResult(status="findings", summary="s")

    def test_findings_status_with_finding(self) -> None:
        """Test that status 'findings' accepts a finding."""
        finding = Finding(key="k", message="m")
        result = ActionResult(status="findings", summary="s", findings=[finding])
        assert result.findings == [finding]

    @pytest.mark.parametrize("status", ["ok", "skipped"])
    def test_status_with_findings_raises(self, status: ActionStatus) -> None:
        """Test that 'ok' and 'skipped' must not carry findings."""
        with pytest.raises(ValueError, match=status):
            ActionResult(
                status=status,
                summary="s",
                findings=[Finding(key="k", message="m")],
            )

    @pytest.mark.parametrize(
        "findings", [[], [Finding(key="k", message="m")]], ids=["none", "some"]
    )
    def test_error_status_accepts_any_findings(self, findings: list[Finding]) -> None:
        """Test that 'error' accepts both no findings and some findings."""
        result = ActionResult(status="error", summary="s", findings=findings)
        assert result.findings == findings


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
