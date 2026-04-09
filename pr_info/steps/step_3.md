# Step 3: Integration tests + architecture docs

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 3: copy
> `test_subprocess_runner_real.py` from mcp_coder into mcp-coder-utils
> (adjusting imports), then update architecture docs to reflect the new
> modules and add `__all__` export guidance. Run all checks.

## WHERE

- **Create:** `tests/test_subprocess_runner_real.py`
- **Modify:** `docs/architecture/architecture.md`
- **Source (tests):** `p_mcp_coder:tests/utils/test_subprocess_runner_real.py`

## WHAT — Integration tests

Copy `p_mcp_coder:tests/utils/test_subprocess_runner_real.py` and change:

1. All imports → `mcp_coder_utils.subprocess_runner`
2. All `patch()` paths → `mcp_coder_utils.subprocess_runner.*`

**Important:** `test_empty_command_list` in the mcp_coder source expects `execute_subprocess([])` to return a `CommandResult` with `return_code == 1`. However, the canonical p_tools source raises `ValueError("Command cannot be empty")`. This test must be updated to use `pytest.raises(ValueError, match="Command cannot be empty")` instead of checking the return value.

**Note:** The integration tests import internal symbols `get_python_isolation_env` and `is_python_command` which are not in `__all__`. This is acceptable for tests — Python does not enforce `__all__` for direct imports.

These tests exercise real subprocess execution (no mocks) — they complement
the mock-based unit tests from Step 1.

## WHAT — Architecture docs

Two changes to `docs/architecture/architecture.md`:

### 1. Update package layout section

Replace the current layout block with:

```
src/mcp_coder_utils/
    __init__.py
    py.typed
    subprocess_runner.py
    subprocess_streaming.py
```

Remove the "Real modules land in Phase 2" paragraph — they have landed.

### 2. Add `__all__` export rule


Add a new rule (rule 5) under **Architectural rules**:

> **`__all__` discipline.** Only add a symbol to `__all__` when it has at least
> one external consumer (or is required by a sibling module like
> `subprocess_streaming`). Internal helpers stay unexported. Promote to `__all__`
> when a second consumer appears.

### 3. Update Tests section
Update the "Tests" section to note that some tests exercise real subprocess execution (not purely mock-based), though no special markers or configuration are needed.

## HOW

- No new source code — tests + docs only
- Integration tests use real Python subprocesses (`sys.executable`)

## Verification

- `pylint`, `mypy`, `pytest -n auto` all pass
- `lint-imports` — no forbidden imports
