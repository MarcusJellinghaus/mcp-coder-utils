# Summary — Issue #57: Tool contract `ToolSpec` and `ToolSink`

Part of MarcusJellinghaus/agent-workbench#13 (step 1). Blocks mcp-tools-sql#96 and mcp-workspace#378.

## Goal

mcp-tools-sql and mcp-workspace export their tools as plain data, so FastMCP and a
LangGraph app (agent-workbench) consume the same tools. One small shared contract in
this leaf library, with no dependency on `mcp`, LangChain or Chainlit.

## Architectural / design changes

- **New module `mcp_coder_utils.tool_spec`**, standalone (no internal dependencies),
  separate from `toolkit.py` (mcp-coder's check / fix contract). Public API:
  - `ToolSpec`: frozen dataclass `name`, `description`, `fn`, `args_model`, `group`, `read_only`.
  - `tool_spec(fn, *, group, read_only, name=None, description=None) -> ToolSpec`:
    builds `args_model` once from `fn`'s signature with `pydantic.create_model`.
  - `ToolSink`: `Protocol` with `add(spec) -> None`. Producers write into it.
  - `ToolCollector`: the default `ToolSink`. Keeps insertion order and rejects duplicate names.
- **Data flow:** a producer calls `tool_spec(...)` for each tool and calls `sink.add(spec)`.
  - An MCP server iterates the collector and calls `add_tool(spec.fn, name=spec.name, description=spec.description)`.
  - A non-MCP consumer validates input with `spec.args_model` and calls `spec.fn`.
- **Async:** no flag. Consumers use `inspect.iscoroutinefunction(spec.fn)`, which also works
  through `log_function_call` (`@wraps` plus an `async def` wrapper).
- **Strict signatures:** `tool_spec` rejects anything pydantic would model wrongly without an
  error: `*args` / `**kwargs`, positional-only, `_`-prefixed and unannotated parameters, and
  unresolvable annotations. Each raises `ValueError`.
- **No aliasing:** a parameter that shadows a `BaseModel` attribute (e.g. `schema`) stays a
  plain field; pydantic's shadow warning is suppressed. LangChain passes only keys present
  in the input, so an alias field would be dropped.
- **New runtime dependency:** `pydantic>=2.7,<3`. It is already required by `mcp` and
  `langchain-core` in every consumer. There is no pydantic isolation contract, the same as
  for `jsonschema` in `toolkit.py`.
- **New import-linter contract:** `mcp_coder_utils` must not import `mcp`, `langchain`,
  `langchain_core` or `chainlit`. The library stays framework-neutral.

## Design decisions (KISS)

- One module function, `tool_spec`, rather than a classmethod. This mirrors FastMCP's function-based registration.
- `ToolCollector` stores a single `dict[str, ToolSpec]`. Insertion order gives the ordering,
  and the key gives the duplicate check. `specs` returns `tuple(self._specs.values())`.
- Unresolvable annotations: a single `except Exception` around
  `inspect.signature(fn, eval_str=True)`, re-raised as `ValueError`.
- The generated model's class name is the tool `name`; it only shows up as the schema `title`.
- Extra input keys are ignored (pydantic default); no model config is needed.

## Files created / modified

| Path | Change | Step |
|------|--------|------|
| `src/mcp_coder_utils/tool_spec.py` | **new** — `ToolSpec`, `tool_spec`, `ToolSink`, `ToolCollector` | 1 |
| `tests/test_tool_spec.py` | **new** — unit tests | 1 |
| `pyproject.toml` | add `pydantic>=2.7,<3` to `dependencies` | 1 |
| `tach.toml` | add `[[modules]]` entry `mcp_coder_utils.tool_spec`, `depends_on = []` | 1 |
| `.importlinter` | add forbidden contract `no_agent_frameworks` | 1 |
| `vulture_whitelist.py` | whitelist `ToolSpec` fields read only downstream | 1 |
| `README.md` | new "Tool contract" section with a minimal example incl. FastMCP registration | 2 |
| `docs/architecture/architecture.md` | list `tool_spec.py` in the package layout | 2 |
| `docs/architecture/enforcement.md` | explain the `no_agent_frameworks` contract | 2 |

No folders are created; no existing source module changes.

## Steps

1. [step_1.md](step_1.md) — `tool_spec` module, tests, dependency and config (one commit).
2. [step_2.md](step_2.md) — README and architecture docs (one commit).
