# Summary — Add `console_level` to `setup_logging`

Issue #36. Give `setup_logging` a third parameter, `console_level`, so it can
write to a **file and the console simultaneously** at independent thresholds,
instead of today's hard file-XOR-console choice.

Blocks `mcp-tools-sql#37`: a `server` command that logs to a file at `INFO`
(full per-tool-call trail) while still showing `OUTPUT`-level messages and
errors on the console when a human runs it in a terminal.

## Target public API

```python
def setup_logging(
    log_level: str | int,
    log_file: str | None = None,
    console_level: str | int | None = None,
) -> None: ...
```

| `console_level` | Behaviour |
|---|---|
| `None` (default) | Exactly today's behaviour — console **iff** no `log_file`. Fully backwards compatible. |
| a level (`OUTPUT`, `"OUTPUT"`, `logging.INFO`, `"INFO"`, …) | Console handler at that level, **in addition to** any file handler. |

Not a breaking change: a new keyword with a default plus widened annotations.
No existing call site changes.

## Architectural / design changes

- **File-XOR-console → two independent sinks.** The `if log_file: … else: …`
  fork (`src/mcp_coder_utils/log_utils.py:165`) is replaced by two independent
  `if` blocks: a file sink and a console sink that can coexist.
- **Root logger level becomes `min(log_level, console_level)`.** Records are
  filtered at the logger before any handler sees them, so the root floor must
  sit at the *lowest* handler threshold or lower-level records are silently
  dropped. The file handler's explicit `setLevel(numeric_level)` therefore
  becomes load-bearing and must stay.
- **Marker-based, idempotent handler management** replaces
  `_is_testing_environment()`. `setup_logging` removes only the handlers *it*
  created (tagged with a marker attribute), then adds fresh sinks. This is
  idempotent under repeated calls, never clobbers pytest's `LogCaptureHandler`
  or a consumer's own handler, and lets `_is_testing_environment()` be deleted
  entirely (KISS — one fewer concept, no early returns).
- **One structlog configuration for all cases.** The single JSON-renderer
  processor chain is configured unconditionally. The latent, never-working
  console variant ending in `ProcessorFormatter.wrap_for_formatter` is deleted
  (it required a `ProcessorFormatter` the console handler never had). Verified
  safe: every `log_function_call` test patches `structlog` wholesale, so nothing
  depends on the old config.
- **`_parse_level(level: str | int) -> int`** extracted from the inline
  level-parsing block (keeping the `getattr` → `getLevelName` fallback that
  resolves `"OUTPUT"`) and shared by both `log_level` and `console_level`.
- **`__all__`** gains `CleanFormatter`, `ExtraFieldsFormatter`,
  `STANDARD_LOG_FIELDS` — already imported cross-repo by `mcp_coder`'s shim, so
  the contract is made to match reality.
- **One init message** at `DEBUG`, naming whichever sinks were configured
  (was two: file at `INFO`, console at `DEBUG`).
- **stderr stays the default** for the console handler (bare `StreamHandler()`,
  no `stream=`) — stdio MCP servers must never write to stdout.

## Constraints preserved (from the issue)

- A test **must** cover `log_level="INFO", console_level=DEBUG` — the case where
  the root floor matters and the motivating `INFO`/`OUTPUT` case would not catch it.
- File handler keeps its explicit `setLevel(numeric_level)`.
- `console_level` without `log_file` is allowed and documented (root floor only).
- No `stream=` parameter is introduced.

## Out of scope (this repo / this PR)

- `mcp_tools_py/log_utils.py` — re-exports by identity, inherits the param, no change.
- `mcp_coder/utils/log_utils.py` shim — `console_level` passthrough is a companion PR.
- `mcp-workspace` — call site only; `--console-only` keeps working, no change.

## Files created / modified

| Path | Action |
|---|---|
| `src/mcp_coder_utils/log_utils.py` | **modified** — the change itself |
| `src/mcp_coder_utils/__init__.py` | unchanged (package `__all__` is `__version__` only; the export list edited lives in `log_utils.py`) |
| `tests/test_log_utils.py` | **modified** — new tests, adjust formatter-selection helper |
| `pr_info/steps/summary.md` | **created** |
| `pr_info/steps/step_1.md` … `step_4.md` | **created** |

No new folders or modules. No call site anywhere changes.

## Steps (one commit each)

1. **`_parse_level` extraction + widen `log_level` annotation** — pure refactor.
2. **`__all__` additions** — export the three formatter symbols.
3. **Marker-based idempotent handler management + single structlog config** —
   behaviour-preserving internal refactor; deletes `_is_testing_environment()`.
4. **Add `console_level` — dual-sink logging** — the feature, with the
   `INFO`/`DEBUG` root-floor test.

Each step is TDD (tests first, then implementation) and must leave pylint,
pytest, and mypy green before its single commit.
