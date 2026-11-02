import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder_utils.log_utils import log_function_call


class TestLogFunctionCall:
    """Tests for the log_function_call decorator."""

    def test_log_function_call_basic(self) -> None:
        """Test the basic functionality of the decorator."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Define a test function
            @log_function_call
            def test_func(a: int, b: int) -> int:
                return a + b

            # Execute
            result = test_func(1, 2)

            # Verify
            assert result == 3
            assert mock_logger.debug.call_count == 2  # Called for start and end logging

    def test_log_function_call_with_path_param(self) -> None:
        """Test that Path objects are properly serialized."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Define a test function with a Path parameter
            @log_function_call
            def path_func(file_path: Path) -> str:
                return str(file_path)

            # Execute
            test_path = Path("/test/path")
            result = path_func(test_path)

            # Verify
            assert result == str(test_path)
            assert mock_logger.debug.call_count == 2

            # Check that mock was called with correct parameters
            # After the lazy formatting change, debug is now called with format string and parameters
            # First call should be: debug("%s(%s)", func_name, params)
            first_call = mock_logger.debug.call_args_list[0]
            assert first_call[0][0] == "%s(%s)"
            assert first_call[0][1] == "path_func"
            # The second argument should be a JSON string of parameters
            params_json = first_call[0][2]

            params = json.loads(params_json)
            assert "file_path" in params
            assert (
                str(test_path) in params["file_path"]
                or str(test_path).replace("/", "\\") in params["file_path"]
            )

            # Second call should be the completion log
            second_call = mock_logger.debug.call_args_list[1]
            assert second_call[0][0] == "%s -> %s (%sms)"
            assert second_call[0][1] == "path_func"
            # Verify result is the string representation of the path
            # The result is the second parameter (after func_name)
            result_arg = second_call[0][2]
            # On Windows, the path might be represented differently
            assert str(test_path).replace("/", "\\") in str(result_arg) or str(
                test_path
            ) in str(result_arg)

    def test_log_function_call_method_skips_self(self) -> None:
        """Test that self is correctly skipped when decorating a method."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            class MyService:
                @log_function_call
                def process(self, name: str, count: int) -> str:
                    return f"{name}:{count}"

            svc = MyService()
            result = svc.process("test", 5)

            assert result == "test:5"
            assert mock_logger.debug.call_count == 2

            first_call = mock_logger.debug.call_args_list[0]
            params_json = first_call[0][2]
            params = json.loads(params_json)

            # self should be skipped, only name and count logged
            assert "self" not in params
            assert params["name"] == "test"
            assert params["count"] == 5

    def test_log_function_call_with_large_result(self) -> None:
        """Test that large results are properly truncated in logs."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Define a test function that returns a large list
            @log_function_call
            def large_result_func() -> list[int]:
                return list(range(1000))

            # Execute
            result = large_result_func()

            # Verify
            assert len(result) == 1000
            assert mock_logger.debug.call_count == 2

            # Get the call args for the second debug call (completion log)
            second_call = mock_logger.debug.call_args_list[1]
            # The format is now: debug("%s -> %s (%sms)", func_name, result, elapsed)
            assert second_call[0][0] == "%s -> %s (%sms)"
            assert second_call[0][1] == "large_result_func"
            # The result (second argument after format string and func_name) should be the truncated message
            result_arg = second_call[0][2]
            assert "<Large result of type list" in result_arg

    def test_log_function_call_with_structured_logging(self) -> None:
        """Test that structured logging is used when available."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            with patch("mcp_coder_utils.log_utils.structlog") as mock_structlog:
                # Setup mock for structlog and for checking if FileHandler is present
                mock_structlogger = mock_structlog.get_logger.return_value

                # Mock to simulate FileHandler being present
                with patch("mcp_coder_utils.log_utils.any", return_value=True):
                    # Define a test function
                    @log_function_call
                    def test_func(a: int, b: int) -> int:
                        return a + b

                    # Execute
                    result = test_func(1, 2)

                    # Verify
                    assert result == 3
                    # Both standard and structured logging should be used
                    assert mock_logger.debug.call_count == 2
                    assert mock_structlogger.debug.call_count == 2


class TestLogFunctionCallLoggerName:
    """Tests for log_function_call decorator using correct logger name.

    These tests verify that the decorator uses the decorated function's module
    name for logging, not the log_utils module name.
    """

    def test_log_function_call_uses_correct_logger_name(self) -> None:
        """Verify logger name is the decorated function's module, not log_utils."""
        captured_logger_names: list[str] = []

        # Create a mock that captures the logger name
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Define function in a specific module context
            @log_function_call
            def my_func() -> int:
                return 42

            # Trigger the logging
            my_func()

            # Capture all logger names that were requested
            captured_logger_names = [
                call[0][0] for call in mock_get_logger.call_args_list if call[0]
            ]

            # Verify getLogger was called with the function's module
            # The function is defined in this test module
            assert any(
                __name__ in name or "test_log_utils" in name
                for name in captured_logger_names
            ), f"Expected test module name in logger names: {captured_logger_names}"

    def test_log_function_call_logger_not_log_utils_for_func_logs(self) -> None:
        """Verify function logs don't use mcp_coder_utils.log_utils as logger name."""
        func_logger_calls: list[str] = []

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            # Root logger mock (returned when called without arguments)
            root_logger_mock = MagicMock()
            root_logger_mock.handlers = []  # No file handlers

            def get_logger_side_effect(name: str = "") -> MagicMock:
                if not name:  # Root logger
                    return root_logger_mock
                return mock_logger

            mock_get_logger.side_effect = get_logger_side_effect

            @log_function_call
            def test_func() -> str:
                return "result"

            test_func()

            # Get all logger name calls (filter out empty string for root logger)
            func_logger_calls = [
                call[0][0]
                for call in mock_get_logger.call_args_list
                if call[0] and call[0][0]
            ]

            # The decorator should get a logger for the decorated function's module
            # No call should be for mcp_coder_utils.log_utils (the decorator module itself)
            log_utils_module_calls = [
                name
                for name in func_logger_calls
                if name == "mcp_coder_utils.log_utils"
            ]
            assert len(log_utils_module_calls) == 0, (
                f"Logger should not be from mcp_coder_utils.log_utils: {func_logger_calls}"
            )

    def test_log_function_call_structlog_uses_correct_module(self) -> None:
        """Verify structlog logger also uses decorated function's module."""
        with patch("mcp_coder_utils.log_utils.structlog") as mock_structlog:
            mock_structlogger = MagicMock()
            mock_structlog.get_logger.return_value = mock_structlogger

            # Simulate file handler present (triggers structlog path)
            mock_file_handler = MagicMock(spec=logging.FileHandler)
            with patch.object(logging.getLogger(), "handlers", [mock_file_handler]):

                @log_function_call
                def logged_func() -> int:
                    return 1

                logged_func()

                # Verify structlog.get_logger was called
                assert mock_structlog.get_logger.called, (
                    "structlog.get_logger should be called"
                )

                # Verify it was called with the function's module (this test module)
                call_args = mock_structlog.get_logger.call_args_list
                module_names = [call[0][0] for call in call_args if call[0]]

                # Should be called with test module name, not log_utils
                assert any(
                    __name__ in name or "test_log_utils" in name
                    for name in module_names
                ), f"Expected test module name in structlog calls: {module_names}"

    def test_log_function_call_debug_uses_func_logger(self) -> None:
        """Verify debug calls use the function-specific logger."""
        with patch("logging.getLogger") as mock_get_logger:
            # Create separate loggers for different modules
            func_logger = MagicMock()
            module_logger = MagicMock()
            # Root logger mock (returned when called without arguments)
            root_logger_mock = MagicMock()
            root_logger_mock.handlers = []  # No file handlers

            def get_logger_side_effect(name: str = "") -> MagicMock:
                if not name:  # Root logger
                    return root_logger_mock
                if "test_log_utils" in name or name == __name__:
                    return func_logger
                return module_logger

            mock_get_logger.side_effect = get_logger_side_effect

            @log_function_call
            def my_test_func() -> int:
                return 123

            my_test_func()

            # Verify the function-specific logger was used for debug calls
            assert func_logger.debug.called, "Function logger should have debug calls"

    def test_log_function_call_error_uses_func_logger(self) -> None:
        """Verify error logs use the function-specific logger."""
        with patch("logging.getLogger") as mock_get_logger:
            func_logger = MagicMock()
            # Root logger mock (returned when called without arguments)
            root_logger_mock = MagicMock()
            root_logger_mock.handlers = []  # No file handlers

            def get_logger_side_effect(name: str = "") -> MagicMock:
                if not name:  # Root logger
                    return root_logger_mock
                if "test_log_utils" in name or name == __name__:
                    return func_logger
                return MagicMock()

            mock_get_logger.side_effect = get_logger_side_effect

            @log_function_call
            def failing_func() -> None:
                raise ValueError("Test error")

            with pytest.raises(ValueError):
                failing_func()

            # Verify the function-specific logger was used for error calls
            assert func_logger.error.called, "Function logger should have error calls"


