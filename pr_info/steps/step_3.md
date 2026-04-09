# Step 3: subprocess_streaming module + unit tests

## BLOCKER

**This step requires access to mcp_coder source files**, which are not available
as a reference project. The following files are needed:

- `src/mcp_coder/utils/subprocess_streaming.py` (~120 lines)
- Streaming tests from mcp_coder (TestStreamSubprocess, TestStreamResult,
  TestStreamSubprocessUsesPrepareEnv)

**Action needed:** Add p_mcp_coder as a reference project, or provide the file
contents directly.

---

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 3: copy
> `subprocess_streaming.py` from mcp_coder into mcp-coder-utils and bring
> its unit tests. Adjust import paths. Run all checks.

## WHERE

- **Create:** `src/mcp_coder_utils/subprocess_streaming.py`
- **Create:** `tests/test_subprocess_streaming.py`

## WHAT — Source module

Copy `mcp_coder:src/mcp_coder/utils/subprocess_streaming.py` as-is, then:

1. Change import from `mcp_coder.utils.subprocess_runner` → `mcp_coder_utils.subprocess_runner`

No other changes. The module contains:

| Symbol | Type | Notes |
|---|---|---|
| `StreamResult` | class | Iterator wrapper with `.result` property |
| `stream_subprocess` | generator | Real-time stdout streaming with inactivity watchdog |

## WHAT — Tests

Copy streaming tests from mcp_coder and change:

1. All imports → `mcp_coder_utils.subprocess_streaming` / `mcp_coder_utils.subprocess_runner`
2. All `patch()` paths → `mcp_coder_utils.*`

## HOW

- `subprocess_streaming` imports `CommandOptions`, `CommandResult`, `prepare_env`
  from `subprocess_runner` (same package — `prepare_env` was added to `__all__`
  in Step 1 for this reason)
- Stdlib only, no new dependencies

## Verification

- `pylint`, `mypy`, `pytest -n auto` all pass
- `lint-imports` — no forbidden imports
