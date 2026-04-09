# Step 2: subprocess_streaming module + unit tests

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 2: copy
> `subprocess_streaming.py` from mcp_coder into mcp-coder-utils and bring
> its unit tests. Adjust import paths. Run all checks.

## WHERE

- **Create:** `src/mcp_coder_utils/subprocess_streaming.py`
- **Create:** `tests/test_subprocess_streaming.py`
- **Source (module):** `p_mcp_coder:src/mcp_coder/utils/subprocess_streaming.py`
- **Source (tests):** `p_mcp_coder:tests/utils/test_subprocess_streaming.py`

## WHAT — Source module

Copy `p_mcp_coder:src/mcp_coder/utils/subprocess_streaming.py` as-is, then:

1. Change import from `mcp_coder.utils.subprocess_runner` → `mcp_coder_utils.subprocess_runner`

No other changes. The module contains:

| Symbol | Type | Notes |
|---|---|---|
| `StreamResult` | class | Iterator wrapper with `.result` property |
| `stream_subprocess` | generator | Real-time stdout streaming with inactivity watchdog |

## WHAT — Tests

Copy `p_mcp_coder:tests/utils/test_subprocess_streaming.py` and change:

1. All imports → `mcp_coder_utils.subprocess_streaming` / `mcp_coder_utils.subprocess_runner`
2. All `patch()` paths → `mcp_coder_utils.*`

The test file contains a single class `TestStreamInactivityWatchdog` with three
methods:

- `test_stream_inactivity_timeout_kills_process`
- `test_stream_active_process_no_timeout`
- `test_stream_subprocess_basic`

**Note:** These are real-process tests, not mock-based. They launch
`sys.executable` and use wall-clock timeouts, so they may have timing
sensitivity on slow CI runners.

## HOW

- `subprocess_streaming` imports `CommandOptions`, `CommandResult`, `prepare_env`
  from `subprocess_runner` (same package — `prepare_env` was added to `__all__`
  in Step 1 for this reason)
- Stdlib only, no new dependencies

## Verification

- `pylint`, `mypy`, `pytest -n auto` all pass
- `lint-imports` — no forbidden imports
