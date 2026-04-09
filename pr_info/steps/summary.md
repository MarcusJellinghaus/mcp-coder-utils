# Summary: Extract log_utils (#2)

## Goal

Create the canonical `log_utils` module in `mcp-coder-utils` by consolidating three existing copies (mcp_coder ~340 lines, mcp_tools_py ~150 lines, mcp_workspace ~160 lines). This eliminates triplicated logging setup code and establishes a shared logging foundation.

## Architectural / Design Changes

### Before
- Three independent `log_utils.py` copies across mcp_coder, mcp_tools_py, mcp_workspace
- mcp_coder has the superset; the two server copies are ~90% identical subsets
- Inconsistent imports (`pythonjsonlogger.json` vs `.jsonlogger`), logging styles (f-strings vs lazy `%s`), and feature sets

### After
- Single canonical `log_utils.py` in the leaf library `mcp_coder_utils`
- All consumers will import from `mcp_coder_utils.log_utils` (adoption in separate PRs)
- Consistent API: lazy `%s` formatting, modern `pythonjsonlogger.json.JsonFormatter`, `@overload`-based typing

### Design Decisions (from issue)
1. **Base:** mcp_coder version (strict superset of both server versions)
2. **Removed:** Third-party log suppression (urllib3/github/httpx/httpcore) — application concern, not library
3. **Removed:** "Set all existing logger levels" loop — too aggressive for a library
4. **Kept:** `_is_testing_environment()` — generic, prevents pytest handler conflicts
5. **Kept:** All formatters (`CleanFormatter`, `ExtraFieldsFormatter`), `OUTPUT` level, redaction support
6. **`__all__`:** Only consumer-used symbols: `["OUTPUT", "log_function_call", "setup_logging"]`

### Public API

| Symbol | Type | In `__all__` |
|---|---|---|
| `setup_logging` | function | Yes |
| `log_function_call` | decorator | Yes |
| `OUTPUT` | constant (int=25) | Yes |
| `CleanFormatter` | class | No (internal) |
| `ExtraFieldsFormatter` | class | No (internal) |
| `_redact_for_logging` | function | No (private) |
| `_is_testing_environment` | function | No (private) |
| `REDACTED_VALUE` | constant | No (internal) |
| `STANDARD_LOG_FIELDS` | frozenset | No (internal) |
| `RedactableDict` | type alias | No (internal) |

## Dependencies

Already in `pyproject.toml` — no changes needed:
- `structlog>=23.2.0`
- `python-json-logger>=3.3.0`

## Prerequisite

The mcp_coder repo is **not available as a reference project**. The implementer must either:
1. Have the user provide `src/mcp_coder/utils/log_utils.py`, `tests/utils/test_log_utils.py`, and `tests/utils/test_log_utils_redaction.py` from mcp_coder
2. Or reconstruct from the issue description + the two available server copies (p_tools, p_workspace)

## Files Created / Modified

| Action | Path |
|---|---|
| **Create** | `src/mcp_coder_utils/log_utils.py` |
| **Create** | `tests/test_log_utils.py` |
| **Create** | `tests/test_log_utils_redaction.py` |
| **Modify** | `docs/architecture/architecture.md` |

## Steps Overview

1. **Step 1** — Create `log_utils.py` module + `test_log_utils.py` (core tests)
2. **Step 2** — Add `test_log_utils_redaction.py` (redaction tests)
3. **Step 3** — Update architecture documentation
