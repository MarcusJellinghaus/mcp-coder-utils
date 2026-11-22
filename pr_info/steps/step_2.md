# Step 2 — `render_rows`, `SectionBuilder`, exact-output test and docs

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly. Step 1 is done: `src/mcp_coder_utils/verify_render.py` has the layout primitives. Follow TDD:
> 1. Write `tests/test_verify_render_builder.py` first.
> 2. Then append `render_rows` and `SectionBuilder` to the module.
> 3. Then update the docs (architecture layout, README row).
>
> Port the code verbatim from reference project `mcp_coder`. Run every check listed in the summary. Delete `.scratch/`. Make exactly one commit. Do not edit `pr_info/TASK_TRACKER.md`.

## WHERE

- `tests/test_verify_render_builder.py`: new
- `src/mcp_coder_utils/verify_render.py`: append after `_pad`
- `vulture_whitelist.py`: only if `run_vulture_check` flags something
- `docs/architecture/architecture.md`: the code block under "Package layout"
- `README.md`: the "Modules" table
- `.scratch/test_probe.py`: temporary, deleted before the commit

## WHAT (added to the module)

```python
import logging
import textwrap
from collections.abc import Iterable, Sequence   # add Sequence

logger = logging.getLogger(__name__)
__all__ = ["STATUS_SYMBOLS", "Line", "Row", "SectionBuilder", "hint_row", "render_rows"]

def render_rows(lines: Sequence[Line]) -> list[str]   # was _render_rows

class SectionBuilder:
    def __init__(self) -> None
    def open(self, title: str) -> None
    def add(self, *lines: Line) -> None
    def close(self) -> None
    def section(self, title: str, lines: Iterable[Line]) -> None
    def __enter__(self) -> "SectionBuilder"
    def __exit__(self, exc_type: type[BaseException] | None, *_rest: object) -> None
```

- Copy the bodies verbatim from mcp_coder `src/mcp_coder/cli/commands/verify_render.py`, including the debug message `"could not flush verify section"` and the `# pylint: disable=broad-exception-caught` comment.
- `close()` must call `render_rows(...)` through the module-global name. Do not alias or bind it.
- Docstrings: keep the originals. Leave the module docstring from step 1 as it is. `add()`'s docstring must not promise wrapping when no section is open.

## ALGORITHM (unchanged from source)

```
render_rows: width = _section_label_width(lines); for item:
    str -> append as-is
    Row -> prefix = _format_row_prefix(..., label_width=width)
           wrap -> extend textwrap.wrap(value, 80, initial_indent=prefix, subsequent_indent=" "*len(prefix))
           else -> append (prefix + value).rstrip()
SectionBuilder: open = close(); print(_pad(title)); buffer=[]; add buffers or prints _format_row/str;
    close renders buffer via render_rows and prints; __exit__ closes, swallowing (debug log) a close error only while an exception is in flight
```

## Tests: port from mcp_coder `tests/cli/commands/test_verify_render.py` and `conftest.py`

**Module-level helpers**, copied verbatim from `conftest.py` lines 26–91:
- `_expected_value_column`
- `_assert_value_at_column`
- `_render` (now calls `render_rows`)
- `_MARKER_RE`
- `_assert_section_aligned`
- `_assert_sections_aligned`

**Then the constants:**
```python
_DEFAULT_COL = _expected_value_column()  # 32
_WIDE_COL = _expected_value_column(label_width=30)  # 40
```

**Imports:**
- `re`
- `from collections.abc import Sequence`
- `from unittest.mock import patch`
- `pytest`
- from `mcp_coder_utils.verify_render`: `_LABEL_WIDTH`, `_MARKER_SLOT_WIDTH`, `STATUS_SYMBOLS`, `Line`, `Row`, `SectionBuilder`, `_format_row`, `_pad`, `hint_row`, `render_rows`

Do not import `Path`, `Any`, `_format_section`, `verify_sections`, `VerifyItem`, `.conftest` or any conftest fixture.

**Port:**
- `TestRenderRows`
- `test_assert_section_aligned_rejects_misaligned_values`
- `TestSectionBuilder`

Rename `_hint` to `hint_row` and `_render_rows` to `render_rows`, including in docstrings. Change `TestRenderRows`'s docstring to ``"""``render_rows`` computes one label width per section."""``.

**Do not port:**
- `test_github_permissions_section_aligned_with_token_hint`
- `TestSectionHelpersThroughBuilder`

