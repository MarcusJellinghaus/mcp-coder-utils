# Step 3 — README and architecture documentation

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` only
> (steps 1–2 are done). Documentation only — no code changes. Keep it concise.
> Run pylint, pytest (`-n auto`) and mypy via the MCP tools to confirm nothing broke.
> Run format_code, then make exactly one commit.

## WHERE

- `README.md` — new section `## Toolkit interface` after `## Install`
- `docs/architecture/architecture.md` — add `toolkit.py` to the package layout block

## WHAT (README section contents)

1. **Purpose** — one sentence: the contract between mcp-coder and toolkits
   (`from mcp_coder_utils.toolkit import ...`).
2. **Public API** — short table: `Toolkit` (`describe`, `run` required;
   `prompt_fragments` → `{}`, `verify` → `[]` defaults), `ToolkitInfo`, `ActionRequest`,
   `ActionResult`, `Finding`, `VerifyItem`, `ActionStatus`, `VerifyStatus`, `JsonSchema`,
   `validate_params`.
3. **Status rules** — meanings of `ok`/`findings`/`error`/`skipped`; `findings` needs ≥1
   finding, `ok`/`skipped` carry none, `error` is permissive. `VerifyItem` status:
   `ok`/`warning`/`error`. `Finding.severity` is a free string (conventionally
   `"error"`/`"warning"`), not validated.
4. **Mutability** — `ActionRequest`, `Finding` frozen (shallow: `params` may be mutable);
   other types mutable. Validation runs only at construction, so code that merges results
   must build a new `ActionResult`.
5. **Parameters schema** — JSON Schema draft 2020-12 (always validated as 2020-12,
   `$schema` ignored); top level must be `"type": "object"` with
   `"additionalProperties": false`; nested objects are the toolkit's responsibility;
   errors are `ValueError`.
6. **Registration** — entry-point group `mcp_coder.toolkits`; the key is the toolkit's
   only identifier and the value users write as `toolkit = "..."`. Short
   `pyproject.toml` example:
   ```toml
   [project.entry-points."mcp_coder.toolkits"]
   mcp-tools-py = "mcp_tools_py.toolkit:PythonToolkit"
   ```
7. **Depths** — free-form strings per toolkit; `quick`/`standard`/`full` are
   conventions; `format` uses `apply`/`check`.
8. **Versioning** — no `api_version`; toolkits pin `mcp-coder-utils`. A contract-breaking
   change requires a major release here and coordinated bumps in toolkit repos.

## HOW / ALGORITHM / DATA

Not applicable (documentation only).
