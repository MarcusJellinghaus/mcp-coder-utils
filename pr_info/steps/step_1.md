# Step 1: Amend the toolkit contract and document it

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`, then implement step 1 of issue #55. Write the tests first and confirm the new ones fail, then change the code, whitelist and README. Run the checks listed in this step, then write the commit message to `pr_info/.commit_message.txt`. Keep to the listed files.

## WHERE

- `tests/test_toolkit.py`
- `src/mcp_coder_utils/toolkit.py`
- `vulture_whitelist.py`
- `README.md`

## Tests first: `tests/test_toolkit.py`

- `_MinimalToolkit.describe` becomes `def describe(self) -> ToolkitInfo`.
- Remove the imports this leaves unused: `from collections.abc import Mapping` and `from typing import Any`.
- `TestToolkitInfo.test_valid_schema`: remove `assert info.fix_prompts == {}`.
- `TestToolkit`: keep `test_is_abstract`, and cover:

```python
def test_config_defaults_to_empty_mapping(self) -> None:
    assert _MinimalToolkit().config == {}

def test_config_is_stored(self) -> None:
    config = {"argv": ["npm", "test"]}
    assert _MinimalToolkit(config).config == config

def test_defaults(self, tmp_path: Path) -> None:
    toolkit = _MinimalToolkit()
    assert toolkit.prompt_fragments() == {}
    assert toolkit.verify(tmp_path) == []
    assert toolkit.verify(tmp_path, action="format") == []
```

Add one-line docstrings matching the file's style. Do not add a test for the absence of `fix_prompts`.

## WHAT: `src/mcp_coder_utils/toolkit.py`

```python
class Toolkit(ABC):
    def __init__(self, config: Mapping[str, Any] | None = None) -> None: ...
    @abstractmethod
    def describe(self) -> ToolkitInfo: ...
    @abstractmethod
    def run(self, request: ActionRequest) -> ActionResult: ...
    def prompt_fragments(self) -> dict[str, str]: ...
    def verify(self, project_dir: Path, action: str | None = None) -> list[VerifyItem]: ...
```

Remove the `fix_prompts` field from `ToolkitInfo`, and its `Attributes` line.

## ALGORITHM

```
__init__:
    self.config = {} if config is None else config   # no validation, never raises
verify (base):
    return []
```

Use `{} if config is None else config`, not `config or {}`, so an empty mapping passed by the caller is kept.

## HOW: docstrings

| Target | New content |
|---|---|
| `Toolkit` class | Replace the sentence saying `describe` receives config with: the constructor stores the toolkit's own config section. Keep the rest. |
| `Toolkit.__init__` | Stores the section as public `self.config`, always a mapping. It only stores; config problems surface in `verify`. |
| `Toolkit.describe` | Remove the `Args` section. |
| `Toolkit.run` | Returns status "error" for an action or depth it doesn't declare, rather than raising or running something else. |
| `Toolkit.verify` | `Args` entry for `action`: `None` checks everything; a name checks only what that action needs. An overriding toolkit returns an "error" item for an action it doesn't declare. |
| `Finding` class | Something that must be fixed. Informational output, such as mypy notes, goes in `ActionResult.raw`. |
| `Finding.severity` | The tool's own label, free-form and not validated. It never decides whether something is a finding. |
| `ActionResult.fix_text` | What the fix prompt inlines. Must carry everything the LLM needs, including locations. |
| `ToolkitInfo.actions` | Action name mapped to its supported depths. Position has no meaning. |

## HOW: `vulture_whitelist.py`

Remove the `Toolkit.describe.config` line. Run `mcp__mcp-tools-py__run_vulture_check`, and add `Toolkit.config  # noqa` only if vulture flags it.

## DATA: `README.md`, under "Toolkit interface"

No new data structures. `self.config` is a `Mapping[str, Any]`, and `verify` still returns `list[VerifyItem]`.

**Public API table**

- `Toolkit` row: abstract base class with the constructor `Toolkit(config: Mapping[str, Any] | None = None)`, which stores the toolkit's own config section as public `self.config`, always a mapping (empty when none is given). It only stores; config problems surface in `verify`. `describe()` and `run(request)` are required; `prompt_fragments()` defaults to `{}` and `verify(project_dir, action=None)` to `[]`. All four read `self.config`.
- `ToolkitInfo` row: remove "fix prompts".
- `VerifyItem` row: stays. State the `verify` rules under "Status rules" below.

**Status rules: edit the existing section, with no new subsections**

- `ok`: the action ran and found nothing that must be fixed. Must carry no findings.
- `error`: the action could not run, including an action or depth `run` doesn't declare. Findings are allowed but not required.
- `run` returns ordinary problems as findings, and crashes and anything undeclared as `error`. It does not raise, and it does not run something else.
- A finding is something that must be fixed. Informational output, such as mypy notes, goes in `raw`.
- `Finding.severity` is the tool's own label, a free string that is not validated. It never decides whether something is a finding. Remove the `"error"`/`"warning"` convention.
- `fix_text` is what the fix prompt inlines. It must carry everything the LLM needs, including locations.
- `verify(project_dir, action=None)`: `None` checks everything; an action name checks only what that action needs. A toolkit that overrides `verify` returns an `error` item for an action it doesn't declare. The base default is `[]`.

**Depths: extend the existing section**

- `quick`, `standard` and `full` are conventions; the `format` action uses `apply` and `check`, which are custom depths.
- `unattended` is a conventional depth for runs with nobody watching: skip whatever reaches external services. Only the toolkit knows how to express that. A toolkit that needs it declares it.
- The caller resolves "nearest lower depth" and logs it, only within `quick < standard < full`. If no lower depth is declared, the result is an error. Position in `ToolkitInfo.actions` has no meaning.
- `unattended` and custom depths never fall back.
- `run` has no ladder: it returns `error` for any action or depth it doesn't declare.

**New section "Prompt fragments", after "Depths"**

`prompt_fragments()` returns text for mcp-coder's prompts, keyed by name:

| Key | Meaning |
|---|---|
| `language_context` | What kind of project this is. |
| `check_instructions` | How the LLM re-runs the checks. |
| `fix.check` | The fix prompt for the `check` action, and the only home for fix prompts. |
| `check_instructions.unattended` | Text the LLM needs in order to re-run tests the way `unattended` does. |

An empty fragment drops its paragraph, and a missing one uses neutral text. A toolkit that omits `fix.check` disables that fix loop. Where `fix_text` goes in the assembled prompt is left to MarcusJellinghaus/mcp_coder#1197.

## Checks

Run in this order, all of which must pass:

1. `mcp__mcp-tools-py__run_pytest_check` with `extra_args: ["-n", "auto"]`
2. `mcp__mcp-tools-py__run_pylint_check`
3. `mcp__mcp-tools-py__run_mypy_check`
4. `mcp__mcp-tools-py__run_vulture_check`

If a check fails on code outside the listed files, write one line to `pr_info/.blocked.txt` and stop.

## Commit

Write this message to `pr_info/.commit_message.txt`. The mcp-coder implement workflow formats and commits.

```
feat(toolkit): amend the contract before its first release
```