**`test_flush_failure_does_not_mask_exception`:**
```python
with patch(
    "mcp_coder_utils.verify_render.render_rows",
    side_effect=ValueError("render failed"),
) as mock_render:
    with pytest.raises(RuntimeError, match="boom"):
        with SectionBuilder() as out:
            out.open("A")
            out.add(Row("a", "[OK]", "x"))
            raise RuntimeError("boom")
mock_render.assert_called_once()
```

**New test `test_exact_output`** (module level, uses `capsys`):

```python
SectionBuilder().section(
    "DEMO",
    [
        Row("Label wider than default", "[OK]", "value"),   # 24 chars -> widens the section
        Row("child", "[WARN]", "nested", 4),
        hint_row("-> fix it"),
        "  [Group]",                                         # freeform str line
        Row("tools", "[ERR]", "alpha, beta, gamma, delta, epsilon, zeta, eta, theta, iota", wrap=True),
    ],
)
assert capsys.readouterr().out == (
    "\n=== DEMO ====...\n"   # literal, one source line per output line
    ...
)
```

- The expected value is one literal string, written as implicitly concatenated pieces, one per output line.
- It starts with the header's leading `"\n"`.
- It contains the `"  [Group]\n"` line and at least two lines for the wrapped row.
- Don't build it from `_pad`, `render_rows` or any other helper.

**Getting the literal:** use a scratch probe that compares against today's mcp_coder.
1. Save `.scratch/test_probe.py`. It renders the same input through `mcp_coder.cli.commands.verify_render.SectionBuilder`, using `Row` and `_hint` from `mcp_coder.cli.commands.verify_formatting`, and through `mcp_coder_utils.verify_render`. It asserts the two captured outputs are equal and prints `repr(output)`.
2. Run it with `mcp__mcp-tools-py__run_pytest_check(extra_args=["-p", "no:cacheprovider", "-n", "0", "-s", ".scratch/test_probe.py"])`. `-n 0` overrides the `-n auto` in `pyproject.toml` addopts; under xdist, `-s` output is not shown.
3. Copy the printed output into the literal.
4. If the outputs differ, first diff the ported module against the reference mcp_coder `verify_render.py` and `verify_formatting.py`. Change the module only if that diff shows a real port error. If the module matches the reference, treat the installed mcp_coder as stale and use the reference source as ground truth. If `mcp_coder.cli.commands.verify_render` can't be imported, write the literal by hand from the layout rules instead.
5. Delete the probe with `mcp__mcp-workspace__delete_directory(".scratch", recursive=True)`.

## Docs

**`architecture.md`:** add `verify_render.py` after `user_app_data.py`, with the same 4-space indent:
```
    user_app_data.py
    verify_render.py
    fs/
```

**`README.md`:** add a row after `tool_verify`:
```
| `verify_render` | Render `verify` output as titled sections of aligned status rows (`SectionBuilder`, `Row`, `hint_row`, `render_rows`, `STATUS_SYMBOLS`). |
```

Leave these unchanged:
- the README intro
- the `pyproject.toml` `description`
- `CLAUDE.md`
- the architecture.md Role paragraph
- `docs/architecture/enforcement.md`: the new module adds no edges between modules

## DATA

- `render_rows` returns `list[str]`, one entry per output line with no trailing newline.
- `SectionBuilder` returns nothing. It prints through `print`.

## Done when

- All checks in the summary pass.
- The `\bmcp_coder\b` search over `tests/test_verify_render_*.py` returns no matches.
- No test was dropped in the port. Collect both files with `run_pytest_check(extra_args=["-n", "0", "--collect-only", "-q", "tests/test_verify_render_layout.py", "tests/test_verify_render_builder.py"])`. The total must equal the ported mcp_coder tests, parametrized cases included, plus `test_exact_output`:
  - `tests/test_verify_render_layout.py`: 32, all of `test_verify_format_pad.py` (unchanged since step 1)
  - `tests/test_verify_render_builder.py`: 18 = `TestRenderRows` 7 + `test_assert_section_aligned_rejects_misaligned_values` 1 + `TestSectionBuilder` 9 + `test_exact_output` 1
  - total: 50. If your own count of the source differs, trust the source and report the mismatch.
- `.scratch/` is gone.
- One commit, e.g. `feat(verify_render): add render_rows and SectionBuilder (#84)`.
