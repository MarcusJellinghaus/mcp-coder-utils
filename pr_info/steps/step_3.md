# Step 3: Implement async support in `log_function_call`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context.
> Implement Step 3: add the async code path to `log_function_call` in `log_utils.py`.
> The async tests from Step 2 must pass after this change.
> Do NOT extract helper functions — duplicate the wrapper body with `await`.

## WHERE

- `src/mcp_coder_utils/log_utils.py`

## WHAT

Two changes inside the `decorator()` function:

### 1. Add `import asyncio` at the top of the file

```python
import asyncio
```

Add it as the first stdlib import (alphabetical order).

### 2. Add `async_wrapper` and the `iscoroutinefunction` branch

Inside `decorator(fn)`, after the existing `wrapper` definition and before
the `return cast(...)` line:

- Define `async def async_wrapper(*args, **kwargs) -> T` with `@wraps(fn)`
- Body is identical to `wrapper` except `result = await fn(*args, **kwargs)`
- After both wrapper definitions, branch on `asyncio.iscoroutinefunction(fn)`:
  - If true: `return cast(Callable[..., T], async_wrapper)`
  - If false: `return cast(Callable[..., T], wrapper)` (existing behavior)

## HOW

- The `iscoroutinefunction` check is on the **original** `fn`, not a wrapped
  version, so it correctly detects async functions
- `@wraps(fn)` on `async_wrapper` preserves `__name__`, `__module__`, etc.
- The existing `return cast(Callable[..., T], wrapper)` line is replaced by
  the branching logic

## ALGORITHM

```python
def decorator(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs) -> T:
        # ... existing sync code, unchanged ...

    @wraps(fn)
    async def async_wrapper(*args, **kwargs) -> T:
        # ... same body as wrapper, but: result = await fn(*args, **kwargs) ...

    if asyncio.iscoroutinefunction(fn):
        return cast(Callable[..., T], async_wrapper)
    return cast(Callable[..., T], wrapper)
```

## DATA

- No new data structures
- Return type unchanged: `Callable[..., T]`
- For async functions, `T` is the awaited return type (mypy handles this)

## Verification

- All 3 async tests from Step 2 pass
- All existing sync tests still pass (no regressions)
- pylint, mypy, pytest all pass

## Commit

`feat(log_utils): support async functions in log_function_call decorator`
