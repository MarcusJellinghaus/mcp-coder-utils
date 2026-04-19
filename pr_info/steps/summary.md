# Summary: Prefer MCP git tools over bash git commands

**Issue:** #16

## Goal

Replace bash git commands (`git status`, `git diff`, `git log`) with MCP workspace tools (`mcp__workspace__git_status`, `mcp__workspace__git_diff`, `mcp__workspace__git_log`, `mcp__workspace__git_merge_base`) across Claude configuration and skill files. MCP tools run without permission prompts, improving automated workflows.

Also remove `Bash(mcp-coder git-tool:*)` — its `compact-diff` functionality is replaced by `mcp__workspace__git_diff`.

## Architectural changes

- **Permission model shift:** Read-only git operations move from Bash allowlist to MCP tool allowlist in `settings.local.json`. This narrows the Bash permission surface.
- **Skill tool declarations:** Skills declare MCP tools instead of Bash git patterns in their `allowed-tools` frontmatter. Body instructions reference MCP tool names instead of bash commands.
- **CLAUDE.md git section:** Restructured into two blocks — MCP tools (preferred) and Bash (no MCP equivalent) — making the preference hierarchy explicit.

## No code changes

This is purely a config/documentation update. No Python source code, no tests.

## Files modified

| File | Change |
|------|--------|
| `.claude/settings.local.json` | Remove 4 Bash permissions, add 4 MCP tools |
| `.claude/CLAUDE.md` | Restructure git operations section |
| `.claude/skills/commit_push/SKILL.md` | Swap 3 Bash git → 3 MCP tools |
| `.claude/skills/implementation_review/SKILL.md` | Swap 3 Bash entries → 2 MCP tools |
| `.claude/skills/plan_review/SKILL.md` | Swap 1 Bash git → 1 MCP tool |
| `.claude/skills/rebase/SKILL.md` | Swap 3 Bash git → 3 MCP tools |
| `.claude/skills/rebase/rebase_design.md` | Update 2 entries in permissions section |

No files created or deleted.

## Steps

1. **Settings + CLAUDE.md** — Update global config and documentation
2. **commit_push + plan_review skills** — Simple skills with minimal body changes
3. **implementation_review + rebase skills** — Skills with more body content to update
