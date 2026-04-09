# Summary: Extract subprocess_runner + subprocess_streaming into mcp-coder-utils

## Goal

Land `subprocess_runner` and `subprocess_streaming` as the first real public modules
in `mcp-coder-utils`, eliminating triplicated code across mcp_coder, mcp_tools_py,
and mcp_config.

## Design / Architectural Changes

**Before:** Three near-identical copies of `subprocess_runner.py` (~500 lines each in
mcp_coder and mcp_tools_py, ~350 in mcp_config) with divergent logging styles,
error handling, and missing features. `subprocess_streaming.py` exists only in mcp_coder.

**After:** One canonical copy of each module in `mcp-coder-utils`. Downstream repos
will adopt these in separate Phase 3 PRs.

**Key design decisions (from issue):**

| Decision | Choice | Rationale |
|---|---|---|
| Base source | mcp_tools_py | Has `format_command` + structured logging + `ValueError` for empty commands |
| Logging style | Structured `extra={}` dicts | Machine-parseable, better for a library |
| Empty command | `ValueError` | Fail-fast; empty command is a caller bug |
| `check_tool_missing_error` msg | Generic (no CLI flag hints) | Let consumers add their own hints |
| `__all__` env helpers | Only `prepare_env` exported | Internal helpers have zero external consumers |
| Module docstring | Generalize | Remove "MCP server contexts" framing — this is a shared library |

**Architecture doc update:** Strengthen existing rule 3 ("≥2 real consumers") with
explicit `__all__` guidance — do not export functions with zero external consumers.

## Files Created

| File | Source | Notes |
|---|---|---|
| `src/mcp_coder_utils/subprocess_runner.py` | p_tools `subprocess_runner.py` | 3 edits: docstring, `check_tool_missing_error` msg, `prepare_env` in `__all__` |
| `src/mcp_coder_utils/subprocess_streaming.py` | mcp_coder `subprocess_streaming.py` | Adjust import path only |
| `tests/test_subprocess_runner.py` | p_tools `test_subprocess_runner.py` | Rewrite imports + mock patch paths |
| `tests/test_subprocess_streaming.py` | mcp_coder streaming tests | Rewrite imports |
| `tests/test_subprocess_runner_real.py` | mcp_coder integration tests | Rewrite imports |

## Files Modified

| File | Change |
|---|---|
| `docs/architecture/architecture.md` | Add `__all__` export guidance, update package layout |


