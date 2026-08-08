# Step 4 — Add `console_level`: simultaneous file + console logging

**Goal:** The feature. Add the `console_level` parameter, compute the root floor
as `min(log_level, console_level)`, and wire the console sink to fire when
`console_level is not None` **or** `log_file is None`. Depends on Steps 1 & 3.

See [summary.md](./summary.md).

## WHERE
- `src/mcp_coder_utils/log_utils.py`
- `tests/test_log_utils.py`

## WHAT
Final signature:
```python
def setup_logging(
    log_level: str | int,
    log_file: str | None = None,
    console_level: str | int | None = None,
) -> None: ...
```

| `console_level` | Behaviour |
|---|---|
| `None` | Console iff no `log_file` (unchanged). |
| a level | Console handler at that level, in addition to any file handler. |

## HOW
- `numeric_console_level = _parse_level(console_level) if console_level is not None else numeric_level`.
- `root.setLevel(min(numeric_level, numeric_console_level))` — replaces the plain
  `setLevel(numeric_level)` from Step 3.
- Console sink condition becomes `console_level is not None or log_file is None`.
- Console handler `setLevel(numeric_console_level)`; formatter chosen from the
  **console** level: `CleanFormatter` if `numeric_console_level >= OUTPUT`, else
  `ExtraFieldsFormatter`.
- File handler unchanged: `setLevel(numeric_level)` stays (now load-bearing —
  root floor can be below `log_level`; that call keeps sub-threshold records out
  of the file).
- Update the single init message to name whichever sinks were configured.
- Extend the docstring: dual mode, `console_level` without `log_file` (allowed —
  `log_level` then only sets the root floor), stderr default, no `stream=`.

## ALGORITHM (delta over Step 3)
```
numeric_level = _parse_level(log_level)
numeric_console_level = _parse_level(console_level) if console_level is not None else numeric_level
root.setLevel(min(numeric_level, numeric_console_level))
...file sink unchanged...
if console_level is not None or log_file is None:
    ch.setLevel(numeric_console_level)
    ch.setFormatter(CleanFormatter() if numeric_console_level >= OUTPUT else ExtraFieldsFormatter(...))
```

## DATA
- No return value. Root logger may carry a file handler and a console handler
  simultaneously, each at its own level; root at `min(...)`.

## TESTS (write first)
Add `class TestSetupLoggingDualMode` in `tests/test_log_utils.py`:
- **Root floor (required by the issue):** `setup_logging("INFO", console_level="DEBUG")`
  → `root.level == logging.DEBUG` (proves DEBUG records are not pre-filtered at
  the logger). This is the case the motivating `INFO`/`OUTPUT` scenario misses.
- **Dual sinks:** `setup_logging("INFO", str(log_file), console_level=OUTPUT)`
  → one marked `FileHandler` at `INFO`, one marked console `StreamHandler` at
  `OUTPUT` with `CleanFormatter`; `root.level == logging.INFO` (min(20,25)=20).
- **Console formatter from console level:** file + `console_level="DEBUG"`
  → console handler uses `ExtraFieldsFormatter`.
- **`console_level` without `log_file`:** `setup_logging("DEBUG", console_level=OUTPUT)`
  → no file handler, one console handler at `OUTPUT`, `root.level == logging.DEBUG`.
- **Backwards compat:** `setup_logging("INFO")` → console only (no file);
  `setup_logging("INFO", str(log_file))` → file only, no console handler.
- Accept both string and int/`OUTPUT` for `console_level`.

## CHECKS
`mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check`
(`-n auto` + fast-unit exclusions), `mcp__tools-py__run_mypy_check` — all green.

## COMMIT
One commit: `console_level` parameter + dual-mode wiring + docstring + tests.
