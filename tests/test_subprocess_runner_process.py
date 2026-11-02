import subprocess
import sys
import threading
import time
from unittest.mock import patch

from mcp_coder_utils.process_helpers import _run_heartbeat
from mcp_coder_utils.subprocess_runner import (
    CommandOptions,
    execute_subprocess,
    launch_process,
)


class TestLaunchProcess:
    """Mock-based tests for launch_process."""

    def test_launch_process_returns_pid(self) -> None:
        """Verify return type is int (PID)."""
        with patch("mcp_coder_utils.subprocess_runner.subprocess.Popen") as mock_popen:
            mock_popen.return_value.pid = 12345
            pid = launch_process(["echo", "hi"])
            assert isinstance(pid, int)
            assert pid == 12345

    def test_launch_process_uses_devnull(self) -> None:
        """Verify stdout/stderr use DEVNULL."""
        with patch("mcp_coder_utils.subprocess_runner.subprocess.Popen") as mock_popen:
            mock_popen.return_value.pid = 1
            launch_process(["echo", "hi"])
            call_kwargs = mock_popen.call_args[1]
            assert call_kwargs["stdout"] == subprocess.DEVNULL
            assert call_kwargs["stderr"] == subprocess.DEVNULL

    def test_launch_process_uses_prepare_env(self) -> None:
        """Mock prepare_env, verify called."""
        with (
            patch("mcp_coder_utils.subprocess_runner.subprocess.Popen") as mock_popen,
            patch(
                "mcp_coder_utils.subprocess_runner.prepare_env",
                return_value={"MERGED": "1"},
            ) as mock_prep,
        ):
            mock_popen.return_value.pid = 1
            launch_process(["echo", "hi"], env={"X": "1"}, env_remove=["Y"])
            mock_prep.assert_called_once_with(["echo", "hi"], {"X": "1"}, ["Y"])
            call_kwargs = mock_popen.call_args[1]
            assert call_kwargs["env"] == {"MERGED": "1"}

    def test_launch_process_passes_cwd_and_shell(self) -> None:
        """Verify args forwarded."""
        with patch("mcp_coder_utils.subprocess_runner.subprocess.Popen") as mock_popen:
            mock_popen.return_value.pid = 1
            # Popen is mocked; verifies shell=True is forwarded.
            launch_process(["echo", "hi"], cwd="/tmp", shell=True)  # noqa: S604
            call_kwargs = mock_popen.call_args[1]
            assert call_kwargs["cwd"] == "/tmp"
            assert call_kwargs["shell"] is True


class TestLogOutput:
    """Tests verifying log messages use format_command() output."""

    def test_debug_log_contains_full_command(self) -> None:
        """Verify DEBUG log at execution start contains the full formatted command."""
        command = [sys.executable, "-c", "print('hello')"]
        with patch("mcp_coder_utils.subprocess_runner.logger") as mock_logger:
            execute_subprocess(command)

        # Find the debug call with "Starting subprocess execution"
        debug_calls = [str(c) for c in mock_logger.debug.call_args_list]
        matching = [c for c in debug_calls if "Starting subprocess execution" in c]
        assert matching, (
            f"No DEBUG log with 'Starting subprocess execution' found in {debug_calls}"
        )
        # Should contain all command parts, not just first 3
        log_text = matching[0]
        assert "print" in log_text, f"Expected full command in log, got: {log_text}"

    def test_error_log_includes_command_and_cwd(self) -> None:
        """Verify ERROR log on failure includes structured error fields."""
        command = ["nonexistent_command_12345"]
        options = CommandOptions(cwd="/some/path")
        with patch("mcp_coder_utils.subprocess_runner.logger") as mock_logger:
            execute_subprocess(command, options)

        # Verify structured error log via extra dict
        assert mock_logger.error.called, "No ERROR log was emitted"
        call_args = mock_logger.error.call_args
        assert call_args[0][0] == "Subprocess execution failed"
        extra = call_args[1]["extra"]
        assert "error" in extra
        assert extra["error_type"] == "FileNotFoundError"
        assert extra["command_preview"] == ["nonexistent_command_12345"]

    def test_error_log_cwd_shows_current_when_none(self) -> None:
        """Verify ERROR log emits structured fields when cwd is None."""
        command = ["nonexistent_command_12345"]
        with patch("mcp_coder_utils.subprocess_runner.logger") as mock_logger:
            execute_subprocess(command)

        assert mock_logger.error.called, "No ERROR log was emitted"
        call_args = mock_logger.error.call_args
        assert call_args[0][0] == "Subprocess execution failed"
        extra = call_args[1]["extra"]
        assert extra["error_type"] == "FileNotFoundError"


class TestHeartbeat:
    """Tests for _run_heartbeat."""

    def test_heartbeat_stops_on_event(self) -> None:
        """Verify thread stops when event set."""
        stop = threading.Event()
        t = threading.Thread(
            target=_run_heartbeat,
            args=(stop, 1, "test", time.time()),
            daemon=True,
        )
        t.start()
        stop.set()
        t.join(timeout=3)
        assert not t.is_alive()

    def test_heartbeat_logs_at_interval(self) -> None:
        """Verify logger.info called with expected format."""
        stop = threading.Event()
        start = time.time()
        with patch("mcp_coder_utils.process_helpers.logger") as mock_logger:
            t = threading.Thread(
                target=_run_heartbeat,
                args=(stop, 0.1, "working", start),
                daemon=True,
            )
            t.start()
            time.sleep(0.35)
            stop.set()
            t.join(timeout=3)
            assert mock_logger.info.call_count >= 1
            # Check format string
            first_call_args = mock_logger.info.call_args_list[0][0]
            assert first_call_args[0] == "%s (elapsed: %dm %ds)"
            assert first_call_args[1] == "working"

    def test_heartbeat_interval_is_int(self) -> None:
        """Verify interval parameter is int type."""
        import inspect

        sig = inspect.signature(_run_heartbeat)
        param = sig.parameters["interval"]
        assert param.annotation is int
