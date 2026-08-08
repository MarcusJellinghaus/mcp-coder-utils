## About this repo

`mcp-coder-utils` is a **leaf library**: shared low-level Python helpers (subprocess, logging, fs) used by `mcp-coder`, `mcp-tools-py`, `mcp-workspace`, and `mcp-config`.

**Architectural rules:**

- Pure Python, language-agnostic. No ecosystem knowledge (no `pyproject.toml` parsing, no venv, no `.csproj`, no SQL).
- Zero internal dependencies. Stdlib + pinned third-party libs only.
- Every public function must have ≥2 real consumers. Single-user helpers stay in the consumer.
- Public API is stable. Renames and signature changes break all 4 downstream repos.

When in doubt, keep it in the consumer until a second consumer needs it.

## MCP Tools — mandatory

**Do NOT use native Claude Code file tools** (`Read`, `Write`, `Edit`, `Glob`, `Grep`, `Bash`) for any operation that has an MCP equivalent. Always use the `mcp__mcp-workspace__*` tools instead. This applies to all file reading, writing, editing, searching, listing, and git operations.

### Tool mapping

| Task | MCP tool |
|------|----------|
| Read file | `mcp__mcp-workspace__read_file` |
| Edit file | `mcp__mcp-workspace__edit_file` |
| Write file | `mcp__mcp-workspace__save_file` |
| Append to file | `mcp__mcp-workspace__append_file` |
| Delete file | `mcp__mcp-workspace__delete_this_file` |
| Move file | `mcp__mcp-workspace__move_file` |
| List directory | `mcp__mcp-workspace__list_directory` |
| Search files | `mcp__mcp-workspace__search_files` |
| Search reference files | `mcp__mcp-workspace__search_reference_files` |
| Read reference project | `mcp__mcp-workspace__read_reference_file` |
| List reference dir | `mcp__mcp-workspace__list_reference_directory` |
| Get reference projects | `mcp__mcp-workspace__get_reference_projects` |
| Run pytest | `mcp__mcp-tools-py__run_pytest_check` |
| Run pylint | `mcp__mcp-tools-py__run_pylint_check` |
| Run mypy | `mcp__mcp-tools-py__run_mypy_check` |
| Run lint-imports | `mcp__mcp-tools-py__run_lint_imports_check` |
| Run vulture | `mcp__mcp-tools-py__run_vulture_check` |
| Format code (black+isort) | `mcp__mcp-tools-py__run_format_code` |
| Get library source | `mcp__mcp-tools-py__get_library_source` |
| Refactoring | `mcp__mcp-tools-py__move_symbol`, `move_module`, `rename_symbol`, `list_symbols`, `find_references` |
| Git (read-only) | `mcp__mcp-workspace__git` |
| Get base branch | `mcp__mcp-workspace__get_base_branch` |
| Check file size | `mcp__mcp-workspace__check_file_size` |
| Check branch status | `mcp__mcp-workspace__check_branch_status` |
| List GitHub issues | `mcp__mcp-workspace__github_issue_list` |
| View GitHub issue | `mcp__mcp-workspace__github_issue_view` |
| View GitHub PR | `mcp__mcp-workspace__github_pr_view` |
| Search GitHub | `mcp__mcp-workspace__github_search` |

### Reference projects

Read-only browse via `mcp__mcp-workspace__read_reference_file`:

- `mcp_coder` — `mcp_coder` source
- `mcp-workspace` — `mcp-workspace` source
- `mcp-config` — `mcp-config` source
- `mcp-tools-py` — `mcp-tools-py` source

## Code quality checks

After making code changes, run:

```
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check
mcp__mcp-tools-py__run_mypy_check
```

All checks must pass before proceeding.

**Pytest:** always use `extra_args: ["-n", "auto"]` for parallel execution. No integration test markers — run everything.

## Git operations

**Prefer MCP tools** for read-only git operations: use `mcp__mcp-workspace__git` with the `command` parameter (log, diff, status, merge_base, show, branch, fetch, rev_parse, ls_tree, ls_files, ls_remote). These run without permission prompts.

**Compact diff:** `mcp__mcp-workspace__git` with command `"diff"` includes compact diff by default — detects moved code, collapses unchanged blocks. Use `compact=False` for raw output.

**Bash commands** for git operations that have no MCP equivalent:

```
git commit / git add
mcp-coder gh-tool set-status <label>  # change issue workflow status label
```

**Status labels:** use `mcp-coder gh-tool set-status` to change issue workflow status — never use raw `gh issue edit` with label flags.

**Before every commit:** run `mcp__mcp-tools-py__run_format_code`, then stage and commit.

**Bash discipline:** no `cd` prefix. Don't chain approved with unapproved commands. Run them separately.

**Commit messages:** standard format, clear and descriptive. No attribution footers.

## Writing style

Be concise. If one line works, don't use three.

## Asking questions

Never use the AskUserQuestion tool. Ask questions as plain text in the chat.

