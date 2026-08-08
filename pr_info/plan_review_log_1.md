# Plan Review Log 1 — Issue #30 `token_fingerprint`

**Branch:** `30-feat-redaction-add-token-fingerprint-helper-for-safe-credential-logging`
**Base:** `main` (up to date, CI passing)
**Plan under review:** `pr_info/steps/summary.md`, `pr_info/steps/step_1.md`
**Task tracker:** 1 step, none complete — review covers the whole plan.
**Started:** 2026-08-08

---

## Round 1 — 2026-08-08

**Verdict:** PASS-WITH-FIXES. Design, contract, worked examples, algorithm and step
granularity all correct. Three defects in the step's process sections would have
made the first implementation attempt fail — two of them silently, at CI rather
than locally.

**Findings**

- *Critical* — `_escape_fragment`'s docstring in `step_1.md` § WHAT had no
  `Returns:` section, tripping ruff `DOC201`. `pyproject.toml` sets
  `[tool.ruff.lint] preview = true, select = ["D", "DOC"]` and `ci.yml` gates on a
  `ruff-docstrings` job. Verified empirically with ruff 0.16.1 against the plan's
  exact code. (`token_fingerprint` escaped it only because ruff exempts summaries
  beginning with "Return".)
- *Critical* — § CHECKS omitted ruff entirely, i.e. precisely the check that would
  have caught the finding above.
- *Critical* — § COMMIT instructed running `./tools/format_all.sh`, which does not
  exist; `tools/` holds only `read_github_deps.py`, `reinstall_local.{bat,sh}`,
  `ruff_check.{bat,sh}`.
- *Accept* — § CHECKS used the tool prefix `mcp__tools-py__*`; the real prefix is
  `mcp__mcp-tools-py__*`. Calls as written would fail with "unknown tool".
- *Accept* — § TESTS listed ~10 independent equality assertions where the adjacent
  `TestRedactEnvVars` already parameterizes, and `planning_principles.md` prefers
  it.
- *Skip* — the "pylint E731" rationale in both files is wrong (E731 is a
  ruff/pycodestyle code, not pylint, and is not enabled here). Conclusion still
  right, reason bogus.
- *Skip* — `summary.md` § "Files created / modified" lists the plan docs
  themselves as "create" though they already exist. Cosmetic.

**Verified as accurate (no action):** `redaction.py`'s existing `__all__` contents;
`test_redaction.py`'s class style and single-import block; that no package-level or
docs change is owed. All worked examples are arithmetically correct, including the
trailing-newline case where `token[-4:]` is `"3f9\n"` rather than `"a3f9"`. All
nine decisions from the issue's Decisions table are followed faithfully.

**Decisions**

- Accepted and fixed autonomously: the three Criticals and both Accepts — all
  mechanical corrections to process sections, no scope or architecture impact.
- Folded in the E731 correction despite its *Skip* rating: both files were being
  edited anyway, and a wrong justification would send the implementer chasing a
  check that cannot fire.
- Left the cosmetic "Files created / modified" table alone.

**User decisions**

- *Q:* `len=N` uses Python `len()` on a `str`, which counts characters (code
  points), while the issue's rationale argues in bytes ("actually 41 bytes and
  broken"). Identical for every real credential; divergent only for a mis-decoded
  non-ASCII paste. Keep character semantics and document (A), switch to byte
  length (B), or keep and leave undocumented (C)?
- *A:* **A** — keep `len()` as-is, state explicitly in the docstring that it counts
  characters (code points), not bytes.

**Changes**

- `pr_info/steps/step_1.md` — full Google-style `Args:`/`Returns:` docstring for
  `_escape_fragment`; characters-not-bytes noted in `token_fingerprint`'s
  docstring; § TESTS restructured to one 8-row `@pytest.mark.parametrize` table
  with the two non-equality assertions kept standalone and a note that
  `mypy --strict` covers `tests/` so each method needs `-> None`; § CHECKS tool
  prefixes corrected, `run_ruff_check` added, E731 parenthetical removed;
  § COMMIT now names `mcp__mcp-tools-py__run_format_code`.
