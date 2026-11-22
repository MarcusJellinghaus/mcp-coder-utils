"""Tests for the per-section renderer and SectionBuilder (verify_render)."""

import re
from collections.abc import Sequence
from unittest.mock import patch

import pytest

from mcp_coder_utils.verify_render import (
    _LABEL_WIDTH,
    _MARKER_SLOT_WIDTH,
    STATUS_SYMBOLS,
    Line,
    Row,
    SectionBuilder,
    _format_row,
    _pad,
    hint_row,
    render_rows,
)


def _expected_value_column(*, label_width: int = _LABEL_WIDTH) -> int:
    """Return the 0-indexed column where the value SHOULD begin.

    Layout: [indent][label.ljust(label_width - (indent - 2))][space][marker.ljust(_MARKER_SLOT_WIDTH)][space][value]
    The label field shrinks as the indent grows, so the value column is
    the same at every indent. Computed purely from layout constants; does
    NOT inspect any line. Use ``_assert_value_at_column`` to verify a real
    line against this.
    """
    return 2 + label_width + 1 + _MARKER_SLOT_WIDTH + 1


def _assert_value_at_column(line: str, expected_col: int) -> None:
    """Assert ``line`` has whitespace at ``expected_col - 1`` and a non-whitespace at ``expected_col``."""
    assert expected_col >= 1, f"expected_col must be >= 1; got {expected_col}"
    assert expected_col < len(line), (
        f"line shorter than expected value column {expected_col}: {line!r}"
    )
    assert line[expected_col - 1].isspace(), (
        f"prefix overflowed past col {expected_col - 1} (expected space): {line!r}"
    )
    assert not line[expected_col].isspace(), (
        f"value missing at col {expected_col} (expected non-space): {line!r}"
    )


def _render(lines: Sequence[Line]) -> str:
    """Render a section's lines to text (test helper)."""
    return "\n".join(render_rows(lines))


_MARKER_RE = re.compile("|".join(re.escape(s) for s in STATUS_SYMBOLS.values()))


def _assert_section_aligned(text: str) -> int:
    """All marker-bearing rows share marker column and value column; return row count."""
    first: tuple[int, int] | None = None
    count = 0
    for line in text.splitlines():
        m = _MARKER_RE.search(line)
        rest = line[m.end() :] if m else ""
        if m is None or not rest.strip():
            continue  # hints, marker-less rows, freeform
        value_col = len(line) - len(rest.lstrip())
        if first is None:
            first = (m.start(), value_col)
        assert m.start() == first[0], (
            f"marker at col {m.start()}, expected {first[0]}: {line!r}"
        )
        _assert_value_at_column(line, first[1])
        count += 1
    return count


def _assert_sections_aligned(output: str) -> None:
    """Apply ``_assert_section_aligned`` to each '=== ' section of ``output``.

    Asserts at least one row was checked overall.
    """
    chunks: list[list[str]] = [[]]
    for line in output.splitlines():
        if line.startswith("=== "):
            chunks.append([])
        chunks[-1].append(line)
    total = sum(_assert_section_aligned("\n".join(chunk)) for chunk in chunks)
    assert total > 0, f"no marker-bearing rows found in output: {output!r}"


_DEFAULT_COL = _expected_value_column()  # 32
_WIDE_COL = _expected_value_column(label_width=30)  # 40


class TestRenderRows:
    """``render_rows`` computes one label width per section."""

    def test_long_label_widens_every_row(self) -> None:
        text = _render(
            [
                Row("a" * 30, "[OK]", "long"),
                Row("short", "[ERR]", "x"),
                Row("child", "[WARN]", "y", 4),
            ]
        )
        assert _WIDE_COL == 40
        for line in text.splitlines():
            _assert_value_at_column(line, _WIDE_COL)

    def test_indents_share_marker_and_value_columns(self) -> None:
        text = _render(
            [
                Row("two", "[OK]", "a", 2),
                Row("four", "[OK]", "b", 4),
                Row("six", "[OK]", "c", 6),
            ]
        )
        lines = text.splitlines()
        assert len({line.index("[OK]") for line in lines}) == 1
        for line in lines:
            _assert_value_at_column(line, _DEFAULT_COL)
        assert _assert_section_aligned(text) == 3

    @pytest.mark.parametrize(
        ("label", "expected_col"),
        [("short", _DEFAULT_COL), ("b" * 30, _WIDE_COL)],
    )
    def test_hint_starts_at_value_column(self, label: str, expected_col: int) -> None:
        lines = _render([Row(label, "[OK]", "v"), hint_row("-> do x")]).splitlines()
        assert lines[1].lstrip() == "-> do x"
        assert len(lines[1]) - len(lines[1].lstrip()) == expected_col

    def test_empty_marker_and_label_less_rows_align(self) -> None:
        lines = _render(
            [
                Row("marked", "[OK]", "a"),
                Row("unmarked", "", "b"),
                Row("", "[WARN]", "c"),
            ]
        ).splitlines()
        for line in lines:
            _assert_value_at_column(line, _DEFAULT_COL)

    def test_wrap_row_wraps_against_value_column(self) -> None:
        value = ", ".join(f"tool_number_{i}" for i in range(20))
        lines = _render([Row("server", "[OK]", value, wrap=True)]).splitlines()
        assert len(lines) > 1
        assert all(len(line) <= 80 for line in lines)
        for line in lines:
            _assert_value_at_column(line, _DEFAULT_COL)
        for line in lines[1:]:
            assert not line[:_DEFAULT_COL].strip()
        joined = " ".join(line[_DEFAULT_COL:] for line in lines)
        assert joined == value

    def test_str_items_pass_through_and_do_not_widen(self) -> None:
        items = ["", "  [Python]", "  pip install x" + "y" * 40]
        lines = _render([*items, Row("label", "[OK]", "v")]).splitlines()
        assert lines[:3] == items
        _assert_value_at_column(lines[3], _DEFAULT_COL)


