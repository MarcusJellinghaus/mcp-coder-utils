# mcp-coder-utils

Shared low-level Python helpers (subprocess, logging, fs) for the mcp-coder family of repos.

Leaf library: no internal dependencies, language-agnostic, safe to import from any MCP server or client in the mcp-coder ecosystem.

## Install

```bash
pip install mcp-coder-utils
```

## Toolkit interface

`mcp_coder_utils.toolkit` is the contract between mcp-coder and the toolkits it runs (`from mcp_coder_utils.toolkit import ...`).

### Public API

| Name | Purpose |
|------|---------|
| `Toolkit` | Abstract base class. `describe` and `run` are required; `prompt_fragments` defaults to `{}` and `verify` to `[]`. |
| `ToolkitInfo` | What `describe` returns: actions with their depths, params schema, LLM permissions, fix prompts. |
| `ActionRequest` | Input to `run`: action, depth, project directory, params. |
| `ActionResult` | Output of `run`: status, summary, findings, fix text, raw output. |
| `Finding` | One issue reported by an action. |
| `VerifyItem` | One check returned by `verify`. |
| `ActionStatus` | `Literal["ok", "findings", "error", "skipped"]` |
| `VerifyStatus` | `Literal["ok", "warning", "error"]` |
| `JsonSchema` | Alias for `dict[str, Any]`. |
| `validate_params` | Validates params against a schema; raises `ValueError`. |

### Status rules

`ActionResult.status`:

- `ok` — the action ran and found nothing. Must carry no findings.
- `findings` — the action ran and found issues. Requires at least one finding.
- `error` — the action could not run. Findings are allowed but not required.
- `skipped` — the action did not apply. Must carry no findings.

`run` returns ordinary problems as findings and crashes as `error`; it does not raise.

`VerifyItem.status` is `ok`, `warning` or `error`. `Finding.severity` is a free string, conventionally `"error"` or `"warning"`, and is not validated.

### Mutability

`ActionRequest` and `Finding` are frozen. Freezing is shallow, so `params` may still be a mutable mapping. The other types are mutable, but validation runs only at construction: code that merges results must build a new `ActionResult` rather than mutate one.

### Parameters schema

`ToolkitInfo.params_schema` is a JSON Schema, always validated as draft 2020-12; `$schema` is ignored. The top level must have `"type": "object"` and `"additionalProperties": false`. Closing nested objects is the toolkit's responsibility. Schema and params errors raise `ValueError`.

### Registration

Toolkits register under the entry-point group `mcp_coder.toolkits`. The entry-point key is the toolkit's only identifier and is the value users write as `toolkit = "..."`.

```toml
[project.entry-points."mcp_coder.toolkits"]
mcp-tools-py = "mcp_tools_py.toolkit:PythonToolkit"
```

### Depths

Depths are free-form strings defined per toolkit. `quick`, `standard` and `full` are conventions; the `format` action uses `apply` and `check`.

### Versioning

There is no `api_version`; toolkits pin `mcp-coder-utils`. A contract-breaking change requires a major release here and coordinated version bumps in the toolkit repos.

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
