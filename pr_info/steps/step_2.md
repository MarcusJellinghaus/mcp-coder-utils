# Step 2 — Export formatter symbols in `__all__`

**Goal:** Add `CleanFormatter`, `ExtraFieldsFormatter`, `STANDARD_LOG_FIELDS`
to `log_utils.__all__`. They are already imported cross-repo by `mcp_coder`'s
shim, so this makes the public contract match reality (decision #4). Independent
of every other step.

See [summary.md](./summary.md).

## WHERE
- `src/mcp_coder_utils/log_utils.py` (the `__all__` list only)
- `tests/test_log_utils.py`

## WHAT
Change:
```python
__all__ = ["OUTPUT", "log_function_call", "setup_logging"]
```
to (order alphabetical or grouped, keep it tidy):
```python
__all__ = [
    "OUTPUT",
    "STANDARD_LOG_FIELDS",
    "CleanFormatter",
    "ExtraFieldsFormatter",
    "log_function_call",
    "setup_logging",
]
```

## HOW
- No code moves; the three names are already defined in the module. Only the
  `__all__` list changes.

## DATA
- None. Static export list.

## TESTS (write first)
Add `class TestPublicExports` in `tests/test_log_utils.py`:
- Each of `"CleanFormatter"`, `"ExtraFieldsFormatter"`, `"STANDARD_LOG_FIELDS"`
  is in `mcp_coder_utils.log_utils.__all__`.
- `from mcp_coder_utils.log_utils import CleanFormatter, ExtraFieldsFormatter, STANDARD_LOG_FIELDS`
  succeeds and the symbols are not `None`.
- (Optional guard) every name in `__all__` resolves to a real module attribute.

## CHECKS
`mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check`
(`-n auto` + fast-unit exclusions), `mcp__tools-py__run_mypy_check` — all green.

## COMMIT
One commit: `__all__` additions + export tests.
