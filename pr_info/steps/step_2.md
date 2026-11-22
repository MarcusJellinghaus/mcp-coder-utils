# Step 2 — `fs/path_security.py`: `check_path_within`, stricter `normalize_path`

## LLM prompt

Read `pr_info/steps/summary.md`, then implement this step
(`pr_info/steps/step_2.md`) exactly. Write the tests first, then the code.
Use the MCP tools listed in `.claude/CLAUDE.md`. One commit for the whole
step; all checks below must pass.

## Precondition

`src/mcp_coder_utils/fs/path_security.py` defines
`normalize_path(requested_path: str, allowed_root: Path) -> Path`. If not,
write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder_utils/fs/path_security.py`
- `src/mcp_coder_utils/fs/__init__.py`
- `tests/test_fs_path_security.py`

## WHAT

```python
def _resolve_within(path: str | Path, root: Path) -> Path: ...   # private
def check_path_within(path: str | Path, root: Path) -> None: ...
def normalize_path(requested_path: str, allowed_root: Path) -> Path: ...  # signature unchanged
```

## HOW

- `path_security.py`: `import errno`; drop `import os` (no longer needed);
  `__all__ = ["check_path_within", "normalize_path"]`; module docstring
  "Path security utilities — containment checks."
- `check_path_within` body: `_resolve_within(path, root)`.
  `normalize_path` body: `return _resolve_within(requested_path, allowed_root)`.
- Both public docstrings document `ValueError` and `OSError` under `Raises:`
  and carry `# noqa: DOC502 - raised by _resolve_within` after the closing
  `"""` (precedent: mcp-workspace `path_utils.normalize_path`).
- `fs/__init__.py`: import and export `check_path_within` (sorted `__all__`).

## ALGORITHM (`_resolve_within`)

```
if ".." in Path(path).parts: raise ValueError(f"Path '{path}' contains a '..' segment")
if "\0" in str(path):        raise ValueError(f"Path '{path}' contains a NUL byte")
try: resolved_root = root.resolve(); resolved = (resolved_root / path).resolve()
except RuntimeError as exc: raise OSError(f"Path '{path}' cannot be resolved: {exc}") from exc
for candidate in (resolved_root, resolved):
    try: candidate.stat()
    except OSError as exc: if exc.errno == errno.ELOOP or getattr(exc, "winerror", None) == 1921: raise
if not resolved.is_relative_to(resolved_root): raise ValueError(f"Path {path} is outside allowed root {resolved_root}")
return resolved
```

Notes:
- Messages are fixed by the issue — copy them exactly.
- Only `path` is checked for `..`; a `..` in `root` is accepted.
- `OSError` from `resolve()` is not caught.
- Call `Path.stat` (method), not `os.stat` — the tests mock `Path.stat`.
- `getattr(exc, "winerror", None)`: typeshed declares `winerror` only on
  win32; direct access fails mypy on CI Linux.
- Comment the `RuntimeError` branch (3.11/3.12 loop) and the stat loop
  (3.13+ `resolve()` returns a partial resolution silently) in one line each.

## DATA

- `check_path_within` → `None`.
- `normalize_path` / `_resolve_within` → resolved absolute `Path`.
- Raises `ValueError` (`..`, NUL, outside) or `OSError` (unresolvable, loop).

## Docstrings (required content)

- `check_path_within`: check only, raises; use when the caller keeps its own
  path form (e.g. a joined path); relative `path` anchored to `root`;
  `OSError` and loops reach the caller on purpose (its policy, e.g. a lexical
  fallback). Loop behaviour, no more than this: a loop the OS reports raises
  `OSError` on every Python version; on Windows a loop is reported only as the
  last component — below a looping junction the partial resolution is
  checked for containment like any path.
