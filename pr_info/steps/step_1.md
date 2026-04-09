# Step 1: subprocess_runner module + unit tests

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 1: copy
> `subprocess_runner.py` from p_tools into mcp-coder-utils and bring its
> unit tests. Apply the three edits specified in the issue. Run all checks.

## WHERE

- **Create:** `src/mcp_coder_utils/subprocess_runner.py`
- **Create:** `tests/test_subprocess_runner.py`

## WHAT — Source module

Copy `p_tools:src/mcp_tools_py/utils/subprocess_runner.py` verbatim, then apply
exactly three edits:

1. **Module docstring** — generalize from "MCP server contexts":
   ```python
   """Subprocess execution utilities with process isolation support.

   This module provides functions for executing command-line tools with proper
   timeout handling and STDIO isolation for Python commands.
   """
   ```

2. **`check_tool_missing_error` return message** — drop CLI flag hints:
   ```python
   return (
       f"{tool_name} is not installed in the Python environment "
       f"at {python_path}."
   )
   ```

3. **`__all__`** — add `"prepare_env"` (needed by subprocess_streaming):
   ```python
   __all__ = [
       ...
       "prepare_env",
       ...
   ]
   ```

No other changes to the source module. All functions, dataclasses, constants,
and re-exports remain identical to p_tools.

## WHAT — Public API (preserved from issue)

| Symbol | Type | In `__all__` |
|---|---|---|
| `CommandResult` | dataclass | yes |
| `CommandOptions` | dataclass | yes |
| `execute_subprocess` | function | yes |
| `execute_command` | function | yes |
| `launch_process` | function | yes |
| `format_command` | function | yes |
| `prepare_env` | function | yes (**added**) |
| `check_tool_missing_error` | function | yes |
| `truncate_stderr` | function | yes |
| `MAX_STDERR_IN_ERROR` | constant | yes |
| `CalledProcessError` | re-export | yes |
| `SubprocessError` | re-export | yes |
| `TimeoutExpired` | re-export | yes |
| `is_python_command` | function | no (internal) |
| `get_python_isolation_env` | function | no (internal) |
| `get_utf8_env` | function | no (internal) |

## WHAT — Tests

Copy `p_tools:tests/test_subprocess_runner.py` and change:

1. **All imports** from `mcp_tools_py.utils.subprocess_runner` → `mcp_coder_utils.subprocess_runner`
2. **All `patch()` paths** from `mcp_tools_py.utils.subprocess_runner.*` → `mcp_coder_utils.subprocess_runner.*`
3. **Update `test_check_tool_missing_found`** — assert against the new generic message
   (no `--python-executable` / `--venv-path` text)

## HOW

- No new dependencies. Stdlib only.
- Import linter: module must not import from mcp_coder, mcp_tools_py, mcp_workspace, mcp_config.

## DATA

All return types and data structures are unchanged from p_tools source.

## Verification

- `pylint` passes on new files
- `mypy` passes on new files
- `pytest -n auto` — all tests pass
- `lint-imports` — no forbidden imports
