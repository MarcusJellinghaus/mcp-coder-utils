## About this repo

`mcp-coder-utils` is a **leaf library**: shared low-level Python helpers (subprocess, logging, fs) used by `mcp-coder`, `mcp-tools-py`, `mcp-workspace`, and `mcp-config`.

**Architectural rules:**

- Pure Python, language-agnostic. No ecosystem knowledge (no `pyproject.toml` parsing, no venv, no `.csproj`, no SQL).
- Zero internal dependencies. Stdlib + pinned third-party libs only.
- Every public function must have ≥2 real consumers. Single-user helpers stay in the consumer.
- Public API is stable. Renames and signature changes break all 4 downstream repos.

When in doubt, keep it in the consumer until a second consumer needs it.

## MCP Tools — mandatory

Use MCP tools for **all** operations. Never use `Read`, `Write`, `Edit`, or `Bash` for tasks that have an MCP equivalent.

### Tool mapping

| Task | MCP tool |
|------|----------|
| Read file | `mcp__workspace__read_file` |
| Edit file | `mcp__workspace__edit_file` |
| Write file | `mcp__workspace__save_file` |
| Append to file | `mcp__workspace__append_file` |
| Delete file | `mcp__workspace__delete_this_file` |
| Move file | `mcp__workspace__move_file` |
| List directory | `mcp__workspace__list_directory` |
| Search files | `mcp__workspace__search_files` |
| Read reference project | `mcp__workspace__read_reference_file` |
| List reference dir | `mcp__workspace__list_reference_directory` |
| Get reference projects | `mcp__workspace__get_reference_projects` |
| Run pytest | `mcp__tools-py__run_pytest_check` |
| Run pylint | `mcp__tools-py__run_pylint_check` |
| Run mypy | `mcp__tools-py__run_mypy_check` |
| Run lint-imports | `mcp__tools-py__run_lint_imports_check` |
| Run vulture | `mcp__tools-py__run_vulture_check` |
| Format code (black+isort) | `mcp__tools-py__run_format_code` |
| Get library source | `mcp__tools-py__get_library_source` |
| Refactoring | `mcp__tools-py__move_symbol`, `move_module`, `rename_symbol`, `list_symbols`, `find_references` |

### Reference projects

Read-only browse via `mcp__workspace__read_reference_file`:

- `p_mcp_coder` — `mcp_coder` source
- `p_workspace` — `mcp-workspace` source
- `p_config` — `mcp-config` source
- `p_tools` — `mcp-tools-py` source

## Code quality checks

After making code changes, run:

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check
mcp__tools-py__run_mypy_check
```

All checks must pass before proceeding.

**Pytest:** always use `extra_args: ["-n", "auto"]` for parallel execution. No integration test markers — run everything.

## Git operations

**Allowed commands via Bash:**

```
git status / diff / commit / log / fetch / ls-tree
gh issue view / gh run view
mcp-coder git-tool compact-diff    # diff that detects moves, collapses unchanged blocks
mcp-coder check branch-status      # CI status, rebase needs, task completion, labels
mcp-coder check file-size           # find files exceeding line-count threshold
mcp-coder gh-tool set-status <label>  # change issue workflow status label
```

**Before every commit:** run `mcp__tools-py__run_format_code`, then stage and commit.

**Bash discipline:** no `cd` prefix. Don't chain approved with unapproved commands. Run them separately.

**Commit messages:** standard format, clear and descriptive. No attribution footers.

## Writing style

Be concise. If one line works, don't use three.

