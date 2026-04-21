# Plan Review Log — Run 1

**Issue:** #20 — feat: add fs/read_file and fs/path_security modules
**Date:** 2026-04-21
**Plan files:** steps 1–4 + summary.md

## Round 1 — 2026-04-21

**Findings:**
1. **Critical — step 3 algorithm mismatch:** `normalize_path` algorithm materially differs from source (return type, containment check, absolute path handling, None guard, known weakness). Plan says "extracted" but is effectively a redesign.
2. **Critical — consumer rule (text.py):** `normalize_line_endings` has only 1 consumer repo (mcp_workspace), violating 2-consumer architectural rule.
3. **Critical — consumer rule (path_security.py):** `normalize_path` also has only 1 consumer repo. Plan acknowledges but justifies with YAGNI-violating "foundational infrastructure" argument.
4. **Accept — read_file uses pathlib:** Minor implementation difference from source (`Path.read_text` vs `open()`), behaviorally equivalent. `str | Path` input is a reasonable improvement.
5. **Accept — architecture doc scope:** Step 4 should only add `fs/` subtree, not fix pre-existing omissions.
6. **Accept — test placement:** Flat `tests/test_fs_*.py` follows existing repo convention.
7. **Accept — no re-export test:** Relying on mypy/pylint for import verification is reasonable.
8. **Accept — step ordering and scoping:** Sensible progression, appropriate granularity.

**Decisions:**
- Finding 1: **Escalated to user** — asked whether faithful extraction or improved extraction
- Finding 2: **Skip** — issue explicitly includes this module; user's deliberate architectural decision
- Finding 3: **Skip** — issue explicitly includes this module; user's deliberate architectural decision
- Findings 4, 6, 7, 8: **Accept** — no changes needed or minor fix applied

**User decisions:**
- Q: Faithful extraction vs improved extraction for `normalize_path`?
- A: "Take all improvements" — Option B (improved extraction with documented deviations)

**Changes:**
- `pr_info/steps/step_3.md` — Reframed as "improved extraction", added deviations table, removed known-weakness test class, updated LLM prompt
- `pr_info/steps/summary.md` — Updated decision 4 (weakness not reproduced), updated path_security description
- `pr_info/steps/step_4.md` — Added scope note for architecture doc (only add fs/ subtree)

**Status:** Changes applied, pending commit

