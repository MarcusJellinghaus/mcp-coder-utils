# Step 4: Integration tests (subprocess_runner real-process tests)

## BLOCKER

**This step requires access to mcp_coder source files**, which are not available
as a reference project. The following file is needed:

- `tests/test_subprocess_runner_real.py` from mcp_coder

**Action needed:** Add p_mcp_coder as a reference project, or provide the file
contents directly.

---

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 4: copy
> `test_subprocess_runner_real.py` from mcp_coder into mcp-coder-utils.
> These are integration tests that exercise real subprocess execution and
> concurrent scenarios. Adjust import paths. Run all checks.

## WHERE

- **Create:** `tests/test_subprocess_runner_real.py`

## WHAT

Copy `mcp_coder:tests/test_subprocess_runner_real.py` and change:

1. All imports → `mcp_coder_utils.subprocess_runner`
2. All `patch()` paths → `mcp_coder_utils.subprocess_runner.*`

These tests exercise real subprocess execution (no mocks) — they complement
the mock-based unit tests from Step 1.

## HOW

- No new source code — tests only
- Tests use real Python subprocesses (sys.executable)

## Verification

- `pylint`, `mypy`, `pytest -n auto` all pass
