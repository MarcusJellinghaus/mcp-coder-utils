# Step 1: Update settings.local.json and CLAUDE.md

**Ref:** [summary.md](summary.md)

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step file.
> Update `.claude/settings.local.json` and `.claude/CLAUDE.md` to prefer MCP git tools over bash git commands, following the specifications below exactly.

## 1A: `.claude/settings.local.json`

**WHERE:** `.claude/settings.local.json`

**WHAT — Remove these 4 entries from `permissions.allow`:**
- `Bash(git diff:*)`
- `Bash(git log:*)`
- `Bash(git status:*)`
- `Bash(mcp-coder git-tool:*)`

**WHAT — Add these 4 entries to `permissions.allow`:**
- `mcp__workspace__git_log`
- `mcp__workspace__git_diff`
- `mcp__workspace__git_status`
- `mcp__workspace__git_merge_base`

**WHAT — Keep unchanged:**
- `Bash(git fetch:*)`
- `Bash(git ls-tree:*)`
- `Bash(find:*)`
- All other existing entries

## 1B: `.claude/CLAUDE.md`

**WHERE:** `.claude/CLAUDE.md`, "Git operations" section (starts at line 65)

**WHAT:** Replace the current single-block git section with two blocks:

```markdown
## Git operations

**MCP tools (preferred):**

| Task | MCP tool |
|------|----------|
| Git status | `mcp__workspace__git_status` |
| Git diff | `mcp__workspace__git_diff` |
| Git log | `mcp__workspace__git_log` |
| Git merge-base | `mcp__workspace__git_merge_base` |

**Bash (no MCP equivalent):**

```
git commit / fetch / show / ls-tree
mcp-coder check branch-status      # CI status, rebase needs, task completion, labels
mcp-coder check file-size           # find files exceeding line-count threshold
mcp-coder gh-tool set-status <label>  # change issue workflow status label
```
```

Keep all content before and after the git section unchanged (including "Before every commit", "Bash discipline", "Commit messages" paragraphs).

## Verification

- No code changes → no pylint/pytest/mypy needed
- Visually confirm JSON is valid
- Confirm no removed entries remain, no duplicates introduced
