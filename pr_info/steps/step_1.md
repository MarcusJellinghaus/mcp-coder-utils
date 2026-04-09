# Step 1: Create log_utils module + all tests

> **Context:** See [summary.md](summary.md) for full overview. This is Step 1 of 2.

## Prompt for LLM

```
Implement Step 1 from pr_info/steps/step_1.md (see pr_info/steps/summary.md for context).
Create the canonical log_utils.py module in mcp_coder_utils and all test files
(log_utils.py, test_log_utils.py, test_log_utils_redaction.py).
Read source files from reference project p_mcp_coder.
```

## Prerequisite

Read source files from reference project `p_mcp_coder` using `mcp__workspace__read_reference_file`:
- `src/mcp_coder/utils/log_utils.py`
- `tests/utils/test_log_utils.py`
- `tests/utils/test_log_utils_redaction.py`

## WHERE

| Action | Path |
|---|---|
| Create | `src/mcp_coder_utils/log_utils.py` |
| Create | `tests/test_log_utils.py` |
| Create | `tests/test_log_utils_redaction.py` |

## WHAT — log_utils.py

Copy mcp_coder's `src/mcp_coder/utils/log_utils.py` with these adjustments:

### Functions / Classes (all from mcp_coder source)

```python
# Module-level
stdlogger = logging.getLogger(__name__)  # resolves to "mcp_coder_utils.log_utils"
T = TypeVar("T")  # used by log_function_call overloads

# Constants
OUTPUT: int = 25  # Custom log level between INFO(20) and WARNING(30)
REDACTED_VALUE: str = "***"
STANDARD_LOG_FIELDS: frozenset[str]
RedactableDict = dict[str | tuple[str, ...], Any]  # type alias

# Public API
def setup_logging(log_level: str, log_file: Optional[str] = None) -> None: ...
def log_function_call(func): ...  # @overload with sensitive_fields variant

# Internal
class CleanFormatter(logging.Formatter): ...
class ExtraFieldsFormatter(logging.Formatter): ...
def _is_testing_environment() -> bool: ...
def _redact_for_logging(params: RedactableDict, sensitive_fields: set[str]) -> RedactableDict: ...
```

### Adjustments from mcp_coder original (6 changes)

1. **Module docstring** → `"Shared logging configuration and utilities."`
2. **Remove** the four `logging.getLogger(...).setLevel(logging.WARNING)` calls for third-party libraries (urllib3, github, httpx, httpcore) near the end of `setup_logging`
3. **Remove** the trailing `stdlogger.debug("Suppressing verbose logs...")` line
4. **Remove** the "set all existing logger levels" loop:
   ```python
   # DELETE this block:
   for name in logging.Logger.manager.loggerDict:
       logger = logging.getLogger(name)
       logger.setLevel(numeric_level)
   ```
5. **Add** `__all__` near the top:
   ```python
   __all__ = ["OUTPUT", "log_function_call", "setup_logging"]
   ```
6. **Add** docstring note to `setup_logging`:
   ```
   Configures structlog globally. Call once at startup;
   repeated calls override the structlog configuration.
   ```

Everything else is a **pure copy** — no other changes.

## WHAT — test_log_utils.py

Copy mcp_coder's `tests/utils/test_log_utils.py` with import path changes:

- `from mcp_coder.utils.log_utils import ...` → `from mcp_coder_utils.log_utils import ...`
- `@patch("mcp_coder.utils.log_utils.stdlogger")` → `@patch("mcp_coder_utils.log_utils.stdlogger")`
- `@patch("mcp_coder.utils.log_utils.structlog")` → `@patch("mcp_coder_utils.log_utils.structlog")`
- Any other `mcp_coder.utils.log_utils` references → `mcp_coder_utils.log_utils`

### Expected test classes (from issue)

- `TestOutputLevel` — verifies OUTPUT level constant
- `TestSetupLogging` — console-only, file logging, invalid level, testing-env handler safety
- `TestLogFunctionCall` — basic, exception, path params, large results, structured logging
- `TestExtraFieldsFormatter` — extra fields formatting
- `TestLogFunctionCallLoggerName` — logger uses calling module's name
- `TestCleanFormatter` — bare CLI output formatting
- `TestSetupLoggingFormatterSelection` — correct formatter chosen per config

## WHAT — test_log_utils_redaction.py

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

## HOW — Integration

- Module uses `logging`, `structlog`, `pythonjsonlogger.json.JsonFormatter`
- `OUTPUT` level registered via `logging.addLevelName(OUTPUT, "OUTPUT")`
- `_is_testing_environment()` detects test environments to avoid clearing pytest's logging handlers
- `setup_logging` configures both stdlib logging and structlog globally
- `log_function_call` is a decorator with `@overload` for optional `sensitive_fields`

## DATA — Key structures

```python
# RedactableDict supports both simple keys and tuple keys for nested redaction
RedactableDict = dict[str | tuple[str, ...], Any]

# STANDARD_LOG_FIELDS — fields that are part of standard log record, not "extra"
STANDARD_LOG_FIELDS: frozenset[str]  # e.g. {"message", "levelname", "name", ...}
```

## Verification

Run all quality checks — all must pass:
- `mcp__tools-py__run_pytest_check`
- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_mypy_check`
