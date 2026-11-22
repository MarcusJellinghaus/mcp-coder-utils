# Step 3 — Docs: architecture layout and README row

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` exactly. Steps 1 and 2 are done: `mcp_coder_utils.verify_render` exists with its full public API. This step changes docs only, so there are no tests to write. Run every check listed in the summary. Make exactly one commit. Do not edit `pr_info/TASK_TRACKER.md`.

## WHERE

- `docs/architecture/architecture.md`: the code block under "Package layout"
- `README.md`: the "Modules" table

## WHAT

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

## HOW

Leave these unchanged:
- the README intro
- the `pyproject.toml` `description`
- `CLAUDE.md`
- the architecture.md Role paragraph
- `docs/architecture/enforcement.md`: the new module adds no edges between modules

## ALGORITHM / DATA

None. This step changes docs only.

## Done when

- All checks in the summary pass.
- One commit, e.g. `docs: add verify_render to architecture layout and README (#84)`.
