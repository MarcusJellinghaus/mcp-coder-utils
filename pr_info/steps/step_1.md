# Step 1 — Add `user_app_data` module + tests

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step (`pr_info/steps/step_1.md`).
> Implement Step 1 exactly as specified. Follow TDD: write the test file
> first, confirm it fails, then add the implementation, then run all three
> required quality checks (`run_pylint_check`, `run_pytest_check`,
> `run_mypy_check`) and fix any issues until all pass. Produce a single
> commit containing tests + implementation. Do not modify any files outside
> the WHERE list.

## WHERE — Files

### Create

- `src/mcp_coder_utils/user_app_data.py`
- `tests/test_user_app_data.py`

### Modify

- _None._

## WHAT — Public API

```python
# src/mcp_coder_utils/user_app_data.py

from pathlib import Path

__all__ = ["get_user_app_data_dir"]


def get_user_app_data_dir(app_name: str) -> Path:
    """Return the per-user data directory for ``app_name``.

    Uses the dotfile-in-home convention on every platform:
    ``~/.<app_name>/``.

    Args:
        app_name: Application name (e.g. ``"mcp_coder"``).

    Returns:
        Absolute path under the user's home directory.

    Raises:
        RuntimeError: If ``Path.home()`` cannot be resolved (mirrors stdlib).
    """
```

## HOW — Integration

- **No** entry in `mcp_coder_utils/__init__.py` (matches the pattern of
  `log_utils`, `redaction`, `subprocess_runner`, etc.).
- Consumers import directly:
  `from mcp_coder_utils.user_app_data import get_user_app_data_dir`.
- No new dependencies, no `pyproject.toml` change.
- No `.importlinter` change — module is inside `mcp_coder_utils` and
  already covered by existing contracts.

## ALGORITHM — Core Logic

```
return Path.home() / f".{app_name}"
```

(That is the entire body. Do not add validation, normalization, or
caching — the issue locks the signature and "mirrors stdlib" behavior.)

## DATA — Return Value

- Type: `pathlib.Path`
- Value: `Path.home() / f".{app_name}"`
- For `app_name="mcp_coder"` on any platform: `Path.home() / ".mcp_coder"`
- The path is **not** created on disk by this helper.

## Tests — `tests/test_user_app_data.py`

Write the tests **first** (TDD). Module docstring optional; tests are
exempt from `D`/`DOC` ruff rules per `pyproject.toml`.

```python
"""Tests for user_app_data module."""

from pathlib import Path

import pytest

from mcp_coder_utils.user_app_data import get_user_app_data_dir


@pytest.mark.parametrize("app_name", ["mcp_coder", "foo"])
def test_returns_dotdir_under_home(app_name: str) -> None:
    assert get_user_app_data_dir(app_name) == Path.home() / f".{app_name}"
```

That is the entire test scope — one parametrized test covering the
issue's three test bullets. The "returns a `Path` instance" bullet is
implicit: equality with `Path.home() / ...` (a `Path`) cannot succeed
against a non-`Path` value, and the return-type annotation is enforced
by mypy strict mode.

## Verification (mandatory before commit)

Run all three MCP checks and ensure each passes:

1. `mcp__tools-py__run_pylint_check`
2. `mcp__tools-py__run_pytest_check` with
   `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
3. `mcp__tools-py__run_mypy_check`

Then run `./tools/format_all.sh` (per CLAUDE.md), review the diff, stage,
and commit.

## Commit

Single commit, message suggestion:

```
Add user_app_data.get_user_app_data_dir helper (#31)
```

## Acceptance Criteria

- [ ] `mcp_coder_utils.user_app_data.get_user_app_data_dir(app_name)`
      returns `Path.home() / f".{app_name}"` on every platform.
- [ ] `__all__ = ["get_user_app_data_dir"]` is defined in the new module.
- [ ] No re-export from `mcp_coder_utils/__init__.py`.
- [ ] Parametrized unit test covers `"mcp_coder"` and `"foo"` cases.
- [ ] All three MCP quality checks pass (pylint, pytest, mypy).
- [ ] Single commit produced.
