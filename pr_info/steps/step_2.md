# Step 2: Add obsidian-wiki and search_reference_files permissions

## References
- Summary: `pr_info/steps/summary.md`
- Issue: #15

## WHERE
- `.claude/settings.local.json` — the `permissions.allow` array

## WHAT
Add 12 new permission strings to the `allow` array and sort the entire array alphabetically:

```json
"mcp__obsidian-wiki__add-tags",
"mcp__obsidian-wiki__create-directory",
"mcp__obsidian-wiki__create-note",
"mcp__obsidian-wiki__delete-note",
"mcp__obsidian-wiki__edit-note",
"mcp__obsidian-wiki__list-available-vaults",
"mcp__obsidian-wiki__move-note",
"mcp__obsidian-wiki__read-note",
"mcp__obsidian-wiki__remove-tags",
"mcp__obsidian-wiki__rename-tag",
"mcp__obsidian-wiki__search-vault",
"mcp__workspace__search_reference_files"
```

## HOW
- Add the 12 new entries to the array, then sort all entries in the array alphabetically.

## DATA
- No return values — file edit only.

## Commit
```
chore(config): add obsidian-wiki and search_reference_files permissions
```

---

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`.
> Edit `.claude/settings.local.json`: add the 12 new permission strings listed in the step to the `permissions.allow` array and sort the entire array alphabetically. Commit with the message from the step.
> No code quality checks needed — config-only change.