class TestLogFunctionCallWithSensitiveFields:
    """Tests for log_function_call decorator with sensitive_fields parameter."""

    def test_log_function_call_without_sensitive_fields(self) -> None:
        """Test that decorator works without sensitive_fields (backward compatible)."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            @log_function_call
            def simple_func(x: int) -> int:
                return x * 2

            result = simple_func(5)
            assert result == 10
            assert mock_logger.debug.call_count == 2

    def test_log_function_call_with_parentheses_no_args(self) -> None:
        """Test that decorator works with empty parentheses."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            @log_function_call()
            def simple_func(x: int) -> int:
                return x * 2

            result: int = simple_func(5)
            assert result == 10
            assert mock_logger.debug.call_count == 2

    def test_log_function_call_redacts_sensitive_params(self) -> None:
        """Test that sensitive parameter values are redacted in logs."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            @log_function_call(sensitive_fields=["token", "password"])
            def auth_func(token: str, username: str) -> bool:  # noqa: F841
                _ = token, username  # consumed by decorator via inspect
                return True

            auth_func(token="secret123", username="user")

            # Verify log contains "***" for token, but "user" for username
            first_call = mock_logger.debug.call_args_list[0]
            log_params = first_call[0][2]  # JSON string of parameters

            assert "***" in log_params
            assert "secret123" not in log_params
            assert "user" in log_params

    def test_log_function_call_redacts_sensitive_return_value(self) -> None:
        """Test that sensitive values in return dict are redacted in logs."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            @log_function_call(sensitive_fields=["token"])
            def get_config() -> dict[str, str]:
                return {"token": "secret", "name": "test"}

            result: dict[str, str] = get_config()

            # Original return value should be unchanged
            assert result["token"] == "secret"
            assert result["name"] == "test"

            # Log should have redacted value
            second_call = mock_logger.debug.call_args_list[1]  # completion log
            result_str = str(second_call)

            assert "***" in result_str
            assert "secret" not in result_str
            assert "test" in result_str

    def test_log_function_call_redacts_nested_sensitive_values(self) -> None:
        """Test that nested sensitive values in return dict are redacted."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            @log_function_call(sensitive_fields=["token", "api_token"])
            def load_config() -> dict[str, dict[str, str]]:
                return {
                    "github": {"token": "ghp_xxx"},
                    "jenkins": {
                        "api_token": "jenkins_xxx",
                        "url": "http://example.com",
                    },
                }

            result: dict[str, dict[str, str]] = load_config()

            # Original return value should be unchanged
            assert result["github"]["token"] == "ghp_xxx"
            assert result["jenkins"]["api_token"] == "jenkins_xxx"

            # Log should have redacted values
            second_call = mock_logger.debug.call_args_list[1]
            result_str = str(second_call)

            assert "ghp_xxx" not in result_str
            assert "jenkins_xxx" not in result_str
            assert "http://example.com" in result_str

    def test_log_function_call_non_dict_return_unchanged(self) -> None:
        """Test that non-dict return values work correctly with sensitive_fields."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            @log_function_call(sensitive_fields=["token"])
            def get_number() -> int:
                return 42

            result: int = get_number()
            assert result == 42
            assert mock_logger.debug.call_count == 2


