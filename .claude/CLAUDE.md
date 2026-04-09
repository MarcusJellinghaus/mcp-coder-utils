--- This file is used by Claude Code - similar to a system prompt. ---

# ⚠️ MANDATORY INSTRUCTIONS - MUST BE FOLLOWED ⚠️

**THESE INSTRUCTIONS OVERRIDE ALL DEFAULT BEHAVIORS - NO EXCEPTIONS**

## About this repo

`mcp-coder-utils` is a **leaf library** in the mcp-coder family: shared low-level Python helpers (subprocess, logging, fs) used by `mcp-coder`, `mcp-tools-py`, `mcp-workspace`, and `mcp-config`.

**Architectural rules:**

- Pure Python, language-agnostic. No knowledge of any specific ecosystem (no `pyproject.toml` parsing, no venv awareness, no `.csproj`, no SQL).
- Zero internal dependencies. Stdlib + a small set of pinned third-party libs only.
- Every public function must have ≥2 real consumers (or be provably generic). Single-user "might be useful" helpers do not belong here — they stay in the consumer.
- Public API is stable. Renames and signature changes break all 4 downstream repos.

When in doubt about whether something belongs here, the answer is usually **no** — keep it in the consumer until a second consumer needs it.

## 🔴 CRITICAL: ALWAYS Use MCP Tools

**MANDATORY**: You MUST use MCP tools for ALL operations when available. DO NOT use standard Claude tools.

**BEFORE EVERY TOOL USE, ASK: "Does an MCP version exist?"**

### Tool Mapping Reference

| Task | ❌ NEVER USE | ✅ USE MCP TOOL |
|------|--------------|------------------|
| Read file | `Read()` | `mcp__workspace__read_file()` |
| Edit file | `Edit()` | `mcp__workspace__edit_file()` |
| Write file | `Write()` | `mcp__workspace__save_file()` |
| Run pytest | `Bash("pytest ...")` | `mcp__tools-py__run_pytest_check()` |
| Run pylint | `Bash("pylint ...")` | `mcp__tools-py__run_pylint_check()` |
| Run mypy | `Bash("mypy ...")` | `mcp__tools-py__run_mypy_check()` |
| Format code | `Bash("black ...")` | `mcp__tools-py__run_format_code()` |
| Lint imports | manual | `mcp__tools-py__run_lint_imports_check()` |
| Vulture check | manual | `mcp__tools-py__run_vulture_check()` |
| Get library source | _(new capability)_ | `mcp__tools-py__get_library_source()` |
| Git operations | ✅ `Bash("git ...")` | ✅ `Bash("git ...")` (allowed) |
| View diff (compact) | `Bash("git diff")` | ✅ `Bash("mcp-coder git-tool compact-diff")` |
| Refactoring | Manual copy-paste | `mcp__tools-py__move_symbol()`, `list_symbols()`, `find_references()`, `get_library_source()` |

## 🔴 CRITICAL: Code Quality Requirements

**MANDATORY**: After making ANY code changes (after EACH edit), you MUST run ALL FIVE code quality checks using the EXACT MCP tool names below:

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check
mcp__tools-py__run_mypy_check
mcp__tools-py__run_lint_imports_check
mcp__tools-py__run_vulture_check
```

This runs:

- **Pylint** - Code quality and style analysis
- **Pytest** - All unit and integration tests
- **Mypy** - Static type checking
- **Lint imports** - Import dependency enforcement
- **Vulture** - Dead code detection

**⚠️ ALL CHECKS MUST PASS** - If ANY issues are found, you MUST fix them immediately before proceeding.

### 📋 Pytest Execution Requirements

**MANDATORY pytest parameters:**

- ALWAYS use `extra_args: ["-n", "auto"]` for parallel execution

This repo has **no integration test markers** — it is a leaf library, all tests are fast unit tests. Run them all every time:

```python
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto"])
```

## 📁 MANDATORY: File Access Tools

**YOU MUST USE THESE MCP TOOLS** for all file operations:

```
mcp__workspace__get_reference_projects
mcp__workspace__list_reference_directory
mcp__workspace__read_reference_file
mcp__workspace__list_directory
mcp__workspace__read_file
mcp__workspace__save_file
mcp__workspace__append_file
mcp__workspace__delete_this_file
mcp__workspace__move_file
mcp__workspace__edit_file
```

**⚠️ ABSOLUTELY FORBIDDEN:** Using `Read`, `Write`, `Edit`, `MultiEdit` tools when MCP filesystem tools are available.

### Reference projects

The following sibling repos are registered as reference projects (read-only browse via `mcp__workspace__read_reference_file`):

- `p_mcp_coder` — `mcp_coder` source (the main consumer; useful when migrating modules in)
- `p_workspace` — `mcp-workspace` source
- `p_config` — `mcp-config` source
- `p_tools` — `mcp-tools-py` source

Use these to read the original source of any module you are about to migrate into `mcp-coder-utils`.

### Quick Examples

```python
# ❌ WRONG - Standard tools
Read(file_path="src/example.py")
Edit(file_path="src/example.py", old_string="...", new_string="...")
Write(file_path="src/new.py", content="...")
Bash("pytest tests/")

