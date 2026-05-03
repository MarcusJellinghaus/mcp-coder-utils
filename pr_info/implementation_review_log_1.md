# Implementation Review Log — chore/round-2026-05

**Branch:** `chore/round-2026-05`
**Base:** `main`
**Started:** 2026-05-03

This branch is a batched-chore round (no GitHub issue, no plan files).
Review scope: the diff `main..HEAD` (7 commits — MCP key renames, Unix launchers,
.venv activation, gitignore unblocking, CI permissions, sleep tool, supervisor
skill propagation).

## Round 1 — 2026-05-03

**Findings:**
- `.claude/settings.local.json` — `mcp__mcp-tools-py__sleep` not in `permissions.allow` (used by issue_analyse skill).
- `.claude/skills/issue_analyse/SKILL.md` — 1-second sleep step has no documented rationale (YAGNI risk).
- `claude.sh:53` — exports `VIRTUAL_ENV` in self-hosting fallback without sourcing activate; misleading.
- `tools/reinstall_local.sh:1` — shebang `#!/bin/bash` inconsistent with sibling scripts (`#!/usr/bin/env bash`).
- `.github/workflows/ci.yml`, `.gitignore`, default `CLAUDE_BIN`, supervisor skill wording — no defects, leave as-is.

**Decisions:**
- **Accept** — sleep allowlist gap, sleep rationale (investigate), `claude.sh` `VIRTUAL_ENV`, `reinstall_local.sh` shebang.
- **Skip** — CI permissions (correctly scoped), gitignore (preparatory only, no leaks), `CLAUDE_BIN` default (env-var override available), supervisor wording (consistent post-rename).

**Changes:**
- Engineer investigated: no preceding write op precedes the sleep — it's a local file read followed by `github_issue_view`. No race condition exists. **Removed** the sleep step and removed `mcp__mcp-tools-py__sleep` from the SKILL.md frontmatter `allowed-tools`.
- Settings allowlist fix **skipped** as a consequence (tool no longer used by any skill).
- `claude.sh` — added a 2-line comment above the `VIRTUAL_ENV` export documenting it as informational; `PATH` is set explicitly later.
- `tools/reinstall_local.sh` — shebang normalized to `#!/usr/bin/env bash`.
- Quality checks: format (clean), pylint (clean), pytest 193/193, mypy (clean).

**Status:** committed (round 1 fixes) — `6162831`.

## Round 2 — 2026-05-03

**Findings:** none. Round 1 fixes verified clean (SKILL.md flow intact, claude.sh comment well-formed, shebang correct). Repo-wide search for old MCP key prefixes (`mcp__workspace__`, `mcp__tools-py__`) returned zero matches — rename is complete.

**Status:** no changes. Loop terminates.

## Final Status

- **Rounds run:** 2 (round 1 produced 3 fixes, round 2 was clean).
- **Commits added by review:** 1 (`6162831`).
- **Quality checks:** pylint clean, pytest 193/193, mypy clean, format clean.
- **Branch state:** ahead of `origin/chore/round-2026-05` by 1 commit (review fixes), plus this log commit pending.

