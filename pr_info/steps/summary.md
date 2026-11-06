# Summary: Amend the toolkit contract before its first release (#55)

Part of MarcusJellinghaus/mcp_coder#1192. Follows #41. Blocks MarcusJellinghaus/mcp-tools-py#272 and MarcusJellinghaus/mcp_coder#1195.

## Goal

Make the contract work for any toolkit, a library or plain CLI configuration, before names become final. No tag contains the contract yet, and `PythonToolkit` is its only implementation.

## Architectural / design changes

| Area | Before | After |
|---|---|---|
| Config delivery | `describe(config)` receives it | `Toolkit(config=None)` stores it as public `self.config`, always a mapping. `describe()` takes no argument. |
| Config errors | Undefined | The constructor only stores; `verify` reports problems, so `mcp-coder verify` can show them. |
| Pre-flight | `verify(project_dir)` checks everything | `verify(project_dir, action=None)`: `None` checks everything, a name checks only that action. An overriding toolkit returns an `error` item for an undeclared action. |
| Fix prompts | `ToolkitInfo.fix_prompts` and `fix.check` | `fix.check` from `prompt_fragments()` is the only home. |
| Meaning of `findings` | Undefined; `severity` conventionally `"error"`/`"warning"` | A finding must be fixed. Informational output goes in `raw`. `severity` is the tool's own label and never decides what is a finding. |
| Meaning of `fix_text` | "Instructions for fixing" | What the fix prompt inlines, carrying everything the LLM needs, including locations. |
| Depths | Free-form, `ToolkitInfo.actions` "in order" | Position has no meaning. The caller resolves "nearest lower depth" and logs it, only within `quick < standard < full`. `unattended` and custom depths never fall back. `run` returns `error` for anything undeclared. |
| Prompt fragments | Undocumented | README defines `language_context`, `check_instructions`, `fix.check` and `check_instructions.unattended`. |

Only the first three rows change code. The rest are documentation: the base class cannot enforce them, because `run` is abstract, the depth ladder belongs to mcp-coder's core, and `PythonToolkit` adopts the rules in mcp-tools-py#272.

## Files

Modified:

- `src/mcp_coder_utils/toolkit.py`
- `tests/test_toolkit.py`
- `vulture_whitelist.py`
- `README.md`

No files or modules are created. `docs/architecture/architecture.md` only lists `toolkit.py` in the package layout, so it does not change.

## Out of scope

- A depth ladder, or any helper for checking declared actions and depths, in this library.
- `PythonToolkit` changes (mcp-tools-py#272).
- Where `fix_text` goes in the assembled prompt (mcp_coder#1197).
- A tag or release; merging to main is what consumers need.

## Merge order

Merging this turns mcp-tools-py's mypy red through `uv.sources`, because `PythonToolkit` still overrides the old signatures. Merge mcp-tools-py#272 straight after this. The window is accepted.

## Steps

One step, because the code, tests, whitelist and README describe the same contract change: [step_1.md](./step_1.md).
