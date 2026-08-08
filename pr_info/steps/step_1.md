# Step 1 — Add `token_fingerprint` to `redaction.py` (TDD, one commit)

> Read `pr_info/steps/summary.md` first — it holds the full contract, the rules,
> and the worked examples this step must satisfy. This is the only
> implementation step; it produces exactly one commit (tests + implementation +
> all checks passing).

## WHERE

- **Implementation:** `src/mcp_coder_utils/redaction.py` (existing file — extend,
  do not create a new module).
- **Tests:** `tests/test_redaction.py` (existing file — add a new test class).
- No new folders or modules.

## WHAT

Add to `src/mcp_coder_utils/redaction.py`:

```python
def _escape_fragment(fragment: str) -> str:
    """Escape a revealed token fragment so control chars can't break a log line."""
    ...

def token_fingerprint(token: str | None) -> str:
    """Return a short, non-reversible identifier for *token*, safe for logs.

    Three states, three outputs:
      * absent  (None or "")      -> ""
      * malformed (len < 16)      -> "<malformed>, len=N"
      * fingerprinted (len >= 16) -> "<esc(first4)>...<esc(last4)>, len=N"

    len=N is always the RAW input length, measured before escaping. Revealed
    parts are escaped per-slice; because escaping expands control characters,
    len and the visible character count may legitimately disagree — that is by
    design (len describes the secret, escaping describes the rendering). The
    input is never stripped: the caller still holds the unstripped token and
    that is what actually failed to authenticate.
    """
    ...
```

## HOW (integration)

- Add `"token_fingerprint"` to the module-level `__all__` list in
  `redaction.py`. Do **not** export `_escape_fragment` (leading underscore,
  internal helper — stays out of `__all__`).
- No new imports required (stdlib `str.encode`/`bytes.decode` only).
- In tests, extend the existing import from `mcp_coder_utils.redaction` to
  include `token_fingerprint`.

## ALGORITHM

```
token_fingerprint(token):
    if not token:                      # None or "" -> absent
        return ""
    length = len(token)                # raw length, BEFORE escaping
    if length < 16:                    # reveal at most half -> need >=16 to show 8
        return f"<malformed>, len={length}"
    head = _escape_fragment(token[:4]) # escape per-slice, not whole-then-slice
    tail = _escape_fragment(token[-4:])
    return f"{head}...{tail}, len={length}"

_escape_fragment(fragment):
    return fragment.encode("unicode_escape").decode("ascii")
```

## DATA

- Input: `token: str | None`.
- Return: plain `str`. Never `None`, never a truthy sentinel.
  - absent → `""`
  - malformed → `"<malformed>, len=N"` (`N` = `len(token)`)
  - fingerprinted → `"<head>...<tail>, len=N"`

## TESTS (write first — TDD)

Add a `TestTokenFingerprint` class to `tests/test_redaction.py`. Use **exact
equality** assertions (not "no char appears" phrasing — `<malformed>` contains
an `a`, so a substring test would be self-defeating).

- `token_fingerprint(None) == ""`
- `token_fingerprint("") == ""`
- `token_fingerprint("abc") == "<malformed>, len=3"`
- `token_fingerprint("ghp_" + "A" * 32 + "a3f9") == "ghp_...a3f9, len=40"`
- `token_fingerprint("sk-abcd1234wxyz5678") == "sk-a...5678, len=19"`
- **Boundaries:** a 15-char string → `"<malformed>, len=15"`; a 16-char string
  → fingerprinted form with `len=16` (assert exact expected string).
- **Escaping / one line:** for the 40-char token + trailing `"\n"`, assert the
  result `== "ghp_...3f9\\n, len=41"` **and** `"\n" not in result` (literal
  newline absent — it is rendered as the two chars `\n`).
- **Middle never leaks:** for a long token whose middle is a distinctive marker
  (e.g. `"AAAA" + "SECRETMIDDLE" + "ZZZZ"`), assert `"SECRETMIDDLE" not in
  token_fingerprint(...)`.

## CHECKS (must all pass before commit)

Run via MCP tools (per CLAUDE.md):

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check   extra_args=["-n", "auto"]
mcp__tools-py__run_mypy_check
```

Fix any issue before proceeding. (Watch for pylint E731 — use the module-level
`def _escape_fragment`, not an assigned lambda.)

## COMMIT

One commit containing the `redaction.py` change and the `test_redaction.py`
change together. Before committing, run `./tools/format_all.sh` and stage the
formatting result, per CLAUDE.md.

Suggested message:

```
feat(redaction): add token_fingerprint helper for safe credential logging
```
