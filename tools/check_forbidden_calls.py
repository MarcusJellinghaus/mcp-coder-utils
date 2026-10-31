"""Fail if ``src/`` spawns processes outside the subprocess wrappers or runs git.

Rules (no allowlist beyond the two wrappers that own process spawning):

- ``subprocess``: ``import subprocess`` / ``from subprocess import``, or a
  process-spawning call from ``os`` (``os.system``, ``os.popen``,
  ``os.spawn*``, ``os.exec*``, ``os.posix_spawn*``, ``os.startfile``) or
  ``asyncio.create_subprocess_*``, outside
  ``src/mcp_coder_utils/subprocess_runner.py`` and
  ``src/mcp_coder_utils/subprocess_streaming.py``. Use those wrappers.
- ``git``: an argv list starting with ``"git"`` (``["git", ...]``, also split
  across lines). This leaf library has no git knowledge; git belongs in
  ``mcp_workspace``.

This is a text scan, not an AST check. It guards against accidents, not
deliberate bypass: an argv that never spells ``"git"`` literally
(``[GIT_BIN, ...]``, ``shlex.split("git status")``) or an aliased import
(``import os as o``) is not caught.

Out of scope: tests and scripts under ``tools/``.
"""

import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Rule:
    """A forbidden pattern, the roots it applies to and the files exempt from it."""

    id: str
    patterns: tuple[re.Pattern[str], ...]
    paths: tuple[str, ...]
    exclude: tuple[str, ...]
    message: str


RULES: tuple[Rule, ...] = (
    Rule(
        "subprocess",
        (
            re.compile(
                r"^[ \t]*(?:import[ \t]+subprocess\b|from[ \t]+subprocess[ \t]+import\b)",
                re.MULTILINE,
            ),
            re.compile(
                r"\bos\.(?:system|popen|spawn\w*|exec[lv]\w*|posix_spawn\w*|startfile)\s*\("
            ),
            re.compile(r"\basyncio\.create_subprocess_(?:exec|shell)\b"),
        ),
        ("src",),
        (
            "src/mcp_coder_utils/subprocess_runner.py",
            "src/mcp_coder_utils/subprocess_streaming.py",
        ),
        "use `mcp_coder_utils.subprocess_runner` or `subprocess_streaming`",
    ),
    Rule(
        "git",
        (re.compile(r'\[\s*"git"'),),
        ("src",),
        (),
        "no git in this leaf library; it belongs in `mcp_workspace`",
    ),
)


def _applies(rule: Rule, rel_path: str) -> bool:
    if rel_path in rule.exclude:
        return False
    return any(rel_path.startswith(f"{root}/") for root in rule.paths)


def find_violations(
    rel_path: str, text: str, rules: Sequence[Rule] = RULES
) -> list[str]:
    """Return "<path>:<line>: [<rule id>] <message>" for every hit in one file."""
    hits: list[str] = []
    for rule in rules:
        if not _applies(rule, rel_path):
            continue
        for pattern in rule.patterns:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                hits.append(f"{rel_path}:{line}: [{rule.id}] {rule.message}")
    return hits


def scan(root: Path) -> list[str]:
    """Return all violations in every *.py under ``root / "src"``."""
    hits: list[str] = []
    for py in sorted((root / "src").rglob("*.py")):
        rel_path = py.relative_to(root).as_posix()
        hits.extend(find_violations(rel_path, py.read_text(encoding="utf-8")))
    return hits


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> int:
    """Print violations; return 1 if any, else 0."""
    hits = scan(_repo_root())
    if hits:
        for hit in hits:
            print(hit)
        print()
        print(f"ERROR: {len(hits)} forbidden call(s) found in src/")
        return 1

    print("OK: no forbidden calls")
    return 0


if __name__ == "__main__":
    sys.exit(main())
