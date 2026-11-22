# Step 1 — `fs/line_endings.py`: count, dominant newline, write

## LLM prompt

Read `pr_info/steps/summary.md`, then implement this step
(`pr_info/steps/step_1.md`) exactly. Write the tests first, then the code.
Use the MCP tools listed in `.claude/CLAUDE.md`. One commit for the whole
step; all checks below must pass.

## Precondition

`src/mcp_coder_utils/fs/text.py` and `tests/test_fs_text.py` exist. If
either is missing, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder_utils/fs/text.py` → `src/mcp_coder_utils/fs/line_endings.py`
  (`move_file`)
- `tests/test_fs_text.py` → `tests/test_fs_line_endings.py` (`move_file`)
- `src/mcp_coder_utils/fs/__init__.py`
- `docs/architecture/architecture.md` (package layout only)

## WHAT

```python
def normalize_line_endings(text: str) -> str: ...          # unchanged
def count_line_endings(data: bytes) -> tuple[int, int, int]: ...
def dominant_newline(data: bytes) -> str | None: ...
def write_text(
    path: Path, text: str, *, newline: str = "\n", append: bool = False
) -> None: ...
```

## HOW

- `line_endings.py`: module docstring "Line-ending counting, choice and
  writing."; `__all__` lists the four functions; `from pathlib import Path`.
- `fs/__init__.py`: import the four from `mcp_coder_utils.fs.line_endings`
  instead of `mcp_coder_utils.fs.text`; add `count_line_endings`,
  `dominant_newline`, `write_text` to `__all__` (sorted).
- Test file: update the module docstring and the import to
  `mcp_coder_utils.fs.line_endings`.
- `architecture.md` package layout: `text.py` → `line_endings.py`, keep the
  list sorted (`line_endings.py`, `path_security.py`, `read_file.py`).

## ALGORITHM

```
count_line_endings: crlf = data.count(b"\r\n")
                    return crlf, data.count(b"\n") - crlf, data.count(b"\r") - crlf
dominant_newline:   crlf, lf, cr = count_line_endings(data); top = max(crlf, lf, cr)
                    winners = [nl for n, nl in ((crlf, "\r\n"), (lf, "\n"), (cr, "\r")) if n == top]
                    return winners[0] if top and len(winners) == 1 else None
write_text:         if newline not in _NEWLINES: raise ValueError(f"newline must be one of ..., got {newline!r}")
                    data = normalize_line_endings(text).replace("\n", newline).encode("utf-8")
                    with path.open("ab" if append else "wb") as handle: handle.write(data)
```

`_NEWLINES = ("\n", "\r\n", "\r")` is a private module constant. The check
uses `not in`, so `""` and `None` both raise `ValueError` (no `TypeError`).

## DATA

- `count_line_endings` → `(crlf, lone_lf, lone_cr)`.
- `dominant_newline` → `"\r\n"`, `"\n"`, `"\r"` or `None` (tie, incl. three-way;
  no line breaks; empty input).
- `write_text` → `None`; raises `ValueError` (invalid `newline`),
  `UnicodeEncodeError` (before the file is opened), `OSError` from `open`
  (e.g. missing parent directory — not created).

## Docstrings (required content)

- `normalize_line_endings`: text in memory; use `write_text` to write to disk.
- `count_line_endings`: raw counts; `dominant_newline` makes the decision.
- `dominant_newline`: `None` covers tie and no line breaks; name the idiom
  `dominant_newline(existing or b"") or default` (bytes only; a missing file
  passes `b""`); choosing `default` is the caller's policy.
- `write_text`: vs `Path.write_text` — normalises first, so
  `newline="\r\n"` cannot produce CR CR LF; lone CR becomes a line break;
  writes bytes, so an encode error leaves an existing file untouched;
  invalid `newline` raises before any file access; parent directories are
  not created; `append=True` on a missing file creates it; choosing
  `newline` is the caller's policy. Google style with `Args:` and `Raises:`
  (`ValueError`).

## Tests (`tests/test_fs_line_endings.py`, write first)

Keep the existing `TestNormalizeLineEndings`. Add:

- `TestCountLineEndings` — parametrised:
  `b"a\r\nb\nc\rd"` → `(1, 1, 1)`; `b"\r\n\r\n"` → `(2, 0, 0)`;
  `b"\n\r"` → `(0, 1, 1)`; `b""` → `(0, 0, 0)`.
- `TestDominantNewline` — parametrised table: CRLF only → `"\r\n"`;
  LF only → `"\n"`; CR only → `"\r"`; mixed with LF majority
  (`b"a\r\nb\nc\n"`) → `"\n"`; tie (`b"a\r\nb\n"`) → `None`; three-way tie
  (`b"a\r\nb\nc\r"`) → `None`; `b"abc"` → `None`; `b""` → `None`.
- `TestWriteText` (all assert `path.read_bytes()`):
  - parametrised `newline` in `"\n"`, `"\r\n"`, `"\r"`: `"a\nb\n"` →
    `b"a" + nl + b"b" + nl`.
  - embedded CRLF / lone CR: `"a\r\nb\rc\n"` default → `b"a\nb\nc\n"`;
    with `newline="\r\n"` → `b"a\r\nb\r\nc\r\n"`.
  - append: existing `b"x\r\n"`, `write_text(p, "y\n", newline="\r\n",
    append=True)` → `b"x\r\ny\r\n"`.
  - `append=True` on a missing file creates it.
  - overwrite replaces existing content.
  - invalid `newline` parametrised `""` and `None`
    (`None` passed with `# type: ignore[arg-type]`; `""` needs none):
    existing `b"old"` stays `b"old"`, `pytest.raises(ValueError)`; also a
    missing target is not created.
  - encode error: existing `b"old"`, `write_text(p, "\ud800")` raises
    `UnicodeEncodeError`; bytes still `b"old"`.
  - parent directory not created: target `tmp_path / "missing" / "f.txt"`
    raises `FileNotFoundError`; `tmp_path / "missing"` does not exist.

## Checks

`run_pylint_check`, `run_pytest_check` (`extra_args: ["-n", "auto"]`),
`run_mypy_check`, `run_ruff_check`, `run_vulture_check`, `run_tach_check`,
`run_lint_imports_check`, `run_deptry_check`, then `run_format_code`.
Commit message: `feat(fs): add line_endings module with count, dominant newline and write (#69)`.
