# Step 2 — README and architecture docs

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly.
> Docs only, no code changes. Keep the text short and follow the Writing style in
> `.claude/CLAUDE.md`. Run pylint, pytest (`-n auto`) and mypy to confirm nothing broke,
> then make exactly one commit.

## Preconditions

- Step 1 is committed (`src/mcp_coder_utils/tool_spec.py` exists). If it does not,
  write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `README.md`
- `docs/architecture/architecture.md`
- `docs/architecture/enforcement.md`

## WHAT / HOW

TDD does not apply (docs only).

### `README.md`

Add a `## Tool contract` section after the `## Toolkit interface` section and before `## Development`:

- One sentence: `mcp_coder_utils.tool_spec` describes tools as plain data, so an MCP server
  and a non-MCP app (e.g. LangGraph) see the same tool.
- A small public API table: `ToolSpec`, `tool_spec`, `ToolSink`, `ToolCollector`.
- Rules, as bullets: `name` / `description` default to `fn.__name__` / `fn.__doc__`, and an
  empty value raises `ValueError`; `group` and `read_only` are required; rejected
  signatures; no aliasing for names like `schema`; extra keys ignored; async detected via
  `inspect.iscoroutinefunction(spec.fn)`; duplicate names in `ToolCollector` raise `ValueError`.
- Minimal example:

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

### `docs/architecture/architecture.md`

Add `tool_spec.py` to the package layout block, between `subprocess_streaming.py` and
`toolkit.py`. Change nothing else.

### `docs/architecture/enforcement.md`

Append one short paragraph to the `## Leaf library` section: `mcp_coder_utils` also stays
framework-neutral. The tool contract is consumed by FastMCP servers and non-MCP apps, so
importing `mcp`, `langchain`, `langchain_core` or `chainlit` would force one framework on
every consumer. Ruleset: the `no_agent_frameworks` contract in
[`.importlinter`](../../.importlinter).

## ALGORITHM / DATA

None (docs only).

## Commit

`docs(tool_spec): document the tool contract (#57)`
