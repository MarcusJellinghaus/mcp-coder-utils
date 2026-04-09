# Step 2: Add SENSITIVE_KEY_PATTERNS and redact_env_vars

> **Context**: See [summary.md](summary.md) for architectural overview. Step 1 must be completed first.

## Objective

Add `SENSITIVE_KEY_PATTERNS` constant and `redact_env_vars` function to `redaction.py`. Follow TDD: write tests first, then implement.

## LLM Prompt

```
Implement Step 2 of issue #4 (see pr_info/steps/summary.md and pr_info/steps/step_2.md).

Add SENSITIVE_KEY_PATTERNS and redact_env_vars to redaction.py using TDD:
1. Write tests in test_redaction.py first
2. Implement the function in redaction.py
3. Update __all__ in redaction.py
4. Run all quality checks (pylint, pytest, mypy)
```

## WHERE

| Action | File |
|--------|------|
| Modify | `src/mcp_coder_utils/redaction.py` |
| Modify | `tests/test_redaction.py` |

## WHAT

### `redaction.py` — new symbols

```python
SENSITIVE_KEY_PATTERNS: frozenset[str] = frozenset({
    "token", "secret", "password", "credential", "api_key", "access_key",
})

def redact_env_vars(
    env: Mapping[str, str],
    extra_patterns: frozenset[str] | None = None,
) -> dict[str, str]:
    """Redact env var values whose keys contain sensitive substrings (case-insensitive)."""
```

### `redaction.__all__` — updated

```python
__all__ = [
    "redact_for_logging", "redact_env_vars",
    "SENSITIVE_KEY_PATTERNS", "REDACTED_VALUE", "RedactableDict",
]
```

## HOW

- `redact_env_vars` uses `SENSITIVE_KEY_PATTERNS` as default deny list
- `extra_patterns` merges with defaults when provided
- Matching: case-insensitive substring check of each pattern against env var key

## ALGORITHM

```
def redact_env_vars(env, extra_patterns=None):
    patterns = SENSITIVE_KEY_PATTERNS | extra_patterns if extra_patterns else SENSITIVE_KEY_PATTERNS
    result = {}
    for key, value in env.items():
        key_lower = key.lower()
        if any(pattern in key_lower for pattern in patterns):
            result[key] = REDACTED_VALUE
        else:
            result[key] = value
    return result
```

## DATA

- Input: `Mapping[str, str]` (e.g., `os.environ` or any string→string mapping)
- Output: `dict[str, str]` — copy with sensitive values replaced by `"***"`
- `SENSITIVE_KEY_PATTERNS`: `frozenset({"token", "secret", "password", "credential", "api_key", "access_key"})`
- No bare `"key"` — avoids false positives on `KEYBOARD_LAYOUT`, `HKEY_*`, etc.

## Tests to write (TDD — write before implementation)

| Test | Assertion |
|------|-----------|
| `test_redact_env_vars_sensitive_keys` | `GITHUB_TOKEN`, `AWS_SECRET_KEY`, `DB_PASSWORD` → redacted |
| `test_redact_env_vars_case_insensitive` | `github_token`, `GitHub_Token` → redacted |
| `test_redact_env_vars_safe_keys_unchanged` | `PATH`, `HOME`, `LANG` → pass through |
| `test_redact_env_vars_no_false_positive_on_key` | `KEYBOARD_LAYOUT`, `HKEY_LOCAL` → NOT redacted |
| `test_redact_env_vars_extra_patterns` | Custom pattern `"conn_str"` redacts `DATABASE_CONN_STR` |
| `test_redact_env_vars_empty_input` | `{}` → `{}` |
| `test_sensitive_key_patterns_contents` | Verify the frozenset contains exactly the 6 expected patterns |

**Note:** Use `@pytest.mark.parametrize` where appropriate — e.g., grouping sensitive keys, case variants, safe keys, and false-positive keys into parameterized test cases.

## Commit message

```
feat: add redact_env_vars with substring-based key matching

Add SENSITIVE_KEY_PATTERNS constant and redact_env_vars function for
case-insensitive substring matching on env var keys. Supports
extra_patterns parameter for caller-specific patterns.
```
