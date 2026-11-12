# Step 2 — `tool_provider` module: `Toolset`, `StaticToolset`, `ToolsetProvider`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`
> exactly. Write the tests first, then the code. Run the checks listed at the
> end; all must pass. Produce one commit:
> `feat(tool_provider): add toolset provider contract`.

## Precondition

If `src/mcp_coder_utils/tool_verify.py` does not exist (step 1 not done),
write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- Create `src/mcp_coder_utils/tool_provider.py`
- Create `tests/test_tool_provider.py`
- Modify `tach.toml` (new `[[modules]]` entry only)
- Modify `.importlinter` (new contract; `no_agent_frameworks` comment)
- Modify `vulture_whitelist.py`
- Modify `docs/architecture/enforcement.md` (one sentence, "Leaf library" section)

## WHAT

### `src/mcp_coder_utils/tool_provider.py`

```python
"""Toolset provider contract: tool packages loaded as entry-point plugins."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from mcp_coder_utils.tool_spec import ToolSpec
from mcp_coder_utils.tool_verify import VerifyItem

__all__ = ["Toolset", "StaticToolset", "ToolsetProvider"]


class Toolset(Protocol):
    """Tool specs built by a provider, plus the resources behind them."""

    @property
    def specs(self) -> tuple[ToolSpec, ...]: ...   # docstring: names unique within one toolset

    def close(self) -> None: ...                   # docstring: releases the toolset's resources


@dataclass(frozen=True)
class StaticToolset:
    """A toolset that holds no resources; close() does nothing."""

    specs: tuple[ToolSpec, ...]

    def close(self) -> None:
        """Do nothing; a static toolset holds no resources."""


class ToolsetProvider(ABC):
    """Base class for tool packages loaded as plugins.  <-- full rules list here

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        self.config: Mapping[str, Any] = {} if config is None else config

    @abstractmethod
    def build(self) -> Toolset: ...

    def verify(self, *, connect: bool = False) -> list[VerifyItem]:
        return []
```

Docstrings (Google style, as in `toolkit.py`):

