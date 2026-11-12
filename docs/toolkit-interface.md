# Toolkit interface

`mcp_coder_utils.toolkit` is the contract between mcp-coder and the toolkits it runs (`from mcp_coder_utils.toolkit import ...`).

## Public API

| Name | Purpose |
|------|---------|
| `Toolkit` | Abstract base class with the constructor `Toolkit(config: Mapping[str, Any] \| None = None)`, which stores the toolkit's own config section as public `self.config`, always a mapping (empty when none is given). It only stores; config problems surface in `verify`. `describe()` and `run(request)` are required; `prompt_fragments()` defaults to `{}` and `verify(project_dir, action=None)` to `[]`. All four read `self.config`. |
| `ToolkitInfo` | What `describe` returns: actions with their depths, params schema, LLM permissions. |
| `ActionRequest` | Input to `run`: action, depth, project directory, params. |
| `ActionResult` | Output of `run`: status, summary, findings, fix text, raw output. |
| `Finding` | One issue reported by an action. |
| `VerifyItem` | One check returned by `verify`. Lives in `mcp_coder_utils.tool_verify`; re-exported here. |
| `ActionStatus` | `Literal["ok", "findings", "error", "skipped"]` |
| `VerifyStatus` | `Literal["ok", "warning", "error"]`. Lives in `mcp_coder_utils.tool_verify`; re-exported here. |
| `JsonSchema` | Alias for `dict[str, Any]`. |
| `validate_params` | Validates params against a schema; raises `ValueError`. |

## Status rules

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

## Mutability

`ActionRequest` and `Finding` are frozen. Freezing is shallow, so `params` may still be a mutable mapping. The other types are mutable, but validation runs only at construction: code that merges results must build a new `ActionResult` rather than mutate one.

## Parameters schema

`ToolkitInfo.params_schema` is a JSON Schema, always validated as draft 2020-12; `$schema` is ignored. The top level must have `"type": "object"` and `"additionalProperties": false`. Closing nested objects is the toolkit's responsibility. Schema and params errors raise `ValueError`.

## Registration

Toolkits register under the entry-point group `mcp_coder.toolkits`. The entry-point key is the toolkit's only identifier and is the value users write as `toolkit = "..."`.

```toml
[project.entry-points."mcp_coder.toolkits"]
mcp-tools-py = "mcp_tools_py.toolkit:PythonToolkit"
```

## Depths

Depths are free-form strings defined per toolkit. `quick`, `standard` and `full` are conventions; the `format` action uses `apply` and `check`, which are custom depths.

`unattended` is a conventional depth for runs with nobody watching: skip whatever reaches external services. Only the toolkit knows how to express that. A toolkit that needs it declares it.

The caller resolves "nearest lower depth" and logs it, only within `quick < standard < full`. If no lower depth is declared, the result is an error. Position in `ToolkitInfo.actions` has no meaning. `unattended` and custom depths never fall back.

`run` has no ladder: it returns `error` for any action or depth it doesn't declare.

## Prompt fragments

`prompt_fragments()` returns text for mcp-coder's prompts, keyed by name:

| Key | Meaning |
|-----|---------|
| `language_context` | What kind of project this is. |
| `check_instructions` | How the LLM re-runs the checks. |
| `check_instructions.unattended` | Text the LLM needs in order to re-run tests the way `unattended` does. |
| `fix.check` | The fix prompt for the `check` action. |
| `fix.test` | The fix prompt for the `test` action. |

`fix.*` fragments are the only place a toolkit supplies fix prompts.

Missing and empty fragments:

- `language_context`, `check_instructions`: an empty fragment drops its paragraph, and a missing one uses neutral text.
- `check_instructions.unattended`: missing or empty, the caller adds no unattended instruction.
- `fix.check`, `fix.test`: missing or empty, findings of that action can't be fixed, so the caller fails them.

When the caller uses a `fix.*` fragment, it appends `fix_text` after the fragment under a heading of its own. Fragments carry no placeholder.

## Versioning

There is no `api_version`; toolkits pin `mcp-coder-utils`. A contract-breaking change requires a major release here and coordinated version bumps in the toolkit repos.
