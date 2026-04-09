# Issue #4: Add redaction module with pattern-based env var redaction

## Goal

Create a dedicated `redaction.py` module consolidating all redaction logic, and add `redact_env_vars` for substring-based env var key matching.

## Architectural / Design Changes

### Before

```
src/mcp_coder_utils/
    log_utils.py        ← owns REDACTED_VALUE, RedactableDict, _redact_for_logging (private)
```

Redaction logic lives inside `log_utils.py` as private helpers. No way to redact env vars by substring match.

### After

```
src/mcp_coder_utils/
    redaction.py        ← NEW: owns all redaction logic (public API)
    log_utils.py        ← imports redact_for_logging from redaction.py
```

- **Separation of concerns**: `log_utils.py` focuses on logging; `redaction.py` owns redaction.
- **Two matching strategies coexist**:
  - `redact_for_logging` — exact key match (existing, renamed from private to public)
  - `redact_env_vars` — case-insensitive substring match (new)
- **No re-exports**: `log_utils.__all__` unchanged; clean break confirmed safe.

### Public API (`redaction.__all__`)

| Symbol | Type | Status |
|--------|------|--------|
| `REDACTED_VALUE` | `str` constant | Moved from `log_utils` |
| `RedactableDict` | Type alias | Moved from `log_utils` |
| `redact_for_logging` | Function | Moved + renamed (was `_redact_for_logging`) |
| `SENSITIVE_KEY_PATTERNS` | `frozenset[str]` | New |
| `redact_env_vars` | Function | New |

## Files Created or Modified

| Action | Path |
|--------|------|
| **Create** | `src/mcp_coder_utils/redaction.py` |
| **Modify** | `src/mcp_coder_utils/log_utils.py` |
| **Create** | `tests/test_redaction.py` |
| **Delete** | `tests/test_log_utils_redaction.py` |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Move redaction symbols to `redaction.py`, update `log_utils.py` imports, move+update existing tests | Refactor: extract redaction module from log_utils |
| 2 | Add `SENSITIVE_KEY_PATTERNS` and `redact_env_vars` with tests (TDD) | feat: add redact_env_vars with substring-based key matching |
