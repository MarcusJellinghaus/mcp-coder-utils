# Step 1: Add `fs/text.py` — `normalize_line_endings()`

**Summary:** [pr_info/steps/summary.md](summary.md)

## LLM Prompt

> Read the summary at `pr_info/steps/summary.md` and this step file.
> Implement `fs/text.py` with its test file using TDD. Create the minimal
> `fs/__init__.py` (empty, just makes it a package). Write tests first, then
> implement the function. Run all quality checks. Commit when green.

## WHERE

| File | Action |
|---|---|
| `src/mcp_coder_utils/fs/__init__.py` | **Create** — empty package init (placeholder) |
| `src/mcp_coder_utils/fs/text.py` | **Create** — module with `normalize_line_endings()` |
| `tests/test_fs_text.py` | **Create** — tests |

## WHAT

### `normalize_line_endings(text: str) -> str`

Normalize CRLF and CR line endings to LF. Used by 3 mcp_workspace modules
for consistent text processing on Windows and Unix.

**Signature:**
```python
def normalize_line_endings(text: str) -> str:
```

**`__all__`:**
```python
__all__ = ["normalize_line_endings"]
```

## HOW

- Pure function, no imports needed beyond typing
- No integration points — standalone utility

## ALGORITHM

```
def normalize_line_endings(text):
    replace \r\n with \n    (CRLF → LF, must be first)
    replace \r with \n      (remaining CR → LF)
    return result
```

## DATA

- **Input:** `str` — text with any line ending style
- **Output:** `str` — text with only `\n` line endings

## TEST CASES

Follow project pattern: class-based, type-annotated methods, `pytest` imports.

```
class TestNormalizeLineEndings:
    - test_crlf_converted_to_lf          — "a\r\nb" → "a\nb"
    - test_cr_converted_to_lf            — "a\rb" → "a\nb"
    - test_lf_unchanged                  — "a\nb" → "a\nb"
    - test_mixed_endings_normalized      — "a\r\nb\rc\nd" → "a\nb\nc\nd"
    - test_empty_string                  — "" → ""
    - test_no_line_endings               — "abc" → "abc"
    - test_only_line_endings             — "\r\n\r\n" → "\n\n"
```

## COMMIT

```
feat(fs): add text module with normalize_line_endings
```
