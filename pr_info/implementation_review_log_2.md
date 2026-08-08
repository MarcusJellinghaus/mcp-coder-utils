# Implementation Review Log 2 — Issue #36

Branch: `36-add-console-level-to-setup-logging-for-simultaneous-console-file-output`
Scope: `console_level` parameter for `setup_logging` (simultaneous console + file output).

Starting state: all 4 implementation tasks complete, CI passing, branch behind `origin/main`
(rebase pending — flagged at the end of review log 1).

## Round 1 — 2026-08-08

**Findings**:
- *Critical* — `src/mcp_coder_utils/log_utils.py:226-234`: `setup_logging` removed **and closed** its
  previously installed handlers before calling `_parse_level`. An invalid `log_level`/`console_level`
  therefore tore down a working logging configuration (closed file handle, root logger left with no
  handlers) and *then* raised. Pre-change code validated first. Regression introduced by this branch.
- *Suggestion* — `log_utils.py:226-229`: file-only mode no longer clears foreign root handlers, so a
  handler installed by a dependency would duplicate records to stderr.
- *Suggestion* — `tests/test_log_utils.py`: root-logger save/strip/restore boilerplate duplicated ~11x.
- *Suggestion* — `log_utils.py:187-188`: mixed `Optional[str]` and `str | int | None` in one signature.
- *Suggestion* — `log_utils.py:254,270`: `getLevelName` renders arbitrary ints as `"Level 23"`.

**Decisions**:
- **Accept** (critical) — reorder validation before teardown, plus regression tests.
- **Skip** (foreign handlers) — deliberate design decision per `pr_info/steps/summary.md`
  ("never clobbers a consumer's own handler"), and already documented in the docstring at
  `log_utils.py:214-216`. Not misleading; no change needed.
- **Accept** (test boilerplate) — DRY violation in code this PR introduced; bounded, test-side only.
- **Skip** (`Optional` vs `|`) — cosmetic; working, readable code.
- **Skip** (`"Level 23"`) — cosmetic; DEBUG-level diagnostic message only.

**Changes**:
- `src/mcp_coder_utils/log_utils.py` — moved both `_parse_level` calls above the handler-removal loop,
  with a comment noting the ordering is load-bearing.
- `tests/test_log_utils.py` — added `clean_root_logger` fixture (replaces the boilerplate in 15 places;
  yields a callable so stripping happens in the call phase, after pytest re-attaches `LogCaptureHandler`).
  Added `test_invalid_log_level_keeps_existing_handlers` and
  `test_invalid_console_level_keeps_existing_handlers`; both verified to fail without the fix.

**Checks**: pylint PASS, mypy (strict) PASS, pytest 216/216 PASS.
(`tests/test_subprocess_runner.py::TestSTDIOIsolation` has a known flaky 5s-timeout failure unrelated
to this branch; confirmed flaky by re-run, not touched.)

**Status**: committed
