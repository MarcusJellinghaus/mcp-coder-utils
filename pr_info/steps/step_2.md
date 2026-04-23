# Step 2: Add async tests for `log_function_call`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context.
> Implement Step 2: add async test cases that define the expected behavior.
> These tests will FAIL until Step 3 implements the async wrapper.
> Tests should mirror the existing sync test patterns in `TestLogFunctionCall`
> and `TestLogFunctionCallWithSensitiveFields`.

## WHERE

- `tests/test_log_utils.py` — add new class `TestLogFunctionCallAsync`

## WHAT

Three test methods in `TestLogFunctionCallAsync`:

### `test_log_function_call_async_basic`
- Decorate an `async def` that returns `a + b`
- `await` the decorated function
- Assert result is correct (e.g., `3` for `1 + 2`)
- Assert `mock_logger.debug.call_count == 2` (start + completion)

### `test_log_function_call_async_exception`
- Decorate an `async def` that raises `ValueError`
- Assert exception propagates via `pytest.raises(ValueError)`
- Assert `mock_logger.error.called` is `True`

### `test_log_function_call_async_with_sensitive_fields`
- Decorate with `@log_function_call(sensitive_fields=["token"])`
- Call with `token="secret123"` and `username="user"`
- Assert `"***"` appears in logged params (redacted)
- Assert `"secret123"` does NOT appear in logged params

## HOW

- Import: uses existing imports (`patch`, `MagicMock`, `pytest`, `log_function_call`)
- Pattern: same `with patch("logging.getLogger")` pattern as sync tests
- All test functions are `async def` — pytest-asyncio `auto` mode handles them

## ALGORITHM (test structure)

```
async def test_...:
    with patch("logging.getLogger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        @log_function_call  # or with sensitive_fields
        async def target_func(...): ...
        result = await target_func(...)
        assert result == expected
        assert mock_logger.debug.call_count == 2
```

## DATA

- Input: simple primitives (`int`, `str`)
- Output: assertions on mock call counts and logged parameter strings

## Commit

`test(log_utils): add async tests for log_function_call (expected to fail)`

Note: These tests are expected to fail at this step. They define the contract
that Step 3 must satisfy.
