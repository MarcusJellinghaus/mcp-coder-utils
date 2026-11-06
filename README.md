# mcp-coder-utils

[![CI](https://github.com/MarcusJellinghaus/mcp-coder-utils/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/MarcusJellinghaus/mcp-coder-utils/actions/workflows/ci.yml) [![PyPI](https://img.shields.io/pypi/v/mcp-coder-utils)](https://pypi.org/project/mcp-coder-utils/) [![Python](https://img.shields.io/python/required-version-toml?tomlFilePath=https://raw.githubusercontent.com/MarcusJellinghaus/mcp-coder-utils/main/pyproject.toml)](https://pypi.org/project/mcp-coder-utils/) [![License](https://img.shields.io/github/license/MarcusJellinghaus/mcp-coder-utils)](LICENSE)

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![mypy](https://img.shields.io/badge/mypy-strict-blue)](https://mypy.readthedocs.io/) [![pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint) [![architecture](https://img.shields.io/badge/architecture-enforced-blue)](docs/architecture/enforcement.md) [![coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/MarcusJellinghaus/9a7892066964f11765a07d74285ad104/raw/mcp-coder-utils-coverage.json)](https://github.com/MarcusJellinghaus/mcp-coder-utils/actions/workflows/ci.yml)

[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/MarcusJellinghaus/mcp-coder-utils/badge)](https://scorecard.dev/viewer/?uri=github.com/MarcusJellinghaus/mcp-coder-utils) [![CodeQL](https://github.com/MarcusJellinghaus/mcp-coder-utils/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/MarcusJellinghaus/mcp-coder-utils/actions/workflows/github-code-scanning/codeql)

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
| `Toolkit` | Abstract base class with the constructor `Toolkit(config: Mapping[str, Any] \| None = None)`, which stores the toolkit's own config section as public `self.config`, always a mapping (empty when none is given). It only stores; config problems surface in `verify`. `describe()` and `run(request)` are required; `prompt_fragments()` defaults to `{}` and `verify(project_dir, action=None)` to `[]`. All four read `self.config`. |
| `ToolkitInfo` | What `describe` returns: actions with their depths, params schema, LLM permissions. |
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

- `ok` — the action ran and found nothing that must be fixed. Must carry no findings.
- `findings` — the action ran and found issues. Requires at least one finding.
- `error` — the action could not run, including an action or depth `run` doesn't declare. Findings are allowed but not required.
- `skipped` — the action did not apply. Must carry no findings.

`run` returns ordinary problems as findings, and crashes and anything undeclared as `error`. It does not raise, and it does not run something else.

A finding is something that must be fixed. Informational output, such as mypy notes, goes in `raw`. `Finding.severity` is the tool's own label, a free string that is not validated. It never decides whether something is a finding.

`fix_text` is what the fix prompt inlines. It must carry everything the LLM needs, including locations.

`VerifyItem.status` is `ok`, `warning` or `error`.

`verify(project_dir, action=None)`: `None` checks everything; an action name checks only what that action needs. A toolkit that overrides `verify` returns an `error` item for an action it doesn't declare. The base default is `[]`.

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

Depths are free-form strings defined per toolkit. `quick`, `standard` and `full` are conventions; the `format` action uses `apply` and `check`, which are custom depths.

`unattended` is a conventional depth for runs with nobody watching: skip whatever reaches external services. Only the toolkit knows how to express that. A toolkit that needs it declares it.

The caller resolves "nearest lower depth" and logs it, only within `quick < standard < full`. If no lower depth is declared, the result is an error. Position in `ToolkitInfo.actions` has no meaning. `unattended` and custom depths never fall back.

`run` has no ladder: it returns `error` for any action or depth it doesn't declare.

### Prompt fragments

`prompt_fragments()` returns text for mcp-coder's prompts, keyed by name:

| Key | Meaning |
|-----|---------|
| `language_context` | What kind of project this is. |
| `check_instructions` | How the LLM re-runs the checks. |
| `fix.check` | The fix prompt for the `check` action, and the only home for fix prompts. |
| `check_instructions.unattended` | Text the LLM needs in order to re-run tests the way `unattended` does. |

An empty fragment drops its paragraph, and a missing one uses neutral text. A toolkit that omits `fix.check` disables that fix loop. Where `fix_text` goes in the assembled prompt is left to MarcusJellinghaus/mcp_coder#1197.

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
