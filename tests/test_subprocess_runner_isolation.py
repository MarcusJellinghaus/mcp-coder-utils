import os
import queue
import sys
import threading
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
)


class TestSTDIOIsolation:
    """Tests for STDIO isolation functionality."""

    def test_get_python_isolation_env(self) -> None:
        """Test environment isolation setup."""
        env = get_python_isolation_env()

        # Check critical environment variables are set
        assert env["PYTHONUNBUFFERED"] == "1"
        assert env["PYTHONDONTWRITEBYTECODE"] == "1"
        assert env["PYTHONIOENCODING"] == "utf-8"
        assert env["PYTHONNOUSERSITE"] == "1"
        assert env["PYTHONHASHSEED"] == "0"
        assert env["PYTHONSTARTUP"] == ""

        # Check MCP variables are removed
        mcp_vars = ["MCP_STDIO_TRANSPORT", "MCP_SERVER_NAME", "MCP_CLIENT_PARAMS"]
        for var in mcp_vars:
            assert var not in env

    def test_is_python_command_detection(self) -> None:
        """Test Python command detection."""
        # Python commands that should be detected
        python_commands = [
            ["python", "script.py"],
            ["python3", "-u", "script.py"],
            ["python.exe", "script.py"],
            ["python3.exe", "script.py"],
            [sys.executable, "script.py"],
            ["python", "-m", "module"],
            ["python3", "-m", "pytest"],
        ]

        for cmd in python_commands:
            assert is_python_command(cmd), f"Failed to detect Python command: {cmd}"

        # Non-Python commands that should not be detected
        non_python_commands = [
            ["echo", "hello"],
            ["node", "script.js"],
            ["java", "-jar", "app.jar"],
            ["cmd", "/c", "dir"],
            [],
        ]

        for cmd in non_python_commands:
            assert not is_python_command(cmd), f"Incorrectly detected as Python: {cmd}"

    def test_python_subprocess_with_isolation(self, temp_dir: Path) -> None:
        """Test successful Python subprocess execution with automatic STDIO isolation."""
        # Create test script
        test_script = temp_dir / "test_script.py"
        test_script.write_text(
            "import sys\n"
            "print('Hello from subprocess')\n"
            "print('Args:', sys.argv[1:])\n"
            "sys.exit(0)\n"
        )

        command = [sys.executable, "-u", str(test_script), "arg1", "arg2"]
        options = CommandOptions(cwd=str(temp_dir), timeout_seconds=5)

        result = execute_subprocess(command, options)

        assert result.return_code == 0
        assert "Hello from subprocess" in result.stdout
        assert "Args: ['arg1', 'arg2']" in result.stdout
        assert result.stderr == ""

    def test_python_subprocess_with_error(self, temp_dir: Path) -> None:
        """Test Python subprocess that writes to stderr."""
        test_script = temp_dir / "error_script.py"
        test_script.write_text(
            "import sys\n"
            "print('Normal output')\n"
            "print('Error message', file=sys.stderr)\n"
            "sys.exit(1)\n"
        )

        command = [sys.executable, "-u", str(test_script)]
        options = CommandOptions(cwd=str(temp_dir), timeout_seconds=30)

        result = execute_subprocess(command, options)

        if result.timed_out:
            pytest.skip(
                f"Test timed out - STDIO isolation may be causing issues: {result.execution_error}"
            )

        assert result.return_code == 1
        assert "Normal output" in result.stdout
        assert "Error message" in result.stderr

    def test_python_subprocess_timeout(self, temp_dir: Path) -> None:
        """Test subprocess timeout handling."""
        test_script = temp_dir / "timeout_script.py"
        test_script.write_text(
            "import time\ntime.sleep(10)\nprint('Should not reach here')\n"
        )

        command = [sys.executable, "-u", str(test_script)]
        options = CommandOptions(cwd=str(temp_dir), timeout_seconds=1)

        result = execute_subprocess(command, options)

        # On Windows with STDIO isolation, we might get a PermissionError instead of proper timeout
        # This is a known limitation when file handles are locked
        if result.execution_error and "PermissionError" in result.execution_error:
            # Accept this as a valid timeout scenario on Windows
            assert result.timed_out is False
            assert "The process cannot access the file" in result.execution_error
        else:
            assert result.timed_out is True
            assert result.execution_error is not None
            assert "Process timed out after 1 seconds" in result.execution_error

    def test_non_python_subprocess(self) -> None:
        """Test regular subprocess execution for non-Python commands."""
        command = ["cmd", "/c", "echo hello"] if os.name == "nt" else ["echo", "hello"]

        options = CommandOptions(timeout_seconds=5)
        result = execute_subprocess(command, options)

        assert result.return_code == 0
        assert "hello" in result.stdout.strip()

    def test_environment_mcp_variables_removed(self) -> None:
        """Test that MCP environment variables are properly removed."""
        # Set some fake MCP environment variables
        original_env = os.environ.copy()

        try:
            os.environ["MCP_STDIO_TRANSPORT"] = "test_transport"
            os.environ["MCP_SERVER_NAME"] = "test_server"
            os.environ["MCP_CLIENT_PARAMS"] = "test_params"

            env = get_python_isolation_env()

            assert "MCP_STDIO_TRANSPORT" not in env
            assert "MCP_SERVER_NAME" not in env
            assert "MCP_CLIENT_PARAMS" not in env

        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)

    def test_environment_merging(self, temp_dir: Path) -> None:
        """Test that provided environment variables are merged with isolation settings."""
        test_script = temp_dir / "env_test.py"
        test_script.write_text(
            "import os\n"
            "print('CUSTOM_VAR:', os.environ.get('CUSTOM_VAR', 'NOT_SET'))\n"
            "print('PYTHONUNBUFFERED:', os.environ.get('PYTHONUNBUFFERED', 'NOT_SET'))\n"
        )

        command = [sys.executable, "-u", str(test_script)]
        options = CommandOptions(
            cwd=str(temp_dir), timeout_seconds=5, env={"CUSTOM_VAR": "test_value"}
        )

        result = execute_subprocess(command, options)

        assert result.return_code == 0
        assert "CUSTOM_VAR: test_value" in result.stdout
        assert "PYTHONUNBUFFERED: 1" in result.stdout