# ✅ CORRECT - MCP tools
mcp__workspace__read_file(file_path="src/example.py")
mcp__workspace__edit_file(file_path="src/example.py", edits=[...])
mcp__workspace__save_file(file_path="src/new.py", content="...")
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto"])
mcp__tools-py__run_format_code()
```

## ✍️ Writing Style

**Be concise.** Keep code comments, commit messages, documentation changes, and prompt additions short and direct. If one line works, don't use three.

## 🚨 COMPLIANCE VERIFICATION

**Before completing ANY task, you MUST:**

1. ✅ Confirm all code quality checks passed using MCP tools
2. ✅ Verify you used MCP tools exclusively (NO `Bash` for code checks, NO `Read`/`Write`/`Edit` for files)
3. ✅ Ensure no issues remain unresolved
4. ✅ State explicitly: "All CLAUDE.md requirements followed"

## 🔧 DEBUGGING AND TROUBLESHOOTING

**When tests fail or skip:**

- Use MCP pytest tool with verbose flags: `extra_args: ["-v", "-s", "--tb=short"]`
- Never fall back to `Bash` commands - always investigate within MCP tools
- If MCP tools don't provide enough detail, ask user for guidance rather than using alternative tools

## 🔧 MCP Server Issues

**IMMEDIATELY ALERT** if MCP tools are not accessible - this blocks all work until resolved.

## 🔄 Git Operations

**MANDATORY: Before ANY commit:**

```
# ALWAYS format code before committing
mcp__tools-py__run_format_code

