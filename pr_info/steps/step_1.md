# Step 1: Migrate .mcp.json reference projects to new KV format

## References
- Summary: `pr_info/steps/summary.md`
- Issue: #15

## WHERE
- `.mcp.json` — the `workspace.args` array

## WHAT
Replace 4 `--reference-project` value strings from old format to new KV format with URLs.

### Old → New mapping

| Old value | New value |
|-----------|-----------|
| `p_mcp_coder=${USERPROFILE}\\Documents\\GitHub\\mcp_coder` | `name=p_coder,path=${USERPROFILE}\\Documents\\GitHub\\mcp_coder,url=https://github.com/MarcusJellinghaus/mcp_coder` |
| `p_workspace=${USERPROFILE}\\Documents\\GitHub\\mcp-workspace` | `name=p_workspace,path=${USERPROFILE}\\Documents\\GitHub\\mcp-workspace,url=https://github.com/MarcusJellinghaus/mcp-workspace` |
| `p_config=${USERPROFILE}\\Documents\\GitHub\\mcp-config` | `name=p_config,path=${USERPROFILE}\\Documents\\GitHub\\mcp-config,url=https://github.com/MarcusJellinghaus/mcp-config` |
| `p_tools=${USERPROFILE}\\Documents\\GitHub\\mcp-tools-py` | `name=p_tools,path=${USERPROFILE}\\Documents\\GitHub\\mcp-tools-py,url=https://github.com/MarcusJellinghaus/mcp-tools-py` |

## HOW
- Use `mcp__workspace__edit_file` with 4 edits (one per reference project string).
- Preserve `\\` backslash escaping throughout.

## DATA
- No return values — file edit only.

## Commit
```
chore(config): migrate .mcp.json reference projects to new KV format
```

---

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`.
> Edit `.mcp.json`: replace the 4 `--reference-project` value strings with the new KV format as specified in the step. Rename `p_mcp_coder` to `p_coder`. Preserve backslash escaping. Commit with the message from the step.
> No code quality checks needed — config-only change.
