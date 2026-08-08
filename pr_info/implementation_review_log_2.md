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

## Round 2 — 2026-08-08

**Findings**:
- *Suggestion* — `src/mcp_coder_utils/log_utils.py:243,259`: two different truthiness tests on the same
  argument (`if log_file:` vs `log_file is None`) mean a falsy-but-not-`None` `log_file` (`""`) skips
  **both** sinks, so `setup_logging("INFO", "")` configures no handlers at all. Pre-change the
  `if/else` fork sent `""` down the console path. Silent no-logging, not an error.
- *Suggestion* — `tests/test_log_utils.py:51-53`: the `clean_root_logger` teardown (added in round 1)
  closes **every** handler on the root logger, including pytest's long-lived `caplog_handler` /
  `report_handler`, which `LoggingPlugin` re-attaches during the teardown phase — then re-adds those
  now-closed instances. A hazard the old inline boilerplate did not have.
- *Suggestion* — downstream heads-up: removing `_is_testing_environment` means `setup_logging` is no
  longer a near-no-op under pytest, so downstream suites calling it un-mocked now get a real stderr
  handler and lowered root level for the rest of the session.
- *Suggestion* — `tests/test_log_utils.py:37-38`: `initial_handlers` / `initial_level` captured at
  fixture-setup time are unconditionally overwritten by `_clean()`; dead state.
- *Suggestion* — `tests/test_log_utils.py:875,958`: uneven handling of the `clean_root_logger()` return.

**Decisions**:
- **Accept** (`log_file=""`) — regression against pre-change behaviour in a leaf library with a stable
  public API contract; one-token fix, silent failure mode removed.
- **Accept** (fixture closes foreign handlers) — defect in code this review cycle introduced last round.
- **Skip** (pytest no-op heads-up) — the intended design per the issue; no change belongs in this repo.
  Surfaced to the user for the companion `mcp_coder` PR / release notes instead.
- **Accept** (dead fixture state) — dead code written last round; trivial cleanup.
- **Skip** (uneven return handling) — cosmetic, correct either way.

**Changes**:
- `src/mcp_coder_utils/log_utils.py` — console-sink condition is now `not log_file`, complementary to
  the file sink's `if log_file:`; no argument value can skip both branches.
- `tests/test_log_utils.py` — `clean_root_logger` teardown detaches all handlers but closes only those
  not identity-present in `initial_handlers`; dead setup-time capture removed, teardown guarded on
  `initial_level is not None`. Added `test_empty_log_file_falls_back_to_console`, verified to fail
  (`assert 0 == 1`) without the fix.

**Checks**: pylint PASS, mypy (strict) PASS, pytest 217/217 PASS.

**Status**: committed
