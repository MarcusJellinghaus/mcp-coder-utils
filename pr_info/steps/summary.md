# Summary — Issue #69: fs: shared line-ending and path-containment mechanisms

## Goal

Extract and unify two mechanisms that mcp-workspace and mcp_coder each solve
with their own code: line endings and path containment. This repo ships the
mechanism; each consumer keeps its policy (which default newline, `.git`
refusal, lexical fallback, ...). Consumers switch over in
mcp-workspace#400 / mcp_coder#1419 after the release (not part of this PR).

## Architectural / design changes

- **`fs/text.py` → `fs/line_endings.py`.** One module for the line-ending
  topic. No consumer imports `mcp_coder_utils.fs.text` directly; consumers
  import from `mcp_coder_utils.fs`, so the rename is local to this repo.
- **New line-ending mechanisms** (`fs/line_endings.py`):
  - `count_line_endings(data: bytes) -> tuple[int, int, int]` — raw
    `(crlf, lone lf, lone cr)` counts, copied verbatim from mcp-workspace.
  - `dominant_newline(data: bytes) -> str | None` — the decision; `None` on
    a tie or no line breaks, so the caller writes
    `dominant_newline(existing or b"") or default`. No `default` parameter:
    mcp-workspace's default costs a git subprocess, which must only run when
    there is nothing to count.
  - `write_text(path, text, *, newline="\n", append=False) -> None` —
    normalise, apply `newline`, encode UTF-8, then write bytes. Encoding
    happens before the file is opened, so an encode error leaves the file
    untouched. Invalid `newline` raises `ValueError` before any file access.
- **New containment check** (`fs/path_security.py`):
  - `check_path_within(path: str | Path, root: Path) -> None` — raises
    `ValueError` with a fixed reason (`..` segment, NUL byte, outside root);
    `OSError` (unresolvable path, symlink loop) propagates on purpose.
  - `normalize_path` keeps its signature but is reimplemented on the same
    private helper `_resolve_within`, which resolves once and returns the
    resolved path. **Behaviour change:** `..` segments and NUL now raise
    `ValueError` on every OS; a symlink loop the OS reports raises `OSError`
    on every Python version. Documented in the docstring (and later in the
    GitHub release notes — maintainer step after merge).
- **Symlink loop handling, no version gate:** `RuntimeError` from either
  `resolve()` call (3.11/3.12) is converted to `OSError`; then `stat()` the
  resolved root and resolved path and re-raise on `ELOOP` / WinError 1921
  (3.13+ `resolve()` no longer raises). Other `stat()` errors are ignored.
  The stat check runs before the containment check.
- **Rule: no git knowledge.** `architecture.md` rule 1 and `.claude/CLAUDE.md`
  gain "No git knowledge (git belongs in mcp-workspace)."
- **No config changes:** `fs` keeps `depends_on = []` in `tach.toml`; stdlib
  only; vulture, tach, import-linter, deptry need no changes.

## KISS choices

- One private helper shared by both public containment functions; the loop
  check is an inline `for` over `(resolved_root, resolved)`, no extra helper.
- One join for every path: `(resolved_root / path).resolve()` — pathlib
  ignores the left side when `path` is absolute, so no `os.path.isabs`
  branch.
- Converted loop error is a plain `OSError(message)`; no errno argument.
- Tests are parametrised: containment cases run against both
  `check_path_within` and `normalize_path`; newline styles, invalid
  `newline` values, `dominant_newline` and `count_line_endings` cases are
  tables.

## Files

| Action | Path |
|---|---|
| Rename + modify | `src/mcp_coder_utils/fs/text.py` → `src/mcp_coder_utils/fs/line_endings.py` |
| Modify | `src/mcp_coder_utils/fs/path_security.py` |
| Modify | `src/mcp_coder_utils/fs/__init__.py` |
| Rename + modify | `tests/test_fs_text.py` → `tests/test_fs_line_endings.py` |
| Modify | `tests/test_fs_path_security.py` |
| Modify | `docs/architecture/architecture.md` |
| Modify | `.claude/CLAUDE.md` |
| Modify | `README.md` |

No new folders. No changes to `tach.toml`, `.importlinter`,
`vulture_whitelist.py`, `pyproject.toml`.

## Steps

1. `fs/line_endings.py`: rename, `count_line_endings`, `dominant_newline`,
   `write_text`, exports, `architecture.md` layout.
2. `fs/path_security.py`: `_resolve_within`, `check_path_within`,
   `normalize_path` reimplementation, export.
3. Docs: "no git knowledge" rule (`architecture.md`, `.claude/CLAUDE.md`),
   README `fs` row.

## Out of scope (consumer policy / post-merge)

`.gitattributes` `eol=` lookup, default newline, `.git` refusal,
`(abs, rel_posix)` return, lexical `OSError` fallback, atomic save,
`describe_line_endings`, `read_file` changes, the GitHub release.
