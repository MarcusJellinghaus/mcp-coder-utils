# Step 1: Add `pytest-asyncio` and configure async test mode

## LLM Prompt

> Read `pr_info/steps/summary.md` for context.
> Implement Step 1: add `pytest-asyncio` to test dependencies and enable async test mode.
> This is infrastructure-only — no application code changes yet.

## WHERE

- `pyproject.toml`

## WHAT

Two changes to `pyproject.toml`:

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

## HOW

- `asyncio_mode = "auto"` means pytest-asyncio automatically handles
  `async def` test functions — no `@pytest.mark.asyncio` needed
- This has zero effect on existing sync tests
- Keep alphabetical ordering in the dependency list

## Verification

- All existing tests still pass (no regressions from adding the dependency)
- pylint, mypy, pytest all pass

## Commit

`feat(test): add pytest-asyncio dependency for async test support`
