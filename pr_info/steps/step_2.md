# Step 2 — Remove `PermissionError` workarounds from existing tests

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly.
> Step 1 (the `ignore_cleanup_errors=True` fix) is already committed. Edit only the
> four tests listed below; change no production code. Run pylint, pytest
> (`extra_args: ["-n", "auto"]`) and mypy; all must pass. Run the formatter, then
> make one commit.

## Precondition

`src/mcp_coder_utils/subprocess_runner.py` creates the isolation temp dir with
`ignore_cleanup_errors=True`. If it does not: write one line to
`pr_info/.blocked.txt` and stop.

## WHERE / WHAT

Test-only edits. No new functions, no signature changes.

| Test | File | Edit |
|---|---|---|
| `test_execute_command_timeout` | `tests/test_subprocess_runner_execute.py` | Delete the `if ... "PermissionError" ...:` branch and its comments; un-indent the `else` body |
| `test_python_subprocess_timeout` | `tests/test_subprocess_runner_isolation.py` | Same as above |
| `test_timeout_kills_subprocess` | `tests/test_subprocess_runner_real.py` | Delete the `PermissionError` branch and comment; un-indent the `else` body |
| `test_environment_variable_isolation_integration` | `tests/test_subprocess_runner_isolation.py` | Delete the two-line `if ... "PermissionError" ...: pytest.skip(...)` block only; keep the `timed_out` skip above it |

## HOW / ALGORITHM

Resulting assertions:

```
test_execute_command_timeout:     return_code == 1; timed_out is True;
                                  execution_error is not None;
                                  "Process timed out after 1 seconds" in execution_error;
                                  runner_type == "subprocess"
test_python_subprocess_timeout:   timed_out is True; execution_error is not None;
                                  "Process timed out after 1 seconds" in execution_error
test_timeout_kills_subprocess:    timed_out; return_code == 1
env isolation integration:        unchanged except the PermissionError skip is gone
```

Leave alone: `test_execute_command_permission_error` (mocked `Popen` raising
`PermissionError`) and the `temp_dir` fixture in `tests/conftest.py`.

## DATA

`CommandResult` from `execute_subprocess` / `execute_command`; on timeout:
`timed_out=True`, `return_code=1`,
`execution_error="Process timed out after 1 seconds"`.

## Verification

- `search_files` with pattern `PermissionError` in `tests/` must only match
  `test_execute_command_permission_error` and `tests/conftest.py`.
- Full pytest run (`-n auto`) passes. If a timeout test fails with a
  `PermissionError` `execution_error`: write one line to `pr_info/.blocked.txt` and stop.

## Commit message

```
test(subprocess_runner): drop PermissionError workarounds in timeout tests (#71)
```
