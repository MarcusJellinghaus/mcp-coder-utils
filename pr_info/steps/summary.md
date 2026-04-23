# Summary: Async Support for `log_function_call` Decorator

**Issue:** #23 — `log_function_call` currently only supports sync functions.
When applied to an `async def`, it returns the coroutine object instead of awaiting it.

## Goal

Make `@log_function_call` work transparently with both sync and async functions,
with no breaking changes to existing sync behavior.

## Design Changes

### Architecture

No new modules, classes, or abstractions. This is a **contained change** within
`log_utils.py` — the decorator gains an async-aware code path.

### How It Works

Inside `decorator()`, we extract the shared logging logic into three private
helper functions to avoid duplicating the wrapper body:

1. `_log_call_start(fn, args, kwargs, sensitive_set)` — handles
   parameter serialization, redaction, and start logging; returns
   `(func_logger, has_structured, start_time)`
2. `_log_call_success(fn, result, start_time, sensitive_set, func_logger, has_structured)` —
   handles timing calculation and result logging
3. `_log_call_error(fn, error, start_time, func_logger, has_structured)` — handles error logging

Both `wrapper` (sync) and `async_wrapper` (async) become thin functions that:
1. Call `_log_call_start(...)` to log parameters
2. Execute `fn(*args, **kwargs)` or `await fn(*args, **kwargs)`
3. Call `_log_call_success(...)` or `_log_call_error(...)` in try/except

The `asyncio.iscoroutinefunction(fn)` check determines which wrapper to return.

### Type Signatures

The existing `@overload` signatures (`Callable[..., T] -> Callable[..., T]`)
already handle async functions correctly because mypy treats `T` as the
awaited return type. No new overloads needed.

Deviation from issue decision: the existing overloads already handle async via
TypeVar inference, so explicit Awaitable overloads are unnecessary.

### Test Infrastructure

`pytest-asyncio` is added to test dependencies with `asyncio_mode = "auto"`,
which only affects `async def` test functions — zero impact on existing sync tests.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder_utils/log_utils.py` | Add `import asyncio`, extract `_log_call_start`/`_log_call_success`/`_log_call_error` helpers, add `async_wrapper`, add `iscoroutinefunction` branch |
| `tests/test_log_utils.py` | Add `TestLogFunctionCallAsync` test class (4 tests) |
| `pyproject.toml` | Add `pytest-asyncio` to test deps, add `asyncio_mode = "auto"` |

## Files Created

None.

## Constraints

- Sync behavior must be **identical** — this is a shared library with 4 downstream repos
- `@wraps(fn)` must be preserved on both wrappers
- `asyncio.iscoroutinefunction()` check must see the original `fn`, not a wrapped version
- Public API is additive only — no signature changes
