# Summary — Issue #28: Cross-repo CI notify-downstream

## Goal

When `main` updates in `mcp-coder-utils`, fan out `repository_dispatch` events
to three downstream repos (`mcp-workspace`, `mcp-tools-py`, `mcp_coder`) so each
can re-run mypy against the latest main and catch interface breaks early.

**Sender-only scope.** Receiver workflows in downstream repos are out of scope
(tracked independently per-repo). Acceptance is measured by *delivery*, not by
anything running downstream.

## Architectural / design changes

**None.** This issue adds a CI/infrastructure workflow only.

- No Python source changes, no test changes, no new dependencies.
- No impact on the package's public API, `__all__` discipline, or
  `.importlinter` contracts.
- No change to `docs/architecture/architecture.md` — the architecture diagram
  already shows `mcp-coder-utils` as the leaf with three consumers
  (`mcp_coder`, `mcp_tools_py`, `mcp_workspace`); the new workflow simply
  notifies those same consumers when main moves. `mcp_config` is not a
  consumer (verified by the issue) and is correctly excluded.

## Files created / modified

| Path | Action | Purpose |
|---|---|---|
| `.github/workflows/notify-downstream.yml` | **Create** | New workflow: on push to `main` (or manual dispatch), send `repository_dispatch` event-type `upstream-main-updated` to each downstream repo via `peter-evans/repository-dispatch@v3` using the `DOWNSTREAM_PAT` secret. |

No other files are touched.

## Out of scope (explicit non-goals from the issue)

- Receiver workflows in downstream repos.
- `[typecheck]` optional-dependency extra (deferred until ≥2 real consumers).
- `mcp-config` as a target (not a consumer of this package).
- Concurrency groups, `paths:` filters, tag/release triggers,
  `workflow_dispatch` branch gating.

## One-time manual setup (outside the agent's scope)

The user must perform these GitHub UI steps before the workflow becomes
functional. They are *not* part of the implementation commit:

1. Create a fine-grained PAT at
   <https://github.com/settings/personal-access-tokens/new>
   - Resource owner: `MarcusJellinghaus`
   - Repo access: `mcp-workspace`, `mcp-tools-py`, `mcp_coder`
   - Permissions: **Contents: Read & write**, **Metadata: Read**
   - Expiration: 1 year (set a calendar reminder)
2. Add the PAT as a repo secret named `DOWNSTREAM_PAT`
   (Settings → Secrets and variables → Actions → New repository secret).

## Implementation plan

A single step. The change is one file, one commit. There is no Python code to
test, no algorithm to verify, and no TDD applies (workflow YAML is declarative
and validated by GitHub Actions on push).

- [step_1.md](step_1.md) — Add `.github/workflows/notify-downstream.yml`.

## Verification (post-merge, by the user)

1. The workflow appears under the repo's Actions tab as a registered workflow
   (parses successfully).
2. The `DOWNSTREAM_PAT` secret exists.
3. After merge, a push to `main` produces three matrix jobs
   (`dispatch-to-mcp-workspace`, `dispatch-to-mcp-tools-py`,
   `dispatch-to-mcp_coder`), each completing successfully.
4. Each downstream repo's Actions tab shows a `repository_dispatch` event
   arriving (event-type `upstream-main-updated`).

## Note on KISS

The earlier discussion considered alternative shapes (single job with three
explicit steps, raw `curl`, dropping `workflow_dispatch`) and rejected each:
the issue's matrix-based YAML is already minimal, idiomatic, and gives the
clearest per-downstream pass/fail reporting in the Actions UI. The plan
implements it verbatim.
