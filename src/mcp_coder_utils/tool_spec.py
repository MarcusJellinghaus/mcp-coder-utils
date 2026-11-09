"""Tool contract: framework-neutral tool specs for MCP and non-MCP consumers."""

import inspect
import warnings
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel, create_model

__all__ = ["ToolSpec", "tool_spec", "ToolSink", "ToolCollector"]


@dataclass(frozen=True)
class ToolSpec:
    """A tool exported as plain data.

    Attributes:
        name: Final tool name, e.g. "query_x".
        description: Human-readable description shown to the LLM.
        fn: The tool function, sync or async.
        args_model: Pydantic model built once from `fn`'s signature.
        group: Fully qualified group, e.g. "sql.update".
        read_only: Whether the tool leaves state unchanged.
    """

    name: str
    description: str
    fn: Callable[..., Any]
    args_model: type[BaseModel]
    group: str
    read_only: bool


def _build_args_model(fn: Callable[..., Any], model_name: str) -> type[BaseModel]:
    """Build a pydantic model from a function's signature.

    Args:
        fn: Function whose parameters become the model fields.
        model_name: Class name of the generated model.

    Returns:
        The generated model class.

    Raises:
        ValueError: If the signature cannot be resolved or has a parameter
            that cannot be modelled (`*args`, `**kwargs`, positional-only,
            `_`-prefixed or unannotated).
    """
    try:
        sig = inspect.signature(fn, eval_str=True)
    except Exception as exc:
        raise ValueError(f"cannot resolve signature of {model_name}: {exc}") from exc
    fields: dict[str, Any] = {}
    for p in sig.parameters.values():
        if p.kind is inspect.Parameter.VAR_POSITIONAL:
            raise ValueError(f"{model_name}: *{p.name} is not supported")
        if p.kind is inspect.Parameter.VAR_KEYWORD:
            raise ValueError(f"{model_name}: **{p.name} is not supported")
        if p.kind is inspect.Parameter.POSITIONAL_ONLY:
            raise ValueError(
                f"{model_name}: positional-only parameter {p.name!r} is not supported"
            )
        if p.name.startswith("_"):
            raise ValueError(
                f"{model_name}: parameter {p.name!r} must not start with '_'"
            )
        if p.annotation is inspect.Parameter.empty:
            raise ValueError(f"{model_name}: parameter {p.name!r} has no annotation")
        fields[p.name] = (p.annotation, ... if p.default is p.empty else p.default)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*shadows an attribute.*")
        return create_model(model_name, **fields)


def tool_spec(
    fn: Callable[..., Any],
    *,
    group: str,
    read_only: bool,
    name: str | None = None,
    description: str | None = None,
) -> ToolSpec:
    """Build a `ToolSpec` from a function.

    Args:
        fn: The tool function, sync or async.
        group: Fully qualified group, e.g. "sql.update".
        read_only: Whether the tool leaves state unchanged.
        name: Tool name; defaults to `fn.__name__`.
        description: Tool description; defaults to `fn.__doc__`.

    Returns:
        The frozen tool spec.

    Raises:
        ValueError: If the name or description is empty, or the signature
            cannot be modelled.
    """
    # A callable without its own __name__ (e.g. functools.partial) would
    # otherwise report its class docstring as the tool description.
    fn_name = getattr(fn, "__name__", None)
    if name is None:
        name = fn_name
    if description is None and fn_name:
        description = fn.__doc__
    if not name:
        raise ValueError("tool name must not be empty")
    if not description:
        raise ValueError(f"tool {name!r}: description must not be empty")
    args_model = _build_args_model(fn, name)
    return ToolSpec(name, description, fn, args_model, group, read_only)


class ToolSink(Protocol):
    """Receiver that producers write tool specs into."""

    def add(self, spec: ToolSpec) -> None:
        """Add one tool spec.

        Args:
            spec: The spec to add.
        """


class ToolCollector:
    """Default `ToolSink`: keeps insertion order and rejects duplicate names."""

    def __init__(self) -> None:
        self._specs: dict[str, ToolSpec] = {}

    def add(self, spec: ToolSpec) -> None:
        """Add one tool spec.

        Args:
            spec: The spec to add.

        Raises:
            ValueError: If a spec with the same name was already added.
        """
        if spec.name in self._specs:
            raise ValueError(f"duplicate tool name {spec.name!r}")
        self._specs[spec.name] = spec

    @property
    def specs(self) -> tuple[ToolSpec, ...]:
        """The collected specs in insertion order.

        Returns:
            The specs as a tuple.
        """
        return tuple(self._specs.values())

    def __iter__(self) -> Iterator[ToolSpec]:
        """Iterate the collected specs in insertion order.

        Returns:
            An iterator over the specs.
        """
        return iter(self._specs.values())

    def __len__(self) -> int:
        """Count the collected specs.

        Returns:
            The number of specs.
        """
        return len(self._specs)
