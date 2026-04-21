# Summary: Add `fs/` subpackage to mcp-coder-utils

**Issue:** #20 — feat: add fs/read_file and fs/path_security modules

## Goal

Create a new `fs/` subpackage under `mcp_coder_utils` containing three stdlib-only
modules that deduplicate utility functions currently copied across multiple mcp-coder
consumer repos (mcp_tools_py, mcp_workspace, mcp_config).

## Architectural Changes

### Before

```
src/mcp_coder_utils/
    __init__.py
    log_utils.py
    redaction.py
    subprocess_runner.py
    subprocess_streaming.py
```

Filesystem-related helpers (file reading, path security, line-ending normalization)
live as local copies inside each consumer repo — duplicated and diverging.

### After

```
src/mcp_coder_utils/
    __init__.py
    log_utils.py
    redaction.py
    subprocess_runner.py
    subprocess_streaming.py
    fs/                          # NEW subpackage
        __init__.py              # re-exports public symbols
        read_file.py             # UTF-8→latin-1 fallback file reader
        path_security.py         # normalize_path() — path traversal prevention
        text.py                  # normalize_line_endings() — CRLF/CR→LF
```

Consumer repos will import from `mcp_coder_utils.fs` instead of maintaining
local copies. This is a **new leaf subpackage** — no new external dependencies,
stdlib only.

### Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Module split | 3 separate files | Security vs I/O vs text — distinct concerns |
| `read_file` version | `encoding` parameter variant | Superset of all existing copies |
| `normalize_path` weakness | Preserved as-is | Pre-existing; out of scope for extraction |
| Dependencies | Zero new deps | All stdlib (`pathlib`, `os`) |
| `__init__.py` exports | Re-export all public symbols | Convenience for consumers |

## Files to Create

| File | Purpose |
|---|---|
| `src/mcp_coder_utils/fs/__init__.py` | Subpackage init, re-exports public API |
| `src/mcp_coder_utils/fs/read_file.py` | `read_file()` function |
| `src/mcp_coder_utils/fs/path_security.py` | `normalize_path()` function |
| `src/mcp_coder_utils/fs/text.py` | `normalize_line_endings()` function |
| `tests/test_fs_read_file.py` | Tests for read_file module |
| `tests/test_fs_path_security.py` | Tests for path_security module |
| `tests/test_fs_text.py` | Tests for text module |

## Files to Modify

| File | Change |
|---|---|
| `docs/architecture/architecture.md` | Add `fs/` subpackage to layout diagram |

## Implementation Order

1. **Step 1** — `fs/text.py` + tests (simplest, no dependencies)
2. **Step 2** — `fs/read_file.py` + tests (I/O with encoding fallback)
3. **Step 3** — `fs/path_security.py` + tests (security boundary logic)
4. **Step 4** — `fs/__init__.py` re-exports + architecture doc update (wiring)
