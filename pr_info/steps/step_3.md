# Step 3 — Module dependency graph docs

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md`
> exactly. Docs and comments only; no tests to write. Run the checks listed at
> the end; all must pass. Produce one commit:
> `docs(architecture): describe the real module dependency graph`.

## Precondition

If `src/mcp_coder_utils/tool_provider.py` does not exist (step 2 not done),
write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `tach.toml` — header comment only
- `docs/architecture/enforcement.md` — "Independence between modules" paragraph
- `docs/architecture/architecture.md` — "Package layout" block

## WHAT

### `tach.toml` header

Replace the "Division of labour" and "No layers" blocks with:

```toml
# Division of labour with import-linter (.importlinter):
# - import-linter owns the forbidden-import contracts.
# - tach adds per-module dependency declarations and cycle detection for
#   src/ (tests/ is not covered — see source_roots below).
#
# No layers. The only dependencies between modules are:
#   log_utils            -> redaction
#   subprocess_streaming -> subprocess_runner, subprocess_helpers
#   subprocess_runner    -> subprocess_helpers
#   tool_provider        -> tool_spec, tool_verify
#   toolkit              -> tool_verify
# All other modules are standalone. There is no stack to enforce;
# depends_on already says everything.
```

Verify the list matches the `depends_on` entries in the same file.

### `docs/architecture/enforcement.md` — "Independence between modules"

Replace the first sentence ("There is no layer stack: the package is two
pairs ... plus standalone modules.") with:

> There is no layer stack. The only dependencies between modules are
> `log_utils` -> `redaction`; `subprocess_streaming` -> `subprocess_runner`,
> `subprocess_helpers`; `subprocess_runner` -> `subprocess_helpers`;
> `tool_provider` -> `tool_spec`, `tool_verify`; `toolkit` -> `tool_verify`.
> All other modules are standalone.

Keep the rest of the paragraph.

### `docs/architecture/architecture.md` — "Package layout"

Add `subprocess_helpers.py`, `tool_provider.py`, `tool_verify.py` in
alphabetical position:

```
    redaction.py
    subprocess_helpers.py
    subprocess_runner.py
    subprocess_streaming.py
    tool_provider.py
    tool_spec.py
    tool_verify.py
    toolkit.py
```

## ALGORITHM / DATA

None.

## Checks

`run_format_code`, `run_pylint_check`, `run_pytest_check(extra_args=["-n", "auto"])`,
`run_mypy_check`, `run_ruff_check`, `run_lint_imports_check`, `run_tach_check`,
`run_vulture_check`.
