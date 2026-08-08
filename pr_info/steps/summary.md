# Summary — `token_fingerprint` helper (Issue #30)

## Goal

Add a shared, pure helper `token_fingerprint(token: str | None) -> str` to
`mcp-coder-utils` that turns a secret token / API key into a short,
non-reversible identifier safe to put in a log line. This consolidates two
behaviourally-identical duplicates living in sibling repos
(`mcp-coder._mask_api_key`, `mcp-workspace.format_token_fingerprint`) into the
shared leaf library.

**This work is library-only.** Downstream adoption (swapping call sites,
deleting the duplicate modules) happens in the sibling repositories and is
tracked as separate follow-up issues — it cannot land here and cannot land
before a release containing this function exists.

## Behaviour (contract)

Three distinct states → three distinct outputs:

| Input | Output | Notes |
|---|---|---|
| `None` or `""` (absent) | `""` | neutral value each caller composes with |
| length `< 16` (malformed) | `<malformed>, len=N` | `N` = raw input length |
| length `>= 16` (fingerprinted) | `{esc(token[:4])}...{esc(token[-4:])}, len=N` | revealed parts escaped |

Worked examples (must match exactly):

| Input | Output |
|---|---|
| `None` / `""` | `""` |
| `"abc"` | `<malformed>, len=3` |
| `"ghp_" + "A"*32 + "a3f9"` | `ghp_...a3f9, len=40` |
| `"sk-abcd1234wxyz5678"` | `sk-a...5678, len=19` |
| the 40-char token above + trailing `"\n"` | `ghp_...3f9\n, len=41` (escaped, one line) |

### Rules (non-negotiable — from the issue)

1. **Threshold is 16** ("reveal at most half"). Below 16, no character of the
   input appears in the output. Boundary: 15 → malformed, 16 → fingerprinted.
2. **`len=N` is always the raw input length**, including the malformed case,
   measured **before** escaping.
3. **Revealed parts are escaped** via
   `fragment.encode("unicode_escape").decode("ascii")`, per slice, so control
   characters cannot break the log line. Escape, never strip.
4. **No token-family prefix registry, no `_` suffix.** Always `token[:4]` /
   `token[-4:]`.
5. **Return type is plain `str`; absent → `""`**, never `None`, never a truthy
   sentinel. Callers compose: `token_fingerprint(t) or "<none>"`,
   `if fingerprint:`, `token_fingerprint(k) or None`.
6. **Absent is not malformed** — different states, kept distinct.
7. **`len` and visible-character count may legitimately disagree** because
   escaping expands characters. This is documented in the docstring so it is
   not "fixed" later.

## Architectural / design changes

- **Scope of change is one function in one existing module.** No new module, no
  new package, no new dependency — the function is added to the existing
  `src/mcp_coder_utils/redaction.py` (stdlib-only, pure, deterministic, no I/O,
  no logging side effects), consistent with the leaf-library rules in
  `docs/architecture/architecture.md` (pure Python, zero internal deps).
- **Public API surface grows by one symbol.** `token_fingerprint` is added to
  `redaction.py`'s `__all__`. Per the `>= 2 real consumers` rule, this is
  satisfied comfortably (5 call sites across 2 sibling repos). Adding to
  `__all__` is a stable-API commitment.
- **Naming exception, accepted knowingly.** The name is noun-first
  (`token_fingerprint`) while its module neighbours are verb-first
  (`redact_for_logging`, `redact_env_vars`). Kept because it reads better at
  call sites and both downstream repos already use the term.
- **Sentinel family alignment.** The malformed placeholder `<malformed>` matches
  the existing `<none>` sentinel style used by downstream callers.
- **No design coupling introduced.** The function does not touch, reuse, or get
  reused by the adjacent container-redaction helpers (`redact_for_logging`,
  `redact_env_vars`); a possible future integration (routing env-var values
  through `token_fingerprint`) is explicitly out of scope.

## KISS notes

- Whole function is ~6 lines. No named threshold constant — a literal `16` with
  an inline comment documents the rule with less indirection.
- The escape incantation is factored into a single small module-level helper
  (`_escape_fragment`) instead of being duplicated inline for head and tail —
  one place to read, one place to get right. (A nested `def` / module helper is
  used rather than an assigned `lambda` to satisfy pylint E731.)
- Escaping is applied **per slice** (after `token[:4]` / `token[-4:]`), never to
  the whole token then sliced — slicing an escaped string would misalign on any
  expanded character and break the `ghp_...3f9\n` case.

## Files created / modified

| Path | Action | What |
|---|---|---|
| `src/mcp_coder_utils/redaction.py` | modify | add `_escape_fragment` helper + `token_fingerprint`; add `"token_fingerprint"` to `__all__` |
| `tests/test_redaction.py` | modify | add `TestTokenFingerprint` covering all states, boundaries, escaping |
| `pr_info/steps/summary.md` | create | this document |
| `pr_info/steps/step_1.md` | create | the single implementation step |

No new folders or modules are created (beyond `pr_info/steps/` for planning docs).

## Out of scope (do not implement here)

- Downstream adoption in `mcp-workspace` (swap 4 call sites, delete
  `utils/token_fingerprint.py` + its tests) — separate follow-up issue.
- Downstream adoption in `mcp-coder` (replace `_mask_api_key` with
  `token_fingerprint(key) or None` at `verification.py:223`, update
  `TestMaskApiKey`) — separate follow-up issue.
- Any token-family prefix registry, `_` suffix fallback, whitespace stripping,
  or SHA-256 variant.
- Routing `redact_env_vars` values through `token_fingerprint`.

## Steps

- **step_1** — TDD add of `token_fingerprint` + tests to `redaction.py` /
  `test_redaction.py` (one commit).
