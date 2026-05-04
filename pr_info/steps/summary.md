# Summary — Issue #31: `user_app_data.get_user_app_data_dir`

## Goal

Expose a tiny helper that returns the per-user data directory for a given
app name (`~/.<app>/`), so every mcp-coder-family repo shares one source
of truth for the dotdir convention.

## Architectural / Design Notes

- **Leaf-library rules preserved.** The new module lives entirely inside
  `mcp_coder_utils` and adds no internal dependencies, no third-party deps,
  and no ecosystem knowledge. `app_name` is a required parameter — defaulting
  it to `"mcp_coder"` would violate architecture rule #1 (no ecosystem
  knowledge in a leaf library).
- **Follows existing submodule pattern.** Like `log_utils.py`, `redaction.py`,
  `subprocess_runner.py`, the new submodule defines its own `__all__` and is
  **not** re-exported from `mcp_coder_utils/__init__.py`. Consumers import
  via `from mcp_coder_utils.user_app_data import get_user_app_data_dir`.
- **Locked public API.** Once released, signature is immutable: param name
  `app_name`, return type `Path`, "directory not file" shape.
- **No platform branching.** `Path.home() / f".{app_name}"` on every platform.
  No XDG, no Apple HIG. This intentionally diverges from `mcp_coder.utils.user_config.get_config_file_path()` (which the follow-up shim PR will fix).
- **`Path.home()` raise behavior is not caught** — mirrors stdlib.
- **`≥2 real consumers` rule satisfied at release-day** by `mcp-workspace`'s
  `config.py` and `github_operations/issues/cache.py` (downstream PR).
- **No changes to `__init__.py`, `pyproject.toml`, `.importlinter`, or
  architecture docs.** The new module is covered by existing import contracts.

## Files Created / Modified

### Created

- `src/mcp_coder_utils/user_app_data.py` — new submodule exposing
  `get_user_app_data_dir(app_name: str) -> Path`.
- `tests/test_user_app_data.py` — unit tests for the helper.

### Modified

- _None._ (No edits to `__init__.py`, `pyproject.toml`, `.importlinter`,
  or architecture docs.)

## Implementation Steps

| Step | File | Description |
|------|------|-------------|
| 1 | `step_1.md` | Add `user_app_data` module + tests + run all quality checks |

Single-step plan: one logical unit, one commit (tests + implementation + passing checks).

## Test Strategy

Trivial unit tests, no platform branching needed. One parametrized
test covering the equality contract for two app names:

- `get_user_app_data_dir("mcp_coder") == Path.home() / ".mcp_coder"`
- `get_user_app_data_dir("foo") == Path.home() / ".foo"`

`Path` return type is enforced by the type annotation + mypy (strict by
default in `run_mypy_check`) and implicit in the equality assertion (a
non-`Path` would not equal a `Path`). No separate `isinstance` test needed.

## References

- Issue: [#31](https://github.com/MarcusJellinghaus/mcp-coder-utils/issues/31)
- Downstream consumer: [mcp-workspace#184](https://github.com/MarcusJellinghaus/mcp-workspace/issues/184)
- Follow-up shim PR tracking: [mcp_coder#949](https://github.com/MarcusJellinghaus/mcp_coder/issues/949)
