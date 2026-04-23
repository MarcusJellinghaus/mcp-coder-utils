# Step 2: Implement async support in `log_function_call`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context.
> Implement Step 2: add the async code path to `log_function_call` in `log_utils.py`.
> Extract shared logging logic into helper functions to avoid duplicating the wrapper body.
> Remove the `@pytest.mark.skip` markers from the async tests added in Step 1.
> All async tests must pass after this change.

## WHERE

- `src/mcp_coder_utils/log_utils.py`
- `tests/test_log_utils.py` — remove `@pytest.mark.skip` from async tests

## WHAT

### 1. Add `import asyncio` at the top of the file

```python
import asyncio
```

Add it as the first stdlib import (alphabetical order).

### 2. Extract helper functions

Extract the shared logging logic from the current `wrapper` into three private
helper functions, defined inside `decorator()` (they capture `fn` and
`sensitive_set` from closure):

#### `_log_call_start(fn, args, kwargs, sensitive_set)`
Handles everything before `fn()` is called:
- Get `func_name`, `module_name`, `line_no` from `fn`
- Get `func_logger` via `logging.getLogger(module_name)`
- Build `log_params` dict from positional and keyword args
- Skip `self`/`cls` for method calls
- Serialize params (Path to str, JSON-test others)
- Apply redaction for sensitive fields
- Check structured logging, log via structlog if enabled
- Log via `func_logger.debug`
- Return `(func_logger, has_structured, start_time)` — call `time.time()` here

#### `_log_call_success(fn, result, start_time, sensitive_set, func_logger, has_structured)`
Handles the success path after `fn()` returns:
- Calculate `elapsed_ms`
- Prepare result for logging (truncate large results)
- Apply redaction to dict results
- Log via structlog if structured
- Log via `func_logger.debug`

#### `_log_call_error(fn, error, start_time, func_logger, has_structured)`
Handles the error path when `fn()` raises:
- Calculate `elapsed_ms`
- Log via structlog if structured
- Log via `func_logger.error`

### 3. Refactor `wrapper` to use helpers

The existing sync `wrapper` becomes thin:
```python
@wraps(fn)
def wrapper(*args, **kwargs) -> T:
    func_logger, has_structured, start_time = _log_call_start(fn, args, kwargs, sensitive_set)
    try:
        result = fn(*args, **kwargs)
        _log_call_success(fn, result, start_time, sensitive_set, func_logger, has_structured)
        return result
    except Exception as e:
        _log_call_error(fn, e, start_time, func_logger, has_structured)
        raise
```

### 4. Add `async_wrapper`

```python
@wraps(fn)
async def async_wrapper(*args, **kwargs) -> T:
    func_logger, has_structured, start_time = _log_call_start(fn, args, kwargs, sensitive_set)
    try:
        result = await fn(*args, **kwargs)
        _log_call_success(fn, result, start_time, sensitive_set, func_logger, has_structured)
        return result
    except Exception as e:
        _log_call_error(fn, e, start_time, func_logger, has_structured)
        raise
```

### 5. Add `iscoroutinefunction` branch

Replace the existing `return cast(...)` with:
```python
if asyncio.iscoroutinefunction(fn):
    return cast(Callable[..., T], async_wrapper)
return cast(Callable[..., T], wrapper)
```

### 6. Remove skip markers from tests

Remove all `@pytest.mark.skip(reason="async support not yet implemented")`
markers from the `TestLogFunctionCallAsync` test class.

## HOW

- The `iscoroutinefunction` check is on the **original** `fn`, not a wrapped
  version, so it correctly detects async functions
- `@wraps(fn)` on `async_wrapper` preserves `__name__`, `__module__`, etc.
- Helper extraction ensures the logging logic is maintained in one place (DRY)
- Both wrappers differ only by `await` on the `fn()` call

## ALGORITHM

```python
def decorator(fn):
    def _log_call_start(fn, args, kwargs, sensitive_set):
        # ... parameter serialization, redaction, start logging ...
        return func_logger, has_structured, time.time()

    def _log_call_success(fn, result, start_time, sensitive_set, func_logger, has_structured):
        # ... timing, result logging ...

    def _log_call_error(fn, error, start_time, func_logger, has_structured):
        # ... error logging ...

    @wraps(fn)
    def wrapper(*args, **kwargs) -> T:
        func_logger, has_structured, start_time = _log_call_start(fn, args, kwargs, sensitive_set)
        try:
            result = fn(*args, **kwargs)
            _log_call_success(fn, result, start_time, sensitive_set, func_logger, has_structured)
            return result
        except Exception as e:
            _log_call_error(fn, e, start_time, func_logger, has_structured)
            raise

    @wraps(fn)
    async def async_wrapper(*args, **kwargs) -> T:
        func_logger, has_structured, start_time = _log_call_start(fn, args, kwargs, sensitive_set)
        try:
            result = await fn(*args, **kwargs)
            _log_call_success(fn, result, start_time, sensitive_set, func_logger, has_structured)
            return result
        except Exception as e:
            _log_call_error(fn, e, start_time, func_logger, has_structured)
            raise

    if asyncio.iscoroutinefunction(fn):
        return cast(Callable[..., T], async_wrapper)
    return cast(Callable[..., T], wrapper)
```

## DATA

- No new data structures
- Return type unchanged: `Callable[..., T]`
- For async functions, `T` is the awaited return type (mypy handles this)

## Verification

- All 4 async tests from Step 1 pass (skip markers removed)
- All existing sync tests still pass (no regressions)
- pylint, mypy, pytest all pass

## Commit

`feat(log_utils): support async functions in log_function_call decorator`
