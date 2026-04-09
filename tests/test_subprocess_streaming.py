"""Tests for subprocess_streaming module.

These are real-process tests (not mock-based). They launch sys.executable
and use wall-clock timeouts, so they may have timing sensitivity on slow
CI runners.
"""

import sys

import pytest

from mcp_coder_utils.subprocess_streaming import StreamResult, stream_subprocess


class TestStreamSubprocessValidation:
    """Tests for input validation in stream_subprocess."""

    def test_stream_subprocess_none_command_raises_type_error(self) -> None:
        """Passing None as command should raise TypeError."""
        with pytest.raises(TypeError, match="Command cannot be None"):
            stream_subprocess(None)  # type: ignore[arg-type]

    def test_stream_subprocess_empty_command_raises_value_error(self) -> None:
        """Passing an empty list as command should raise ValueError."""
        with pytest.raises(ValueError, match="Command cannot be empty"):
            stream_subprocess([])


class TestStreamInactivityWatchdog:
    """Tests for the inactivity watchdog in stream_subprocess."""

    def test_stream_inactivity_timeout_kills_process(self) -> None:
        """A process that hangs (no output) should be killed by the watchdog."""
        # Script prints one line then sleeps forever
        script = "import sys, time; print('start', flush=True); time.sleep(60)"
        result = stream_subprocess(
            [sys.executable, "-c", script],
            inactivity_timeout_seconds=2,
        )

        lines = list(result)
        assert "start" in lines

        cmd_result = result.result
        assert cmd_result.timed_out is True
        assert cmd_result.return_code != 0

    def test_stream_active_process_no_timeout(self) -> None:
        """A process that keeps producing output should not be killed."""
        # Script prints lines with small delays — well within the watchdog
        script = (
            "import sys, time\n"
            "for i in range(5):\n"
            "    print(f'line {i}', flush=True)\n"
            "    time.sleep(0.3)\n"
        )
        result = stream_subprocess(
            [sys.executable, "-c", script],
            inactivity_timeout_seconds=5,
        )

        lines = list(result)
        assert len(lines) == 5

        cmd_result = result.result
        assert cmd_result.timed_out is False
        assert cmd_result.return_code == 0

    def test_stream_subprocess_basic(self) -> None:
        """Basic streaming without a watchdog should yield all lines."""
        script = (
            "import sys\n"
            "for i in range(3):\n"
            "    print(f'hello {i}', flush=True)\n"
        )
        result = stream_subprocess([sys.executable, "-c", script])

        assert isinstance(result, StreamResult)

        lines = list(result)
        assert lines == ["hello 0", "hello 1", "hello 2"]

        cmd_result = result.result
        assert cmd_result.return_code == 0
        assert cmd_result.timed_out is False
        assert cmd_result.runner_type == "streaming"
