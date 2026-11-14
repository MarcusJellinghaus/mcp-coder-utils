import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder_utils.subprocess_runner import (
    CommandOptions,
    execute_command,
    execute_subprocess,
)


class TestExecuteSubprocess:
    """Tests for execute_subprocess function."""

    def test_execute_simple_command(self) -> None:
        """Test executing a simple command."""
        result = execute_subprocess([sys.executable, "-c", "print('hello')"])

        assert result.return_code == 0
        assert "hello" in result.stdout
        assert result.stderr == ""
        assert not result.timed_out
        assert result.execution_error is None
        assert result.command == [sys.executable, "-c", "print('hello')"]
        assert result.runner_type == "subprocess"
        assert result.execution_time_ms is not None
        assert result.execution_time_ms > 0

    def test_execute_command_with_options(self, temp_dir: Path) -> None:
        """Test executing a command with custom options."""
        options = CommandOptions(
            cwd=str(temp_dir),
            timeout_seconds=30,
            env={"TEST_VAR": "test_value"},
        )

        result = execute_subprocess(
            [
                sys.executable,
                "-c",
                "import os; print(os.environ.get('TEST_VAR', 'NOT_FOUND'))",
            ],
            options,
        )

        assert result.return_code == 0
        assert "test_value" in result.stdout
        assert result.command is not None
        assert result.runner_type == "subprocess"

    def test_execute_command_with_error(self) -> None:
        """Test executing a command that returns an error."""
        result = execute_subprocess([sys.executable, "-c", "import sys; sys.exit(1)"])

        assert result.return_code == 1
        assert not result.timed_out
        assert result.execution_error is None
        assert result.runner_type == "subprocess"

    def test_execute_command_not_found(self) -> None:
        """Test executing a command that doesn't exist."""
        result = execute_subprocess(["nonexistent_command_12345"])

        assert result.return_code == 1
        assert result.timed_out is False
        assert result.execution_error is not None
        # Platform-specific error messages
        assert (
            "Executable not found" in result.execution_error
            or "FileNotFoundError" in result.execution_error
            or "No such file or directory" in result.execution_error
        )
        assert result.runner_type == "subprocess"

    def test_execute_command_timeout(self) -> None:
        """Test executing a command that times out."""
        options = CommandOptions(timeout_seconds=1)

        result = execute_subprocess(
            [sys.executable, "-c", "import time; time.sleep(5)"], options
        )

        assert result.return_code == 1
        assert result.timed_out is True
        assert result.execution_error is not None
        assert "Process timed out after 1 seconds" in result.execution_error
        assert result.runner_type == "subprocess"

    def test_execute_command_permission_error(self) -> None:
        """Test handling permission errors."""
        with patch("subprocess.Popen") as mock_popen:
            mock_popen.side_effect = PermissionError("Access denied")

            result = execute_subprocess(["test_command"])

            assert result.return_code == 1
            assert not result.timed_out
            assert result.execution_error is not None
            assert "PermissionError" in result.execution_error
            assert result.runner_type == "subprocess"

    def test_execute_command_unexpected_error(self) -> None:
        """Test handling OS-level errors."""
        with patch("subprocess.Popen") as mock_popen:
            mock_popen.side_effect = OSError("Unexpected OS error")

            result = execute_subprocess(["test_command"])

            assert result.return_code == 1
            assert not result.timed_out
            assert result.execution_error is not None
            assert "Unexpected OS error" in result.execution_error
            assert result.runner_type == "subprocess"

    def test_execute_command_with_check_option(self) -> None:
        """Test execute with check=True raises exception on failure."""
        options = CommandOptions(check=True)

        with pytest.raises(subprocess.CalledProcessError):
            execute_subprocess(
                [sys.executable, "-c", "import sys; sys.exit(1)"], options
            )

    def test_execute_command_with_input_data(self) -> None:
        """Test executing a command with input data."""
        options = CommandOptions(input_data="test input\n")

        result = execute_subprocess(
            [sys.executable, "-c", "import sys; print(sys.stdin.read().strip())"],
            options,
        )

        assert result.return_code == 0
        assert "test input" in result.stdout

    def test_none_command_error(self) -> None:
        """Test that None command raises TypeError."""
        with pytest.raises(TypeError):
            execute_subprocess(None)  # type: ignore[arg-type]


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_execute_command(self) -> None:
        """Test the execute_command convenience function."""
        result = execute_command([sys.executable, "-c", "print('test')"])

        assert result.return_code == 0
        assert "test" in result.stdout
        assert result.runner_type == "subprocess"

    def test_execute_command_with_params(self, temp_dir: Path) -> None:
        """Test execute_command with custom parameters."""
        result = execute_command(
            [sys.executable, "-c", "import os; print(os.getcwd())"],
            cwd=str(temp_dir),
            timeout_seconds=30,
            env={"TEST": "value"},
        )

        assert result.return_code == 0
        assert str(temp_dir) in result.stdout
        assert result.runner_type == "subprocess"


class TestErrorHandling:
    """Tests for error handling scenarios."""

    def test_empty_command_list(self) -> None:
        """Test handling of empty command list."""
        with pytest.raises(ValueError, match="Command cannot be empty"):
            execute_subprocess([])

    def test_execution_time_tracking(self) -> None:
        """Test that execution time is tracked."""
        result = execute_subprocess(
            [sys.executable, "-c", "import time; time.sleep(0.1)"]
        )

        assert result.execution_time_ms is not None
        assert result.execution_time_ms >= 100  # At least 100ms due to sleep

    def test_execution_with_env_vars(self) -> None:
        """Test execution with environment variables."""
        options = CommandOptions(env={"CUSTOM_VAR": "custom_value"})

        result = execute_subprocess(
            [
                sys.executable,
                "-c",
                "import os; print(os.environ.get('CUSTOM_VAR', 'NOT_SET'))",
            ],
            options,
        )

        assert result.return_code == 0
        assert "custom_value" in result.stdout
