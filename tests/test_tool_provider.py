"""Tests for tool_provider module."""

import dataclasses
import json
import sys
from pathlib import Path

import pytest

from mcp_coder_utils.subprocess_runner import execute_command
from mcp_coder_utils.tool_provider import StaticToolset, Toolset, ToolsetProvider
from mcp_coder_utils.tool_spec import ToolSpec

SRC_DIR = Path(__file__).resolve().parents[1] / "src"

# Modules that must not load on the provider contract's import path.
FORBIDDEN = ("mcp", "jsonschema", "referencing", "mcp_coder_utils.toolkit")


class _MinimalProvider(ToolsetProvider):
    """Provider implementing only the abstract method."""

    def build(self) -> Toolset:
        return StaticToolset(())


@dataclasses.dataclass(frozen=True)
class _ResourceToolset:
    """Stand-in for a resource-holding toolset such as mcp-tools-sql's SqlToolset."""

    specs: tuple[ToolSpec, ...]
    label: str

    def close(self) -> None:
        """Release nothing; satisfies the Toolset protocol."""


class TestToolsetProvider:
    """Tests for the ToolsetProvider base class."""

    def test_stores_config(self) -> None:
        """Test that the given config is stored."""
        assert _MinimalProvider({"a": 1}).config == {"a": 1}

    def test_config_defaults_to_empty_mapping(self) -> None:
        """Test that config is an empty mapping when none is given."""
        assert _MinimalProvider().config == {}

    def test_verify_defaults_to_empty(self) -> None:
        """Test that the default verify returns no items."""
        provider = _MinimalProvider()
        assert provider.verify() == []
        assert provider.verify(connect=True) == []

    def test_build_returns_static_toolset(self) -> None:
        """Test that a concrete provider's build returns its toolset."""
        toolset = _MinimalProvider().build()
        assert isinstance(toolset, StaticToolset)
        assert toolset.specs == ()

    def test_build_is_abstract(self) -> None:
        """Test that a subclass without build cannot be instantiated."""

        class _NoBuild(ToolsetProvider):  # pylint: disable=abstract-method
            pass

        with pytest.raises(TypeError):
            _NoBuild()  # type: ignore[abstract]  # pylint: disable=abstract-class-instantiated


class TestToolset:
    """Tests for StaticToolset and the Toolset protocol."""

    def test_static_toolset_close_does_nothing(self) -> None:
        """Test that close on a static toolset does not raise."""
        StaticToolset(()).close()

    def test_toolset_protocol_accepts_dataclasses(self) -> None:
        """Test that frozen dataclasses satisfy the Toolset protocol (mypy-checked)."""
        stand_in = _ResourceToolset(specs=(), label="x")
        assert stand_in.label == "x"
        resource: Toolset = stand_in
        static: Toolset = StaticToolset(())
        assert resource.specs == () and static.specs == ()
        resource.close()
        static.close()


def test_import_loads_no_heavy_modules() -> None:
    """Test that the provider contract loads no MCP, jsonschema or toolkit."""
    script = (
        "import json, sys, mcp_coder_utils, mcp_coder_utils.tool_provider, "
        "mcp_coder_utils.tool_verify; "
        "print(json.dumps({'file': mcp_coder_utils.__file__, "
        "'modules': sorted(sys.modules)}))"
    )
    result = execute_command(
        [sys.executable, "-c", script], env={"PYTHONPATH": str(SRC_DIR)}
    )
    assert result.return_code == 0, result.stderr
    data = json.loads(result.stdout)
    # This checkout, not an installed copy.
    assert Path(data["file"]).resolve().is_relative_to(SRC_DIR)
    loaded = [
        m for m in data["modules"] for x in FORBIDDEN if m == x or m.startswith(x + ".")
    ]
    assert loaded == []
