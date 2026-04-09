"""Integration tests for subprocess_runner — real subprocess execution (no mocks).

These tests complement the mock-based unit tests in test_subprocess_runner.py
by exercising real Python subprocesses via sys.executable.
"""

import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

from mcp_coder_utils.subprocess_runner import (
    CommandOptions,
    CommandResult,
    execute_command,
    execute_subprocess,
    get_python_isolation_env,
    is_python_command,
    prepare_env,
)


class TestRealSubprocessExecution:
    """Tests that run real subprocesses — no mocking."""

    def test_simple_python_print(self) -> None:
        """Run a real Python subprocess that prints to stdout."""
        result = execute_subprocess([sys.executable, "-c", "print('hello world')"])
        assert result.return_code == 0
        assert "hello world" in result.stdout
        assert not result.timed_out

    def test_stderr_output(self) -> None:
        """Run a subprocess that writes to stderr."""
        result = execute_subprocess(
            [sys.executable, "-c", "import sys; print('err', file=sys.stderr)"]
        )
        assert result.return_code == 0
        assert "err" in result.stderr

    def test_nonzero_exit_code(self) -> None:
        """Run a subprocess that exits with a non-zero code."""
        result = execute_subprocess([sys.executable, "-c", "import sys; sys.exit(42)"])
        assert result.return_code == 42
        assert not result.timed_out

    def test_multiline_output(self) -> None:
        """Capture multi-line stdout from a real subprocess."""
        script = "for i in range(5): print(f'line {i}')"
        result = execute_subprocess([sys.executable, "-c", script])
        assert result.return_code == 0
        for i in range(5):
            assert f"line {i}" in result.stdout

    def test_large_stdout(self) -> None:
        """Ensure large stdout is captured without truncation."""
        script = "print('x' * 10_000)"
        result = execute_subprocess([sys.executable, "-c", script])
        assert result.return_code == 0
        assert len(result.stdout.strip()) == 10_000

    def test_execution_time_tracked(self) -> None:
        """Verify execution_time_ms is populated."""
        result = execute_subprocess(
            [sys.executable, "-c", "import time; time.sleep(0.1)"]
        )
        assert result.execution_time_ms is not None
        assert result.execution_time_ms >= 50  # allow some slack

    def test_command_field_preserved(self) -> None:
        """Verify the command list is stored in the result."""
        cmd = [sys.executable, "-c", "pass"]
        result = execute_subprocess(cmd)
        assert result.command == cmd

    def test_runner_type_is_subprocess(self) -> None:
        """Verify runner_type is always 'subprocess'."""
        result = execute_subprocess([sys.executable, "-c", "pass"])
        assert result.runner_type == "subprocess"


class TestRealEnvironmentIsolation:
    """Verify environment isolation with real subprocesses."""

    def test_python_isolation_env_applied(self) -> None:
        """MCP variables must be absent in the child process."""
        original_env = os.environ.copy()
        try:
            os.environ["MCP_STDIO_TRANSPORT"] = "should_be_removed"
            result = execute_subprocess(
                [
                    sys.executable,
                    "-c",
                    "import os; print(os.environ.get('MCP_STDIO_TRANSPORT', 'ABSENT'))",
                ]
            )
            assert result.return_code == 0
            assert "ABSENT" in result.stdout
        finally:
            os.environ.clear()
            os.environ.update(original_env)

    def test_custom_env_vars_merged(self) -> None:
        """Caller-supplied env vars appear in the child process."""
        options = CommandOptions(env={"MY_CUSTOM_VAR": "custom_value_123"})
        result = execute_subprocess(
            [
                sys.executable,
                "-c",
                "import os; print(os.environ.get('MY_CUSTOM_VAR', 'MISSING'))",
            ],
            options,
        )
        assert result.return_code == 0
        assert "custom_value_123" in result.stdout

    def test_pythonunbuffered_set_for_python_commands(self) -> None:
        """PYTHONUNBUFFERED=1 should be set for Python commands."""
        result = execute_subprocess(
            [
                sys.executable,
                "-c",
                "import os; print(os.environ.get('PYTHONUNBUFFERED', 'NOT_SET'))",
            ]
        )
        assert result.return_code == 0
        assert "1" in result.stdout


class TestRealCommandDetection:
    """Verify is_python_command works with sys.executable paths."""

    def test_sys_executable_detected(self) -> None:
        """sys.executable must be detected as a Python command."""
        assert is_python_command([sys.executable, "-c", "pass"])

    def test_plain_python_detected(self) -> None:
        """'python' must be detected as a Python command."""
        assert is_python_command(["python", "-m", "pip"])

    def test_non_python_not_detected(self) -> None:
        """Non-Python executables must not be detected."""
        assert not is_python_command(["git", "status"])
        assert not is_python_command(["node", "app.js"])

    def test_empty_command_not_detected(self) -> None:
        """Empty command list returns False."""
        assert not is_python_command([])


