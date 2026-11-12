# Toolset providers

`mcp_coder_utils.tool_provider` is the contract between a consumer (e.g. agent-workbench) and the tool packages it loads as plugins. The consumer finds a provider by name through an entry point, passes it its own config table, and gets tool specs plus something to close. `VerifyItem` is imported from `mcp_coder_utils.tool_verify`.

## Public API

| Name | Purpose |
|------|---------|
| `ToolsetProvider` | Abstract base class; `ToolsetProvider(config: Mapping[str, Any] \| None = None)` stores the provider's config table as public `self.config`, always a mapping. It only stores. `build()` is required; `verify(*, connect=False)` defaults to `[]`. |
| `Toolset` | Protocol: read-only `specs: tuple[ToolSpec, ...]` and `close()`. A frozen dataclass with a `specs` field satisfies it. |
| `StaticToolset` | Frozen dataclass `StaticToolset(specs)` for providers holding no resources; `close()` does nothing. |
| `VerifyItem` / `VerifyStatus` | In `mcp_coder_utils.tool_verify`: one check returned by `verify`; status `ok`, `warning` or `error`. |

## Rules

- `config` is the consumer's TOML table as parsed. Unknown keys give a `warning` row in `verify` and are ignored by `build`. Missing or wrongly typed keys give an `error` row in `verify` and a `ValueError` from `build`.
- `build` raises `ValueError` for every problem it detects, config or environment (missing file, unreadable file, missing driver). Any other exception is a provider bug.
- Path values are absolute or start with `~`; a relative path is an error (the consumer's working directory is undefined).
- `build` can be called repeatedly; each returned `Toolset` owns its resources and `close` releases them.
- `build` opens no connection, makes no network call and writes nothing to disk; connections open on first use.
- `verify` never raises for problems it detects. `verify(connect=False)` opens no connection and makes no network call. Invariant: no `error` row under `connect=False` means `build` on the same config succeeds.
- `verify(connect=True)` returns at least the rows of `verify(connect=False)`.
- A provider whose `build` can fail overrides `verify`; the default `[]` is only right for a provider whose `build` cannot fail.
- Rows about the provider's own config table are named `config.<key>`; other row names (including other `config.*` names) are free.
- Spec names are unique within one toolset; the consumer detects clashes across toolsets.

## Registration

The consumer names the entry-point group and defines it as a constant on its side. The entry-point name is the consumer's config name; the value is the provider class.

```toml
[project.entry-points."agent_workbench.toolsets"]
sql = "mcp_tools_sql.toolset:SqlToolsetProvider"
```

## Versioning

There is no `api_version`; providers pin `mcp-coder-utils`. A contract-breaking change requires a major release here and coordinated changes in the provider repos.

## Example

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
