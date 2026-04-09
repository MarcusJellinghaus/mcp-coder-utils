# Step 1: Extract redaction module from log_utils

> **Context**: See [summary.md](summary.md) for architectural overview.

## Objective

Move existing redaction symbols from `log_utils.py` into a new `redaction.py` module. Rename `_redact_for_logging` → `redact_for_logging` (public API). Update all imports. Split existing tests: move `TestRedactForLogging` and `TestRedactForLoggingTupleKeys` to `test_redaction.py`, move `TestLogFunctionCallWithSensitiveFields` to the existing `test_log_utils.py`.

## LLM Prompt

```
Implement Step 1 of issue #4 (see pr_info/steps/summary.md and pr_info/steps/step_1.md).

Move redaction symbols from log_utils.py to a new redaction.py module:
- Move REDACTED_VALUE, RedactableDict, _redact_for_logging
- Rename _redact_for_logging → redact_for_logging (public)
- Update log_utils.py to import from redaction.py
- Move TestRedactForLogging and TestRedactForLoggingTupleKeys from test_log_utils_redaction.py → test_redaction.py
- Move TestLogFunctionCallWithSensitiveFields from test_log_utils_redaction.py → test_log_utils.py (it tests log_function_call which stays in log_utils.py)
- Delete test_log_utils_redaction.py after both moves
- Run all quality checks (pylint, pytest, mypy)
```

## WHERE

| Action | File |
|--------|------|
| Create | `src/mcp_coder_utils/redaction.py` |
| Modify | `src/mcp_coder_utils/log_utils.py` |
| Create | `tests/test_redaction.py` |
| Modify | `tests/test_log_utils.py` |
| Delete | `tests/test_log_utils_redaction.py` |

## WHAT

### `redaction.py` — moved symbols

```python
__all__ = ["redact_for_logging", "REDACTED_VALUE", "RedactableDict"]

RedactableDict = dict[str | tuple[str, ...], Any]
REDACTED_VALUE = "***"

def redact_for_logging(
    data: RedactableDict,
    sensitive_fields: set[str],
) -> RedactableDict:
    """Create a copy of data with sensitive fields redacted for logging."""
```

### `log_utils.py` — changes

- Remove: `REDACTED_VALUE`, `RedactableDict`, `_redact_for_logging` definitions
- Add: `from mcp_coder_utils.redaction import REDACTED_VALUE, RedactableDict, redact_for_logging`
- Update three call sites: `_redact_for_logging(...)` → `redact_for_logging(...)`
- `__all__` stays unchanged

## HOW

- `log_utils.py` imports `redact_for_logging` from `redaction.py` for internal use
- No re-exports — `log_utils.__all__` never contained redaction symbols

## ALGORITHM

```
1. Use `mcp__tools-py__move_symbol` to move `REDACTED_VALUE`, `RedactableDict`, and `_redact_for_logging` from `log_utils.py` to `redaction.py` (the tool updates imports automatically)
2. In redaction.py: rename `_redact_for_logging` → `redact_for_logging` (public API)
3. In log_utils.py: replace _redact_for_logging → redact_for_logging (3 call sites in log_utils.py)
4. Move `TestRedactForLogging` and `TestRedactForLoggingTupleKeys` from test_log_utils_redaction.py → test_redaction.py, update imports to mcp_coder_utils.redaction, rename _redact_for_logging → redact_for_logging
5. Move `TestLogFunctionCallWithSensitiveFields` from test_log_utils_redaction.py → tests/test_log_utils.py (it tests log_function_call which lives in log_utils.py), update imports as needed
6. Delete test_log_utils_redaction.py after both moves
7. Run pylint, pytest, mypy — all must pass
```

## DATA

No new data structures. `redact_for_logging` signature and behavior are identical to `_redact_for_logging`.

## Commit message

```
refactor: extract redaction module from log_utils

Move REDACTED_VALUE, RedactableDict, _redact_for_logging from log_utils.py
into new redaction.py module. Rename to public API: redact_for_logging.
log_utils.py imports from redaction.py internally.
```
