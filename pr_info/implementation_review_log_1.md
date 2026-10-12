# review-implementation review log 1

## Round 1 — 2026-10-12
**Findings**:
Diff and spec read; checking whether repo config (import-linter/tach) restricts third-party imports before writing the report.`src/mcp_coder_utils/toolkit.py:38` — medium — `_check_schema` builds the meta-validator without `format_checker=Draft202012Validator.FORMAT_CHECKER`, so it is weaker than the `check_schema()` the issue asks for. A schema with a malformed `"pattern"` (for example `"["`) would pass `ToolkitInfo`, and `validate_params` would later fail with `re.error` instead of `ValueError`. Pass the format checker and add a test with a bad-regex schema. (Analytical: I reasoned this from the code and did not run a probe.)
`pyproject.toml:38` — low — `types-jsonschema` has no version bound, while every other dev dependency has a `>=` floor.
**Decisions**:
Verdict(decision='tasks', tasks=['In src/mcp_coder_utils/toolkit.py:38, build the meta-validator in `_check_schema` with `format_checker=Draft202012Validator.FORMAT_CHECKER` so it matches `Draft202012Validator.check_schema()`. A schema with an invalid `pattern` must then raise `ValueError` when `ToolkitInfo` is built, not `re.error` later in `validate_params`.', 'Add a test that builds `ToolkitInfo` with a params schema containing an invalid regex (for example `{"type": "object", "properties": {"x": {"type": "string", "pattern": "["}}}`) and asserts that it raises `ValueError`.', 'In pyproject.toml:38, add a `>=` version floor to `types-jsonschema` to match the other dev dependencies.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-10-12
**Findings**:
Done reviewing: the diff against main is in, the issue, epic and plan are read, and I'm writing up the report.

`src/mcp_coder_utils/toolkit.py:61` — medium — An unresolvable `$ref` (for example `{"$ref": "#/$defs/missing"}`, or a remote URI) passes the meta-schema check in `_check_schema` and in `ToolkitInfo`. `validate_params` then lets a `jsonschema`/`referencing` resolution error escape instead of `ValueError`. That breaks the issue's Errors decision: errors must be `ValueError`, and `jsonschema` types must stay out of the public API. Fix: catch `jsonschema` errors around `iter_errors` and re-raise them as `ValueError`, and add a test. This is analytical: I reasoned from jsonschema ≥4.18 behaviour and did not run a probe.
`tests/test_toolkit.py:117` — low — No test covers the Draft decision that validation ignores the schema's `$schema` and always uses draft 2020-12. For example, a schema declaring draft-07 should still be validated with 2020-12 semantics.
**Decisions**:
Verdict(decision='tasks', tasks=['In src/mcp_coder_utils/toolkit.py:61, wrap the `iter_errors` call in `validate_params` so that `jsonschema` and `referencing` resolution errors (such as an unresolvable `$ref`) are re-raised as `ValueError` with the original exception chained (`raise ... from exc`). Before writing the fix, run a scratch probe to confirm which exception type is actually raised. Add a test showing that a schema with `{"$ref": "#/$defs/missing"}` makes `validate_params` raise `ValueError`.', 'In tests/test_toolkit.py, add a test showing that a schema declaring `"$schema": "http://json-schema.org/draft-07/schema#"` is still validated with draft 2020-12 semantics. Use a keyword whose behaviour differs between the two drafts, for example `prefixItems`, which 2020-12 enforces and draft-07 ignores.'], escalate_reason=None)
**Changes**:
applied

## Round 3 — 2026-10-12
**Findings**:
Still reviewing. Next I'm checking the import-linter contracts against the new third-party imports.NO FINDINGS
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
rebase-needed
**Escalate reason**: rebase