- `normalize_path`: check + resolved path; same rules as `check_path_within`.
  State the behaviour change: `"sub/../file.txt"` now raises; NUL raises the
  same `ValueError` on every OS; a symlink loop the OS reports raises
  `OSError` (3.11/3.12 raised `RuntimeError`, 3.13+ returned a partial path).

## Tests (`tests/test_fs_path_security.py`, write first)

Update the module docstring. Existing tests:
`test_traversal_rejected` and `test_deep_traversal_rejected` → match
`"contains a '..' segment"`. All other existing tests unchanged.

Shared test helpers:
- fixture `identity_resolve`: `patch.object(Path, "resolve", autospec=True,
  side_effect=lambda self, strict=False: self)`.
- `_symlink_or_skip(link: Path, target: Path)`: `os.symlink`, `pytest.skip`
  on `OSError` / `NotImplementedError`.

`CHECKS = [check_path_within, normalize_path]`; parametrise
`@pytest.mark.parametrize("check", CHECKS)` (pass `str` paths) for:
- `..` leading (`"../x"`) and mid-path (`"sub/../file.txt"`) →
  `ValueError` "contains a '..' segment".
- NUL (`"a\0b"`) → `ValueError` "contains a NUL byte".
- inside relative (`"sub/file.txt"`) and absolute (`str(tmp_path / "f")`) → no raise.
- absolute outside → `ValueError` "outside allowed root".
- `root` containing `..` (`tmp_path / "sub" / ".."`, `sub` created) with
  `"file.txt"` → no raise.
- `OSError` from `resolve()` (`side_effect=OSError("boom")`) → `OSError`.
- `..` with `resolve()` raising `OSError` → `ValueError` (check runs first).
- `RuntimeError` from `resolve()` (`side_effect=RuntimeError("loop")`) → `OSError`.
- stat loop on the resolved path (with `identity_resolve`, `root = tmp_path`,
  path `"sub/file.txt"`): capture `real_stat = Path.stat` before patching,
  then `patch.object(Path, "stat", autospec=True, side_effect=fake_stat)`
  where `fake_stat(self, **kwargs)` returns `real_stat(self)` when
  `self == root` and raises the loop error otherwise. Parametrised exception
  factory: `OSError(errno.ELOOP, "loop")`; and an `OSError("loop")` with
  `setattr(exc, "winerror", 1921)  # noqa: B010 - typeshed declares winerror only on win32; attribute assignment fails mypy on Linux`
  → `OSError`. The root stats cleanly, so only the path-stat check
  (Decision 15) can raise; an implementation that stats only the root fails.
- looping `root`, outside `path` (with `identity_resolve`): `Path.stat`
  mocked (`autospec=True`) to raise `OSError(errno.ELOOP, ...)` only when
  `self == root`, else `FileNotFoundError`; `path = str(tmp_path.parent / "out")`
  → `OSError`.
- other `stat()` errors ignored: nonexistent inside path → no raise
  (covered by the inside-relative case; nothing exists).
- real symlink escape: `root = tmp_path / "root"`, link `root / "link"` →
  `tmp_path / "outside"` (created) → `ValueError` "outside allowed root".
- real symlink loop: `root = tmp_path / "root"`, `root.mkdir()` first, then
  links `root / "a"` → `root / "b"` and `root / "b"` → `root / "a"`;
  `check("a", root)` (relative to `root`, so the loop is the last path
  component) → `OSError`.

Plus one test: `check_path_within(Path("sub/file.txt"), tmp_path)` accepts a
`Path`; and `normalize_path` returns `tmp_path / "sub" / "file.txt"` (existing
tests already cover the return value).

## Checks

`run_pylint_check`, `run_pytest_check` (`extra_args: ["-n", "auto"]`),
`run_mypy_check`, `run_ruff_check`, `run_vulture_check`, `run_tach_check`,
`run_lint_imports_check`, `run_deptry_check`, `check_file_size` on the two
changed files, then `run_format_code`.
Commit message: `feat(fs): add check_path_within, stricter normalize_path (#69)`.
