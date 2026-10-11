# Step 2 — JSON Schema validation, `ToolkitInfo` and the `Toolkit` base class

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` only
> (step 1 is done). Follow TDD: extend `tests/test_toolkit.py` first, then
> `src/mcp_coder_utils/toolkit.py` and `pyproject.toml`. Reinstall the package so
> `jsonschema` and `types-jsonschema` are available. Run pylint, pytest (`-n auto`),
> mypy, ruff and vulture via the MCP tools; all must pass. Add a `vulture_whitelist.py`
> entry only if vulture flags a new public name. Run format_code, then make exactly
> one commit.

## WHERE

- `pyproject.toml`
  - `[project] dependencies`: add `"jsonschema>=4.20"`
  - `[project.optional-dependencies] dev`: add `"types-jsonschema"`
- `src/mcp_coder_utils/toolkit.py` (extend)
- `tests/test_toolkit.py` (extend)

## WHAT

```python
from abc import ABC, abstractmethod
from jsonschema import Draft202012Validator

# __all__ += ["JsonSchema", "validate_params", "ToolkitInfo", "Toolkit"]

JsonSchema = dict[str, Any]


def _check_schema(schema: JsonSchema) -> None: ...          # private, raises ValueError


def validate_params(schema: JsonSchema, params: Mapping[str, Any]) -> None: ...
    # raises ValueError


@dataclass
class ToolkitInfo:
    actions: dict[str, list[str]]                 # action -> ordered depths
    params_schema: JsonSchema
    llm_permissions: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    fix_prompts: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None: ...          # raises ValueError


class Toolkit(ABC):
    @abstractmethod
    def describe(self, config: Mapping[str, Any]) -> ToolkitInfo: ...

    @abstractmethod
    def run(self, request: ActionRequest) -> ActionResult: ...

    def prompt_fragments(self) -> dict[str, str]:
        return {}

    def verify(self, project_dir: Path) -> list[VerifyItem]:
        return []
```

## HOW

- `jsonschema` is imported only in `toolkit.py`; its errors never escape — schema and
  params errors are collected with `iter_errors` and raised as one `ValueError`.
- Always `Draft202012Validator`, never the schema's `$schema`.
- `Toolkit` docstring states the contract: `run` never raises for ordinary findings
  (a crash returns status `error`); `describe` receives the toolkit's own config section.

## ALGORITHM

```
_check_schema(schema):
    meta = Draft202012Validator(Draft202012Validator.META_SCHEMA)
    errors = [f"{e.json_path}: {e.message}" for e in meta.iter_errors(schema)]
    if errors: raise ValueError("Invalid params schema:\n" + "\n".join("  " + e for e in errors))
validate_params(schema, params):
    _check_schema(schema)
    errors = [f"{e.json_path}: {e.message}" for e in Draft202012Validator(schema).iter_errors(dict(params))]
    if errors: raise ValueError("Invalid params:\n" + "\n".join("  " + e for e in errors))
ToolkitInfo.__post_init__:
    _check_schema(params_schema)
    if params_schema.get("type") != "object" or params_schema.get("additionalProperties") is not False:
        raise ValueError('params_schema must have "type": "object" and "additionalProperties": false')
```

`dict(params)` lets a non-`dict` top-level `Mapping` pass the `"object"` type check.

## DATA

- `validate_params` returns `None`; on failure the `ValueError` message lists every
  problem, one per line, prefixed with its location (`$`, `$.markers`, ...).
- A malformed schema (in `validate_params` or `ToolkitInfo`) raises one `ValueError`
  listing every schema problem the same way (location in the schema, e.g. `$.type`).
- `Toolkit` defaults: `prompt_fragments() -> {}`, `verify(...) -> []`.

## Tests (`tests/test_toolkit.py`)

Shared valid schema, e.g.
`{"type": "object", "properties": {"markers": {"type": "string"}}, "additionalProperties": False}`.

- `TestValidateParams`
  - valid params → no error
  - unknown key → `ValueError`, message mentions the key
  - wrong type → `ValueError`, message contains `$.markers`
  - malformed schema (e.g. `{"type": 5}`) → `ValueError`
- `TestToolkitInfo`
  - valid schema → constructed; `llm_permissions == {}`, `fix_prompts == {}`
  - malformed schema → `ValueError`
  - schema with two errors (e.g. `{"type": "object", "additionalProperties": False,
    "properties": {"a": {"type": 5}, "b": {"minLength": -1}}}`) → `ValueError` whose
    message contains both locations (`$.properties.a.type`, `$.properties.b.minLength`)
  - `additionalProperties` missing or `True` → `ValueError` (parametrize)
  - top-level `"type"` not `"object"` → `ValueError`
- `TestToolkit`
  - `Toolkit()` → `TypeError` (abstract)
  - minimal subclass implementing `describe`/`run`: `prompt_fragments() == {}`,
    `verify(tmp_path) == []`
