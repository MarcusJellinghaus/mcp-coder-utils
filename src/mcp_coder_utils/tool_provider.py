"""Toolset provider contract: tool packages loaded as entry-point plugins."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from mcp_coder_utils.tool_spec import ToolSpec
from mcp_coder_utils.tool_verify import VerifyItem

__all__ = ["Toolset", "StaticToolset", "ToolsetProvider"]


class Toolset(Protocol):
    """Tool specs built by a provider, plus the resources behind them."""

    @property
    def specs(self) -> tuple[ToolSpec, ...]:
        """The toolset's specs; names are unique within one toolset.

        Returns:
            The specs as a tuple.
        """

    def close(self) -> None:
        """Release the toolset's resources."""


@dataclass(frozen=True)
class StaticToolset:
    """A toolset that holds no resources; close() does nothing.

    Attributes:
        specs: The toolset's specs; names are unique within one toolset.
    """

    specs: tuple[ToolSpec, ...]

    def close(self) -> None:
        """Do nothing; a static toolset holds no resources."""


class ToolsetProvider(ABC):
    """Base class for tool packages loaded as plugins.

    Rules for providers:

    - `config` is the consumer's TOML table as parsed. Unknown keys give a
      "warning" row in `verify` and are ignored by `build`. Missing or wrongly
      typed keys give an "error" row in `verify` and a `ValueError` from
      `build`.
    - `build` raises `ValueError` for every problem it detects, config or
      environment (missing file, unreadable file, missing driver). Any other
      exception is a provider bug.
    - Path values are absolute or start with `~`; a relative path is an error
      (the consumer's working directory is undefined).
    - `build` can be called repeatedly; each returned `Toolset` owns its
      resources and `close` releases them.
    - `build` opens no connection, makes no network call and writes nothing to
      disk; connections open on first use.
    - `verify` never raises for problems it detects. `verify(connect=False)`
      opens no connection and makes no network call. Invariant: no "error"
      row under `connect=False` means `build` on the same config succeeds.
      `verify(connect=True)` returns at least the rows of
      `verify(connect=False)`.
    - A provider whose `build` can fail overrides `verify`; the default `[]`
      is only right for a provider whose `build` cannot fail.
    - Rows about the provider's own config table are named `config.<key>`;
      other row names (including other `config.*` names) are free.
    - Spec names are unique within one toolset; the consumer detects clashes
      across toolsets.
    - Registration: the consumer names the entry-point group; entry-point
      name = the consumer's config name, value = the provider class.
    """

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        """Store the provider's own config table as public `self.config`.

        It only stores; config problems surface in `verify`.

        Args:
            config: The provider's own config table. `self.config` is always a
                mapping, empty when none is given.
        """
        self.config: Mapping[str, Any] = {} if config is None else config

    @abstractmethod
    def build(self) -> Toolset:
        """Build the toolset. Opens no connection.

        Returns:
            The toolset.

        Raises:
            ValueError: For every problem it detects, config or environment.
        """

    def verify(self, *, connect: bool = False) -> list[VerifyItem]:
        """Check that the provider can build its toolset.

        Never raises for problems it detects.

        Args:
            connect: `False` opens no connection and makes no network call;
                `True` may connect.

        Returns:
            One item per check; empty by default.
        """
        return []
