## About this repo

`mcp-coder-utils` is a **leaf library**: shared low-level Python helpers (subprocess, logging, fs) used by `mcp-coder`, `mcp-tools-py`, `mcp-workspace`, and `mcp-tools-sql`.

**Architectural rules:**

- Pure Python, language-agnostic. No ecosystem knowledge (no `pyproject.toml` parsing, no venv, no `.csproj`, no SQL).
- Zero internal dependencies. Stdlib + pinned third-party libs only.
- Every public function must have ≥2 real consumers. Single-user helpers stay in the consumer.
- Public API is stable. Renames and signature changes break every downstream repo.

When in doubt, keep it in the consumer until a second consumer needs it.

## MCP Tools — mandatory

**Do NOT use native Claude Code file tools** (`Read`, `Write`, `Edit`, `Glob`, `Grep`, `Bash`) for any operation that has an MCP equivalent. Always use the `mcp__mcp-workspace__*` tools instead. This applies to all file reading, writing, editing, searching, listing, and git operations.

**Justify Bash.** Before a Bash command or script, say in chat, on two lines:

- *What it does* — one sentence.
- *Why MCP doesn't* — which tool you'd have used, and what stops it.

If you can't name the gap, use the MCP tool. Exempt: the approved git/gh commands under Git operations.

**No session scratchpad.** MCP tools can't write outside the project. Temporary files go in `.scratch/`.

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
| Check a Python semantic before claiming it | scratch probe — see [Scratch probes](#scratch-probes) |
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

Sibling repos are readable in full via the reference tools and `git` with `reference_name` (`get_reference_projects` lists them). Check there before asking about another repo.

## Code quality checks

After making code changes, run:

```
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check
mcp__mcp-tools-py__run_mypy_check
```

All checks must pass before proceeding.

**Pytest:** always use `extra_args: ["-n", "auto"]` for parallel execution. No integration test markers — run everything.

## Scratch probes

Don't assert Python behaviour you haven't run. Probe it:

```python
mcp__mcp-workspace__save_file(".scratch/test_probe.py", ...)
mcp__mcp-tools-py__run_pytest_check(extra_args=["-p", "no:cacheprovider", ".scratch/test_probe.py"])
```

A path argument scopes the run, so a probe costs seconds. Delete when done — `delete_directory(".scratch", recursive=True)`; CI blocks any PR carrying one. `.scratch/` is not gitignored: the MCP file tools refuse ignored paths.

Never use `python -c` via Bash. If you reason instead of running, label the conclusion analytical.

## Git operations

**Prefer MCP tools** for read-only git operations: use `mcp__mcp-workspace__git` with the `command` parameter (log, diff, status, merge_base, show, branch, fetch, rev_parse, ls_tree, ls_files, ls_remote). These run without permission prompts.

**Compact diff:** `mcp__mcp-workspace__git` with command `"diff"` includes compact diff by default — detects moved code, collapses unchanged blocks. Use `compact=False` for raw output.

**Allowed commands via Bash tool.** These have no MCP equivalent — use Bash directly. Skills that instruct bash commands (e.g. `git commit`) must also use Bash.

```
git commit / add / rebase / push / checkout -b / branch
gh issue create / edit / comment (labels only via set-status)
gh issue view (cross-repo only — otherwise use the MCP tool)
mcp-coder gh-tool set-status <label>
mcp-coder check branch-status
```

**Status labels:** use `mcp-coder gh-tool set-status` to change issue workflow status — never use raw `gh issue edit` with label flags.

**Slash-prefixed `gh` arguments:** prefix with `MSYS_NO_PATHCONV=1` — Git Bash rewrites a leading `/` into a Windows path.

**Before every commit:** run `mcp__mcp-tools-py__run_format_code`, then stage and commit.

**Bash discipline:** no `cd` prefix. Don't chain approved with unapproved commands. Run them separately.

**Commit messages:** standard format. See Writing style for length. No attribution footers.

## Writing style

Be concise. Shorter is better — chat, commits, PRs, docs, comments alike.

Say it once. Never restate what the reader can already see: the diff, the code, the issue, or my own earlier message. Cut it; don't rephrase it.

If a sentence isn't load-bearing, delete it.

Readable beats short. Cut what I don't need; don't compress what stays — complete sentences, no arrow chains or invented abbreviations. Lead with the outcome.

## Asking questions

Never use the AskUserQuestion tool. Ask questions as plain text in the chat.

## Obsidian knowledge base

Shared knowledge base across my repos (`obsidian-dev-wiki`), via the `obsidian-wiki` MCP server.

**Read at the start of non-trivial work:** `Home.md` (index), the `Repos/<current repo>.md` note, and any `Processes/` note matching the task. If a process note covers the task, follow it rather than improvising.

**Write only what passes all three tests:**

- *durable* — still true in 6 months (not status, versions, or task state)
- *general* — applies beyond the one issue that produced it
- *homeless* — no better place already exists

Existing homes, check before writing: code and docstrings; the repo's `docs/`; CLAUDE.md for how-I-work rules; the GitHub issue for a single defect's root cause; git history for what changed when.

**Always write to `Field Notes/`**, for Marcus to promote. Only edit `Repos/`, `Processes/`, or `Plans/` when Marcus explicitly asks for it. If an existing note already covers the topic, name it in the Field Note (`Promote into [[Note Name]]`) instead of editing that note. Follow `Conventions.md` for frontmatter and naming.

