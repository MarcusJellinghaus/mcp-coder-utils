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
    """Escape a revealed token fragment so control chars can't break a log line.

    Args:
        fragment: A slice of the raw token that will be shown in the log.

    Returns:
        The fragment with control and non-ASCII characters escaped.
    """
    ...

def token_fingerprint(token: str | None) -> str:
    """Return a short, non-reversible identifier for *token*, safe for logs.

    Three states, three outputs:
      * absent  (None or "")      -> ""
      * malformed (len < 16)      -> "<malformed>, len=N"
      * fingerprinted (len >= 16) -> "<esc(first4)>...<esc(last4)>, len=N"

    len=N is always the RAW input length, measured before escaping, and counts
    characters (code points), not bytes. Revealed parts are escaped per-slice;
    because escaping expands control characters, len and the visible character
    count may legitimately disagree — that is by design (len describes the
    secret, escaping describes the rendering). The input is never stripped: the
    caller still holds the unstripped token and that is what actually failed to
    authenticate.

    Args:
        token: The raw secret token, or None when no token is configured.

    Returns:
        "" when absent, "<malformed>, len=N" when shorter than 16 characters,
        otherwise "<esc(first4)>...<esc(last4)>, len=N".
    """
    ...
```

Both docstrings carry Google-style `Args:` / `Returns:` sections, matching the
convention of the existing functions in `redaction.py`. This is required, not
cosmetic: ruff's `DOC201` (docstring-missing-returns) is enabled via
`select = ["D", "DOC"]` with `preview = true` and would otherwise fail.

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

Every test method needs a `-> None` return annotation — `mypy --strict` covers
`tests/` as well as `src/`.

**One parametrized table for the pure input → expected cases**, matching the
`@pytest.mark.parametrize` style already used by `TestRedactEnvVars` in the same
file:

| `token` | expected |
|---|---|
| `None` | `""` |
| `""` | `""` |
| `"abc"` | `"<malformed>, len=3"` |
| `"A" * 15` (boundary, below threshold) | `"<malformed>, len=15"` |
| `"A" * 16` (boundary, at threshold) | `"AAAA...AAAA, len=16"` |
| `"ghp_" + "A" * 32 + "a3f9"` | `"ghp_...a3f9, len=40"` |
| `"sk-abcd1234wxyz5678"` | `"sk-a...5678, len=19"` |
| `"ghp_" + "A" * 32 + "a3f9" + "\n"` | `"ghp_...3f9\\n, len=41"` |

(The last expected value is the Python literal — a backslash followed by `n`,
not a newline.)

**Two standalone tests for the non-equality assertions** (they check absence,
not an exact value, so they do not belong in the table):

- **Stays on one line:** for the 40-char token + trailing `"\n"`, assert
  `"\n" not in result` — the literal newline is absent, rendered as the two
  characters `\n`.
- **Middle never leaks:** for a long token whose middle is a distinctive marker
  (e.g. `"AAAA" + "SECRETMIDDLE" + "ZZZZ"`), assert `"SECRETMIDDLE" not in
  token_fingerprint(...)`.

## CHECKS (must all pass before commit)

Run via MCP tools (per CLAUDE.md):

```
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check   extra_args=["-n", "auto"]
mcp__mcp-tools-py__run_mypy_check
mcp__mcp-tools-py__run_ruff_check
```

`run_ruff_check` is not optional here: CI gates on it via the
`ruff-docstrings` job (`ruff check src tests`), and the `DOC` rules are the
ones most likely to trip on a newly added docstring.

Fix any issue before proceeding. (Use the module-level `def _escape_fragment`
rather than an assigned lambda — plain readability.)

## COMMIT

One commit containing the `redaction.py` change and the `test_redaction.py`
change together. Before committing, run `mcp__mcp-tools-py__run_format_code`
(black + isort) and stage the formatting result, per CLAUDE.md.

Suggested message:

```
feat(redaction): add token_fingerprint helper for safe credential logging
```