def test_assert_section_aligned_rejects_misaligned_values() -> None:
    text = "\n".join(
        [
            _format_row("a", "[OK]", "x", indent=2),
            _format_row("b" * 30, "[OK]", "y", indent=2),
        ]
    )
    with pytest.raises(AssertionError):
        _assert_section_aligned(text)


class TestSectionBuilder:
    """``SectionBuilder`` streams section by section."""

    def test_open_prints_header_rows_after_close(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        out = SectionBuilder()
        out.open("A")
        assert capsys.readouterr().out == _pad("A") + "\n"
        out.add(Row("a", "[OK]", "x"))
        assert capsys.readouterr().out == ""
        out.close()
        assert capsys.readouterr().out == _render([Row("a", "[OK]", "x")]) + "\n"

    def test_open_second_section_closes_first(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        out = SectionBuilder()
        out.open("A")
        out.add(Row("a", "[OK]", "x"))
        out.open("B")
        assert capsys.readouterr().out.splitlines() == [
            *_pad("A").splitlines(),
            _render([Row("a", "[OK]", "x")]),
            *_pad("B").splitlines(),
        ]

    def test_section_without_rows_uses_default_width(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        out = SectionBuilder()
        out.open("A")
        out.add("  [Python]", "  " + "z" * 50, hint_row("-> do x"))
        out.close()
        hint_line = capsys.readouterr().out.splitlines()[-1]
        assert hint_line.lstrip() == "-> do x"
        assert len(hint_line) - len(hint_line.lstrip()) == _DEFAULT_COL

    def test_add_without_open_section_prints_immediately(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        out = SectionBuilder()
        out.add(Row("label", "[OK]", "value", 4))
        assert capsys.readouterr().out == (
            _format_row("label", "[OK]", "value", indent=4) + "\n"
        )
        out.add("text")
        assert capsys.readouterr().out == "text\n"

    def test_close_twice_is_noop(self, capsys: pytest.CaptureFixture[str]) -> None:
        out = SectionBuilder()
        out.open("A")
        out.add(Row("a", "[OK]", "x"))
        out.close()
        capsys.readouterr()
        out.close()
        assert capsys.readouterr().out == ""

    def test_exception_flushes_open_section(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(RuntimeError):
            with SectionBuilder() as out:
                out.open("A")
                out.add(Row("a", "[OK]", "flushed"))
                raise RuntimeError("boom")
        assert "flushed" in capsys.readouterr().out

    def test_flush_failure_does_not_mask_exception(self) -> None:
        with patch(
            "mcp_coder_utils.verify_render.render_rows",
            side_effect=ValueError("render failed"),
        ) as mock_render:
            with pytest.raises(RuntimeError, match="boom"):
                with SectionBuilder() as out:
                    out.open("A")
                    out.add(Row("a", "[OK]", "x"))
                    raise RuntimeError("boom")
        mock_render.assert_called_once()

    def test_normal_exit_closes_open_section(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with SectionBuilder() as out:
            out.open("A")
            out.add(Row("a", "[OK]", "closed on exit"))
        assert "closed on exit" in capsys.readouterr().out

    def test_sections_get_independent_widths(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with SectionBuilder() as out:
            out.section("A", [Row("a", "[OK]", "x")])
            out.section("B", [Row("b" * 30, "[OK]", "y"), Row("c", "[WARN]", "z", 4)])
        output = capsys.readouterr().out
        lines = output.splitlines()
        a_idx = lines.index(_pad("A").strip("\n"))
        b_idx = lines.index(_pad("B").strip("\n"))
        _assert_value_at_column(lines[a_idx + 1], _DEFAULT_COL)
        _assert_value_at_column(lines[b_idx + 1], _WIDE_COL)
        _assert_value_at_column(lines[b_idx + 2], _WIDE_COL)
        _assert_sections_aligned(output)


def test_exact_output(capsys: pytest.CaptureFixture[str]) -> None:
    SectionBuilder().section(
        "DEMO",
        [
            Row("Label wider than default", "[OK]", "value"),
            Row("child", "[WARN]", "nested", 4),
            hint_row("-> fix it"),
            "  [Group]",
            Row(
                "tools",
                "[ERR]",
                "alpha, beta, gamma, delta, epsilon, zeta, eta, theta, iota",
                wrap=True,
            ),
        ],
    )
    assert capsys.readouterr().out == (
        "\n"
        "=== DEMO ==================================================================\n"
        "  Label wider than default [OK]   value\n"
        "    child                  [WARN] nested\n"
        "                                  -> fix it\n"
        "  [Group]\n"
        "  tools                    [ERR]  alpha, beta, gamma, delta, epsilon, zeta, eta,\n"
        "                                  theta, iota\n"
    )
