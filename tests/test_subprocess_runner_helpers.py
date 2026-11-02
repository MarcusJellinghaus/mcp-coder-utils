import os
import sys
from unittest.mock import patch

import pytest

from mcp_coder_utils.subprocess_runner import (
    CommandOptions,
    CommandResult,
    check_tool_missing_error,
    format_command,
    prepare_env,
    truncate_stderr,
)


class TestFormatCommand:
    """Tests for format_command() utility."""

    @pytest.mark.parametrize(
        "command,expected_truncated",
        [
            # Exactly 200 chars - no truncation
            (["x" * 200], False),
            # 201 chars - truncated
            (["x" * 201], True),
            # Well under limit
            (["echo", "hello"], False),
        ],
    )
    def test_truncation_boundary(
        self, command: list[str], expected_truncated: bool
    ) -> None:
        """Test truncation at the 200-character boundary."""
        result = format_command(command)
        if expected_truncated:
            assert result.endswith("...")
            assert len(result) == 203  # 200 + len("...")
        else:
            assert not result.endswith("...")

    def test_single_element_command(self) -> None:
        """Test formatting a single-element command."""
        result = format_command(["echo"])
        assert result == "echo"

    def test_empty_command(self) -> None:
        """Test formatting an empty command list."""
        result = format_command([])
        assert result == ""

    def test_unix_uses_shlex_join(self) -> None:
        """Test that Unix platforms use shlex.join()."""
        with patch("mcp_coder_utils.subprocess_runner.os.name", "posix"):
            result = format_command(["echo", "hello world"])
            # shlex.join quotes arguments with spaces
            assert result == "echo 'hello world'"

    def test_windows_uses_list2cmdline(self) -> None:
        """Test that Windows platforms use subprocess.list2cmdline()."""
        with patch("mcp_coder_utils.subprocess_runner.os.name", "nt"):
            result = format_command(["echo", "hello world"])
            # list2cmdline quotes arguments with spaces
            assert result == 'echo "hello world"'


class TestCommandResult:
    """Tests for CommandResult dataclass."""

    def test_command_result_creation(self) -> None:
        """Test creating a CommandResult instance."""
        result = CommandResult(
            return_code=0,
            stdout="output",
            stderr="",
            timed_out=False,
            execution_error=None,
            command=["echo", "test"],
            runner_type="subprocess",
            execution_time_ms=100,
        )

        assert result.return_code == 0
        assert result.stdout == "output"
        assert result.stderr == ""
        assert not result.timed_out
        assert result.execution_error is None
        assert result.command == ["echo", "test"]
        assert result.runner_type == "subprocess"
        assert result.execution_time_ms == 100

    def test_command_result_defaults(self) -> None:
        """Test CommandResult with minimal required fields."""
        result = CommandResult(
            return_code=1,
            stdout="",
            stderr="error",
            timed_out=True,
        )

        assert result.return_code == 1
        assert result.stdout == ""
        assert result.stderr == "error"
        assert result.timed_out
        assert result.execution_error is None
        assert result.command is None
        assert result.runner_type is None
        assert result.execution_time_ms is None


class TestCommandOptions:
    """Tests for CommandOptions dataclass."""

    def test_command_options_defaults(self) -> None:
        """Test CommandOptions with default values."""
        options = CommandOptions()

        assert options.cwd is None
        assert options.timeout_seconds == 120
        assert options.env is None
        assert options.capture_output is True
        assert options.text is True
        assert not options.check
        assert not options.shell
        assert options.input_data is None

    def test_command_options_custom(self) -> None:
        """Test CommandOptions with custom values."""
        # shell=True is the field under test; nothing is executed.
        options = CommandOptions(  # noqa: S604
            cwd="/tmp",
            timeout_seconds=60,
            env={"TEST": "value"},
            capture_output=False,
            text=False,
            check=True,
            shell=True,
            input_data="test input",
        )

        assert options.cwd == "/tmp"
        assert options.timeout_seconds == 60
        assert options.env == {"TEST": "value"}
        assert not options.capture_output
        assert not options.text
        assert options.check
        assert options.shell
        assert options.input_data == "test input"


