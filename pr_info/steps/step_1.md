# Step 1 — `tool_spec` module, tests, dependency and config

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> TDD: write `tests/test_tool_spec.py` first, then `src/mcp_coder_utils/tool_spec.py`, then
> the config changes. Use the MCP tools from `.claude/CLAUDE.md`. Run pylint, pytest
> (`-n auto`), mypy, lint-imports, tach and vulture; all must pass. Format with
> `run_format_code`, then make exactly one commit.

## Preconditions

- `pydantic` (v2, >=2.7) must be importable in the project venv. If it is not,
  write one line to `pr_info/.blocked.txt` and stop.
- If lint-imports fails only because a forbidden module (`langchain`, `langchain_core`,
  `chainlit`, `mcp`) is not installed, and you cannot find a contract option that fixes it,
  write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `tests/test_tool_spec.py` (new)
- `src/mcp_coder_utils/tool_spec.py` (new)
- `pyproject.toml`, `tach.toml`, `.importlinter`, `vulture_whitelist.py` (modify)

## WHAT

```python
__all__ = ["ToolSpec", "tool_spec", "ToolSink", "ToolCollector"]

@dataclass(frozen=True)
class ToolSpec:
    name: str                     # final tool name, e.g. "query_x"
    description: str
    fn: Callable[..., Any]        # sync or async
    args_model: type[BaseModel]   # built once from fn's signature
    group: str                    # fully qualified, e.g. "sql.update"
    read_only: bool

def tool_spec(
    fn: Callable[..., Any],
    *,
    group: str,
    read_only: bool,
    name: str | None = None,
    description: str | None = None,
) -> ToolSpec: ...

def _build_args_model(fn: Callable[..., Any], model_name: str) -> type[BaseModel]: ...

class ToolSink(Protocol):
    def add(self, spec: ToolSpec) -> None: ...

class ToolCollector:
    def __init__(self) -> None: ...            # self._specs: dict[str, ToolSpec] = {}
    def add(self, spec: ToolSpec) -> None: ...  # ValueError on duplicate name
    @property
    def specs(self) -> tuple[ToolSpec, ...]: ...
    def __iter__(self) -> Iterator[ToolSpec]: ...
    def __len__(self) -> int: ...
```

Google-style docstrings with `Args` / `Returns` / `Raises` as in `toolkit.py`
(ruff D and DOC rules apply).

## HOW

- Imports: `inspect`, `warnings`, `collections.abc.Callable`, `collections.abc.Iterator`,
  `dataclasses.dataclass`, `typing.Any`, `typing.Protocol`, `pydantic.BaseModel`,
  `pydantic.create_model`. No internal imports. Do not import `mcp`, LangChain or Chainlit.
- `pyproject.toml`: add `"pydantic>=2.7,<3",` to `[project] dependencies`.
- `tach.toml`: after the `toolkit` entry add
  ```toml
  [[modules]]
  path = "mcp_coder_utils.tool_spec"
  # Tool contract (ToolSpec, ToolSink) for MCP and non-MCP consumers. No internal dependencies.
  depends_on = []
  ```
- `.importlinter`: add a contract in the existing comment style:
  ```ini
  # -----------------------------------------------------------------------------
  # Contract: No MCP or Agent Framework Dependencies
  # -----------------------------------------------------------------------------
  # mcp_coder_utils.tool_spec is consumed by both FastMCP servers and non-MCP
  # apps (LangGraph). The library must stay framework-neutral.
  # -----------------------------------------------------------------------------
  [importlinter:contract:no_agent_frameworks]
  name = No MCP or Agent Framework Dependencies
  type = forbidden
  source_modules =
      mcp_coder_utils
  forbidden_modules =
      mcp
      langchain
      langchain_core
      chainlit
  ```
- `vulture_whitelist.py`: add a block `# Public tool contract fields, read by downstream consumers`
  importing from `mcp_coder_utils.tool_spec` and referencing exactly the symbols vulture
  reports (expected: `ToolSpec.group`, `ToolSpec.read_only`; add others only if reported).

## ALGORITHM

`tool_spec`:
```
name = fn.__name__ if name is None else name; same for description with fn.__doc__
if not name or not description: raise ValueError (say which one)
args_model = _build_args_model(fn, name)
return ToolSpec(name, description, fn, args_model, group, read_only)
```

`_build_args_model`:
```
try: sig = inspect.signature(fn, eval_str=True)
except Exception as exc: raise ValueError(f"cannot resolve signature of {model_name}: {exc}") from exc
for p in sig.parameters.values():
    reject (ValueError, naming the parameter) VAR_POSITIONAL, VAR_KEYWORD, POSITIONAL_ONLY,
    names starting with "_", annotation is inspect.Parameter.empty
    fields[p.name] = (p.annotation, ... if p.default is p.empty else p.default)
with warnings.catch_warnings(): filterwarnings("ignore", message=".*shadows an attribute.*")
    return create_model(model_name, **fields)
```

`ToolCollector.add`: `if spec.name in self._specs: raise ValueError(...)`, else store it.

## DATA

- `tool_spec` returns a frozen `ToolSpec`.
- `args_model` is a pydantic model class. Fields keep `Annotated[..., Field(...)]` metadata
  (description, constraints). Parameters with defaults are optional. Extra keys are ignored.
- `ToolCollector.specs` is a tuple in insertion order. Iteration yields the same order.

## Tests (`tests/test_tool_spec.py`, write first)

Module-level sample tools using `Annotated[int, Field(ge=1, description="...")]`.

- Sync function: spec fields set; `inspect.iscoroutinefunction(spec.fn)` is False.
- Async function: `inspect.iscoroutinefunction(spec.fn)` is True.
- Function wrapped by `log_function_call` (sync and async): spec builds; the descriptions
  survive; async is still detected.
- `args_model.model_validate` accepts good arguments. A violated `ge=1` raises
  `pydantic.ValidationError`.
- `args_model.model_json_schema()` holds the parameter descriptions. A defaulted parameter
  is not in `"required"`, and an unset defaulted parameter validates to its default.
- An extra key is ignored.
- `name` / `description` default to `fn.__name__` / `fn.__doc__`; explicit overrides win.
- `ValueError` for: no docstring, `name=""`, `description=""`.
- One parametrized test with a `ValueError` for each rejected signature: `*args`,
  `**kwargs`, positional-only, `_`-prefixed, unannotated, unresolvable string annotation
  (e.g. `"Missing"`).
- A `schema` parameter: no warning is emitted (`warnings.catch_warnings` with an `error`
  filter); `model_validate({"schema": "x"})` round-trips; the JSON schema property is
  `"schema"` (no alias).
- Collector: `sink: ToolSink = ToolCollector()`; add two specs → `specs`, `list(collector)`
  and `len` reflect insertion order; adding a duplicate name raises `ValueError`.

## Commit

`feat(tool_spec): add ToolSpec and ToolSink tool contract (#57)`