- `ToolsetProvider` class docstring holds the full rules list (the only copy
  in code):
  - `config` is the consumer's TOML table as parsed. Unknown keys → `warning`
    row in `verify`, ignored by `build`. Missing / wrongly typed keys →
    `error` row in `verify`, `ValueError` from `build`.
  - `build` raises `ValueError` for every problem it detects, config or
    environment (missing file, unreadable file, missing driver). Any other
    exception is a provider bug.
  - Path values are absolute or start with `~`; a relative path is an error
    (the consumer's working directory is undefined).
  - `build` can be called repeatedly; each returned `Toolset` owns its
    resources and `close` releases them.
  - `build` opens no connection, makes no network call and writes nothing to
    disk; connections open on first use.
  - `verify` never raises for problems it detects. `verify(connect=False)`
    opens no connection and makes no network call. Invariant: no `error` row
    under `connect=False` → `build` on the same config succeeds.
    `verify(connect=True)` returns at least the rows of `verify(connect=False)`.
  - A provider whose `build` can fail overrides `verify`; the default `[]` is
    only right for a provider whose `build` cannot fail.
  - Rows about the provider's own config table are named `config.<key>`;
    other row names (including other `config.*` names) are free.
  - Spec names are unique within one toolset; the consumer detects clashes
    across toolsets.
  - Registration: the consumer names the entry-point group; entry-point name
    = the consumer's config name, value = the provider class.
- `__init__`: "Store the provider's own config table as public `self.config`.
  It only stores; config problems surface in `verify`." Args: `config` —
  `self.config` is always a mapping, empty when none is given.
- `build`: Returns the toolset. Raises `ValueError` for every problem it
  detects. Opens no connection.
- `verify`: Args `connect` — `False` opens no connection and makes no network
  call; `True` may connect. Returns one item per check; empty by default.
  Never raises for problems it detects.

No `@runtime_checkable`, no `typing.override`, no `typing_extensions`.

### `tach.toml`

```toml
[[modules]]
path = "mcp_coder_utils.tool_provider"
# Toolset provider contract (Toolset, StaticToolset, ToolsetProvider). Never
# imports toolkit (keeps jsonschema off consumers' start paths).
depends_on = [
    { path = "mcp_coder_utils.tool_spec" },
    { path = "mcp_coder_utils.tool_verify" },
]
```

### `.importlinter`

Add after `no_agent_frameworks`:

```ini
# -----------------------------------------------------------------------------
# Contract: Tool Provider Contract Stays Light
# -----------------------------------------------------------------------------
# tool_provider and tool_verify sit on consumers' start paths. jsonschema
# (~125 ms, with referencing) belongs to toolkit only. Forbidding toolkit too
# makes a violation name the cause. Runtime check: tests/test_tool_provider.py.
# -----------------------------------------------------------------------------
[importlinter:contract:light_tool_provider]
name = Tool Provider Contract Stays Light
type = forbidden
source_modules =
    mcp_coder_utils.tool_provider
    mcp_coder_utils.tool_verify
forbidden_modules =
    jsonschema
    referencing
    mcp_coder_utils.toolkit
```

Update the `no_agent_frameworks` comment: the contract covers every module of
the package; the tool contracts (`tool_spec`, `tool_provider`, `tool_verify`)
are consumed by FastMCP servers and non-MCP apps (LangGraph, agent-workbench),
so the library must stay framework-neutral. Contract body unchanged.

### `docs/architecture/enforcement.md`

In "Leaf library", after the `no_agent_frameworks` paragraph, add one paragraph:

> `tool_provider` and `tool_verify` sit on consumers' start paths, so they must
> not load `jsonschema` or `referencing`, directly or through `toolkit`.
> Ruleset: the `light_tool_provider` contract in [`.importlinter`](../../.importlinter).

### `vulture_whitelist.py`

Run vulture after the code exists. The `connect` parameter of the base
`ToolsetProvider.verify` is expected to be reported; add it in the file's
existing style:

```python
# Base ToolsetProvider.verify doesn't read `connect`; overriding providers do
from mcp_coder_utils.tool_provider import ToolsetProvider
ToolsetProvider.connect  # noqa
```

Add other members only if vulture reports them. Ruff and vulture must pass.

## Tests (write first) — `tests/test_tool_provider.py`

```python
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


class _MinimalProvider(ToolsetProvider):
    def build(self) -> Toolset:
        return StaticToolset(())


@dataclasses.dataclass(frozen=True)
class _ResourceToolset:
    """Stand-in for a resource-holding toolset such as mcp-tools-sql's SqlToolset."""
    specs: tuple[ToolSpec, ...]
    label: str
    def close(self) -> None: ...
```

Tests:

1. `test_stores_config` — `_MinimalProvider({"a": 1}).config == {"a": 1}`.
2. `test_config_defaults_to_empty_mapping` — `_MinimalProvider().config == {}`.
3. `test_verify_defaults_to_empty` — `verify() == []` and `verify(connect=True) == []`.
4. `test_build_is_abstract` — a subclass without `build` raises `TypeError`
   on instantiation (`# type: ignore[abstract]` on that line).
5. `test_static_toolset_close_does_nothing` — `StaticToolset(()).close() is None`.
6. `test_toolset_protocol_accepts_dataclasses` — mypy-checked assignments:
   ```python
   resource: Toolset = _ResourceToolset(specs=(), label="x")
   static: Toolset = StaticToolset(())
   assert resource.specs == () and static.specs == ()
   ```
7. `test_import_loads_no_heavy_modules` — subprocess test (see ALGORITHM).

## ALGORITHM — subprocess test

```
script = "import json, sys, mcp_coder_utils, mcp_coder_utils.tool_provider; "
         "print(json.dumps({'file': mcp_coder_utils.__file__, 'modules': sorted(sys.modules)}))"
result = execute_command([sys.executable, "-c", script], env={"PYTHONPATH": str(SRC_DIR)})
assert result.return_code == 0, result.stderr
data = json.loads(result.stdout)
assert Path(data["file"]).resolve().is_relative_to(SRC_DIR)   # this checkout, not an installed copy
loaded = [m for m in data["modules"] for x in FORBIDDEN if m == x or m.startswith(x + ".")]
assert loaded == []   # FORBIDDEN = ("mcp", "jsonschema", "referencing", "mcp_coder_utils.toolkit")
```

Use `execute_command` (the `subprocess_isolation` contract forbids importing
`subprocess` in tests). Exact-name matching: a plain `startswith("mcp")`
would match `mcp_coder_utils` itself.

## DATA

- `ToolsetProvider.config: Mapping[str, Any]` (never `None`).
- `ToolsetProvider.build() -> Toolset`; `ToolsetProvider.verify(*, connect=False) -> list[VerifyItem]`.
- `StaticToolset(specs: tuple[ToolSpec, ...])`, frozen.

## Checks

`run_format_code`, `run_pylint_check`, `run_pytest_check(extra_args=["-n", "auto"])`,
`run_mypy_check`, `run_ruff_check`, `run_lint_imports_check`, `run_tach_check`,
`run_vulture_check`.
