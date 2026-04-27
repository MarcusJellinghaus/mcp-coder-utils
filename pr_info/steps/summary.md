# Summary: Fix stream_subprocess ignoring options.input_data

**Issue:** #26 — `stream_subprocess()` silently drops `options.input_data`

## Problem

`stream_subprocess()` in `subprocess_streaming.py` never sets `stdin=subprocess.PIPE` and never writes `input_data` to the process. Any caller passing `CommandOptions(input_data=...)` has the input silently ignored.

This breaks the iCoder streaming path for Claude Code CLI, which passes the prompt via stdin.

## Design Changes

**No architectural changes.** This is a localized bug fix within `subprocess_streaming.py`.

The fix aligns `stream_subprocess()` with the existing `_run_subprocess()` pattern in `subprocess_runner.py`, which already handles `input_data` correctly:

| Aspect | Before (broken) | After (fixed) |
|--------|-----------------|---------------|
| `stdin` arg in `Popen` | Missing (inherits parent) | `subprocess.PIPE` when `input_data` set, else `subprocess.DEVNULL` |
| `input_data` handling | Ignored | Written to `process.stdin`, then stdin closed before read loop |

**Note:** Defaulting `stdin` to `DEVNULL` (instead of inheriting parent stdin) when no `input_data` is set is an intentional behavioral change beyond the bug fix — it prevents the child process from inheriting the MCP server's stdin and aligns with `_run_subprocess()`. See issue #26 Decisions table.

**Key constraint:** stdin must be written and closed *before* entering the stdout read loop to avoid deadlock.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder_utils/subprocess_streaming.py` | Add `stdin` arg to `Popen`, write+close `input_data` before read loop |
| `tests/test_subprocess_streaming.py` | Add one happy-path test for stdin piping |

## Implementation Steps

- [Step 1](step_1.md) — Add test + fix for `input_data` piping in `stream_subprocess`
