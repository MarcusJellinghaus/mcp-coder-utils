# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Layout primitives and tach entry
See [step_1.md](./steps/step_1.md)

- [x] Implementation: `tests/test_verify_render_layout.py` (32 tests ported from `test_verify_format_pad.py`), `src/mcp_coder_utils/verify_render.py` layout primitives, `tach.toml` entry
- [x] Quality checks: format, pylint, pytest, mypy, ruff, lint-imports, tach, vulture, deptry, `\bmcp_coder\b` search — fix all issues
- [x] Commit message prepared

### Step 2: `render_rows`, `SectionBuilder`, exact-output test and docs
See [step_2.md](./steps/step_2.md)

- [ ] Implementation: `tests/test_verify_render_builder.py` (18 tests incl. `test_exact_output`), `render_rows` and `SectionBuilder` in `verify_render.py`, `architecture.md` layout, README Modules row, `.scratch/` deleted
- [ ] Quality checks: format, pylint, pytest, mypy, ruff, lint-imports, tach, vulture, deptry, `\bmcp_coder\b` search, 50-test collect count — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against `main`
- [ ] PR summary prepared
