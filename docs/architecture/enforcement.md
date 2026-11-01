# Architecture Enforcement

An LLM working on this code sees only part of it and doesn't know the big picture. Asked to fix a problem, it will plausibly import across a boundary or bypass a wrapper — the change looks local and the tests pass. The architecture rules make that fail in CI, so an LLM cannot change or disregard the architecture by accident. The rules live in config files, with each rule's rationale as a comment; this page explains why they exist and how to extend them. What runs where: [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml).

## Leaf library

`mcp_coder_utils` is the bottom of the mcp-coder dependency graph. Importing a sibling repo (`mcp_coder`, `mcp_tools_py`, `mcp_workspace`, `mcp_config`) would create a cycle between repos. Ruleset: the `leaf_library` contract in [`.importlinter`](../../.importlinter). The package also has no git knowledge: an argv starting with `"git"` is caught by rule `git` in [`tools/check_forbidden_calls.py`](../../tools/check_forbidden_calls.py).

## Independence between modules

There is no layer stack: the package is two pairs (`log_utils` -> `redaction`, `subprocess_streaming` -> `subprocess_runner`) plus standalone modules. Each module declares what it may import, so a new dependency between modules is a visible decision. Ruleset: the `depends_on` lists in [`tach.toml`](../../tach.toml). Production code never imports tests: the `no_test_imports_in_source` contract in [`.importlinter`](../../.importlinter).

## Third-party wrappers

One module owns each external library. An upgrade or a replacement then touches one place, and tests mock one place. `subprocess` is owned by `subprocess_runner` and `subprocess_streaming`; everything else, tests included, imports through them. Ruleset: the `subprocess_isolation` contract in [`.importlinter`](../../.importlinter). Spawning a process without importing `subprocess` (`os.system`, `os.popen`, `asyncio.create_subprocess_*`) is invisible to import-linter, so rule `subprocess` in [`tools/check_forbidden_calls.py`](../../tools/check_forbidden_calls.py) guards it.

## No import cycles

Cycles make import order fragile and the declared dependencies meaningless. Two guards catch them, at different grain: [pylint `R0401`](https://pylint.readthedocs.io/en/stable/user_guide/messages/refactor/cyclic-import.html) ([`pyproject.toml`](../../pyproject.toml)) finds any cyclic import between modules and also runs locally, and tach `forbid_circular_dependencies` ([`tach.toml`](../../tach.toml)) catches cycles between the declared modules.

## No dead code

Unused code misleads an LLM reading the code and costs context. [vulture](https://github.com/jendrikseipp/vulture) finds it ([`tools/vulture_check.sh`](../../tools/vulture_check.sh)); [`vulture_whitelist.py`](../../vulture_whitelist.py) lists the intentional exceptions (public API read by downstream consumers, mock and `LogRecord` attributes).

## Declared dependencies match imports

An import that works only through a transitive dependency breaks when that dependency changes. [deptry](https://deptry.com/) checks this. Ruleset: `[tool.deptry]` in [`pyproject.toml`](../../pyproject.toml).

## No URL dependencies

PyPI rejects packages whose dependencies are direct URLs (`pkg @ git+https://...`), and they make installs non-portable. [`tools/check_no_url_deps.py`](../../tools/check_no_url_deps.py) fails on any in `[project]`; GitHub sources go in `[tool.mcp-coder.install-from-github]`.

## Small files

A file must fit an LLM's context window to be read whole. `mcp-coder check file-size` enforces the limit. Ruleset: [`.large-files-allowlist`](../../.large-files-allowlist) and the line limit in [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml).

## Why both import-linter and tach

Neither covers everything. [import-linter](https://import-linter.readthedocs.io/en/stable/) handles third-party isolation and forbidden contracts, tests included. [tach](https://docs.gauge.sh/) handles explicit `depends_on` lists and cycle detection, but does not isolate third-party libraries and here covers `src/` only. Use tach for module-to-module dependencies and import-linter for fine-grained rules.

## Adding or changing rules

- **New external dependency** that one module should own: add a third-party isolation contract (wrapper pattern).
- **New module:** add a `[[modules]]` entry with its `depends_on` in [`tach.toml`](../../tach.toml).
- **A rule import-linter cannot express** (a call, not an import): add it to `RULES` in [`tools/check_forbidden_calls.py`](../../tools/check_forbidden_calls.py).
- **An import that is intentionally allowed despite a rule:** add it to `ignore_imports` with a comment saying why.