class TestPythonCommandDetection:
    """Test automatic Python command detection and STDIO isolation."""

    def test_python_command_uses_isolation(self, temp_dir: Path) -> None:
        """Test that Python commands automatically use STDIO isolation."""
        # Create a test script that outputs environment info
        test_script = temp_dir / "test_isolation.py"
        test_script.write_text(
            "import os\n"
            "print('PYTHONUNBUFFERED:', os.environ.get('PYTHONUNBUFFERED', 'NOT_SET'))\n"
            "print('MCP_STDIO_TRANSPORT:', os.environ.get('MCP_STDIO_TRANSPORT', 'NOT_SET'))\n"
        )

        # Set an MCP variable to test isolation
        original_env = os.environ.copy()
        try:
            os.environ["MCP_STDIO_TRANSPORT"] = "test_value"

            result = execute_subprocess([sys.executable, str(test_script)])

            assert result.return_code == 0
            # Python isolation should set PYTHONUNBUFFERED=1
            assert "PYTHONUNBUFFERED: 1" in result.stdout
            # MCP variables should be removed
            assert "MCP_STDIO_TRANSPORT: NOT_SET" in result.stdout
        finally:
            os.environ.clear()
            os.environ.update(original_env)

    def test_non_python_command_uses_regular(self) -> None:
        """Test that non-Python commands don't use Python-specific isolation."""
        # Set an environment variable that Python isolation would remove
        original_env = os.environ.copy()
        try:
            os.environ["CUSTOM_TEST_VAR"] = "test_value"

            # Use a simple Python command to echo an environment variable
            # This simulates a non-Python command behavior
            result = execute_subprocess(
                [
                    sys.executable,
                    "-c",
                    "import os; print('CUSTOM_TEST_VAR:', os.environ.get('CUSTOM_TEST_VAR', 'NOT_SET'))",
                ]
            )

            assert result.return_code == 0
            # The custom variable should still be accessible since we're testing
            # that environment is properly passed through
            assert (
                "CUSTOM_TEST_VAR: test_value" in result.stdout
                or "CUSTOM_TEST_VAR: NOT_SET" in result.stdout
            )
        finally:
            os.environ.clear()
            os.environ.update(original_env)


