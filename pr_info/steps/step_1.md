# Step 1 — Status aliases and result types

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` only.
> Follow TDD: write `tests/test_toolkit.py` first, then `src/mcp_coder_utils/toolkit.py`.
> Run pylint, pytest (`-n auto`), mypy, ruff and vulture via the MCP tools; all must
> pass. Run format_code, then make exactly one commit.

## WHERE

- `src/mcp_coder_utils/toolkit.py` (new)
- `tests/test_toolkit.py` (new)

## WHAT

```python
"""Toolkit contract: result types shared by mcp-coder and toolkit implementations."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, get_args

__all__ = [
    "ActionStatus",
    "VerifyStatus",
    "Finding",
    "ActionRequest",
    "ActionResult",
    "VerifyItem",
]

ActionStatus = Literal["ok", "findings", "error", "skipped"]
VerifyStatus = Literal["ok", "warning", "error"]


@dataclass(frozen=True)
class Finding:
    key: str                     # stable, line-insensitive id
    message: str
    path: str | None = None
    rule: str | None = None
    severity: str | None = None  # free string, not validated


@dataclass(frozen=True)
class ActionRequest:
    action: str
    depth: str
    project_dir: Path
    params: Mapping[str, Any]


@dataclass
class ActionResult:
    status: ActionStatus
    summary: str
    findings: list[Finding] = field(default_factory=list)
    fix_text: str = ""
    raw: str = ""

    def __post_init__(self) -> None: ...   # raises ValueError


@dataclass
class VerifyItem:
    name: str
    status: VerifyStatus
    message: str = ""
    hint: str | None = None

    def __post_init__(self) -> None: ...   # raises ValueError
```

Each class gets a Google-style docstring with an `Attributes:` section; each
`__post_init__` gets a docstring with a `Raises:` section (ruff `D`/`DOC`).

## HOW

- Stdlib only in this step.
- Status checks are inline in each `__post_init__`; allowed values come from
  `get_args(ActionStatus)` / `get_args(VerifyStatus)`.

## ALGORITHM

```
ActionResult.__post_init__:
    if status not in get_args(ActionStatus): raise ValueError(unknown status, list allowed)
    if status == "findings" and not findings: raise ValueError("findings" needs findings)
    if status in ("ok", "skipped") and findings: raise ValueError(status must not carry findings)
    # "error": any findings allowed
VerifyItem.__post_init__:
    if status not in get_args(VerifyStatus): raise ValueError(unknown status, list allowed)
```

## DATA

- All constructors return the dataclass instance or raise `ValueError` with a readable
  message naming the offending status.

## Tests (`tests/test_toolkit.py`)

Class-based, `-> None` annotations (mypy `--strict`). Invalid literals need
`# type: ignore[arg-type]`; assignments to frozen fields need `# type: ignore[misc]`.
Parametrized valid-status tests type their parameter as `ActionStatus` /
`VerifyStatus` (not `str`), otherwise mypy reports `arg-type`.

- `TestFinding`
  - assigning to a field (e.g. `finding.key = "x"`) → `dataclasses.FrozenInstanceError`
- `TestActionRequest`
  - assigning to a field (e.g. `request.action = "x"`) → `dataclasses.FrozenInstanceError`
- `TestActionResult`
  - only `status` + `summary` required; defaults `findings == []`, `fix_text == ""`, `raw == ""`
  - unknown status → `ValueError`
  - `"findings"` with empty list → `ValueError`
  - `"findings"` with one `Finding` → ok
  - `"ok"` and `"skipped"` with findings → `ValueError` (parametrize)
  - `"error"` with no findings and with findings → ok (parametrize)
- `TestVerifyItem`
  - defaults `message == ""`, `hint is None`
  - each of `ok`/`warning`/`error` accepted (parametrize)
  - unknown status → `ValueError`
