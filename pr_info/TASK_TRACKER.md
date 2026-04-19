# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Migrate .mcp.json reference projects to new KV format
> [Details](./steps/step_1.md) — Replace 4 `--reference-project` value strings with new `name=...,path=...,url=...` KV format; rename `p_mcp_coder` → `p_coder`

- [x] Implementation (edit `.mcp.json` with 4 reference project string replacements)
- [x] Commit message prepared

**Commit message:** `chore(config): migrate .mcp.json reference projects to new KV format`

### Step 2: Add obsidian-wiki and search_reference_files permissions
> [Details](./steps/step_2.md) — Add 12 new permission strings to `.claude/settings.local.json` and sort array alphabetically

- [ ] Implementation (add 12 permissions to `allow` array, sort alphabetically)
- [ ] Commit message prepared

### Step 3: Update CLAUDE.md reference projects and tool mapping
> [Details](./steps/step_3.md) — Rename `p_mcp_coder` → `p_coder` in reference projects; add `search_reference_files` to tool mapping table

- [ ] Implementation (2 edits to `.claude/CLAUDE.md`)
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: verify all 3 config files are updated correctly
- [ ] PR summary prepared
