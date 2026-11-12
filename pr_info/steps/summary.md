# Summary — #61 Toolset provider contract: tool packages as entry-point plugins, with verify

## Goal

A consumer (agent-workbench) loads tool packages as plugins. It finds a
`ToolsetProvider` subclass by name in its own entry-point group, passes it the
provider's own config table, and gets back `VerifyItem` rows from `verify`
and a `Toolset` (specs + `close`) from `build`. The consumer never imports a
tool package or knows its config keys.

```
consumer config [tools.<name>]  ──►  entry point <name> in the consumer's group
                                         │  ToolsetProvider subclass
                                         ▼
                      provider = cls(table)
                      provider.verify(connect=False) -> list[VerifyItem]
                      provider.build()               -> Toolset(specs, close)
```

## Architectural / design changes

- **New module `tool_verify`** — new home of `VerifyItem` and `VerifyStatus`
  (moved from `toolkit`, unchanged apart from a generic docstring). Stdlib
  only. Reason: `toolkit` imports `jsonschema` (~125 ms), and providers sit on
  consumers' start paths.
- **`toolkit` re-exports** `VerifyItem` / `VerifyStatus` (kept in
  `toolkit.__all__`), so existing `from mcp_coder_utils.toolkit import
  VerifyItem` keeps working downstream. `toolkit` now depends on `tool_verify`.
- **New module `tool_provider`** — the toolset provider contract:
  - `Toolset` — `Protocol` with a read-only `specs` property and `close()`.
    Not `@runtime_checkable`.
  - `StaticToolset` — frozen dataclass for providers that hold no resources;
    `close()` does nothing.
  - `ToolsetProvider(ABC)` — stores `config` (like `toolkit.Toolkit`);
    abstract `build() -> Toolset`; `verify(*, connect=False) -> list[VerifyItem]`
    defaults to `[]`.
  - Depends on `tool_spec` and `tool_verify`; never on `toolkit`. Does not
    re-export `VerifyItem` (one canonical path: `tool_verify`).
- **No discovery helper.** The consumer owns the entry-point group name and
  the lookup (same pattern as mcp_coder's `mcp_coder.toolkits`).
- **New import-linter contract `light_tool_provider`**: `tool_provider` and
  `tool_verify` must not import `jsonschema`, `referencing` or
  `mcp_coder_utils.toolkit`. A subprocess test checks the same at runtime.
- **Module dependency graph after this change**:
  `log_utils → redaction`; `subprocess_streaming → subprocess_runner,
  subprocess_helpers`; `subprocess_runner → subprocess_helpers`;
  `tool_provider → tool_spec, tool_verify`; `toolkit → tool_verify`; all other
  modules standalone.
- **Package role** now includes tool contracts (toolkit, tool spec, toolset
  provider); consumers now also include `mcp-tools-sql` and `agent-workbench`
  (added to the `leaf_library` contract).
- `StaticToolset` is an accepted exception to the ≥2-consumers rule (decided in
  the issue).

## Design decisions taken in planning (KISS)

- The subprocess import test keeps the child trivial: it prints
  `mcp_coder_utils.__file__` and `sorted(sys.modules)` as JSON; the pytest
  side does the `__file__` check and the exact-name module checks.
- The full provider rules list lives once in the `ToolsetProvider` class
  docstring and once in the README; method docstrings carry only their own
  Returns/Raises plus the one rule each needs.

## Files

### Created
- `src/mcp_coder_utils/tool_verify.py`
- `src/mcp_coder_utils/tool_provider.py`
- `tests/test_tool_verify.py`
- `tests/test_tool_provider.py`

### Modified
- `src/mcp_coder_utils/toolkit.py` — remove `VerifyItem` / `VerifyStatus` definitions, re-export from `tool_verify`
- `tests/test_toolkit.py` — remove `TestVerifyItem`, add compatibility test
- `tach.toml` — new `[[modules]]`, `toolkit` depends_on, header comment
- `.importlinter` — new `light_tool_provider` contract, `no_agent_frameworks` comment, `leaf_library` modules + comment
- `vulture_whitelist.py` — `connect` parameter of `ToolsetProvider.verify`
- `docs/architecture/enforcement.md` — Leaf library, Independence between modules
- `docs/architecture/architecture.md` — Role, diagram, rules 2 and 4, Package layout
- `README.md` — intro, Toolkit interface table, new `## Toolset providers`, Related repos
- `pyproject.toml` — `description`
- `.claude/CLAUDE.md` — About this repo, Reference projects

## Steps

1. `tool_verify` module: move `VerifyItem` / `VerifyStatus`, re-export from `toolkit`.
2. `tool_provider` module with its tests and guards (tach, import-linter, vulture, enforcement sentence).
3. Module dependency graph docs: `tach.toml` header, `enforcement.md`, `architecture.md` package layout.
4. Package role wording and sibling-repo lists.
5. README `## Toolset providers` section and Toolkit interface table rows.

## Checks (every step)

`run_format_code`, then pylint, pytest (`extra_args: ["-n", "auto"]`), mypy,
ruff, lint-imports, tach, vulture. All must pass before committing. The final
step also runs `check_file_size(max_lines=750)`.
