# Step 1 — `tool_verify` module: move `VerifyItem` / `VerifyStatus` out of `toolkit`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`
> exactly. Write the tests first, then the code. Run the checks listed at the
> end; all must pass. Produce one commit:
> `refactor(tool_verify): move VerifyItem and VerifyStatus out of toolkit`.

## WHERE

- Create `src/mcp_coder_utils/tool_verify.py`
- Create `tests/test_tool_verify.py`
- Modify `src/mcp_coder_utils/toolkit.py`
- Modify `tests/test_toolkit.py`
- Modify `tach.toml`

## WHAT

### `src/mcp_coder_utils/tool_verify.py`

```python
"""Verification result type shared by toolkits and toolset providers."""

from dataclasses import dataclass
from typing import Literal, get_args

__all__ = ["VerifyItem", "VerifyStatus"]

VerifyStatus = Literal["ok", "warning", "error"]


@dataclass
class VerifyItem:
    """Result of one verification check. Validated at construction only.
    ... (Attributes block unchanged from toolkit.VerifyItem)
    """
    name: str
    status: VerifyStatus
    message: str = ""
    hint: str | None = None

    def __post_init__(self) -> None: ...  # unchanged body from toolkit
```

Move the code verbatim from `toolkit.py`; the only text change is the class
docstring's first line: `Result of one verification check. Validated at
construction only.` (drop "toolkit").

### `src/mcp_coder_utils/toolkit.py`

- Delete the `VerifyStatus = Literal[...]` line and the whole `VerifyItem` class.
- Add `from mcp_coder_utils.tool_verify import VerifyItem, VerifyStatus`
  (first-party import block, after the third-party imports).
- Keep `"VerifyStatus"` and `"VerifyItem"` in `__all__` (that makes it an
  explicit re-export for ruff F401).
- `Literal` and `get_args` stay imported (still used by `ActionStatus` / `ActionResult`).

### `tach.toml`

```toml
[[modules]]
path = "mcp_coder_utils.toolkit"
# Toolkit contract (base class + result types). Re-exports VerifyItem and
# VerifyStatus from tool_verify.
depends_on = [
    { path = "mcp_coder_utils.tool_verify" },
]

[[modules]]
path = "mcp_coder_utils.tool_verify"
# Verification result type (VerifyItem, VerifyStatus). Stdlib only; no jsonschema.
depends_on = []
```

Place the `tool_verify` entry next to `tool_spec`. Do not touch the header
comment here (step 3).

## Tests (write first)

### `tests/test_tool_verify.py`

Move `class TestVerifyItem` from `tests/test_toolkit.py` unchanged (three
tests: defaults, valid status parametrized over `ok`/`warning`/`error`,
unknown status raises `ValueError` matching `"bogus"`). Imports:

```python
"""Tests for tool_verify module."""

import pytest

from mcp_coder_utils.tool_verify import VerifyItem, VerifyStatus
```

### `tests/test_toolkit.py`

- Remove `class TestVerifyItem`.
- Remove `VerifyItem` and `VerifyStatus` from the `from mcp_coder_utils.toolkit import (...)` block.
- Add imports: `import mcp_coder_utils.toolkit as toolkit_module` and
  `from mcp_coder_utils import tool_verify` (the name `toolkit` is already a
  local variable in `TestToolkit`; don't shadow it).
- Add, where `TestVerifyItem` was:

```python
def test_verify_types_reexported_from_tool_verify() -> None:
    """Test that toolkit re-exports the tool_verify objects in __all__."""
    assert toolkit_module.VerifyItem is tool_verify.VerifyItem
    assert toolkit_module.VerifyStatus is tool_verify.VerifyStatus
    assert {"VerifyItem", "VerifyStatus"} <= set(toolkit_module.__all__)
```

If mypy rejects comparing the `VerifyStatus` type alias as a value, compare
`vars(toolkit_module)["VerifyStatus"] is vars(tool_verify)["VerifyStatus"]`
instead.

## ALGORITHM

None — a move plus a re-export.

## DATA

Unchanged: `VerifyItem(name, status, message="", hint=None)`;
`VerifyStatus = Literal["ok", "warning", "error"]`.

## Checks

`run_format_code`, `run_pylint_check`, `run_pytest_check(extra_args=["-n", "auto"])`,
`run_mypy_check`, `run_ruff_check`, `run_lint_imports_check`, `run_tach_check`,
`run_vulture_check`.
