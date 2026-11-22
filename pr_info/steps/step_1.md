# Step 1 — Layout primitives and tach entry

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly. Follow TDD:
> 1. Write `tests/test_verify_render_layout.py` first.
> 2. Then create `src/mcp_coder_utils/verify_render.py` with the layout primitives only.
> 3. Then add the tach entry.
>
> Port the code verbatim from reference project `mcp_coder` (`mcp__mcp-workspace__read_reference_file`). Run every check listed in the summary. Make exactly one commit. Do not edit `pr_info/TASK_TRACKER.md`.

## Precondition

Reference file `src/mcp_coder/cli/commands/verify_formatting.py` in reference project `mcp_coder` must define all of:
- `STATUS_SYMBOLS`, `_MARKER_SLOT_WIDTH`, `_LABEL_WIDTH`
- `Row`, `Line`, `_hint`
- `_section_label_width`, `_format_row_prefix`, `_format_row`, `_pad`

If it doesn't, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `tests/test_verify_render_layout.py`: new
- `src/mcp_coder_utils/verify_render.py`: new
- `tach.toml`: new `[[modules]]` entry, placed after `mcp_coder_utils.user_app_data`
- `vulture_whitelist.py`: only if `run_vulture_check` flags something

## WHAT (module content for this step, in source order)

```python
"""Rendering primitives for status-check output.

Tabular rows (label, status marker, value) grouped into titled sections;
the rows of one section share one label width, so their marker and value
columns line up.
"""

from collections.abc import Iterable
from typing import NamedTuple

__all__ = ["STATUS_SYMBOLS", "Line", "Row", "hint_row"]

STATUS_SYMBOLS: dict[str, str] = {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}
_MARKER_SLOT_WIDTH: int = max(len(v) for v in STATUS_SYMBOLS.values())
_LABEL_WIDTH: int = 22  # minimum label width; sections widen automatically

class Row(NamedTuple): label: str; marker: str; value: str; indent: int = 2; wrap: bool = False
Line = Row | str
def hint_row(text: str) -> Row                     # was _hint
def _section_label_width(lines: Iterable[Line]) -> int
def _format_row_prefix(label: str, marker: str, *, indent: int, label_width: int = _LABEL_WIDTH) -> str
def _format_row(label: str, marker: str, value: str, *, indent: int) -> str
def _pad(title: str) -> str
```

- Copy each body verbatim from `verify_formatting.py`. Keep the original formatting of `STATUS_SYMBOLS`, which is multi-line; the one-line form above is only a summary.
- Do not port `keyword`, `re`, `Any`, `cast`, the `claude_mcp_guard` / `mcp_verification` imports, `_KEY_REGEX`, `_looks_like_key`, `_LABEL_MAP`, `_BRANCH_PROTECTION_CHILDREN`, or any `_format_*_section`.
- Docstrings: keep the originals of the ported functions, and use the module docstring above. Make sure no docstring mentions the verify command, `verify.py`, or the import direction between the two old files.

## HOW

- **`tach.toml`:**
  ```toml
  [[modules]]
  path = "mcp_coder_utils.verify_render"
  # Verify output rendering (rows, sections, status markers). Stdlib only.
  depends_on = []
  ```
  The header comment needs no edit: the module is standalone.
- **Tests:** import from `mcp_coder_utils.verify_render`:
  - `_LABEL_WIDTH`, `_MARKER_SLOT_WIDTH`
  - `Line`, `Row`
  - `_format_row`, `_format_row_prefix`, `_pad`, `_section_label_width`
  - `hint_row`

## Tests: port all of mcp_coder `tests/cli/commands/test_verify_format_pad.py`

Port `TestPadHeader`, `TestFormatRowHelpers` and `TestPerSectionColumnRule` with these changes:
- Module docstring: `"""Tests for verify_render header padding and row-layout helpers."""`
- Rename `_hint` to `hint_row` everywhere, including the test names, e.g. `test_hint_row_is_empty_label_and_marker_row` and `test_hint_row_text_starts_at_value_column`.
- `TestFormatRowHelpers` docstring: remove "(Step 1)".
- `test_long_title_not_truncated`: replace the MCP SERVERS literal with a generic ASCII title longer than 71 characters, and assert exact output:
  ```python
  long = "A GENERIC SECTION TITLE THAT IS LONG ENOUGH TO EXCEED THE SEVENTY-FIVE LIMIT"
  assert len(long) > 71
  assert _pad(long) == f"\n=== {long} "
  ```
- No `mcp_coder` imports.

## ALGORITHM (unchanged from source)

```
_section_label_width: max(22, len(label) + indent - 2 for each Row; str ignored)
_format_row_prefix:   " "*indent + label.ljust(width - (indent-2)) + " " + marker.ljust(6) + " "
_format_row:          (prefix at one-row width + value).rstrip()
_pad:                 "\n" + "=== TITLE " + "=" * max(0, 75 - len("=== TITLE "))
```

## DATA

- `Row`: a NamedTuple `(label, marker, value, indent=2, wrap=False)`.
- `Line`: `Row | str`.
- `hint_row(text)` returns `Row("", "", text)`.
- The prefix length is always `label_width + 10`, which is 32 at the default width.

## Done when

- All checks in the summary pass.
- The `\bmcp_coder\b` search over `tests/test_verify_render_*.py` returns no matches.
- One commit, e.g. `feat(verify_render): add verify layout primitives (#84)`.
