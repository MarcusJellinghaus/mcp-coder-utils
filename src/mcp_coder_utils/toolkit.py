"""Toolkit contract: base class and types shared by mcp-coder and toolkits."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, get_args

from jsonschema import Draft202012Validator

__all__ = [
    "ActionStatus",
    "VerifyStatus",
    "Finding",
    "ActionRequest",
    "ActionResult",
    "VerifyItem",
    "JsonSchema",
    "validate_params",
    "ToolkitInfo",
    "Toolkit",
]

ActionStatus = Literal["ok", "findings", "error", "skipped"]
VerifyStatus = Literal["ok", "warning", "error"]
JsonSchema = dict[str, Any]


def _check_schema(schema: JsonSchema) -> None:
    """Check a schema against the JSON Schema draft 2020-12 meta-schema.

    Args:
        schema: Schema to check.

    Raises:
        ValueError: Listing every schema problem, one per line.
    """
    meta = Draft202012Validator(Draft202012Validator.META_SCHEMA)
    errors = [f"{e.json_path}: {e.message}" for e in meta.iter_errors(schema)]
    if errors:
        raise ValueError(
            "Invalid params schema:\n" + "\n".join("  " + e for e in errors)
        )


def validate_params(schema: JsonSchema, params: Mapping[str, Any]) -> None:
    """Validate params against a JSON Schema (always draft 2020-12).

    Args:
        schema: Schema to validate against.
        params: Params to validate.

    Raises:
        ValueError: If the schema is malformed or the params do not match it;
            the message lists every problem, one per line.
    """
    _check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = [
        f"{e.json_path}: {e.message}" for e in validator.iter_errors(dict(params))
    ]
    if errors:
        raise ValueError("Invalid params:\n" + "\n".join("  " + e for e in errors))


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


@dataclass
class ToolkitInfo:
    """Static description of a toolkit. Validated at construction only.

    Attributes:
        actions: Action name mapped to its supported depths, in order.
        params_schema: JSON Schema for action params; must be a closed object.
        llm_permissions: Permission lists for the LLM, keyed by name.
        fix_prompts: Prompts for fixing findings, keyed by name.
    """

    actions: dict[str, list[str]]
    params_schema: JsonSchema
    llm_permissions: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    fix_prompts: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate params_schema.

        Raises:
            ValueError: If params_schema is malformed or not a closed object.
        """
        _check_schema(self.params_schema)
        if (
            self.params_schema.get("type") != "object"
            or self.params_schema.get("additionalProperties") is not False
        ):
            raise ValueError(
                'params_schema must have "type": "object" and '
                '"additionalProperties": false'
            )


class Toolkit(ABC):
    """Base class for toolkits run by mcp-coder.

    `describe` receives the toolkit's own config section. `run` never raises
    for ordinary findings; a crash is returned as status "error".
    """

    @abstractmethod
    def describe(self, config: Mapping[str, Any]) -> ToolkitInfo:
        """Describe the toolkit's actions and params.

        Args:
            config: The toolkit's own config section.

        Returns:
            The toolkit description.
        """

    @abstractmethod
    def run(self, request: ActionRequest) -> ActionResult:
        """Run one action.

        Args:
            request: The action to run.

        Returns:
            The action outcome; a crash is returned as status "error".
        """

    def prompt_fragments(self) -> dict[str, str]:
        """Return prompt fragments contributed by the toolkit.

        Returns:
            Fragments keyed by name; empty by default.
        """
        return {}

    def verify(self, project_dir: Path) -> list[VerifyItem]:
        """Check that the toolkit can run in a project.

        Args:
            project_dir: Root directory of the project.

        Returns:
            One item per check; empty by default.
        """
        return []
