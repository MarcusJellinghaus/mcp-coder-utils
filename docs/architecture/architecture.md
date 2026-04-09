# Architecture — `mcp-coder-utils`

## Role

`mcp-coder-utils` is a **leaf library** in the mcp-coder family of repositories.
It provides shared low-level Python helpers (subprocess, logging, filesystem)
consumed by `mcp-coder`, `mcp-tools-py`, `mcp-workspace`, and `mcp-config`.

```
┌──────────────┐  ┌────────────────┐  ┌──────────────┐  ┌──────────────┐
│  mcp_coder   │  │  mcp_tools_py  │  │ mcp_workspace│  │  mcp_config  │
└──────┬───────┘  └────────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                   │                 │                 │
       └───────────────────┴────────┬────────┴─────────────────┘
                                    ▼
                          ┌──────────────────┐
                          │ mcp-coder-utils  │   (leaf — no internal deps)
                          └──────────────────┘
```

## Architectural rules

1. **Pure Python, language-agnostic.** No knowledge of any specific ecosystem
   (no `pyproject.toml` parsing, no venv awareness, no `.csproj`, no SQL).
2. **Zero internal dependencies.** Stdlib + a small set of pinned third-party
   libs only. Never imports from `mcp_coder`, `mcp_tools_py`, `mcp_workspace`,
   or `mcp_config`. Enforced by `.importlinter`.
3. **≥2 real consumers required.** Every public function must have at least
   two real consumers (or be provably generic). Single-user "might be useful"
   helpers belong in the consumer.
4. **Stable public API.** Renames and signature changes break all 4 downstream
   repos. Treat the top-level exports as a contract.

## Package layout

```
src/mcp_coder_utils/
    __init__.py
    py.typed
```

Real modules land in Phase 2 — see `repo_architecture_plan/mcp_utils_plan.md`
in the `mcp_coder` repo for the migration plan. Initial scope:

- `subprocess_runner` — canonical subprocess wrapper (merge of `mcp_coder`
  and `mcp_tools_py` versions)
- `subprocess_streaming` — pairs with `subprocess_runner`
- `log_utils` — structured logging with redaction support

## Tests

All tests are fast unit tests — there are no integration markers. Run with:

```
pytest -n auto
```
