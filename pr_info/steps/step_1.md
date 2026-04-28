# Step 1 — Add notify-downstream workflow

Single-step implementation. See [summary.md](summary.md) for context, scope
boundaries, and the manual PAT/secret setup the user must perform separately.

## WHERE

- **Create:** `.github/workflows/notify-downstream.yml`
- **Modify:** *(none)*
- **Delete:** *(none)*

## WHAT

A GitHub Actions workflow file. No Python functions, no signatures, no public
API. The workflow declares:

- **Trigger:** `push` to `main`, plus `workflow_dispatch` for manual runs.
- **Job:** `dispatch-to-downstream` running on `ubuntu-latest`, with a matrix
  over three downstream repo names.
- **Permissions:** job-level `contents: read` (least-privilege; the dispatch
  itself uses the `DOWNSTREAM_PAT` secret, not `GITHUB_TOKEN`).
- **Action:** `peter-evans/repository-dispatch@v3` sends event-type
  `upstream-main-updated` with payload `{"upstream": "mcp-coder-utils",
  "sha": "<github.sha>"}`.

## HOW (integration points)

- Lives alongside existing workflows in `.github/workflows/` (`ci.yml`,
  `publish.yml`, `approve-command.yml`, `label-new-issues.yml`). No
  cross-references to those files.
- Depends on a repo secret `DOWNSTREAM_PAT` (created manually by the user;
  see summary). The workflow file references it as
  `${{ secrets.DOWNSTREAM_PAT }}`.
- Uses the third-party action `peter-evans/repository-dispatch@v3` —
  no local code.

## ALGORITHM

Declarative YAML; no algorithm. Per-matrix-element behaviour is a single
HTTP POST performed by `peter-evans/repository-dispatch@v3`:

```
for downstream in [mcp-workspace, mcp-tools-py, mcp_coder]:   # parallel via matrix
    POST https://api.github.com/repos/MarcusJellinghaus/<downstream>/dispatches
        Authorization: token <DOWNSTREAM_PAT>
        body: {"event_type": "upstream-main-updated",
               "client_payload": {"upstream": "mcp-coder-utils", "sha": <github.sha>}}
```

`fail-fast: false` ensures one failed dispatch does not cancel the siblings.

## DATA

- **Inputs:** `github.sha` (built-in), `secrets.DOWNSTREAM_PAT` (repo secret).
- **Matrix values:** `[mcp-workspace, mcp-tools-py, mcp_coder]`. Note the
  underscore in `mcp_coder` — the repo is genuinely
  `MarcusJellinghaus/mcp_coder`, not `mcp-coder`. Do not "fix" it.
- **Dispatch payload:** `{"upstream": "mcp-coder-utils", "sha": "<sha>"}`.
- **Event-type:** `upstream-main-updated`.
- **Outputs:** none (fire-and-forget; downstream receivers are out of scope).

## TDD

Not applicable. Workflow YAML is declarative and is validated by GitHub
Actions itself on push. There are no Python tests to add. The repo's
existing CI (`ci.yml`) does not lint workflow files, so no in-repo check
will run against this file — it is verified by GitHub on push.

## File contents

Create `.github/workflows/notify-downstream.yml` with exactly this content
(verbatim from the issue):

```yaml
name: Notify downstream of main update

# When this repo's main changes, fan out repository_dispatch events to
# mcp-workspace, mcp-tools-py, and mcp_coder so each can re-run mypy
# against the latest main of this package.
#
# Requires repo secret DOWNSTREAM_PAT — a fine-grained PAT with
#   Contents: Read & write   (on each target repo)
#   Metadata: Read
# Create at: https://github.com/settings/personal-access-tokens/new
# Add to this repo via: Settings → Secrets and variables → Actions → New repository secret.

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  dispatch-to-downstream:
    name: dispatch-to-${{ matrix.downstream }}
    runs-on: ubuntu-latest
    permissions:
      contents: read
    strategy:
      fail-fast: false
      matrix:
        downstream: [mcp-workspace, mcp-tools-py, mcp_coder]
    steps:
      - name: Send upstream-main-updated to ${{ matrix.downstream }}
        uses: peter-evans/repository-dispatch@v3
        with:
          token: ${{ secrets.DOWNSTREAM_PAT }}
          repository: MarcusJellinghaus/${{ matrix.downstream }}
          event-type: upstream-main-updated
          client-payload: '{"upstream": "mcp-coder-utils", "sha": "${{ github.sha }}"}'
```

## Checks

Standard project quality gates do not apply (no Python touched). The
mandatory MCP checks (`pylint`, `pytest`, `mypy`) will pass trivially as
none of the targeted source/test files change. Run them anyway to confirm
no incidental regressions:

- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_pytest_check` with `extra_args=["-n", "auto"]`
- `mcp__tools-py__run_mypy_check`

## Commit

Single commit covering this one file. Suggested message:

```
Add notify-downstream workflow for cross-repo CI (#28)
```

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement
> Step 1: create the new file `.github/workflows/notify-downstream.yml` with
> the exact YAML content shown in step_1.md (verbatim from issue #28). Do
> not modify any other file. Do not create the `DOWNSTREAM_PAT` secret —
> that is a manual user action documented in the summary. After saving the
> file, run the three mandatory MCP checks (pylint, pytest with
> extra_args=["-n", "auto"], mypy) to confirm no regressions, then produce a single
> commit with the message `Add notify-downstream workflow for cross-repo CI
> (#28)`.
