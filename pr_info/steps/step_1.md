# Step 1 — Grandchild regression test + `ignore_cleanup_errors=True`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> TDD: add the test first and run it (it must fail on Windows), then apply the
> one-line fix and run it again (it must pass). Run pylint, pytest
> (`extra_args: ["-n", "auto"]`) and mypy; all must pass. Run the formatter, then
> make one commit. Do not touch any other test in this step.

## WHERE

- `tests/test_subprocess_runner_real.py` — add one test method to the existing class
  `TestRealExecuteCommand`; add `import tempfile` to the imports.
- `src/mcp_coder_utils/subprocess_runner.py` — `_run_subprocess`, STDIO-isolation
  branch, the `with tempfile.TemporaryDirectory() as temp_dir:` line.

## WHAT

### Test (in `TestRealExecuteCommand`)

```python
@pytest.mark.skipif(os.name != "nt", reason="Windows file locking only")
def test_grandchild_holding_output_files_does_not_lose_result(
    self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A grandchild holding stdout/stderr open must not discard the child's result."""
```

### Fix

```python
with tempfile.TemporaryDirectory(
    prefix="mcp_coder_utils_", ignore_cleanup_errors=True
) as temp_dir:
```

Nothing else in `_run_subprocess` changes. The `return` stays inside the `with`.

## HOW

- `monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))` so the leftover directory
  lands under pytest's `tmp_path` instead of `%TEMP%`.
- The grandchild is spawned inside the child's `-c` script string, so the test module
  does not import `subprocess` (import-linter `subprocess_isolation` contract and
  `tools/check_forbidden_calls.py` are unaffected).
- Use `execute_command` with no `timeout_seconds` (default is fine; the child exits
  at once). Do not wait for the grandchild; do not parse logs.

## ALGORITHM (test)

```
monkeypatch tempfile.tempdir -> str(tmp_path)
child = "import subprocess, sys\n"
        "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(5)'],"
        " stdout=sys.stdout, stderr=sys.stderr)\n"
        "print('child done', flush=True)\n"
result = execute_command([sys.executable, "-c", child])
assert result.return_code == 0; "child done" in result.stdout; result.execution_error is None
```

## DATA

- `execute_command` returns `CommandResult`; expected:
  `return_code == 0`, `"child done" in stdout`, `execution_error is None`.
- Without the fix (Windows): `return_code == 1`, `stdout == ""`,
  `execution_error` starts with `"PermissionError: [WinError 32]"`.

## Order of work

1. Add the test. On Windows, run only it
   (`extra_args: ["tests/test_subprocess_runner_real.py", "-k", "grandchild"]`).
   - Expected: fails with the `PermissionError` result above.
   - If on Windows it passes before the fix: write one line to `pr_info/.blocked.txt`
     and stop.
   - On non-Windows it is skipped; continue.
2. Apply the fix. Re-run the test; it must pass on Windows.
3. Run pylint, pytest (`-n auto`), mypy. Run the formatter. Commit.

## Commit message

```
fix(subprocess_runner): ignore temp dir cleanup errors in STDIO isolation (#71)
```
