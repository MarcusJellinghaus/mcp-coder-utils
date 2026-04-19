# Step 3: Update implementation_review, rebase skill, and rebase design doc

**Ref:** [summary.md](summary.md)

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step file.
> Update the `implementation_review` skill, `rebase` skill, and `rebase_design.md` to use MCP git tools instead of bash git commands, following the specifications below exactly.

## 3A: `.claude/skills/implementation_review/SKILL.md`

**WHERE:** `.claude/skills/implementation_review/SKILL.md`

**WHAT — allowed-tools frontmatter:** Replace these bash entries:
- `Bash(git status *)` → `mcp__workspace__git_status`
- `Bash(git diff *)` → `mcp__workspace__git_diff`
- Remove `Bash(mcp-coder git-tool *)` — replaced by `mcp__workspace__git_diff`

Keep `Bash(git fetch *)`, `Bash(mcp-coder check branch-status *)` — no MCP equivalent.

**WHAT — body:**
- In "ensure we're up to date" section: replace `git status` with `mcp__workspace__git_status`
- In "Code Review Request" section: replace `mcp-coder git-tool compact-diff` with `mcp__workspace__git_diff`

## 3B: `.claude/skills/rebase/SKILL.md`

**WHERE:** `.claude/skills/rebase/SKILL.md`

**WHAT — allowed-tools frontmatter:** Replace these bash entries:
- `Bash(git status *)` → `mcp__workspace__git_status`
- `Bash(git log *)` → `mcp__workspace__git_log`
- `Bash(git diff *)` → `mcp__workspace__git_diff`

Keep all other Bash entries (`git branch`, `git fetch`, `git rebase`, `git add`, `git rm`, `git commit`, `git checkout --ours/--theirs`, `git restore`, `git stash`, `git push --force-with-lease`, `git rev-parse`, `gh run view`, `gh issue view`, `mcp-coder gh-tool get-base-branch`) — no MCP equivalent or write operations.

**WHAT — body:**
- The `!git status` auto-run line at the top: replace with `!mcp__workspace__git_status`
- In "Pre-flight Checks" and "Workflow" sections: where `git status`, `git log`, or `git diff` appear as investigative commands, note they use MCP tools

## 3C: `.claude/skills/rebase/rebase_design.md`

**WHERE:** `.claude/skills/rebase/rebase_design.md`

**WHAT — "Rebase-Specific Permissions" section:** Replace:
- `Bash(git status:*)` → `mcp__workspace__git_status`
- `Bash(git log:*)` → `mcp__workspace__git_log`

Move these two out of the bash block and list them as MCP tools. Keep all other Bash entries in the bash block unchanged (`git branch`, `git ls-files`, `git fetch`, `git rebase`, `git add`, `git rm`, `git commit`, `git checkout --ours/--theirs`, `git restore`, `git stash`, `git push --force-with-lease`).

## Verification

- No code changes → no pylint/pytest/mypy needed
- Confirm frontmatter YAML is valid in both skill files
- Confirm `mcp-coder git-tool` references are fully removed
- Confirm no bash git entries remain for status/diff/log in these files
