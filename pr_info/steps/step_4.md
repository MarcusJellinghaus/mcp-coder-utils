# Step 4 — Package role wording and sibling-repo lists

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md`
> exactly. Wording and config-list changes only; no tests to write. Use the
> exact sentences given below. Run the checks listed at the end; all must
> pass. Produce one commit:
> `docs: name tool contracts in the package role; add mcp-tools-sql and agent-workbench`.

## WHERE

- `.importlinter` — `leaf_library` contract
- `docs/architecture/enforcement.md` — "Leaf library" first paragraph
- `docs/architecture/architecture.md` — Role, diagram, rules 2 and 4
- `README.md` — intro sentence, "Related repos"
- `pyproject.toml` — `description`
- `.claude/CLAUDE.md` — "About this repo", "Reference projects"

## WHAT

### `.importlinter` — `leaf_library`

- `forbidden_modules`: add `mcp_tools_sql` and `agent_workbench`.
- Comment: "It must not import from any sibling repo (mcp_coder, mcp_tools_py,
  mcp_workspace, mcp_config, mcp_tools_sql, agent_workbench)."

### `docs/architecture/enforcement.md` — "Leaf library"

Module list becomes (`mcp_coder`, `mcp_tools_py`, `mcp_workspace`,
`mcp_config`, `mcp_tools_sql`, `agent_workbench`).

### `docs/architecture/architecture.md`

- Role: first sentence unchanged; second sentence becomes exactly:
  "It provides shared low-level Python helpers (subprocess, logging, filesystem)
  and tool contracts (toolkit, tool spec, toolset provider), consumed by
  `mcp-coder`, `mcp-tools-py`, `mcp-workspace`, `mcp-tools-sql`, and
  `agent-workbench`."
- Diagram: add a fifth box `agent_workbench` (same underscore style as the
  other boxes), all five arrows joining into `mcp-coder-utils`. Keep the
  box-drawing characters aligned, e.g.:
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
- Rule 2: "Never imports from `mcp_coder`, `mcp_tools_py`, `mcp_workspace`,
  `mcp_config`, `mcp_tools_sql`, or `agent_workbench`."
- Rule 4: "break all 4 downstream repos" → "break all 5 downstream repos".

### `README.md`

- Intro line becomes exactly:
  "Shared low-level Python helpers (subprocess, logging, fs) and tool contracts
  (toolkit, tool spec, toolset provider) for the mcp-coder family of repos."
- "Related repos": append
  - `- [mcp-tools-sql](https://github.com/MarcusJellinghaus/mcp-tools-sql) — tool package: SQL tools`
  - `- [agent-workbench](https://github.com/MarcusJellinghaus/agent-workbench) — chat app: loads tool packages as plugins`
- `## Development` paragraph: unchanged.

### `pyproject.toml`

```toml
description = "Shared low-level Python helpers (subprocess, logging, fs) and tool contracts (toolkit, tool spec, toolset provider) for the mcp-coder family of repos"
```

(no trailing period)

### `.claude/CLAUDE.md`

- "About this repo" first line becomes exactly:
  "`mcp-coder-utils` is a **leaf library**: shared low-level Python helpers
  (subprocess, logging, fs) and tool contracts (toolkit, tool spec, toolset
  provider), used by `mcp-coder`, `mcp-tools-py`, `mcp-workspace`,
  `mcp-tools-sql`, and `agent-workbench`."
- "Reference projects" list: append
  - `` `mcp-tools-sql` — `mcp-tools-sql` source ``
  - `` `agent-workbench` — `agent-workbench` source ``

## ALGORITHM / DATA

None.

## Checks

`run_format_code`, `run_pylint_check`, `run_pytest_check(extra_args=["-n", "auto"])`,
`run_mypy_check`, `run_ruff_check`, `run_lint_imports_check`, `run_tach_check`,
`run_vulture_check`.