class TestRealPrepareEnv:
    """Verify prepare_env builds correct environments with real os.environ."""

    def test_python_command_gets_isolation(self) -> None:
        """Python commands get isolation env with PYTHONUNBUFFERED etc."""
        env = prepare_env([sys.executable, "-c", "pass"], None, None)
        assert env["PYTHONUNBUFFERED"] == "1"
        assert env["PYTHONDONTWRITEBYTECODE"] == "1"

    def test_non_python_command_gets_utf8(self) -> None:
        """Non-Python commands get UTF-8 env."""
        env = prepare_env(["git", "status"], None, None)
        assert env["PYTHONIOENCODING"] == "utf-8"
        assert env["PYTHONUTF8"] == "1"

    def test_path_inherited(self) -> None:
        """PATH from parent process must be inherited."""
        env = prepare_env(["echo", "hi"], None, None)
        env_path = env.get("PATH", env.get("Path", ""))
        assert env_path  # should not be empty


class TestRealGetPythonIsolationEnv:
    """Verify get_python_isolation_env with the real os.environ."""

    def test_mcp_vars_stripped(self) -> None:
        """MCP-specific variables must be removed."""
        original_env = os.environ.copy()
        try:
            os.environ["MCP_STDIO_TRANSPORT"] = "value"
            os.environ["MCP_SERVER_NAME"] = "value"
            os.environ["MCP_CLIENT_PARAMS"] = "value"
            env = get_python_isolation_env()
            assert "MCP_STDIO_TRANSPORT" not in env
            assert "MCP_SERVER_NAME" not in env
            assert "MCP_CLIENT_PARAMS" not in env
        finally:
            os.environ.clear()
            os.environ.update(original_env)

    def test_isolation_keys_present(self) -> None:
        """All Python isolation keys must be set."""
        env = get_python_isolation_env()
        assert env["PYTHONUNBUFFERED"] == "1"
        assert env["PYTHONDONTWRITEBYTECODE"] == "1"
        assert env["PYTHONIOENCODING"] == "utf-8"
        assert env["PYTHONNOUSERSITE"] == "1"
        assert env["PYTHONHASHSEED"] == "0"
        assert env["PYTHONSTARTUP"] == ""


class TestRealCwdHandling:
    """Verify cwd option works with real subprocesses."""

    def test_cwd_respected(self, tmp_path: Path) -> None:
        """Subprocess runs in the specified working directory."""
        options = CommandOptions(cwd=str(tmp_path))
        result = execute_subprocess(
            [sys.executable, "-c", "import os; print(os.getcwd())"],
            options,
        )
        assert result.return_code == 0
        # Normalise paths for comparison (Windows can have different casing)
        assert os.path.normcase(result.stdout.strip()) == os.path.normcase(
            str(tmp_path)
        )


class TestRealTimeoutHandling:
    """Verify timeout behaviour with real subprocesses."""

    def test_timeout_kills_subprocess(self) -> None:
        """A subprocess exceeding the timeout must be killed."""
        options = CommandOptions(timeout_seconds=1)
        result = execute_subprocess(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            options,
        )
        # On Windows with STDIO isolation, PermissionError is acceptable
        if result.execution_error and "PermissionError" in result.execution_error:
            assert result.return_code == 1
        else:
            assert result.timed_out
            assert result.return_code == 1

    def test_fast_command_does_not_timeout(self) -> None:
        """A fast command must complete within a generous timeout."""
        options = CommandOptions(timeout_seconds=30)
        result = execute_subprocess(
            [sys.executable, "-c", "print('fast')"],
            options,
        )
        assert result.return_code == 0
        assert not result.timed_out
        assert "fast" in result.stdout


class TestRealInputData:
    """Verify stdin input_data with real subprocesses."""

    def test_stdin_piped_to_subprocess(self) -> None:
        """Data sent via input_data should appear on subprocess stdin."""
        options = CommandOptions(input_data="hello from stdin\n")
        result = execute_subprocess(
            [sys.executable, "-c", "import sys; print(sys.stdin.read().strip())"],
            options,
        )
        assert result.return_code == 0
        assert "hello from stdin" in result.stdout


class TestEmptyCommand:
    """Verify empty-command validation."""

    def test_empty_command_list(self) -> None:
        """execute_subprocess([]) must raise ValueError."""
        with pytest.raises(ValueError, match="Command cannot be empty"):
            execute_subprocess([])

    def test_none_command(self) -> None:
        """execute_subprocess(None) must raise TypeError."""
        with pytest.raises(TypeError):
            execute_subprocess(None)  # type: ignore[arg-type]


class TestRealExecuteCommand:
    """Verify the execute_command convenience wrapper with real subprocesses."""

    def test_basic_execution(self) -> None:
        """execute_command wraps execute_subprocess correctly."""
        result = execute_command([sys.executable, "-c", "print('via execute_command')"])
        assert result.return_code == 0
        assert "via execute_command" in result.stdout

    def test_with_cwd(self, tmp_path: Path) -> None:
        """execute_command respects the cwd parameter."""
        result = execute_command(
            [sys.executable, "-c", "import os; print(os.getcwd())"],
            cwd=str(tmp_path),
        )
        assert result.return_code == 0
        assert os.path.normcase(result.stdout.strip()) == os.path.normcase(
            str(tmp_path)
        )