- `pr_info/steps/summary.md` — E731 justification dropped from § KISS notes
  (module-level `def` kept as a readability choice); characters-not-bytes added to
  behaviour rule 7.
- `pr_info/steps/Decisions.md` — created (mandated by the `plan_update` skill),
  8 rows covering only what this review actually decided.

**Status:** applied, NOT committed — `/commit_push` is `disable-model-invocation`
and is reserved for explicit user invocation, so the supervisor cannot commit on
its own. The four changed files below are uncommitted in the working tree; the
user must run `/commit_push` themselves.

Intended commit message: `docs(pr_info): apply plan review fixes for token_fingerprint step`

---

## Round 2 — 2026-08-08

**Findings:** none at Critical or Accept level.

All six round 1 fixes verified as correctly landed, each against the real config
rather than assumed: the `_escape_fragment` docstring satisfies DOC201 under
`pyproject.toml`'s `preview = true, select = ["D","DOC"]`, google convention, and
is D401/D415-clean; `.github/workflows/ci.yml` really does run `ruff check src
tests` as the `ruff-docstrings` job and `mypy --strict src tests`, so both cited
rationales hold; no stale `format_all.sh`, `mcp__tools-py__`, or E731 reference
survives anywhere in `pr_info/steps/`.

All 8 parametrize rows re-derived from the § ALGORITHM pseudocode rather than
taken on trust, including the 16-char boundary (head 0–3, tail 12–15, no overlap
— exactly "reveal at most half") and the 41-char newline case (`token[-4:]` is
`"3f9\n"`, escaping to the 5 characters `3f9\n`).

`Decisions.md` is accurate, its "Where applied" column correct for all 8 rows, and
it does not duplicate or drift from the issue's own 9-row table.

Clean on fresh checks: no package-level re-export owed (`__init__.py` exports only
`__version__`); no README/docs update owed; no `vulture_whitelist.py` entry needed;
ruff `per-file-ignores` exempts `tests/**` from `D`/`DOC`, so the step's docstring
requirements correctly scope to `src` only.

*Skip* — § TESTS mentions only `-> None` while `mypy --strict` also wants
parameter annotations. Self-evident on the first mypy run; not worth an edit.

**Decisions:** nothing to accept, nothing to escalate.

**User decisions:** none required.

**Changes:** none.

**Status:** no changes needed — loop terminates.

---

## Final Status

**Rounds run:** 2. Round 1 found 3 Critical + 2 Accept defects and applied them;
round 2 verified them and found nothing further.

**Verdict:** the plan is **ready to implement as written**. It matches issue #30's
contract and all nine of its Decisions, conforms to `planning_principles.md`
(one step, one commit, checks green as exit criterion, parameterized tests), and
its claims about the existing codebase and CI configuration have been verified
against the real files.

**Substance untouched throughout:** both rounds confirmed the design, contract,
worked examples, algorithm and scope were correct from the start. Every fix was to
the step's *process* sections — the parts that would have failed CI, not the parts
that describe the function.

**Outstanding action — commits not made.** `/commit_push` is configured
`disable-model-invocation` and is reserved for explicit user invocation, so this
supervisor could not commit between rounds or at the end. These four files are
applied but uncommitted in the working tree:

- `pr_info/steps/step_1.md` (modified)
- `pr_info/steps/summary.md` (modified)
- `pr_info/steps/Decisions.md` (new, untracked)
- `pr_info/plan_review_log_1.md` (modified)

The user must run `/commit_push` themselves. Suggested message:
`docs(pr_info): apply plan review fixes for token_fingerprint step`

**Also outstanding:** the GitHub issue still carries `status-14f:plan-review-failed`,
which is now stale. Per CLAUDE.md this is changed with
`mcp-coder gh-tool set-status <label>`, never raw `gh issue edit`.