# Then verify formatting worked
git diff  # Should show formatting changes if any
```

**Format all code before committing:**

- Run `mcp__tools-py__run_format_code` to format with black and isort
- Review the changes to ensure they're formatting-only
- Stage the formatted files
- Then commit

**ALLOWED git operations via Bash tool:**

```
git status
git diff
git commit
git log
git fetch
git ls-tree
gh issue view
gh run view
mcp-coder git-tool compact-diff
mcp-coder check branch-status
mcp-coder check file-size
mcp-coder gh-tool set-status <label>
```

**Status labels:** Use `mcp-coder gh-tool set-status` to change issue workflow status — never use raw `gh issue edit` with label flags. (Note: this repo's labels are not yet configured — set up label set before relying on status workflow.)

**Compact diff for code review:**

Use `mcp-coder git-tool compact-diff` instead of `git diff` when reviewing branch changes. It detects moved code, collapses unchanged blocks, and separates committed vs uncommitted changes. Supports `--exclude PATTERN` to filter files.

**⚠️ Bash discipline (applies to subagents too):**

- No `cd` prefix — the working directory is already correct.
- Stick to approved commands above. Avoid unapproved bash commands — they trigger user authorization prompts and interrupt the workflow.
- Do not chain approved commands with unapproved ones (e.g. `git status && echo "---" && git diff`). The `echo` makes the whole command unapproved. Run approved commands separately instead.

**Git commit message format:**

- Use standard commit message format without advertising footers
- Focus on clear, descriptive commit messages
- No required Claude Code attribution or links

## 📏 File Size Check

Check for large files (>750 lines) that may impact LLM context:

```bash
mcp-coder check file-size --max-lines 750
mcp-coder check branch-status --llm-truncate
```

---

## 📋 TODO — repo bootstrap

This repo is freshly scaffolded. The following items still need to be copied over from `mcp_coder` (or created from scratch) and the CLAUDE.md sections referenced below should be updated when each lands.

### Files / configs to copy or create

| Item | Source in `mcp_coder` | Status | Notes |
|---|---|---|---|
| **CI workflows** | `.github/workflows/*.yml` | ❌ missing | pytest, pylint, mypy, vulture, lint-imports, ruff. Will likely need adapting (no integration markers, no langchain/mlflow paths) |
| **PR template** | `.github/PULL_REQUEST_TEMPLATE.md` | ❌ missing | |
| **Issue templates** | `.github/ISSUE_TEMPLATE/` | ❌ missing | |
| **Label set + config** | `src/mcp_coder/config/labels.json` + `labels_schema.md` | ❌ missing | Required before `mcp-coder gh-tool set-status` works here. Apply via `mcp-coder gh-tool` |
| **`.importlinter` config** | `.importlinter` (root) | ❌ missing | Defines import dependency rules. Even leaf libraries benefit from one rule: "no internal cycles" |
| **`tools/format_all.bat` + `.sh`** | `tools/format_all.{bat,sh}` | ❌ missing | Can be skipped if MCP `run_format_code` is the only entry point |
| **`tools/ruff_check.bat` + `.sh`** | `tools/ruff_check.{bat,sh}` | ❌ missing | Needed if ruff docstring checks are wired up |
| **`tools/lint_imports.bat` + `.sh`** | `tools/lint_imports.{bat,sh}` | ❌ missing | Wrappers around `lint-imports` (import-linter) |
| **`tools/vulture_check.bat` + `.sh`** | `tools/vulture_check.{bat,sh}` | ❌ missing | |
| **`tools/checks2clipboard.bat`** | `tools/checks2clipboard.bat` | ❌ missing | Optional dev convenience |
| **`.claude/skills/`** | `.claude/skills/` | ❌ missing | Workflow skills (commit_push, rebase, issue_*, plan_*, implementation_*). Most are mcp-coder-workflow-specific and may not all apply |
| **`.claude/agents/`** | `.claude/agents/` | ❌ missing | Sub-agent definitions if any are reused |
| **`.claude/knowledge_base/`** | `.claude/knowledge_base/` | ❌ missing | Project-specific knowledge — most won't apply, copy selectively |
| **`LICENSE`** | `LICENSE` | ❌ missing | MIT, same as mcp-coder |
| **`CONTRIBUTING.md`** | `CONTRIBUTING.md` (if present) | ❓ unknown | |
| **Refactoring guide** | `docs/processes-prompts/refactoring-guide.md` | ❌ missing | Worth copying once real refactoring starts |
| **Repo settings** | (GitHub UI / API) | ⚠️ partially done | Branch protection on `main` ✅ applied. **Still TODO:** disable merge-commit + rebase-merge (squash-only), set squash title=`PR_TITLE` and message=`PR_BODY`, disable wiki — to match `mcp_coder`'s conventions |

### Real content (per `repo_architecture_plan/mcp_utils_plan.md`)

| Module | Source | Phase |
|---|---|---|
| `subprocess_runner` | merge of `mcp_coder` + `mcp_tools_py` versions | Phase 2 |
| `subprocess_streaming` | `mcp_coder` (moves with `subprocess_runner`) | Phase 2 |
| `log_utils` | `mcp_coder` (canonical — has redaction + custom levels) | Phase 2 |
| `fs/read_file` | dedupe of `mcp_tools_py` + `mcp_config` copies | later |
| `fs/path_security` | `mcp_workspace`'s `path_utils.py` | later |

### CLAUDE.md sections to revisit when items land

When the items above are added, the following CLAUDE.md sections need to be updated to match — search for the **TODO markers** below:

- **Tool Mapping Reference** — currently lists "manual" for lint imports, vulture, format. **TODO:** when `tools/*.{bat,sh}` wrappers exist, add them as the "Bash" alternative (or remove entirely if MCP-only is enforced)
- **Pytest Execution Requirements** — currently says "no integration test markers". **TODO:** if any integration tests are ever added (e.g. `subprocess_integration` for the real shell), add them here with the recommended `not` exclusion pattern
- **File Access Tools — Reference projects** — list of registered reference repos. **TODO:** keep in sync with `.mcp.json` if any are added/removed
- **ALLOWED git operations** — currently lists `mcp-coder gh-tool set-status` but flags that labels aren't configured. **TODO:** remove the caveat once the label set is applied
- **About this repo — architectural rules** — **TODO:** when the first real modules land (Phase 2), add a "Public API" section listing every top-level export so future sessions know not to break it
