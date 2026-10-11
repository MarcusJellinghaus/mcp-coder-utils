# Summary — Issue #41: Add the toolkit base class and result types

Part of epic MarcusJellinghaus/mcp_coder#1192 (section "Toolkit interface", as amended
by the epic's comment and the Decisions table in issue #41). Consumers:
mcp-tools-py#245 (implements `Toolkit`) and mcp_coder#1195 (loads and runs toolkits).

## Goal

A neutral home for the toolkit contract, so toolkits do not depend on mcp-coder.

## Architectural / design changes

- **New flat module `mcp_coder_utils.toolkit`.** It holds only the contract: data types,
  status aliases, JSON Schema validation and an abstract base class. No file reading,
  no `pyproject.toml` parsing, no ecosystem knowledge — config arrives as a plain
  `Mapping`, so non-Python repos work too.
- **New third-party dependency `jsonschema>=4.20`** (draft 2020-12). It is wrapped:
  every `jsonschema` error surfaces as `ValueError`; `jsonschema` types are not part of
  the public API. Validation always uses `Draft202012Validator`, ignoring `$schema`.
- **Validation at construction only.** `ActionResult`, `VerifyItem` and `ToolkitInfo`
  validate in `__post_init__`. They stay mutable (the `command` toolkit merges step
  results), so code that merges results must build a new `ActionResult`.
- **Frozen vs. mutable.** `ActionRequest` and `Finding` are `frozen=True` (shallow:
  `params` may hold a mutable mapping). `ActionResult`, `ToolkitInfo`, `VerifyItem` are
  mutable.
- **No `name`, no `api_version`** on `Toolkit`. The entry-point key in group
  `mcp_coder.toolkits` is the only identifier; compatibility rests on the pinned
  `mcp-coder-utils` version (breaking change = major release here).
- **Status types** `ActionStatus` / `VerifyStatus` are public `Literal` aliases; runtime
  checks derive allowed values via `typing.get_args`, so there is one source of truth.
- **The entry-point group is documented in the README only** — no exported constant.

## Public API (`toolkit.__all__`)

| Name | Kind |
|---|---|
| `ActionStatus` | `Literal["ok", "findings", "error", "skipped"]` |
| `VerifyStatus` | `Literal["ok", "warning", "error"]` |
| `JsonSchema` | `dict[str, Any]` |
| `Finding` | frozen dataclass |
| `ActionRequest` | frozen dataclass |
| `ActionResult` | dataclass, validated |
| `VerifyItem` | dataclass, validated |
| `ToolkitInfo` | dataclass, validated (`params_schema`) |
| `validate_params(schema, params)` | function, raises `ValueError` |
| `Toolkit` | ABC |

## Files created / modified

| Path | Change | Step |
|---|---|---|
| `src/mcp_coder_utils/toolkit.py` | **new** — status aliases, result types | 1 |
| `tests/test_toolkit.py` | **new** — result-type tests | 1 |
| `pyproject.toml` | add `jsonschema>=4.20` (deps), `types-jsonschema` (dev) | 2 |
| `src/mcp_coder_utils/toolkit.py` | add `JsonSchema`, `validate_params`, `ToolkitInfo`, `Toolkit` | 2 |
| `tests/test_toolkit.py` | add schema, `ToolkitInfo` and `Toolkit` tests | 2 |
| `README.md` | new "Toolkit interface" section | 3 |
| `docs/architecture/architecture.md` | add `toolkit.py` to package layout | 3 |
| `vulture_whitelist.py` | only if vulture flags new public names | 1–2 |

No changes to `__init__.py` (consumers import `mcp_coder_utils.toolkit` directly, like
the other flat modules) and no new import-linter contract.

## Steps

1. Status aliases and result types (`Finding`, `ActionRequest`, `ActionResult`, `VerifyItem`) — `step_1.md`
2. JSON Schema validation, `ToolkitInfo` and the `Toolkit` base class — `step_2.md`
3. README and architecture documentation — `step_3.md`

## Checks (every step)

`mcp__mcp-tools-py__run_pylint_check`, `mcp__mcp-tools-py__run_pytest_check`
(`extra_args: ["-n", "auto"]`), `mcp__mcp-tools-py__run_mypy_check` (CI runs
`mypy --strict src tests`), `mcp__mcp-tools-py__run_ruff_check` (Google docstrings,
`Raises:` sections), `mcp__mcp-tools-py__run_vulture_check`. Run
`mcp__mcp-tools-py__run_format_code` before committing.
