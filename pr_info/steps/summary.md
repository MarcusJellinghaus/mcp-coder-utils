# Issue #15: Migrate .mcp.json to new KV format and add permissions

## Summary

Migrate MCP workspace reference project configuration from deprecated `name=path` format to the new `name=...,path=...,url=...` KV format. Add obsidian-wiki MCP permissions and `search_reference_files` permission. Update CLAUDE.md documentation to match.

## Architectural / Design Changes

- **No code changes** — config-only PR across three files.
- **Reference project naming**: `p_mcp_coder` shortened to `p_coder` for consistency with `p_tools`, `p_config`, `p_workspace`.
- **Reference project metadata**: Each reference project now carries a `url` field pointing to its GitHub repo, enabling mcp-workspace to provide repo URL context.
- **New MCP server permissions**: 11 obsidian-wiki tool permissions and 1 workspace tool permission added, enabling Claude to use these tools without per-call approval when the servers are configured.

## Files Modified

| File | Change |
|------|--------|
| `.mcp.json` | Migrate 4 `--reference-project` args to new KV format with URLs; rename `p_mcp_coder` → `p_coder` |
| `.claude/settings.local.json` | Add 12 new permissions to `allow` array and sort alphabetically |
| `.claude/CLAUDE.md` | Rename `p_mcp_coder` → `p_coder` in reference projects section; add `search_reference_files` to tool mapping table |

## Implementation Steps

| Step | File | Description |
|------|------|-------------|
| 1 | `.mcp.json` | Migrate reference projects to new KV format |
| 2 | `.claude/settings.local.json` | Add obsidian-wiki and search_reference_files permissions |
| 3 | `.claude/CLAUDE.md` | Update reference project name and tool mapping |

## Constraints

- No code changes → no pylint/pytest/mypy checks required.
- Windows paths use escaped backslashes (`\\`) in `.mcp.json` — must be preserved.
- No TDD applicable — pure config file edits.
