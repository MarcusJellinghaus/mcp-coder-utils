# Step 2: Add redaction tests

> **Context:** See [summary.md](summary.md) for full overview. This is Step 2 of 3.

## Prompt for LLM

```
Implement Step 2 from pr_info/steps/step_2.md (see pr_info/steps/summary.md for context).
Add the redaction test file for log_utils. The module code already exists from Step 1.
The source is mcp_coder's test_log_utils_redaction.py — obtain it from the user if not available.
```

## Prerequisite

- Step 1 complete (log_utils.py and test_log_utils.py exist and pass)
- Obtain mcp_coder source: `tests/utils/test_log_utils_redaction.py`

## WHERE

| Action | Path |
|---|---|
| Create | `tests/test_log_utils_redaction.py` |

## WHAT

Copy mcp_coder's `tests/utils/test_log_utils_redaction.py` with import path changes:

- `from mcp_coder.utils.log_utils import ...` → `from mcp_coder_utils.log_utils import ...`
- Any patch targets: `mcp_coder.utils.log_utils.` → `mcp_coder_utils.log_utils.`

### Expected test classes (from issue)

- `TestRedactForLogging` — tests `_redact_for_logging` with various field types
- `TestRedactForLoggingTupleKeys` — tests tuple-key redaction (nested field paths)
- `TestLogFunctionCallWithSensitiveFields` — tests the `sensitive_fields` overload of `log_function_call`

### Key imports needed

```python
from mcp_coder_utils.log_utils import (
    REDACTED_VALUE,
    _redact_for_logging,
    log_function_call,
)
```

## HOW

Pure test file addition — no production code changes. Tests exercise:
- `_redact_for_logging(params, sensitive_fields)` → returns dict with matching fields replaced by `REDACTED_VALUE`
- `log_function_call(sensitive_fields=frozenset({...}))` → decorator variant that redacts specified fields in log output

## DATA

```python
# _redact_for_logging input/output example:
_redact_for_logging(
    {"api_key": "secret123", "name": "test"},
    frozenset({"api_key"})
) == {"api_key": "***REDACTED***", "name": "test"}

# Tuple keys for nested paths:
_redact_for_logging(
    {("config", "token"): "secret"},
    frozenset({("config", "token")})
) == {("config", "token"): "***REDACTED***"}
```

## Verification

Run all quality checks — all must pass:
- `mcp__tools-py__run_pytest_check`
- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_mypy_check`