class TestPrepareEnv:
    """Unit tests for prepare_env()."""

    def test_python_command_uses_isolation_env(self) -> None:
        """Verify Python commands get isolation env."""
        env = prepare_env([sys.executable, "-c", "pass"], None, None)
        # Python isolation env sets these
        assert env["PYTHONUNBUFFERED"] == "1"
        assert env["PYTHONDONTWRITEBYTECODE"] == "1"

    def test_non_python_command_uses_utf8_env(self) -> None:
        """Verify non-Python commands get UTF-8 base env."""
        env = prepare_env(["echo", "hello"], None, None)
        assert env["PYTHONIOENCODING"] == "utf-8"
        assert env["PYTHONUTF8"] == "1"

    def test_caller_env_merged_on_top(self) -> None:
        """Verify env dict is merged, not replaced."""
        env = prepare_env(["echo", "hi"], {"MY_CUSTOM": "val"}, None)
        assert env["MY_CUSTOM"] == "val"
        # Should still have base env keys
        assert "PATH" in env or "Path" in env

    def test_env_inherits_parent_path(self) -> None:
        """Verify PATH from parent env is preserved (the bug fix)."""
        # "Path" is deliberate: Windows spells it that way; test is case-agnostic.
        original_path = os.environ.get("PATH", os.environ.get("Path", ""))  # noqa: SIM112
        env = prepare_env(["echo", "hi"], {"MY_VAR": "test"}, None)
        # PATH should be inherited from os.environ, not lost
        env_path = env.get("PATH", env.get("Path", ""))
        assert env_path == original_path

    def test_env_remove_keys(self) -> None:
        """Verify env_remove removes specified keys."""
        env = prepare_env(
            ["echo", "hi"],
            env={"KEEP": "yes", "REMOVE_ME": "gone"},
            env_remove=["REMOVE_ME"],
        )
        assert env["KEEP"] == "yes"
        assert "REMOVE_ME" not in env

    def test_claudecode_inherited_from_parent(self) -> None:
        """Verify CLAUDECODE is inherited from parent env (not stripped)."""
        original_env = os.environ.copy()
        try:
            os.environ["CLAUDECODE"] = "1"
            env = prepare_env(["echo", "hi"], None, None)
            assert env.get("CLAUDECODE") == "1"
        finally:
            os.environ.clear()
            os.environ.update(original_env)

    def test_env_remove_none_is_noop(self) -> None:
        """Verify None env_remove doesn't error."""
        env = prepare_env(["echo", "hi"], None, None)
        assert isinstance(env, dict)


class TestCommandOptionsEnvRemove:
    """Tests for env_remove field on CommandOptions."""

    def test_env_remove_defaults_none(self) -> None:
        """Verify default is None."""
        opts = CommandOptions()
        assert opts.env_remove is None

    def test_env_remove_with_values(self) -> None:
        """Verify setting a list works."""
        opts = CommandOptions(env_remove=["FOO", "BAR"])
        assert opts.env_remove == ["FOO", "BAR"]


class TestMergedUtilities:
    """Parametrized tests for check_tool_missing_error and truncate_stderr."""

    @pytest.mark.parametrize("tool", ["pytest", "pylint", "mypy"])
    def test_check_tool_missing_found(self, tool: str) -> None:
        """Parametrize with pytest/pylint/mypy."""
        stderr = f"No module named {tool}"
        result = check_tool_missing_error(stderr, tool, "/usr/bin/python")
        assert result is not None
        assert tool in result

    def test_check_tool_missing_not_found(self) -> None:
        """Returns None when no match."""
        result = check_tool_missing_error(
            "some other error", "pytest", "/usr/bin/python"
        )
        assert result is None

    def test_truncate_stderr_short(self) -> None:
        """No truncation needed."""
        short = "short error"
        assert truncate_stderr(short) == short

    def test_truncate_stderr_long(self) -> None:
        """Truncation with '...'."""
        long_str = "x" * 600
        result = truncate_stderr(long_str)
        assert result.endswith("...")
        assert len(result) == 503  # 500 + len("...")

    def test_truncate_stderr_exact(self) -> None:
        """Exact boundary."""
        exact = "x" * 500
        assert truncate_stderr(exact) == exact


@pytest.fixture
def sample_command() -> list[str]:
    """Sample command for testing."""
    return [sys.executable, "-c", "print('test')"]


@pytest.fixture
def sample_command_options() -> CommandOptions:
    """Sample command options for testing."""
    return CommandOptions(
        cwd=None,
        timeout_seconds=30,
        env={"TEST": "value"},
    )


@pytest.fixture
def sample_command_result() -> CommandResult:
    """Sample command result for testing."""
    return CommandResult(
        return_code=0,
        stdout="test output",
        stderr="",
        timed_out=False,
        command=["echo", "test"],
        runner_type="subprocess",
        execution_time_ms=100,
    )


def test_sample_command_with_fixture(sample_command: list[str]) -> None:
    """Test sample command fixture."""
    assert len(sample_command) == 3
    assert sample_command[0] == sys.executable


def test_command_options_with_fixture(sample_command_options: CommandOptions) -> None:
    """Test command options fixture."""
    assert sample_command_options.timeout_seconds == 30
    assert sample_command_options.env is not None
    assert sample_command_options.env["TEST"] == "value"


def test_command_result_creation_with_fixture(
    sample_command_result: CommandResult,
) -> None:
    """Test command result creation using fixture."""
    assert sample_command_result.return_code == 0
    assert sample_command_result.stdout == "test output"
    assert sample_command_result.runner_type == "subprocess"
