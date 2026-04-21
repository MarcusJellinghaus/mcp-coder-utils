# Step 2: Add `fs/read_file.py` — `read_file()`

**Summary:** [pr_info/steps/summary.md](summary.md)

## LLM Prompt

> Read the summary at `pr_info/steps/summary.md` and this step file.
> Implement `fs/read_file.py` with its test file using TDD. Write tests first,
> then implement the function. Run all quality checks. Commit when green.

## WHERE

| File | Action |
|---|---|
| `src/mcp_coder_utils/fs/read_file.py` | **Create** — module with `read_file()` |
| `tests/test_fs_read_file.py` | **Create** — tests |

## WHAT

### `read_file(file_path: str | Path, encoding: str = "utf-8") -> str`

Read a file with encoding fallback. Tries the specified encoding first,
falls back to latin-1 on `UnicodeDecodeError`. This deduplicates the ~30-line
reader copied across mcp_tools_py, mcp_config, and mcp_tools_py's pytest runner.

**Signature:**
```python
from pathlib import Path

def read_file(file_path: str | Path, encoding: str = "utf-8") -> str:
```

**`__all__`:**
```python
__all__ = ["read_file"]
```

## HOW

- Uses `pathlib.Path` for file I/O
- No external dependencies — stdlib only
- Raises `FileNotFoundError` / `OSError` for missing/unreadable files (no suppression)

## ALGORITHM

```
def read_file(file_path, encoding="utf-8"):
    path = Path(file_path)
    try:
        return path.read_text(encoding=encoding)
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")
```

## DATA

- **Input:** `file_path` (str or Path), `encoding` (str, default "utf-8")
- **Output:** `str` — file contents
- **Raises:** `FileNotFoundError` if file doesn't exist, `OSError` for I/O errors

## TEST CASES

Follow project pattern: class-based, type-annotated, `tmp_path` fixture for temp files.

```
class TestReadFile:
    - test_read_utf8_file               — writes UTF-8 file, reads back correctly
    - test_read_latin1_fallback         — writes latin-1 bytes (e.g. 0xe9), reads via fallback
    - test_read_with_explicit_encoding  — encoding="latin-1" reads latin-1 directly (no fallback)
    - test_file_not_found_raises        — non-existent path raises FileNotFoundError
    - test_accepts_path_object          — Path() input works same as str
    - test_empty_file                   — empty file returns ""
```

## COMMIT

```
feat(fs): add read_file module with encoding fallback
```
