# Step 2: Update commit_push and plan_review skills

**Ref:** [summary.md](summary.md)

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step file.
> Update the `commit_push` and `plan_review` skill files to use MCP git tools instead of bash git commands, following the specifications below exactly.

## 2A: `.claude/skills/commit_push/SKILL.md`

**WHERE:** `.claude/skills/commit_push/SKILL.md`

**WHAT — allowed-tools frontmatter:** Replace these bash entries:
- `Bash(git status *)` → `mcp__workspace__git_status`
- `Bash(git diff *)` → `mcp__workspace__git_diff`
- `Bash(git log *)` → `mcp__workspace__git_log`

Keep `Bash(git add *)`, `Bash(git commit *)`, `Bash(git push *)` — no MCP equivalent.

**WHAT — body:** Update "Review Changes" section to reference MCP tools:
- Replace the `git status` / `git diff` bash block with instructions to use `mcp__workspace__git_status` and `mcp__workspace__git_diff`

## 2B: `.claude/skills/plan_review/SKILL.md`

**WHERE:** `.claude/skills/plan_review/SKILL.md`

**WHAT — allowed-tools frontmatter:** Replace:
- `Bash(git status *)` → `mcp__workspace__git_status`

Keep `Bash(git fetch *)` — no MCP equivalent.

**WHAT — body:** Update the "ensure we're up to date" section:
- Keep `git fetch` as bash command
- Replace `git status` with `mcp__workspace__git_status`

## Verification

- No code changes → no pylint/pytest/mypy needed
- Confirm frontmatter YAML is valid
- Confirm no bash git entries remain for status/diff/log in these files
