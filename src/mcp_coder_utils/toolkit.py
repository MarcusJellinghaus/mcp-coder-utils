"""Toolkit contract: result types shared by mcp-coder and toolkit implementations."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, get_args

__all__ = [
    "ActionStatus",
    "VerifyStatus",
    "Finding",
    "ActionRequest",
    "ActionResult",
    "VerifyItem",
]

ActionStatus = Literal["ok", "findings", "error", "skipped"]
VerifyStatus = Literal["ok", "warning", "error"]


@dataclass(frozen=True)
class Finding:
    """A single issue reported by a toolkit action.

    Attributes:
        key: Stable, line-insensitive identifier used to match findings across runs.
        message: Human-readable description.
        path: File the finding refers to, if any.
        rule: Rule or check identifier, if any.
        severity: Free-form severity string; not validated.
    """

    key: str
    message: str
    path: str | None = None
    rule: str | None = None
    severity: str | None = None


@dataclass(frozen=True)
class ActionRequest:
    """A request to run one toolkit action.

    Attributes:
        action: Name of the action to run.
        depth: Requested depth of the run.
        project_dir: Root directory of the project to operate on.
        params: Action parameters. Frozen only shallowly; the mapping may be mutable.
    """

    action: str
    depth: str
    project_dir: Path
    params: Mapping[str, Any]


@dataclass
class ActionResult:
    """Outcome of a toolkit action. Validated at construction only.

    Attributes:
        status: Overall outcome.
        summary: One-line human-readable summary.
        findings: Issues found; required for "findings", forbidden for "ok"/"skipped".
        fix_text: Instructions for fixing the findings.
        raw: Raw tool output.
    """

    status: ActionStatus
    summary: str
    findings: list[Finding] = field(default_factory=list)
    fix_text: str = ""
    raw: str = ""

    def __post_init__(self) -> None:
        """Validate status and its consistency with findings.

        Raises:
            ValueError: If status is unknown, "findings" has no findings, or
                "ok"/"skipped" carries findings.
        """
        allowed = get_args(ActionStatus)
        if self.status not in allowed:
            raise ValueError(
                f"Unknown action status {self.status!r}; allowed: {', '.join(allowed)}"
            )
        if self.status == "findings" and not self.findings:
            raise ValueError("Status 'findings' requires at least one finding")
        if self.status in ("ok", "skipped") and self.findings:
            raise ValueError(f"Status {self.status!r} must not carry findings")


@dataclass
class VerifyItem:
    """Result of one toolkit verification check. Validated at construction only.

    Attributes:
        name: Name of the check.
        status: Outcome of the check.
        message: Human-readable detail.
        hint: Suggested remedy, if any.
    """

    name: str
    status: VerifyStatus
    message: str = ""
    hint: str | None = None

    def __post_init__(self) -> None:
        """Validate status.

        Raises:
            ValueError: If status is unknown.
        """
        allowed = get_args(VerifyStatus)
        if self.status not in allowed:
            raise ValueError(
                f"Unknown verify status {self.status!r}; allowed: {', '.join(allowed)}"
            )
