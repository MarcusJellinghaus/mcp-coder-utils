# mcp-coder-utils

Shared low-level Python helpers (subprocess, logging, fs) for the mcp-coder family of repos.

Leaf library: no internal dependencies, language-agnostic, safe to import from any MCP server or client in the mcp-coder ecosystem.

## Install

```bash
pip install mcp-coder-utils
```

## Development

```bash
tools\reinstall_local.bat
```

This creates a local `.venv`, installs the package in editable mode with dev dependencies, and overrides the sibling repos (`mcp-coder`, `mcp-tools-py`, `mcp-workspace`) with their latest GitHub versions.

## Related repos

- [mcp_coder](https://github.com/MarcusJellinghaus/mcp_coder) — CLI client and workflows
- [mcp-tools-py](https://github.com/MarcusJellinghaus/mcp-tools-py) — MCP server: Python code checks
- [mcp-workspace](https://github.com/MarcusJellinghaus/mcp-workspace) — MCP server: file operations
- [mcp-config](https://github.com/MarcusJellinghaus/mcp-config) — MCP client config CLI
