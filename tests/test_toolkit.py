"""Tests for toolkit module."""

import dataclasses
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from mcp_coder_utils.toolkit import (
    ActionRequest,
    ActionResult,
    ActionStatus,
    Finding,
    JsonSchema,
    Toolkit,
    ToolkitInfo,
    VerifyItem,
    VerifyStatus,
    validate_params,
)

SCHEMA: JsonSchema = {
    "type": "object",
    "properties": {"markers": {"type": "string"}},
    "additionalProperties": False,
}


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


class TestValidateParams:
    """Tests for validate_params."""

    def test_valid_params(self) -> None:
        """Test that valid params pass."""
        validate_params(SCHEMA, {"markers": "slow"})

    def test_unknown_key_raises(self) -> None:
        """Test that an unknown key is rejected and named."""
        with pytest.raises(ValueError, match="bogus"):
            validate_params(SCHEMA, {"bogus": 1})

    def test_wrong_type_raises(self) -> None:
        """Test that a wrong type is rejected with its location."""
        with pytest.raises(ValueError, match=r"\$\.markers"):
            validate_params(SCHEMA, {"markers": 5})

    def test_malformed_schema_raises(self) -> None:
        """Test that a malformed schema is rejected."""
        with pytest.raises(ValueError, match="Invalid params schema"):
            validate_params({"type": 5}, {})


class TestToolkitInfo:
    """Tests for the ToolkitInfo dataclass."""

    def test_valid_schema(self) -> None:
        """Test construction with a valid schema and default fields."""
        info = ToolkitInfo(actions={"check": ["quick"]}, params_schema=SCHEMA)
        assert info.llm_permissions == {}
        assert info.fix_prompts == {}

    def test_malformed_schema_raises(self) -> None:
        """Test that a malformed schema is rejected."""
        with pytest.raises(ValueError):
            ToolkitInfo(actions={}, params_schema={"type": 5})

    def test_invalid_regex_pattern_raises(self) -> None:
        """Test that a schema with an invalid regex pattern is rejected."""
        schema: JsonSchema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {"x": {"type": "string", "pattern": "["}},
        }
        with pytest.raises(ValueError, match="Invalid params schema"):
            ToolkitInfo(actions={}, params_schema=schema)

    def test_schema_errors_all_reported(self) -> None:
        """Test that every schema problem is listed with its location."""
        schema: JsonSchema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {"a": {"type": 5}, "b": {"minLength": -1}},
        }
        with pytest.raises(ValueError) as exc_info:
            ToolkitInfo(actions={}, params_schema=schema)
        message = str(exc_info.value)
        assert "$.properties.a.type" in message
        assert "$.properties.b.minLength" in message

    @pytest.mark.parametrize(
        "schema",
        [{"type": "object"}, {"type": "object", "additionalProperties": True}],
        ids=["missing", "true"],
    )
    def test_additional_properties_not_false_raises(self, schema: JsonSchema) -> None:
        """Test that additionalProperties must be false."""
        with pytest.raises(ValueError, match="additionalProperties"):
            ToolkitInfo(actions={}, params_schema=schema)

    def test_type_not_object_raises(self) -> None:
        """Test that the top-level type must be object."""
        with pytest.raises(ValueError, match="object"):
            ToolkitInfo(
                actions={},
                params_schema={"type": "array", "additionalProperties": False},
            )


class _MinimalToolkit(Toolkit):
    """Toolkit implementing only the abstract methods."""

    def describe(self, config: Mapping[str, Any]) -> ToolkitInfo:
        return ToolkitInfo(actions={}, params_schema=SCHEMA)

    def run(self, request: ActionRequest) -> ActionResult:
        return ActionResult(status="ok", summary="s")


class TestToolkit:
    """Tests for the Toolkit base class."""

    def test_is_abstract(self) -> None:
        """Test that the base class cannot be instantiated."""
        with pytest.raises(TypeError):
            Toolkit()  # type: ignore[abstract]  # pylint: disable=abstract-class-instantiated

    def test_defaults(self, tmp_path: Path) -> None:
        """Test default prompt_fragments and verify."""
        toolkit = _MinimalToolkit()
        assert toolkit.prompt_fragments() == {}
        assert toolkit.verify(tmp_path) == []
