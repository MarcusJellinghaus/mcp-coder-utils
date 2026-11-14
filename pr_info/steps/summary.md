# Summary — #71: temp dir cleanup failure discards a completed result (Windows)

## Problem

`_run_subprocess` (STDIO-isolation branch) writes the child's stdout/stderr into a
`tempfile.TemporaryDirectory()`. On Windows, a grandchild that inherits those file
handles and outlives the child makes the directory cleanup raise
`PermissionError: [WinError 32] ... stderr.txt`. The exception from `__exit__`
replaces the already-built `CompletedProcess`; `execute_subprocess` then reports
`return_code=1`, `stdout=""`, `execution_error="PermissionError: ..."`. The same
cleanup error can also replace an in-flight `TimeoutExpired`, so timeouts were
sometimes reported as `PermissionError` instead of `timed_out=True`.

## Fix

One line in `src/mcp_coder_utils/subprocess_runner.py`:

```python
with tempfile.TemporaryDirectory(prefix="mcp_coder_utils_", ignore_cleanup_errors=True) as temp_dir:
```

- `ignore_cleanup_errors=True` (Python ≥3.10; project requires ≥3.11) stops cleanup
  errors from replacing the return value or the `TimeoutExpired`.
- `prefix="mcp_coder_utils_"` makes leftover directories identifiable in `%TEMP%`.
- The `return` stays inside the `with`. No logging, no `try`/`finally`.

## Architectural / design changes

- **None to the public API.** Signatures, `CommandResult`, `CommandOptions` and
  `__all__` are unchanged. No new module, no new dependency, no new import between
  modules (`tach.toml` / `.importlinter` untouched).
- **Behaviour change (Windows only):** a failed temp dir cleanup is now silent.
  The directory (with `stdout.txt` / `stderr.txt`) may remain in the system temp dir.
  This is by design (KISS); the prefix identifies it. This is the only temp dir the
  library creates.
- **Test contract tightened:** existing tests no longer accept or skip on
  `PermissionError` from this cleanup; the three timeout tests require
  `timed_out=True`.
- **Out of scope:** the pipe-branch grandchild hang (`stdout=PIPE`), tracked in #72.

## Files

| File | Change | Step |
|---|---|---|
| `src/mcp_coder_utils/subprocess_runner.py` | Modify one line (`TemporaryDirectory` args) | 1 |
| `tests/test_subprocess_runner_real.py` | Add Windows-only grandchild test (step 1); remove `PermissionError` branch in `test_timeout_kills_subprocess` (step 2) | 1, 2 |
| `tests/test_subprocess_runner_execute.py` | Remove `PermissionError` branch in `test_execute_command_timeout` | 2 |
| `tests/test_subprocess_runner_isolation.py` | Remove `PermissionError` branch in `test_python_subprocess_timeout`; remove `PermissionError` skip in `test_environment_variable_isolation_integration` | 2 |

No files or folders are created outside `pr_info/steps/`.

## Steps

1. [step_1.md](./step_1.md) — New grandchild regression test + the one-line fix.
2. [step_2.md](./step_2.md) — Remove the `PermissionError` workarounds from four existing tests.

## Not touched

- `test_execute_command_permission_error` (`tests/test_subprocess_runner_execute.py`):
  mocks `Popen` to raise `PermissionError` — a legitimate test.
- `temp_dir` fixture in `tests/conftest.py`: tolerates its own cleanup failure, unrelated.
- The `timed_out` skip in `test_environment_variable_isolation_integration`: a
  different concern, stays.
