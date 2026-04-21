# Step 3: Add `fs/path_security.py` — `normalize_path()`

**Summary:** [pr_info/steps/summary.md](summary.md)

## LLM Prompt

> Read the summary at `pr_info/steps/summary.md` and this step file.
> Implement `fs/path_security.py` with its test file using TDD. Write tests first,
> then implement the function. This is an improved extraction — see the "Intentional
> deviations" section below. Run all quality checks. Commit when green.

## WHERE

| File | Action |
|---|---|
| `src/mcp_coder_utils/fs/path_security.py` | **Create** — module with `normalize_path()` |
| `tests/test_fs_path_security.py` | **Create** — tests |

## WHAT

### `normalize_path(requested_path: str, allowed_root: Path) -> Path`

Security boundary function that resolves a requested path and verifies it falls
within an allowed root directory. Prevents path traversal attacks (e.g. `../../etc/passwd`).

Based on mcp_workspace's `path_utils.py`, with API improvements for the shared
library. Currently 1 consumer but foundational security infrastructure.

### Intentional deviations from the source

| Aspect | Source (`path_utils.py`) | This implementation |
|---|---|---|
| Return type | `tuple[Path, str]` (resolved path + relative) | `Path` only — consumers can derive the relative path themselves |
| Containment check | `os.path.commonpath()` | `is_relative_to()` — cleaner, stricter |
| Absolute path handling | varies | `resolve()` for consistent canonicalization |
| None guard | `allowed_root` typed as `Optional[Path]` | `allowed_root` typed as `Path` — no None guard needed |
| Non-existent paths | try/except falls through (known weakness) | `resolve()` + `is_relative_to()` is stricter — non-existent paths within the root resolve correctly and are accepted; traversal via non-existent intermediates is still caught |

**Signature:**
```python
from pathlib import Path

def normalize_path(requested_path: str, allowed_root: Path) -> Path:
```

**Raises:** `ValueError` when the resolved path is outside `allowed_root`.

**`__all__`:**
```python
__all__ = ["normalize_path"]
```

## HOW

- Uses `pathlib.Path.resolve()` to canonicalize both paths
- Checks resolved path starts with resolved root via `Path.is_relative_to()`
- Raises `ValueError` with descriptive message on traversal attempt
- No external dependencies

## ALGORITHM

```
def normalize_path(requested_path, allowed_root):
    resolved_root = allowed_root.resolve()
    if os.path.isabs(requested_path):
        resolved = Path(requested_path).resolve()
    else:
        resolved = (resolved_root / requested_path).resolve()
    if not resolved.is_relative_to(resolved_root):
        raise ValueError(f"Path {requested_path} is outside allowed root")
    return resolved
```

## DATA

- **Input:** `requested_path` (str), `allowed_root` (Path)
- **Output:** `Path` — resolved, validated absolute path
- **Raises:** `ValueError` if path escapes allowed_root

## TEST CASES

Follow project pattern: class-based, type-annotated, `tmp_path` fixture.

```
class TestNormalizePath:
    - test_simple_relative_path         — "file.txt" resolves within root
    - test_subdirectory_path            — "sub/file.txt" resolves within root
    - test_traversal_rejected           — "../outside.txt" raises ValueError
    - test_deep_traversal_rejected      — "a/../../outside" raises ValueError
    - test_absolute_path_within_root    — absolute path inside root accepted
    - test_absolute_path_outside_root   — absolute path outside root raises ValueError
    - test_dot_path                     — "." resolves to root itself
    - test_returns_resolved_path        — result is absolute (resolved)

class TestNormalizePathNonExistentPaths:
    - test_nonexistent_path_within_root  — non-existent "fake/file.txt" resolves
      within root and is accepted (normal resolve() behavior, not a weakness)
```

## COMMIT

```
feat(fs): add path_security module with normalize_path
```