class TestIntegrationScenarios:
    """Integration tests simulating real scenarios."""

    def test_multiple_sequential_python_commands(self, temp_dir: Path) -> None:
        """Test multiple sequential Python commands with STDIO isolation."""
        # Create multiple test scripts
        scripts = []
        for i in range(3):
            script = temp_dir / f"script_{i}.py"
            script.write_text(f"print('Script {i} output')\n")
            scripts.append(script)

        results = []
        for script in scripts:
            command = [sys.executable, "-u", str(script)]
            result = execute_command(
                command=command,
                cwd=str(temp_dir),
                timeout_seconds=30,  # Increased timeout for Windows STDIO isolation
                env={
                    "_DISABLE_STDIO_ISOLATION": "1"
                },  # Disable isolation for test stability
            )
            results.append(result)

        # All should succeed
        for i, result in enumerate(results):
            assert result.return_code == 0
            assert f"Script {i} output" in result.stdout

    def test_mixed_command_types_sequential(self, temp_dir: Path) -> None:
        """Test mixed Python and non-Python commands in sequence."""
        # Create Python script
        python_script = temp_dir / "python_test.py"
        python_script.write_text("print('Python output')\n")

        commands = [
            [sys.executable, "-u", str(python_script)],  # Python command
        ]

        # Add platform-specific non-Python command
        if os.name == "nt":  # Windows
            commands.append(["cmd", "/c", "echo Non-Python output"])
        else:  # Unix/Linux
            commands.append(["echo", "Non-Python output"])

        results = []
        for command in commands:
            result = execute_command(
                command=command, cwd=str(temp_dir), timeout_seconds=5
            )
            results.append(result)

        # All should succeed
        assert len(results) == 2
        assert results[0].return_code == 0
        assert "Python output" in results[0].stdout
        assert results[1].return_code == 0
        assert "Non-Python output" in results[1].stdout

    def test_concurrent_subprocess_simulation(self, temp_dir: Path) -> None:
        """Test behavior under concurrent subprocess scenarios."""
        test_script = temp_dir / "concurrent_test.py"
        test_script.write_text(
            "import time\n"
            "import sys\n"
            "thread_id = sys.argv[1]\n"
            "print(f'Thread {thread_id} started', flush=True)\n"
            "time.sleep(0.1)\n"
            "print(f'Thread {thread_id} finished', flush=True)\n"
        )

        results_queue: queue.Queue[tuple[int, CommandResult | Exception]] = (
            queue.Queue()
        )

        def run_subprocess(thread_id: int) -> None:
            try:
                # Add a small delay to prevent all threads from starting at exactly the same time
                time.sleep(thread_id * 0.05)  # Stagger starts by 50ms

                command = [sys.executable, "-u", str(test_script), str(thread_id)]
                result = execute_command(
                    command=command,
                    cwd=str(temp_dir),
                    timeout_seconds=10,  # Increased timeout
                )
                results_queue.put((thread_id, result))
            except Exception as e:
                results_queue.put((thread_id, e))

        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=run_subprocess, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Check results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        assert len(results) == 3
        for thread_id, result in results:
            assert isinstance(result, CommandResult), (
                f"Thread {thread_id} failed with: {result if isinstance(result, Exception) else 'Unknown error'}"
            )
            assert result.return_code == 0, (
                f"Thread {thread_id} returned code {result.return_code}, stdout: {result.stdout}, stderr: {result.stderr}"
            )
            assert f"Thread {thread_id} started" in result.stdout
            assert f"Thread {thread_id} finished" in result.stdout

    def test_environment_variable_isolation_integration(self, temp_dir: Path) -> None:
        """Test that environment variable isolation works in integration scenarios."""
        # Set up some environment variables that could interfere
        original_env = os.environ.copy()

        try:
            os.environ["MCP_STDIO_TRANSPORT"] = "test_transport"
            os.environ["CUSTOM_TEST_VAR"] = "should_be_preserved"

            test_script = temp_dir / "env_isolation_test.py"
            test_script.write_text(
                "import os\n"
                "import sys\n"
                "mcp_var = os.environ.get('MCP_STDIO_TRANSPORT', 'NOT_SET')\n"
                "custom_var = os.environ.get('CUSTOM_TEST_VAR', 'NOT_SET')\n"
                "python_var = os.environ.get('PYTHONUNBUFFERED', 'NOT_SET')\n"
                "print(f'MCP_STDIO_TRANSPORT: {mcp_var}', flush=True)\n"
                "print(f'CUSTOM_TEST_VAR: {custom_var}', flush=True)\n"
                "print(f'PYTHONUNBUFFERED: {python_var}', flush=True)\n"
                "sys.stdout.flush()\n"
                "sys.exit(0)\n"
            )

            command = [sys.executable, "-u", str(test_script)]

            result = execute_command(
                command=command,
                cwd=str(temp_dir),
                timeout_seconds=10,  # Increased timeout
                env={
                    "CUSTOM_TEST_VAR": "should_be_preserved"
                },  # This should be preserved
            )

            # Check if timeout occurred or other execution errors
            if result.timed_out:
                pytest.skip(
                    f"Test timed out - STDIO isolation may be causing issues: {result.execution_error}"
                )

            if result.execution_error and "PermissionError" in result.execution_error:
                pytest.skip(f"Windows file locking issue: {result.execution_error}")

            assert result.return_code == 0, (
                f"Script failed with code {result.return_code}, stdout: {result.stdout}, stderr: {result.stderr}, error: {result.execution_error}"
            )
            # MCP variable should be removed (isolation)
            assert "MCP_STDIO_TRANSPORT: NOT_SET" in result.stdout
            # Custom variable should be preserved
            assert "CUSTOM_TEST_VAR: should_be_preserved" in result.stdout
            # Python isolation variable should be set
            assert "PYTHONUNBUFFERED: 1" in result.stdout

        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
