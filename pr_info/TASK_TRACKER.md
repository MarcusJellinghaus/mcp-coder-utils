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

### Step 1: `fs/line_endings.py` — count, dominant newline, write
See [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code): rename `text.py` → `line_endings.py` and its test file, add `count_line_endings`, `dominant_newline`, `write_text`, update `fs/__init__.py` exports and `architecture.md` package layout
- [x] Quality checks (pylint, pytest, mypy, ruff, vulture, tach, lint-imports, deptry, format) — fix all issues
- [x] Commit message prepared

### Step 2: `fs/path_security.py` — `check_path_within`, stricter `normalize_path`
See [step_2.md](./steps/step_2.md)

- [ ] Implementation (tests + production code): add `_resolve_within` and `check_path_within`, reimplement `normalize_path` on it, export `check_path_within` from `fs/__init__.py`
- [ ] Quality checks (pylint, pytest, mypy, ruff, vulture, tach, lint-imports, deptry, file size, format) — fix all issues
- [ ] Commit message prepared

### Step 3: Docs — "no git knowledge" rule and README `fs` row
See [step_3.md](./steps/step_3.md)

- [ ] Implementation: add rule to `architecture.md` and `.claude/CLAUDE.md`, update README `fs` row
- [ ] Quality checks (pytest, format) — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against `main`, address findings
- [ ] PR summary prepared (incl. `normalize_path` behaviour change for release notes)
