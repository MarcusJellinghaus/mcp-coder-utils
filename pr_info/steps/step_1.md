# Step 1: Add `pytest-asyncio` dependency and async tests for `log_function_call`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context.
> Implement Step 1: add `pytest-asyncio` to test dependencies, enable async test mode,
> and add async test cases that define the expected behavior.
> Tests should be marked with `@pytest.mark.skip` since async support is not yet implemented.
> Tests should mirror the existing sync test patterns in `TestLogFunctionCall`
> and `TestLogFunctionCallWithSensitiveFields`.

## WHERE

- `pyproject.toml`
- `tests/test_log_utils.py` — add new class `TestLogFunctionCallAsync`

## WHAT

### pyproject.toml changes

1. Add `pytest-asyncio` to `[project.optional-dependencies] test`:
   ```toml
   test = [
       "pytest",
       "pytest-asyncio",
       "pytest-xdist",
   ]
   ```

2. Add `asyncio_mode = "auto"` to `[tool.pytest.ini_options]`:
   ```toml
   asyncio_mode = "auto"
   ```

### Test changes

Four test methods in `TestLogFunctionCallAsync`, each marked with
`@pytest.mark.skip(reason="async support not yet implemented")`:

#### `test_log_function_call_async_basic`
- Decorate an `async def` that returns `a + b`
- `await` the decorated function
- Assert result is correct (e.g., `3` for `1 + 2`)
- Assert `mock_logger.debug.call_count == 2` (start + completion)

#### `test_log_function_call_async_exception`
- Decorate an `async def` that raises `ValueError`
- Assert exception propagates via `pytest.raises(ValueError)`
- Assert `mock_logger.error.called` is `True`

#### `test_log_function_call_async_with_sensitive_fields`
- Decorate with `@log_function_call(sensitive_fields=["token"])`
- Call with `token="secret123"` and `username="user"`
- Assert `"***"` appears in logged params (redacted)
- Assert `"secret123"` does NOT appear in logged params

#### `test_log_function_call_async_method_skips_self`
- Define a class with an `async def` method decorated with `@log_function_call`
- Call the method and assert result is correct
- Assert `"self"` does NOT appear in logged params (mirrors sync
  `test_log_function_call_method_skips_self`)

## HOW

- `asyncio_mode = "auto"` means pytest-asyncio automatically handles
  `async def` test functions — no `@pytest.mark.asyncio` needed
- This has zero effect on existing sync tests
- Keep alphabetical ordering in the dependency list
- Import: uses existing imports (`patch`, `MagicMock`, `pytest`, `log_function_call`)
- Pattern: same `with patch("logging.getLogger")` pattern as sync tests
- All test functions are `async def` — pytest-asyncio `auto` mode handles them
- Tests are skipped so pytest passes; Step 2 removes the skip marks

## ALGORITHM (test structure)

```
@pytest.mark.skip(reason="async support not yet implemented")
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

## Verification

- All existing tests still pass (no regressions from adding the dependency)
- New async tests are skipped (not failing)
- pylint, mypy, pytest all pass

## Commit

`feat(test): add pytest-asyncio and async tests for log_function_call`
