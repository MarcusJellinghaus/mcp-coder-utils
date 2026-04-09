# Step 2: Update architecture documentation

> **Context:** See [summary.md](summary.md) for full overview. This is Step 2 of 2.

## Prompt for LLM

```
Implement Step 2 from pr_info/steps/step_2.md (see pr_info/steps/summary.md for context).
Update the architecture documentation to include log_utils.py in the package layout.
```

## Prerequisite

- Step 1 complete (all code and tests in place, passing)

## WHERE

| Action | Path |
|---|---|
| Modify | `docs/architecture/architecture.md` |

## WHAT

Update the "Package layout" section to add `log_utils.py`:

```
src/mcp_coder_utils/
    __init__.py
    py.typed
    log_utils.py
    subprocess_runner.py
    subprocess_streaming.py
```

Keep alphabetical order (log_utils.py before subprocess_runner.py).

## HOW

Single edit to `docs/architecture/architecture.md` — add the `log_utils.py` line in the package layout code block.

No other documentation changes needed. The module docstring in `log_utils.py` (set in Step 1) serves as the primary documentation.

## Verification

Run all quality checks — all must pass:
- `mcp__tools-py__run_pytest_check`
- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_mypy_check`
