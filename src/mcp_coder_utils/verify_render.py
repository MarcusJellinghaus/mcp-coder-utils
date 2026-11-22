"""Rendering primitives for status-check output.

Tabular rows (label, status marker, value) grouped into titled sections;
the rows of one section share one label width, so their marker and value
columns line up.
"""

from collections.abc import Iterable
from typing import NamedTuple

__all__ = ["STATUS_SYMBOLS", "Line", "Row", "hint_row"]

STATUS_SYMBOLS: dict[str, str] = {
    "success": "[OK]",
    "failure": "[ERR]",
    "warning": "[WARN]",
}

_MARKER_SLOT_WIDTH: int = max(len(v) for v in STATUS_SYMBOLS.values())
_LABEL_WIDTH: int = 22  # minimum label width; sections widen automatically


class Row(NamedTuple):
    """One tabular row; label and/or marker may be empty."""

    label: str
    marker: str
    value: str
    indent: int = 2
    wrap: bool = False


Line = Row | str  # str = freeform line (group header, blank, notice), printed as-is


def hint_row(text: str) -> Row:
    """Hint/continuation line: starts at the section's value column.

    Args:
        text: Hint text.

    Returns:
        A label-less, marker-less ``Row`` that never widens its section.
    """
    return Row("", "", text)


def _section_label_width(lines: Iterable[Line]) -> int:
    """Return the label width of a section: the default, widened to fit.

    Each ``Row`` needs ``len(label) + indent - 2`` so that its label fits in
    the field left over after its extra indent; ``str`` items are ignored.

    Args:
        lines: The section's lines.

    Returns:
        ``max(_LABEL_WIDTH, len(label) + indent - 2)`` over the ``Row`` items.
    """
    return max(
        [
            _LABEL_WIDTH,
            *(len(r.label) + r.indent - 2 for r in lines if isinstance(r, Row)),
        ]
    )


def _format_row_prefix(
    label: str, marker: str, *, indent: int, label_width: int = _LABEL_WIDTH
) -> str:
    """Render the column-aligned prefix portion of a tabular row.

    Empty marker is padded to ``_MARKER_SLOT_WIDTH`` so the value column
    starts at the same horizontal position regardless of marker presence.
    The label field is ``label_width - (indent - 2)``, so the prefix is
    ``label_width + 10`` long at every indent: rows of one section share
    their marker and value columns. Callers size ``label_width`` with
    ``_section_label_width`` so no label exceeds its field.

    Args:
        label: Row label (may be empty for label-less rows).
        marker: Status marker (e.g. ``[OK]``, ``[ERR]``, ``[WARN]``, or "").
        indent: Number of leading spaces.
        label_width: Label width of the section (at indent 2).

    Returns:
        ``indent + label_field + " " + marker_field + " "`` WITHOUT
        rstrip — the trailing space and the full marker-slot padding are
        preserved. Used directly by callers that need the prefix without
        a value (e.g. ``textwrap.wrap`` continuation indent).
    """
    field = label_width - (indent - 2)
    return f"{' ' * indent}{label.ljust(field)} {marker.ljust(_MARKER_SLOT_WIDTH)} "


def _format_row(label: str, marker: str, value: str, *, indent: int) -> str:
    """Render a tabular row (labeled or label-less) as a one-row section.

    Composed on top of ``_format_row_prefix``; appends the value and
    rstrips trailing whitespace. Label-less rows pass ``label=""``;
    the empty label is padded so the value column aligns with
    neighbouring labeled rows. A label too long for ``_LABEL_WIDTH``
    widens this row's columns instead of overrunning the marker.

    Args:
        label: Row label (may be empty for label-less rows).
        marker: Status marker (e.g. ``[OK]``, ``[ERR]``, ``[WARN]``, or "").
        value: Row value text.
        indent: Number of leading spaces.

    Returns:
        Formatted row string with trailing whitespace stripped.
    """
    width = _section_label_width([Row(label, marker, value, indent)])
    return (
        _format_row_prefix(label, marker, indent=indent, label_width=width) + value
    ).rstrip()


def _pad(title: str) -> str:
    r"""Return a section header line padded to 75 chars with '='."""
    prefix = f"=== {title} "
    return "\n" + prefix + "=" * max(0, 75 - len(prefix))
