"""Verification result type shared by toolkits and toolset providers."""

from dataclasses import dataclass
from typing import Literal, get_args

__all__ = ["VerifyItem", "VerifyStatus"]

VerifyStatus = Literal["ok", "warning", "error"]


@dataclass
class VerifyItem:
    """Result of one verification check. Validated at construction only.

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
