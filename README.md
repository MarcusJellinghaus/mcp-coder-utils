# mcp-coder-utils

[![CI](https://github.com/MarcusJellinghaus/mcp-coder-utils/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/MarcusJellinghaus/mcp-coder-utils/actions/workflows/ci.yml) [![PyPI](https://img.shields.io/pypi/v/mcp-coder-utils)](https://pypi.org/project/mcp-coder-utils/) [![Python](https://img.shields.io/python/required-version-toml?tomlFilePath=https://raw.githubusercontent.com/MarcusJellinghaus/mcp-coder-utils/main/pyproject.toml)](https://pypi.org/project/mcp-coder-utils/) [![License](https://img.shields.io/github/license/MarcusJellinghaus/mcp-coder-utils)](LICENSE)

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![mypy](https://img.shields.io/badge/mypy-strict-blue)](https://mypy.readthedocs.io/) [![pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint) [![architecture](https://img.shields.io/badge/architecture-enforced-blue)](docs/architecture/enforcement.md) [![coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/MarcusJellinghaus/9a7892066964f11765a07d74285ad104/raw/mcp-coder-utils-coverage.json)](https://github.com/MarcusJellinghaus/mcp-coder-utils/actions/workflows/ci.yml)

[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/MarcusJellinghaus/mcp-coder-utils/badge)](https://scorecard.dev/viewer/?uri=github.com/MarcusJellinghaus/mcp-coder-utils) [![CodeQL](https://github.com/MarcusJellinghaus/mcp-coder-utils/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/MarcusJellinghaus/mcp-coder-utils/actions/workflows/github-code-scanning/codeql)

Shared low-level Python helpers (subprocess, logging, fs) and tool contracts (toolkit, tool spec, toolset provider) for the mcp-coder family of repos.

Leaf library: no internal dependencies, language-agnostic, safe to import from any MCP server or client in the mcp-coder ecosystem.

## Install

```bash
pip install mcp-coder-utils
```

## Modules

| Module | Purpose |
|--------|---------|
| `subprocess_runner` | Run commands with timeouts, UTF-8 and Python STDIO isolation (`execute_command`, `execute_subprocess`, `launch_process`). |
| `subprocess_streaming` | Stream a subprocess's stdout line by line, with an inactivity watchdog that kills hung processes (`stream_subprocess`). |
| `log_utils` | Logging setup and formatters (`setup_logging`, `log_function_call`). |
| `redaction` | Mask secrets before logging (`redact_for_logging`, `redact_env_vars`, `token_fingerprint`). |
| `fs` | Read a file as UTF-8 with a latin-1 fallback, reject paths outside a root, convert CRLF/CR to LF (`read_file`, `normalize_path`, `normalize_line_endings`). |
| `user_app_data` | Per-user data directory, `~/.<app_name>/` (`get_user_app_data_dir`). |
| `toolkit` | Contract between mcp-coder and its toolkits; see [Toolkit interface](#toolkit-interface). |
| `tool_spec` | Tools as plain data, shared by MCP and non-MCP consumers; see [Tool contract](#tool-contract). |
| `tool_provider` | Contract for tool packages loaded as plugins; see [Toolset providers](#toolset-providers). |
| `tool_verify` | `VerifyItem` / `VerifyStatus`, the check rows returned by `verify` in toolkits and toolset providers. |

## Toolkit interface

`mcp_coder_utils.toolkit` is the contract between mcp-coder and the toolkits it runs (`from mcp_coder_utils.toolkit import ...`). A toolkit subclasses `Toolkit`, describes the actions and depths it offers, runs one `(action, depth)` at a time and returns an `ActionResult` with findings and fix text. It also supplies prompt fragments and checks its own setup. Toolkits register under the entry-point group `mcp_coder.toolkits`.

The full contract — types, status rules, depths, prompt fragments, versioning — is in [docs/toolkit-interface.md](https://github.com/MarcusJellinghaus/mcp-coder-utils/blob/main/docs/toolkit-interface.md).

## Tool contract

`mcp_coder_utils.tool_spec` describes tools as plain data, so an MCP server and a non-MCP app (e.g. LangGraph) see the same tool. A producer wraps each function with `tool_spec(fn, group=..., read_only=...)` and adds it to a `ToolSink`; consumers iterate a `ToolCollector` and register each `ToolSpec` their own way.

The full contract — types, signature rules, an example with an MCP and a non-MCP consumer — is in [docs/tool-contract.md](https://github.com/MarcusJellinghaus/mcp-coder-utils/blob/main/docs/tool-contract.md).

## Toolset providers

`mcp_coder_utils.tool_provider` is the contract between a consumer (e.g. agent-workbench) and the tool packages it loads as plugins. The consumer finds a provider by name through an entry point, passes it its own config table, and gets tool specs plus something to close. A provider subclasses `ToolsetProvider`: `verify` checks the config, `build` returns a `Toolset`.

The full contract — types, rules, registration, versioning and an example — is in [docs/toolset-providers.md](https://github.com/MarcusJellinghaus/mcp-coder-utils/blob/main/docs/toolset-providers.md).

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
- [mcp-tools-sql](https://github.com/MarcusJellinghaus/mcp-tools-sql) — tool package: SQL tools
- [agent-workbench](https://github.com/MarcusJellinghaus/agent-workbench) — chat app: loads tool packages as plugins
