# Step 3: Update CLAUDE.md reference projects and tool mapping

## References
- Summary: `pr_info/steps/summary.md`
- Issue: #15

## WHERE
- `.claude/CLAUDE.md`

## WHAT
Two edits:

1. **Reference projects section** — rename `p_mcp_coder` to `p_coder`:
   ```
   - `p_mcp_coder` — `mcp_coder` source
   ```
   →
   ```
   - `p_coder` — `mcp_coder` source
   ```

2. **Tool mapping table** — add `search_reference_files` row:
   ```
   | Search reference files | `mcp__workspace__search_reference_files` |
   ```
   Insert after the existing `Get reference projects` row.

## HOW
- Use `mcp__workspace__edit_file` with 2 edits.

## DATA
- No return values — file edit only.

## Commit
```
chore(docs): update CLAUDE.md reference project name and tool mapping
```

---

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`.
> Edit `.claude/CLAUDE.md`: (1) rename `p_mcp_coder` to `p_coder` in the reference projects list, (2) add a `Search reference files` row to the tool mapping table after `Get reference projects`. Commit with the message from the step.
> No code quality checks needed — config-only change.
