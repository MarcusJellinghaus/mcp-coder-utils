# Step 1 — Extract `_parse_level`, widen `log_level` annotation

**Goal:** Pure refactor. No behaviour change. Lift the inline level-parsing
block into a shared helper and widen `log_level` to accept `int` as well as
`str`. This is the foundation for `console_level` in Step 4.

See [summary.md](./summary.md).

## WHERE
- `src/mcp_coder_utils/log_utils.py`
- `tests/test_log_utils.py`

## WHAT
New module-level helper (unexported — internal):

```python
def _parse_level(level: str | int) -> int: ...
```

Widen `setup_logging`'s first parameter annotation:

```python
def setup_logging(log_level: str | int, log_file: Optional[str] = None) -> None: ...
```

(Leave the two-sink restructure and `console_level` for later steps.)

## HOW
- Move the existing `getattr(logging, log_level.upper(), None)` →
  `logging.getLevelName(...)` fallback out of `setup_logging` into
  `_parse_level`. In `setup_logging`, replace the inline block with
  `numeric_level = _parse_level(log_level)`.
- No new imports.

## ALGORITHM (`_parse_level`)
```
if isinstance(level, int): return level
name = level.upper()
num = getattr(logging, name, None)
if not isinstance(num, int): num = logging.getLevelName(name)   # resolves "OUTPUT"
if not isinstance(num, int): raise ValueError(f"Invalid log level: {level}")
return num
```

## DATA
- Returns: `int` numeric level.
- Raises: `ValueError` on an unknown string level (unchanged behaviour;
  `test_invalid_log_level` must still pass).

## TESTS (write first)
Add `class TestParseLevel` in `tests/test_log_utils.py`:
- `_parse_level("INFO") == logging.INFO`
- `_parse_level("output") == OUTPUT` (case-insensitive, custom level)
- `_parse_level(logging.DEBUG) == logging.DEBUG` (int passthrough)
- `_parse_level(OUTPUT) == OUTPUT` (int passthrough of the exported constant)
- `_parse_level("NOPE")` raises `ValueError`
- Existing `test_invalid_log_level` and `test_setup_logging_accepts_output`
  continue to pass unchanged.

## CHECKS
Run and pass before committing:
`mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check`
(with `-n auto` and the fast-unit exclusion markers), `mcp__tools-py__run_mypy_check`.

## COMMIT
One commit: `_parse_level` helper + widened annotation + its tests.