class TestLogFunctionCallAsync:
    """Tests for log_function_call decorator with async functions."""

    async def test_log_function_call_async_basic(self) -> None:
        """Test that the decorator works with basic async functions."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            @log_function_call
            async def add(a: int, b: int) -> int:
                return a + b

            result = await add(1, 2)

            assert result == 3
            assert mock_logger.debug.call_count == 2

    async def test_log_function_call_async_exception(self) -> None:
        """Test that exceptions from async functions propagate correctly."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            @log_function_call
            async def failing() -> None:
                raise ValueError("async error")

            with pytest.raises(ValueError):
                await failing()

            assert mock_logger.error.called is True

    async def test_log_function_call_async_with_sensitive_fields(self) -> None:
        """Test that sensitive fields are redacted for async functions."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            @log_function_call(sensitive_fields=["token"])
            async def auth(token: str, username: str) -> bool:
                _ = token, username
                return True

            await auth(token="secret123", username="user")

            first_call = mock_logger.debug.call_args_list[0]
            log_params = first_call[0][2]

            assert "***" in log_params
            assert "secret123" not in log_params

    async def test_log_function_call_async_method_skips_self(self) -> None:
        """Test that self is skipped when decorating an async method."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            class MyService:
                @log_function_call
                async def process(self, name: str) -> str:
                    return f"processed:{name}"

            svc = MyService()
            result = await svc.process("test")

            assert result == "processed:test"
            assert mock_logger.debug.call_count == 2

            first_call = mock_logger.debug.call_args_list[0]
            log_params = first_call[0][2]
            assert "self" not in log_params
