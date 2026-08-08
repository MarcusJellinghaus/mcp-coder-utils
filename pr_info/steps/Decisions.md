# Decisions — plan review round 1 (Issue #30)

Decisions taken during the plan review of `summary.md` / `step_1.md`.
Issue-level decisions live in the issue's own Decisions table and are not
repeated here.

| # | Topic | Decision | Where applied |
|---|---|---|---|
| 1 | `len=N` unit | **Characters (code points), not bytes.** Plain `len()` semantics kept as-is; the ambiguity is resolved by documenting it, not by changing behaviour. | `step_1.md` § WHAT docstring, `summary.md` rule 7 |
| 2 | `_escape_fragment` docstring | **Full Google-style `Args:` / `Returns:` sections**, like every other function in `redaction.py`. Verified requirement: ruff `DOC201` (enabled via `select = ["D", "DOC"]`, `preview = true`) fails on the one-line form. | `step_1.md` § WHAT |
| 3 | ruff in the step's checks | **Added `mcp__mcp-tools-py__run_ruff_check`.** CI gates on it via the `ruff-docstrings` job, so omitting it moves the failure from local to CI. | `step_1.md` § CHECKS |
| 4 | MCP tool names | Corrected prefix `mcp__tools-py__` → **`mcp__mcp-tools-py__`** for pylint / pytest / mypy. | `step_1.md` § CHECKS |
| 5 | Formatting command | **`mcp__mcp-tools-py__run_format_code`**, per CLAUDE.md. The previously referenced `./tools/format_all.sh` does not exist in this repo. | `step_1.md` § COMMIT |
| 6 | Test structure | **One `@pytest.mark.parametrize` table** for the input → expected cases, matching `TestRedactEnvVars` in the same file; the two absence assertions (`"\n" not in result`, `"SECRETMIDDLE" not in result`) stay as standalone tests. Every test method annotated `-> None` (`mypy --strict` covers `tests/`). | `step_1.md` § TESTS |
| 7 | pylint E731 rationale | **Dropped.** E731 is a ruff/pycodestyle code, not pylint, and is not enabled here. The module-level `def` guidance stays, justified by readability. | `step_1.md` § CHECKS, `summary.md` § KISS notes |
| 8 | "Files created / modified" table listing the plan docs as "create" | **Left as-is** — cosmetic, deliberately not changed. | — |

Not changed by this review: the design, the contract, the worked examples, the
algorithm, and the scope — all confirmed correct against the issue and against
the current `src/mcp_coder_utils/redaction.py` / `tests/test_redaction.py`.
