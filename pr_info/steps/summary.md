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

Inside `decorator()`, after defining the existing sync `wrapper`, we:

1. Define an `async def async_wrapper` that mirrors `wrapper` but uses
   `await fn(*args, **kwargs)` instead of `fn(*args, **kwargs)`
2. Use `asyncio.iscoroutinefunction(fn)` to decide which wrapper to return

The two wrappers share identical logging logic (params, timing, redaction,
structured logging). The duplication is intentional — extracting helpers would
add indirection for a single `await` keyword difference. KISS over DRY here.

### Type Signatures

The existing `@overload` signatures (`Callable[..., T] -> Callable[..., T]`)
already handle async functions correctly because mypy treats `T` as the
awaited return type. No new overloads needed.

### Test Infrastructure

`pytest-asyncio` is added to test dependencies with `asyncio_mode = "auto"`,
which only affects `async def` test functions — zero impact on existing sync tests.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder_utils/log_utils.py` | Add `import asyncio`, add `async_wrapper`, add `iscoroutinefunction` branch |
| `tests/test_log_utils.py` | Add `TestLogFunctionCallAsync` test class (3 tests) |
| `pyproject.toml` | Add `pytest-asyncio` to test deps, add `asyncio_mode = "auto"` |

## Files Created

None.

## Constraints

- Sync behavior must be **identical** — this is a shared library with 4 downstream repos
- `@wraps(fn)` must be preserved on both wrappers
- `asyncio.iscoroutinefunction()` check must see the original `fn`, not a wrapped version
- Public API is additive only — no signature changes
