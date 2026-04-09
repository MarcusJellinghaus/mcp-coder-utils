# Step 2: Update architecture docs

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 2: update
> `docs/architecture/architecture.md` to reflect the new modules and add
> explicit `__all__` export guidance. Run all checks.

## WHERE

- **Modify:** `docs/architecture/architecture.md`

## WHAT

Two changes to the architecture doc:

### 1. Update package layout section

Replace the current layout block with:

```
src/mcp_coder_utils/
    __init__.py
    py.typed
    subprocess_runner.py
    subprocess_streaming.py
```

Remove the "Real modules land in Phase 2" paragraph — they have landed.

### 2. Add `__all__` export rule

Add a new rule (rule 5) under **Architectural rules**:

> **`__all__` discipline.** Only add a symbol to `__all__` when it has at least
> one external consumer (or is required by a sibling module like
> `subprocess_streaming`). Internal helpers stay unexported. Promote to `__all__`
> when a second consumer appears.

## HOW

Pure documentation change. No code changes.

## Verification

- All quality checks still pass (no code changed)
