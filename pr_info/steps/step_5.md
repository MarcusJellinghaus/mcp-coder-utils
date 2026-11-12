# Step 5 — README: `## Toolset providers` section and Toolkit interface rows

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_5.md`
> exactly. README only; no tests to write. Model the new section on the
> existing `## Toolkit interface` and `## Tool contract` sections. Run the
> checks listed at the end; all must pass. Produce one commit:
> `docs(readme): document the toolset provider contract`.

## Precondition

If `src/mcp_coder_utils/tool_provider.py` does not exist (step 2 not done),
write one line to `pr_info/.blocked.txt` and stop.

## WHERE

`README.md` only.

## WHAT

### `## Toolkit interface` → Public API table

Replace the two rows:

```
| `VerifyItem` | One check returned by `verify`. Lives in `mcp_coder_utils.tool_verify`; re-exported here. |
| `VerifyStatus` | `Literal["ok", "warning", "error"]`. Lives in `mcp_coder_utils.tool_verify`; re-exported here. |
```

### New `## Toolset providers` section (after `## Tool contract`, before `## Development`)

Intro (one or two sentences): `mcp_coder_utils.tool_provider` is the contract
between a consumer (e.g. agent-workbench) and the tool packages it loads as
plugins. The consumer finds a provider by name through an entry point, passes
it its own config table, and gets tool specs plus something to close.
`VerifyItem` is imported from `mcp_coder_utils.tool_verify`.

#### `### Public API`

| Name | Purpose |
|------|---------|
| `ToolsetProvider` | Abstract base class; `ToolsetProvider(config: Mapping[str, Any] \| None = None)` stores the provider's config table as public `self.config`, always a mapping. It only stores. `build()` is required; `verify(*, connect=False)` defaults to `[]`. |
| `Toolset` | Protocol: read-only `specs: tuple[ToolSpec, ...]` and `close()`. A frozen dataclass with a `specs` field satisfies it. |
| `StaticToolset` | Frozen dataclass `StaticToolset(specs)` for providers holding no resources; `close()` does nothing. |
| `VerifyItem` / `VerifyStatus` | In `mcp_coder_utils.tool_verify`: one check returned by `verify`; status `ok`, `warning` or `error`. |

#### `### Rules`

The same list as the `ToolsetProvider` class docstring (step 2), as bullets:
config table / unknown keys / missing or wrongly typed keys; `build` raises
`ValueError` only; absolute or `~` paths; repeated `build`, each `Toolset`
owns its resources; `build` opens no connection, no network, no disk writes;
`verify` never raises, `connect=False` makes no connection, invariant (no
`error` row under `connect=False` → `build` succeeds); `connect=True` returns
a superset of `connect=False` rows; override `verify` if `build` can fail;
`config.<key>` row names; spec names unique within one toolset, consumer
detects clashes across toolsets.

#### `### Registration`

The consumer names the entry-point group and defines it as a constant on its
side. Entry-point name = the consumer's config name; value = the provider class.

```toml
[project.entry-points."agent_workbench.toolsets"]
sql = "mcp_tools_sql.toolset:SqlToolsetProvider"
```

#### `### Versioning`

There is no `api_version`; providers pin `mcp-coder-utils`. A contract-breaking
change requires a major release here and coordinated changes in the provider repos.

#### `### Example`

A minimal provider plus a consumer loop. Keep it short; it must be correct
Python against the real API:

```python
from collections.abc import Mapping
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

from mcp_coder_utils.tool_provider import StaticToolset, Toolset, ToolsetProvider
from mcp_coder_utils.tool_spec import ToolCollector, tool_spec
from mcp_coder_utils.tool_verify import VerifyItem


class NotesProvider(ToolsetProvider):
    def verify(self, *, connect: bool = False) -> list[VerifyItem]:
        items = [
            VerifyItem(f"config.{key}", "warning", "unknown key, ignored")
            for key in self.config.keys() - {"path"}
        ]
        path = self.config.get("path")
        if not isinstance(path, str) or not Path(path).expanduser().is_absolute():
            items.append(VerifyItem("config.path", "error", "must be an absolute or ~ path"))
        else:
            items.append(VerifyItem("config.path", "ok", path))
        return items

    def build(self) -> Toolset:
        errors = [i.message for i in self.verify() if i.status == "error"]
        if errors:
            raise ValueError("; ".join(errors))
        root = Path(self.config["path"]).expanduser()

        def list_notes() -> str:
            """List the note files."""
            return "\n".join(p.name for p in root.glob("*.md"))

        collector = ToolCollector()
        collector.add(tool_spec(list_notes, group="notes", read_only=True))
        return StaticToolset(collector.specs)


# Consumer
TOOLSETS_GROUP = "agent_workbench.toolsets"


def load_toolset(name: str, table: Mapping[str, Any]) -> Toolset:
    (entry_point,) = entry_points(group=TOOLSETS_GROUP, name=name)
    provider: ToolsetProvider = entry_point.load()(table)
    for item in provider.verify():
        print(item.status, item.name, item.message)
    return provider.build()  # raises ValueError on any problem it detects


toolset = load_toolset("notes", {"path": "~/notes"})
try:
    ...  # hand toolset.specs to the agent
finally:
    toolset.close()
```

## ALGORITHM / DATA

None.

## Checks

`run_format_code`, `run_pylint_check`, `run_pytest_check(extra_args=["-n", "auto"])`,
`run_mypy_check`, `run_ruff_check`, `run_lint_imports_check`, `run_tach_check`,
`run_vulture_check`, `check_file_size(max_lines=750)`.
