# Step 4: Wire up `fs/__init__.py` re-exports + update architecture docs

**Summary:** [pr_info/steps/summary.md](summary.md)

## LLM Prompt

> Read the summary at `pr_info/steps/summary.md` and this step file.
> Update `fs/__init__.py` to re-export all public symbols from the three modules.
> Update the architecture doc with the new package layout. Run all quality checks.
> Commit when green.

## WHERE

| File | Action |
|---|---|
| `src/mcp_coder_utils/fs/__init__.py` | **Modify** — add re-exports and `__all__` |
| `docs/architecture/architecture.md` | **Modify** — add `fs/` to package layout |

## WHAT

### `fs/__init__.py`

Re-export all public symbols so consumers can do:
```python
from mcp_coder_utils.fs import read_file, normalize_path, normalize_line_endings
```

**`__all__`:**
```python
__all__ = [
    "normalize_line_endings",
    "normalize_path",
    "read_file",
]
```

**Imports:**
```python
from mcp_coder_utils.fs.path_security import normalize_path
from mcp_coder_utils.fs.read_file import read_file
from mcp_coder_utils.fs.text import normalize_line_endings
```

### `docs/architecture/architecture.md`

Add the `fs/` subpackage to the "Package layout" section:

```
src/mcp_coder_utils/
    __init__.py
    py.typed
    log_utils.py
    redaction.py
    subprocess_runner.py
    subprocess_streaming.py
    fs/
        __init__.py
        path_security.py
        read_file.py
        text.py
```

## HOW

- No new logic — wiring only
- Verify imports resolve correctly via quality checks (mypy, pylint)

## TEST CASES

No new test file. Verify via:
- `mypy` — confirms imports resolve
- `pylint` — no import errors
- Existing tests from steps 1–3 continue to pass

## COMMIT

```
feat(fs): wire up __init__ re-exports and update architecture docs
```
