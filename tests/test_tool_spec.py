"""Tests for tool_spec module."""

import dataclasses
import inspect
import warnings
from collections.abc import Callable
from typing import Annotated, Any

import pytest
from pydantic import Field, ValidationError

from mcp_coder_utils.log_utils import log_function_call
from mcp_coder_utils.tool_spec import ToolCollector, ToolSink, ToolSpec, tool_spec


def query_x(
    limit: Annotated[int, Field(ge=1, description="Maximum rows to return")],
    table: Annotated[str, Field(description="Table to query")] = "items",
) -> str:
    """Query rows from a table."""
    return f"{table}:{limit}"


async def query_async(
    limit: Annotated[int, Field(ge=1, description="Maximum rows to return")],
) -> int:
    """Query rows asynchronously."""
    return limit


@log_function_call
def logged_sync(
    limit: Annotated[int, Field(ge=1, description="Maximum rows to return")],
) -> int:
    """Logged sync tool."""
    return limit


@log_function_call
async def logged_async(
    limit: Annotated[int, Field(ge=1, description="Maximum rows to return")],
) -> int:
    """Logged async tool."""
    return limit


def no_doc(limit: int) -> int:
    return limit


def with_schema(schema: Annotated[str, Field(description="Schema name")]) -> str:
    """Tool with a parameter that shadows a BaseModel attribute."""
    return schema


def _var_positional(*args: int) -> None:
    """Reject *args."""


def _var_keyword(**kwargs: int) -> None:
    """Reject **kwargs."""


def _positional_only(x: int, /) -> None:
    """Reject positional-only."""


def _underscore(_x: int) -> None:
    """Reject _-prefixed."""


def _unannotated(x) -> None:  # type: ignore[no-untyped-def]  # noqa: ANN001
    """Reject unannotated."""


def _unresolvable(x: "Missing") -> None:  # type: ignore[name-defined]  # noqa: F821
    """Reject unresolvable annotation."""


class TestToolSpec:
    """Tests for tool_spec and ToolSpec."""

    def test_sync_function(self) -> None:
        """Test that a sync function builds a spec with all fields set."""
        spec = tool_spec(query_x, group="sql.query", read_only=True)
        assert isinstance(spec, ToolSpec)
        assert spec.name == "query_x"
        assert spec.description == "Query rows from a table."
        assert spec.fn is query_x
        assert spec.group == "sql.query"
        assert spec.read_only is True
        assert not inspect.iscoroutinefunction(spec.fn)

    def test_is_frozen(self) -> None:
        """Test that fields cannot be reassigned."""
        spec = tool_spec(query_x, group="sql.query", read_only=True)
        with pytest.raises(dataclasses.FrozenInstanceError):
            spec.name = "other"  # type: ignore[misc]

    def test_async_function(self) -> None:
        """Test that an async function is detected as a coroutine function."""
        spec = tool_spec(query_async, group="sql.query", read_only=True)
        assert inspect.iscoroutinefunction(spec.fn)

    @pytest.mark.parametrize(
        ("fn", "is_async"), [(logged_sync, False), (logged_async, True)]
    )
    def test_log_function_call_wrapped(
        self, fn: Callable[..., Any], is_async: bool
    ) -> None:
        """Test that log_function_call wrappers keep signature and async-ness."""
        spec = tool_spec(fn, group="g", read_only=False)
        assert inspect.iscoroutinefunction(spec.fn) is is_async
        schema = spec.args_model.model_json_schema()
        assert schema["properties"]["limit"]["description"] == "Maximum rows to return"

    def test_validate_good_arguments(self) -> None:
        """Test that valid arguments pass validation."""
        spec = tool_spec(query_x, group="g", read_only=True)
        args = spec.args_model.model_validate({"limit": 5, "table": "t"})
        assert dict(args) == {"limit": 5, "table": "t"}

    def test_validate_constraint_violation(self) -> None:
        """Test that a violated ge=1 constraint raises ValidationError."""
        spec = tool_spec(query_x, group="g", read_only=True)
        with pytest.raises(ValidationError):
            spec.args_model.model_validate({"limit": 0})

    def test_json_schema_and_defaults(self) -> None:
        """Test descriptions in the schema and handling of defaulted params."""
        spec = tool_spec(query_x, group="g", read_only=True)
        schema = spec.args_model.model_json_schema()
        assert schema["properties"]["limit"]["description"] == "Maximum rows to return"
        assert schema["properties"]["table"]["description"] == "Table to query"
        assert schema["required"] == ["limit"]
        args = spec.args_model.model_validate({"limit": 1})
        assert dict(args) == {"limit": 1, "table": "items"}

    def test_extra_key_ignored(self) -> None:
        """Test that unknown keys are ignored."""
        spec = tool_spec(query_x, group="g", read_only=True)
        args = spec.args_model.model_validate({"limit": 1, "bogus": 2})
        assert dict(args) == {"limit": 1, "table": "items"}

    def test_explicit_name_and_description(self) -> None:
        """Test that explicit name and description override the defaults."""
        spec = tool_spec(
            query_x, group="g", read_only=True, name="other", description="Desc"
        )
        assert spec.name == "other"
        assert spec.description == "Desc"

    @pytest.mark.parametrize(
        ("fn", "kwargs", "match"),
        [
            (no_doc, {}, "description"),
            (query_x, {"name": ""}, "name"),
            (query_x, {"description": ""}, "description"),
        ],
    )
    def test_missing_name_or_description(
        self, fn: Callable[..., Any], kwargs: dict[str, str], match: str
    ) -> None:
        """Test that an empty name or description raises ValueError."""
        with pytest.raises(ValueError, match=match):
            tool_spec(fn, group="g", read_only=True, **kwargs)

    @pytest.mark.parametrize(
        ("fn", "match"),
        [
            (_var_positional, "args"),
            (_var_keyword, "kwargs"),
            (_positional_only, "x"),
            (_underscore, "_x"),
            (_unannotated, "x"),
            (_unresolvable, "signature"),
        ],
    )
    def test_rejected_signatures(self, fn: Callable[..., Any], match: str) -> None:
        """Test that unsupported signatures raise ValueError."""
        with pytest.raises(ValueError, match=match):
            tool_spec(fn, group="g", read_only=True)

    def test_schema_parameter_not_aliased(self) -> None:
        """Test that a 'schema' parameter stays a plain field without warnings."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            spec = tool_spec(with_schema, group="g", read_only=True)
        args = spec.args_model.model_validate({"schema": "x"})
        assert dict(args) == {"schema": "x"}
        json_schema = spec.args_model.model_json_schema()
        assert list(json_schema["properties"]) == ["schema"]


class TestToolCollector:
    """Tests for ToolCollector."""

    def test_insertion_order(self) -> None:
        """Test that specs, iteration and len reflect insertion order."""
        collector = ToolCollector()
        sink: ToolSink = collector
        first = tool_spec(query_x, group="g", read_only=True)
        second = tool_spec(query_async, group="g", read_only=True)
        sink.add(first)
        sink.add(second)
        assert collector.specs == (first, second)
        assert list(collector) == [first, second]
        assert len(collector) == 2

    def test_duplicate_name_rejected(self) -> None:
        """Test that adding a duplicate name raises ValueError."""
        collector = ToolCollector()
        collector.add(tool_spec(query_x, group="g", read_only=True))
        with pytest.raises(ValueError, match="query_x"):
            collector.add(
                tool_spec(query_async, group="g", read_only=True, name="query_x")
            )
