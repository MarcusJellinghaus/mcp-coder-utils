# Summary — #84 Shared verify rendering primitives (moved from mcp_coder)

Step 1 of epic MarcusJellinghaus/mcp-workspace#408. Moves the generic row/section renderer of `mcp-coder verify` into a new module, `mcp_coder_utils.verify_render`, so `mcp-workspace verify` (mcp-workspace#409) and `mcp-coder verify` (mcp_coder#1444) share one renderer. This repo only adds the module; consumers switch to it later.

## Architectural / design changes

- **New standalone module** `src/mcp_coder_utils/verify_render.py`. Standard library only (`logging`, `textwrap`, `collections.abc`, `typing`). Its tach `depends_on = []`, so it adds no edges between modules.
- **One module from two files.** It merges the generic primitives of mcp_coder `src/mcp_coder/cli/commands/verify_formatting.py` with all of `verify_render.py`. The code is copied verbatim, in source order. Only two names change, and the docstrings become generic.
- **App-specific code stays in mcp_coder:** `_LABEL_MAP`, `_format_section`, `_looks_like_key`, `_KEY_REGEX`, `_BRANCH_PROTECTION_CHILDREN`, and the MCP / Claude / tools-exposed sections. Git/GitHub section logic moves to mcp-workspace in #409.
- **Narrow public API.** Six names go in `__all__`. Every other name is a private internal:

| mcp_coder today | Here | Public |
|---|---|---|
| `STATUS_SYMBOLS` | `STATUS_SYMBOLS` (plain `dict[str, str]`) | yes |
| `Row`, `Line` | `Row`, `Line` | yes |
| `_hint` | `hint_row` | yes |
| `SectionBuilder` | `SectionBuilder` | yes |
| `_render_rows` | `render_rows` | yes |
| `_pad`, `_section_label_width`, `_format_row_prefix`, `_format_row`, `_LABEL_WIDTH`, `_MARKER_SLOT_WIDTH` | same | no |

- **Output must be byte-identical** to today's `mcp-coder verify`:
  - label width at least 22, widened per section
  - marker slot 6, computed once at import
  - header `\n=== TITLE ` padded with `=` to 75 characters
  - `wrap=True` rows wrapped at 80
  - `Row` lines rstripped; `str` lines printed unchanged
  - a `wrap=True` row with an empty value prints nothing
- **`SectionBuilder` behaviour is kept:**
  - it prints when called, so a redirected `sys.stdout` is honoured
  - `add()` with no open section prints each row through `_format_row` and ignores `wrap`
  - `close()` calls `render_rows` through the module-global name
- **Logger name** becomes `mcp_coder_utils.verify_render`. It is used only for a debug message when a section can't be flushed during an exception.
- **Tests** follow the repo's flat layout. No ported test imports `mcp_coder`. An exact-output test pins the byte layout inside this repo.

## Files

| Path | Action | Step |
|---|---|---|
| `src/mcp_coder_utils/verify_render.py` | create | 1 (primitives), 2 (`render_rows`, `SectionBuilder`) |
| `tests/test_verify_render_layout.py` | create | 1 |
| `tests/test_verify_render_builder.py` | create | 2 |
| `tach.toml` | modify: new `[[modules]]` entry | 1 |
| `vulture_whitelist.py` | modify only if `run_vulture_check` flags something | 1, 2 |
| `docs/architecture/architecture.md` | modify: package layout | 3 |
| `README.md` | modify: Modules table row | 3 |

No changes to `.importlinter`, `pyproject.toml`, `CLAUDE.md`, or the one-line repo descriptions.

## Steps

1. `step_1.md`: layout primitives, `tests/test_verify_render_layout.py`, tach entry.
2. `step_2.md`: `render_rows` and `SectionBuilder`, `tests/test_verify_render_builder.py`, exact-output test.
3. `step_3.md`: docs (architecture layout, README row).

## Checks (every step)

Run the formatter, then these `mcp__mcp-tools-py__*` checks:
- `run_pylint_check`
- `run_pytest_check` with `extra_args: ["-n", "auto"]`
- `run_mypy_check`
- `run_ruff_check`
- `run_lint_imports_check`
- `run_tach_check`
- `run_vulture_check`
- `run_deptry_check`

All must pass before the step's single commit.

Steps 1 and 2 also need this search to return no matches: `mcp__mcp-workspace__search_files` with pattern `\bmcp_coder\b` and glob `tests/test_verify_render_*.py`.
