# Step 3 — Marker-based idempotent handlers + single structlog config

**Goal:** Behaviour-preserving internal refactor of `setup_logging`. Replace the
`_is_testing_environment()` machinery and the file-XOR-console `if/else` with
(a) a marker-based idempotent handler pass, (b) two independent sink `if` blocks
(console condition still `log_file is None` — the feature parameter comes in
Step 4), (c) one unconditional structlog JSON config, (d) one DEBUG init message.
**No public API change in this step.** All existing tests must still pass.

See [summary.md](./summary.md).

## WHERE
- `src/mcp_coder_utils/log_utils.py`
- `tests/test_log_utils.py`

## WHAT
- Add a module constant marker, e.g. `_HANDLER_MARKER = "_mcp_coder_utils_handler"`.
- Delete `_is_testing_environment()` entirely (only used by `setup_logging`).
- `setup_logging(log_level: str | int, log_file: Optional[str] = None) -> None`
  body restructured (signature unchanged from Step 1).

## HOW
- Handler dedup keys on `getattr(h, _HANDLER_MARKER, False)`, **not**
  `isinstance(StreamHandler)`. This leaves pytest's `LogCaptureHandler` and any
  consumer handler untouched, so no testing-environment special-casing is needed.
- Configure structlog **once, unconditionally**, using the JSON-renderer chain
  (the current file-branch processors). Delete the console-branch variant ending
  in `structlog.stdlib.ProcessorFormatter.wrap_for_formatter`. Safe: all
  `log_function_call` tests patch `mcp_coder_utils.log_utils.structlog` wholesale.
- File sink keeps its explicit `fh.setLevel(numeric_level)` (load-bearing later).
- Tag every handler this function creates with the marker before `addHandler`.

## ALGORITHM (`setup_logging` core)
```
root = logging.getLogger()
for h in root.handlers[:]:                  # remove ONLY our previous handlers
    if getattr(h, _HANDLER_MARKER, False): root.removeHandler(h); h.close()
numeric_level = _parse_level(log_level)
root.setLevel(numeric_level)                # min() arrives in Step 4
if log_file:                                # file sink
    os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
    fh = FileHandler(log_file); fh.setLevel(numeric_level)
    fh.setFormatter(JsonFormatter(fmt=...)); setattr(fh, _HANDLER_MARKER, True)
    root.addHandler(fh)
if log_file is None:                        # console sink (XOR preserved this step)
    ch = StreamHandler(); ch.setLevel(numeric_level)
    ch.setFormatter(CleanFormatter() if numeric_level >= OUTPUT
                    else ExtraFieldsFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    setattr(ch, _HANDLER_MARKER, True); root.addHandler(ch)
structlog.configure(processors=[... JSONRenderer ...], ...)   # once, all cases
stdlogger.debug("Logging initialized: %s", ", ".join(sinks))  # sinks = ["file=...","console=..."]
```

## DATA
- `sinks`: list of human-readable sink descriptors for the single init message
  (e.g. `["file=/path level=INFO"]`, `["console level=OUTPUT"]`).
- No return value; configures the root logger + structlog globally.

## TESTS (write first)
Add to `tests/test_log_utils.py` (guarding the marker/idempotency behaviour):
- **Idempotency:** call `setup_logging("INFO")` twice → exactly one marked
  console handler on root (no stacking).
- **Marker isolation:** pre-attach a plain `StreamHandler` (no marker) to root,
  call `setup_logging("INFO")` → the foreign handler survives *and* our marked
  handler is added.
- **Cleanup:** repeated file-mode calls to the same path do not accumulate
  marked `FileHandler`s.
- Existing `TestSetupLogging`, `TestSetupLoggingFormatterSelection`,
  `TestOutputLevel`, and all `TestLogFunctionCall*` classes must pass unchanged.
- Simplify `TestSetupLoggingFormatterSelection._get_console_formatter` only if
  its manual handler-stripping now conflicts; otherwise leave it as-is.

## CHECKS
`mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check`
(`-n auto` + fast-unit exclusions), `mcp__tools-py__run_mypy_check` — all green.
Watch for pylint dead-code / unused-import warnings after deleting
`_is_testing_environment()`.

## COMMIT
One commit: refactor + new marker/idempotency tests, all existing tests green.
