# Architecture — `mcp-coder-utils`

## Role

`mcp-coder-utils` is a **leaf library** in the mcp-coder family of repositories.
It provides shared low-level Python helpers (subprocess, logging, filesystem)
and tool contracts (toolkit, tool spec, toolset provider), consumed by
`mcp-coder`, `mcp-tools-py`, `mcp-workspace`, `mcp-tools-sql`, and
`agent-workbench`.

```
┌───────────┐ ┌──────────────┐ ┌───────────────┐ ┌───────────────┐ ┌─────────────────┐
│ mcp_coder │ │ mcp_tools_py │ │ mcp_workspace │ │ mcp_tools_sql │ │ agent_workbench │
└─────┬─────┘ └──────┬───────┘ └───────┬───────┘ └───────┬───────┘ └────────┬────────┘
      │              │                 │                 │                  │
      └──────────────┴─────────────────┼─────────────────┴──────────────────┘
                                       ▼
                             ┌──────────────────┐
                             │ mcp-coder-utils  │   (leaf — no internal deps)
                             └──────────────────┘
```

## Architectural rules

Rules are enforced by tooling, see [enforcement.md](enforcement.md).

1. **Pure Python, language-agnostic.** No knowledge of any specific ecosystem
   (no `pyproject.toml` parsing, no venv awareness, no `.csproj`, no SQL).
2. **Zero internal dependencies.** Stdlib + a small set of pinned third-party
   libs only. Never imports from `mcp_coder`, `mcp_tools_py`, `mcp_workspace`,
   `mcp_config`, `mcp_tools_sql`, or `agent_workbench`. Enforced by
   `.importlinter`. Dependencies between modules inside the package are
   declared in `tach.toml`; `tach check` enforces them and forbids cycles.
3. **Shared topics, real consumers.**
   - A module (one topic, e.g. line endings) enters when at least two
     consumers need that topic. Its API is designed as one whole.
   - Every public function has at least one real consumer. No speculative
     "might be useful" API.
   - Mechanism here, policy in the consumer. Counting line endings is shared;
     choosing which ending to write stays in the tool that writes.
   - Only stable code. Code that still changes with one consumer's features
     stays in that consumer: a leaf library is the most-depended-on package,
     and every change here is a coordinated release downstream.
4. **Stable public API.** Renames and signature changes break all 5 downstream
   repos. Treat the top-level exports as a contract.
5. **`__all__` discipline.** Only add a symbol to `__all__` when it has at least
   one external consumer (or is required by a sibling module like
   `subprocess_streaming`). Internal helpers stay unexported. Promote to `__all__`
   when an external consumer appears.

## Package layout

```
src/mcp_coder_utils/
    __init__.py
    py.typed
    log_utils.py
    redaction.py
    subprocess_helpers.py
    subprocess_runner.py
    subprocess_streaming.py
    tool_provider.py
    tool_spec.py
    tool_verify.py
    toolkit.py
    user_app_data.py
    fs/
        __init__.py
        path_security.py
        read_file.py
        text.py
```

## Tests

All tests are fast unit tests — there are no integration markers. Some tests
exercise real subprocess execution (not purely mock-based) but require no
special markers or configuration. Run with:

```
pytest -n auto
```
