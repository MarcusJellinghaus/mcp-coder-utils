# Issue Roadmap — mcp-coder-utils

High-level plan. Each `###` is a future GitHub issue.

---

## Phase 1 — Finish scaffolding

### Done (on branch `bootstrap/claude-launchers`)

- [x] CI workflows (`.github/workflows/`)
- [x] Labels (applied via `mcp-coder gh-tool define-labels`)
- [x] `.importlinter` (2 contracts)
- [x] Skills, agents, knowledge base (all 20 skills copied)
- [x] LICENSE, .gitattributes, .python-version
- [x] vulture_whitelist.py, .large-files-allowlist, py.typed
- [x] docs/architecture/architecture.md (stub)
- [x] .github/dependabot.yml
- [x] tools/ruff_check.{bat,sh}
- [x] .gitignore updates

### Update README and CLAUDE.md

- `README.md`: rewrite with real description (leaf library, scope, stable public API)
- `.claude/CLAUDE.md`: strip the bootstrap TODO section

### Configure GitHub repo settings

- Squash-only merge (disable merge commit + rebase merge)
- Squash title = PR_TITLE, message = PR_BODY
- Disable wiki
- Branch protection on `main` (partially done)

### Missing scaffolding (low priority)

- PR template (`.github/PULL_REQUEST_TEMPLATE.md`)
- Issue templates (`.github/ISSUE_TEMPLATE/`)

### Merge bootstrap PR and tag v0.1.0

- Create PR
- Merge `bootstrap/claude-launchers` to `main`
- Create initial release tag `v0.1.0`

---

## Phase 2 — First real modules

### Extract subprocess_runner

Merge mcp_coder and mcp_tools_py versions into a single canonical implementation.

- mcp_coder contributes: heartbeat, launch_process, env_remove, get_utf8_env, FileNotFoundError/PermissionError handling
- mcp_tools_py contributes: format_command helper, structured logging via `extra={}`
- Canonical = mcp_coder as base + absorb mcp_tools_py's format_command + logging style
- Move tests alongside

### Extract subprocess_streaming

Pairs with subprocess_runner — must move together. Depends only on subprocess_runner (internal import).

### Extract log_utils

Canonical source: mcp_coder's version (superset). Features:

- Custom OUTPUT log level (25)
- CleanFormatter for CLI
- Testing-env detection
- Redaction support (`_redact_for_logging`, `log_function_call` with `sensitive_fields`)
- structlog + python-json-logger integration

Server versions (mcp_tools_py, mcp_workspace) are smaller subsets — they adopt this one.

---

## Phase 3 — Consumer adoption

### Adopt mcp-coder-utils in mcp_coder

- Add `mcp-coder-utils` to pyproject.toml dependencies
- Register as reference project in `.mcp.json`
- Add "Shared libraries" block to CLAUDE.md
- Replace `from mcp_coder.utils.subprocess_runner import ...` (and log_utils, subprocess_streaming) with `from mcp_coder_utils...`
- Delete local copies

### Adopt mcp-coder-utils in mcp_tools_py

- Add `mcp-coder-utils` to pyproject.toml dependencies
- Register as reference project in `.mcp.json`
- Add "Shared libraries" block to CLAUDE.md
- Replace local subprocess_runner + log_utils with mcp-coder-utils imports
- Delete local copies

### Adopt mcp-coder-utils in mcp_workspace

- Add `mcp-coder-utils` to pyproject.toml dependencies
- Register as reference project in `.mcp.json`
- Add "Shared libraries" block to CLAUDE.md
- Replace local log_utils with mcp-coder-utils import
- Delete local copy

### Adopt mcp-coder-utils in mcp_config

- Add `mcp-coder-utils` to pyproject.toml dependencies
- Register as reference project in `.mcp.json`
- Add "Shared libraries" block to CLAUDE.md
- Replace local subprocess_runner + file_utils with mcp-coder-utils imports
- Delete local copies

---

## Later — park until needed

### Extract fs/read_file

30-line UTF-8 → latin-1 fallback reader. Literal duplicates in mcp_tools_py and mcp_config. Trivial dedupe.

### Extract fs/path_security

`normalize_path()` from mcp_workspace's `path_utils.py`. Path traversal prevention. Different responsibility from read_file — separate module.

---

## CLAUDE.md maintenance notes

Update these CLAUDE.md sections when relevant items land:

- **Tool mapping** — add entries if new MCP tools appear
- **Pytest** — add integration markers if any are introduced
- **Reference projects** — keep in sync with `.mcp.json`
- **About this repo** — add "Public API" section listing top-level exports once Phase 2 lands
