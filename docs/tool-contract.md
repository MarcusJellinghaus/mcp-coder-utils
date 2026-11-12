# Tool contract

`mcp_coder_utils.tool_spec` describes tools as plain data, so an MCP server and a non-MCP app (e.g. LangGraph) see the same tool.

## Public API

| Name | Purpose |
|------|---------|
| `ToolSpec` | Frozen dataclass: `name`, `description`, `fn`, `args_model`, `group`, `read_only`. |
| `tool_spec` | `tool_spec(fn, *, group, read_only, name=None, description=None)` builds a `ToolSpec`; `args_model` is a pydantic model built once from `fn`'s signature. |
| `ToolSink` | Protocol with `add(spec) -> None`. Producers write into it. |
| `ToolCollector` | Default `ToolSink`. Keeps insertion order; iterable, with `len()` and `specs`. |

## Rules

- `name` and `description` default to `fn.__name__` and `fn.__doc__`. An empty value raises `ValueError`.
- `group` (fully qualified, e.g. `"sql.update"`) and `read_only` are required.
- Rejected signatures raise `ValueError`: `*args`, `**kwargs`, positional-only, `_`-prefixed or unannotated parameters, and annotations that cannot be resolved.
- No aliasing: a parameter named like a `BaseModel` attribute (e.g. `schema`) stays a plain field.
- Extra input keys are ignored.
- There is no async flag: consumers check `inspect.iscoroutinefunction(spec.fn)`.
- `ToolCollector.add` raises `ValueError` on a duplicate name.

## Example

```python
from typing import Annotated

from pydantic import Field

from mcp_coder_utils.tool_spec import ToolCollector, ToolSink, tool_spec


def query_x(
    max_rows: Annotated[int, Field(ge=1, description="Maximum rows to return.")] = 100,
) -> str:
    """Run query x."""
    ...


def register(sink: ToolSink) -> None:
    sink.add(tool_spec(query_x, group="sql.query", read_only=True))


collector = ToolCollector()
register(collector)

# MCP consumer (FastMCP)
for spec in collector:
    mcp.add_tool(spec.fn, name=spec.name, description=spec.description)

# Non-MCP consumer
for spec in collector:
    args = spec.args_model.model_validate(raw_args)
    result = spec.fn(**dict(args))  # await it if inspect.iscoroutinefunction(spec.fn)
```
