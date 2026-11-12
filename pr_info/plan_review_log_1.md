# review-plan review log 1

## Round 1 — 2026-11-12
**Findings**:
Reading the remaining source and doc files to verify the plan's concrete claims.`pr_info/steps/step_2.md:216` — medium — `test_static_toolset_close_does_nothing` asserts `StaticToolset(()).close() is None`. Under mypy strict, which checks the tests, using the result of a function that returns `None` likely triggers `func-returns-value`, so the step's mypy check would fail (my reasoning, not run). Call `StaticToolset(()).close()` as a plain statement instead: the test still passes as long as it doesn't raise.

`pr_info/steps/step_2.md:205` — low — The extra field `label` on `_ResourceToolset` is only ever passed as a constructor keyword and never read. vulture runs on `tests` at `--min-confidence 60`, so it will likely report it as unused (my reasoning, not run). The existing whitelist entries for fields like `Finding.rule` suggest keyword arguments in calls don't count as uses. The plan's "add other members only if vulture reports them" only covers `src`. State how the step handles it, for example by reading `_ResourceToolset(...).label` before assigning to the `Toolset`-typed variable.
**Decisions**:
Verdict(decision='tasks', tasks=["In pr_info/steps/step_2.md:216, change `test_static_toolset_close_does_nothing` to call `StaticToolset(()).close()` as a plain statement instead of asserting `... is None`, so mypy strict does not report `func-returns-value`. The test should pass as long as the call doesn't raise.", "In pr_info/steps/step_2.md:205, say how the unused `label` field on the `_ResourceToolset` test helper is kept from failing vulture (runs on `tests` at `--min-confidence 60`). Either read `.label` in the test, for example assert on it before assigning the instance to the `Toolset`-typed variable, or drop the field if no test needs it. Don't add a whitelist entry."], escalate_reason=None)
**Changes**:
applied
