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

### Step 1: `tool_verify` module — move `VerifyItem` / `VerifyStatus` out of `toolkit`
See [step_1.md](./steps/step_1.md)

- [x] Implementation: `tests/test_tool_verify.py`, re-export test in `tests/test_toolkit.py`, `src/mcp_coder_utils/tool_verify.py`, `toolkit.py` re-export, `tach.toml` entries
- [x] Quality checks (format, pylint, pytest, mypy, ruff, lint-imports, tach, vulture) — fix all issues
- [x] Commit message prepared: `refactor(tool_verify): move VerifyItem and VerifyStatus out of toolkit`

### Step 2: `tool_provider` module — `Toolset`, `StaticToolset`, `ToolsetProvider`
See [step_2.md](./steps/step_2.md)

- [ ] Implementation: `tests/test_tool_provider.py` (incl. subprocess no-heavy-imports test), `src/mcp_coder_utils/tool_provider.py`, `tach.toml`, `.importlinter` `light_tool_provider` contract + `no_agent_frameworks` comment, `vulture_whitelist.py`, `docs/architecture/enforcement.md` paragraph
- [ ] Quality checks (format, pylint, pytest, mypy, ruff, lint-imports, tach, vulture) — fix all issues
- [ ] Commit message prepared: `feat(tool_provider): add toolset provider contract`

### Step 3: Module dependency graph docs
See [step_3.md](./steps/step_3.md)

- [ ] Implementation: `tach.toml` header comment, `docs/architecture/enforcement.md` "Independence between modules", `docs/architecture/architecture.md` "Package layout"
- [ ] Quality checks (format, pylint, pytest, mypy, ruff, lint-imports, tach, vulture) — fix all issues
- [ ] Commit message prepared: `docs(architecture): describe the real module dependency graph`

### Step 4: Package role wording and sibling-repo lists
See [step_4.md](./steps/step_4.md)

- [ ] Implementation: `.importlinter` `leaf_library`, `docs/architecture/enforcement.md`, `docs/architecture/architecture.md` (role, diagram, rules 2 and 4), `README.md` intro + related repos, `pyproject.toml` description, `.claude/CLAUDE.md`
- [ ] Quality checks (format, pylint, pytest, mypy, ruff, lint-imports, tach, vulture) — fix all issues
- [ ] Commit message prepared: `docs: name tool contracts in the package role; add mcp-tools-sql and agent-workbench`

### Step 5: README — `## Toolset providers` section and Toolkit interface rows
See [step_5.md](./steps/step_5.md)

- [ ] Implementation: `README.md` Toolkit interface rows, new `## Toolset providers` section (Public API, Rules, Registration, Versioning, Example)
- [ ] Quality checks (format, pylint, pytest, mypy, ruff, lint-imports, tach, vulture, file size ≤ 750 lines) — fix all issues
- [ ] Commit message prepared: `docs(readme): document the toolset provider contract`

## Pull Request

- [ ] PR review: review the full branch diff against `main`, address findings
- [ ] PR summary prepared
