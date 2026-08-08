"""Tests for log_utils module."""

import io
import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import mcp_coder_utils.log_utils as log_utils_module
from mcp_coder_utils.log_utils import (
    OUTPUT,
    STANDARD_LOG_FIELDS,
    CleanFormatter,
    ExtraFieldsFormatter,
    _HANDLER_MARKER,
    _parse_level,
    log_function_call,
    setup_logging,
)


class TestOutputLevel:
    """Tests for the custom OUTPUT log level."""

    def test_output_level_is_registered(self) -> None:
        """Test that OUTPUT level name is registered with logging."""
        assert logging.getLevelName(25) == "OUTPUT"

    def test_output_level_value(self) -> None:
        """Test that OUTPUT constant has the expected value."""
        assert OUTPUT == 25

    def test_output_between_info_and_warning(self) -> None:
        """Test that OUTPUT sits between INFO and WARNING."""
        assert logging.INFO < OUTPUT < logging.WARNING

    def test_setup_logging_accepts_output(self) -> None:
        """Test that setup_logging works with OUTPUT level."""
        root_logger = logging.getLogger()
        initial_handlers = root_logger.handlers[:]
        initial_level = root_logger.level

        try:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            setup_logging("OUTPUT")

            assert root_logger.level == 25
        finally:
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
            for handler in initial_handlers:
                root_logger.addHandler(handler)
            root_logger.setLevel(initial_level)


class TestParseLevel:
    """Tests for the _parse_level helper."""

    def test_parse_string_level(self) -> None:
        """Standard string level names resolve to their numeric value."""
        assert _parse_level("INFO") == logging.INFO

    def test_parse_custom_string_level_case_insensitive(self) -> None:
        """Custom level names resolve case-insensitively via getLevelName."""
        assert _parse_level("output") == OUTPUT

    def test_parse_int_passthrough(self) -> None:
        """Integer levels are returned unchanged."""
        assert _parse_level(logging.DEBUG) == logging.DEBUG

    def test_parse_output_constant_passthrough(self) -> None:
        """The exported OUTPUT int constant passes through unchanged."""
        assert _parse_level(OUTPUT) == OUTPUT

    def test_parse_invalid_string_raises(self) -> None:
        """An unknown string level raises ValueError."""
        with pytest.raises(ValueError):
            _parse_level("NOPE")


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def test_setup_logging_console_only(self) -> None:
        """Test that console logging is configured correctly."""
        # Setup - store initial state to restore later
        root_logger = logging.getLogger()
        initial_handlers = root_logger.handlers[:]
        initial_level = root_logger.level

        try:
            # Clear existing handlers
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            # Execute
            setup_logging("INFO")

            # Verify
            handlers = root_logger.handlers
            assert len(handlers) == 1
            assert isinstance(handlers[0], logging.StreamHandler)
            assert root_logger.level == logging.INFO

        finally:
            # Cleanup - restore original state
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)

            for handler in initial_handlers:
                root_logger.addHandler(handler)
            root_logger.setLevel(initial_level)

    def test_setup_logging_with_file(self, tmp_path: Path) -> None:
        """Test that file logging is configured correctly."""
        # Setup - use pytest's tmp_path for automatic cleanup
        log_file = tmp_path / "logs" / "test.log"

        # Store initial handlers to restore later
        root_logger = logging.getLogger()
        initial_handlers = root_logger.handlers[:]
        initial_level = root_logger.level

        try:
            # Execute
            setup_logging("DEBUG", str(log_file))

            # Verify
            handlers = root_logger.handlers
            # In testing environment, we may have additional handlers from pytest
            # so we check that at least one file handler was added
            file_handlers: list[logging.FileHandler] = [
                h for h in handlers if isinstance(h, logging.FileHandler)
            ]
            assert len(file_handlers) >= 1, "At least one file handler should be added"
            assert root_logger.level == logging.DEBUG

            # Verify log directory was created
            assert log_file.parent.exists()

            # Verify our specific file handler exists with correct path
            our_file_handler: logging.FileHandler | None = None
            for handler in file_handlers:
                if isinstance(
                    handler, logging.FileHandler
                ) and handler.baseFilename == str(log_file.absolute()):
                    our_file_handler = handler
                    break

            assert (
                our_file_handler is not None
            ), "Our specific file handler should exist"

        finally:
            # Comprehensive cleanup - close and remove handlers to avoid resource leaks
            # 1. Close and remove all current handlers
            for handler in root_logger.handlers[:]:  # type: ignore[assignment]
                handler.close()
                root_logger.removeHandler(handler)

            # 2. Restore original handlers and level
            for handler in initial_handlers:  # type: ignore[assignment]
                root_logger.addHandler(handler)
            root_logger.setLevel(initial_level)

            # Note: tmp_path cleanup is automatic via pytest fixture

    def test_invalid_log_level(self) -> None:
        """Test that an invalid log level raises a ValueError."""
        with pytest.raises(ValueError):
            setup_logging("INVALID_LEVEL")


class TestSetupLoggingIdempotency:
    """Tests for marker-based idempotent handler management."""

    def test_repeated_console_calls_single_marked_handler(self) -> None:
        """Two console-mode calls leave exactly one marked console handler."""
        root_logger = logging.getLogger()
        initial_handlers = root_logger.handlers[:]
        initial_level = root_logger.level

        try:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            setup_logging("INFO")
            setup_logging("INFO")

            marked = [
                h
                for h in root_logger.handlers
                if getattr(h, _HANDLER_MARKER, False)
            ]
            assert len(marked) == 1
            assert isinstance(marked[0], logging.StreamHandler)
        finally:
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
            for handler in initial_handlers:
                root_logger.addHandler(handler)
            root_logger.setLevel(initial_level)

    def test_foreign_handler_survives(self) -> None:
        """A pre-attached unmarked handler survives; ours is still added."""
        root_logger = logging.getLogger()
        initial_handlers = root_logger.handlers[:]
        initial_level = root_logger.level
        foreign_handler = logging.StreamHandler()

        try:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            root_logger.addHandler(foreign_handler)

            setup_logging("INFO")

            # Foreign handler untouched.
            assert foreign_handler in root_logger.handlers
            assert not getattr(foreign_handler, _HANDLER_MARKER, False)

            # Our marked handler added alongside it.
            marked = [
                h
                for h in root_logger.handlers
                if getattr(h, _HANDLER_MARKER, False)
            ]
            assert len(marked) == 1
            assert marked[0] is not foreign_handler
        finally:
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
            for handler in initial_handlers:
                root_logger.addHandler(handler)
            root_logger.setLevel(initial_level)

    def test_repeated_file_calls_single_marked_file_handler(
        self, tmp_path: Path
    ) -> None:
        """Repeated file-mode calls to the same path do not accumulate handlers."""
        log_file = tmp_path / "logs" / "test.log"
        root_logger = logging.getLogger()
        initial_handlers = root_logger.handlers[:]
        initial_level = root_logger.level

        try:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            setup_logging("DEBUG", str(log_file))
            setup_logging("DEBUG", str(log_file))
            setup_logging("DEBUG", str(log_file))

            marked_file_handlers = [
                h
                for h in root_logger.handlers
                if getattr(h, _HANDLER_MARKER, False)
                and isinstance(h, logging.FileHandler)
            ]
            assert len(marked_file_handlers) == 1
        finally:
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
            for handler in initial_handlers:
                root_logger.addHandler(handler)
            root_logger.setLevel(initial_level)


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


class TestExtraFieldsFormatter:
    """Tests for ExtraFieldsFormatter class."""

    def test_format_without_extra_fields(self) -> None:
        """Test formatting a log record with no extra fields."""
        formatter = ExtraFieldsFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)

        # Standard message should remain unchanged (no extra fields suffix)
        assert "Test message" in formatted
        assert "{" not in formatted  # No JSON suffix

    def test_format_with_extra_fields(self) -> None:
        """Test formatting a log record with extra fields."""
        formatter = ExtraFieldsFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        # Add extra field
        record.custom_field = "custom_value"

        formatted = formatter.format(record)

        # Extra fields should be appended as JSON
        assert "Test message" in formatted
        assert "custom_field" in formatted
        assert "custom_value" in formatted

    def test_format_with_multiple_extra_fields(self) -> None:
        """Test formatting with multiple extra fields."""
        formatter = ExtraFieldsFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        # Add multiple extra fields
        record.user_id = 123
        record.request_id = "abc-456"
        record.action = "login"

        formatted = formatter.format(record)

        # All extra fields should be included
        assert "Test message" in formatted
        assert "user_id" in formatted
        assert "123" in formatted
        assert "request_id" in formatted
        assert "abc-456" in formatted
        assert "action" in formatted
        assert "login" in formatted


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
            assert (
                len(log_utils_module_calls) == 0
            ), f"Logger should not be from mcp_coder_utils.log_utils: {func_logger_calls}"

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
                assert (
                    mock_structlog.get_logger.called
                ), "structlog.get_logger should be called"

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


class TestCleanFormatter:
    """Tests for CleanFormatter class."""

    def test_output_level_no_prefix(self) -> None:
        """OUTPUT-level messages have no prefix."""
        formatter = CleanFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=OUTPUT,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        assert result == "Test message"

    def test_warning_level_has_prefix(self) -> None:
        """WARNING-level messages get 'WARNING: ' prefix."""
        formatter = CleanFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        assert result == "WARNING: Test message"

    def test_error_level_has_prefix(self) -> None:
        """ERROR-level messages get 'ERROR: ' prefix."""
        formatter = CleanFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        assert result == "ERROR: Test message"

    def test_extra_fields_appended_as_json(self) -> None:
        """Extra fields are appended as JSON."""
        formatter = CleanFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=OUTPUT,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.custom_field = "custom_value"
        result = formatter.format(record)
        assert "Test message" in result
        assert "custom_field" in result
        assert "custom_value" in result

    def test_no_extra_fields_no_json(self) -> None:
        """No JSON suffix when no extra fields."""
        formatter = CleanFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=OUTPUT,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        assert "{" not in result


class TestSetupLoggingFormatterSelection:
    """Tests for formatter selection based on threshold."""

    def _get_console_formatter(self, log_level: str) -> logging.Formatter:
        """Helper to get the console formatter after setup_logging."""
        root_logger = logging.getLogger()
        initial_handlers = root_logger.handlers[:]
        initial_level = root_logger.level

        try:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            setup_logging(log_level)

            stream_handlers = [
                h
                for h in root_logger.handlers
                if isinstance(h, logging.StreamHandler)
                and not isinstance(h, logging.FileHandler)
            ]
            assert len(stream_handlers) == 1
            formatter = stream_handlers[0].formatter
            assert formatter is not None
            return formatter
        finally:
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
            for handler in initial_handlers:
                root_logger.addHandler(handler)
            root_logger.setLevel(initial_level)

    def test_output_threshold_uses_clean_formatter(self) -> None:
        """OUTPUT threshold should use CleanFormatter."""
        formatter = self._get_console_formatter("OUTPUT")
        assert isinstance(formatter, CleanFormatter)

    def test_info_threshold_uses_extra_fields_formatter(self) -> None:
        """INFO threshold should use ExtraFieldsFormatter."""
        formatter = self._get_console_formatter("INFO")
        assert isinstance(formatter, ExtraFieldsFormatter)

    def test_debug_threshold_uses_extra_fields_formatter(self) -> None:
        """DEBUG threshold should use ExtraFieldsFormatter."""
        formatter = self._get_console_formatter("DEBUG")
        assert isinstance(formatter, ExtraFieldsFormatter)


class TestSetupLoggingDualMode:
    """Tests for the console_level parameter and simultaneous file+console sinks."""

    def _marked_handlers(self) -> list[logging.Handler]:
        """Return the handlers setup_logging tagged on the root logger."""
        root_logger = logging.getLogger()
        return [h for h in root_logger.handlers if getattr(h, _HANDLER_MARKER, False)]

    def test_root_floor_is_min_of_levels(self) -> None:
        """log_level=INFO, console_level=DEBUG -> root floor lowered to DEBUG.

        Proves DEBUG records are not pre-filtered at the logger. This is the
        case the motivating INFO/OUTPUT scenario would miss.
        """
        root_logger = logging.getLogger()
        initial_handlers = root_logger.handlers[:]
        initial_level = root_logger.level

        try:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            setup_logging("INFO", console_level="DEBUG")

            assert root_logger.level == logging.DEBUG
        finally:
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
            for handler in initial_handlers:
                root_logger.addHandler(handler)
            root_logger.setLevel(initial_level)

    def test_dual_sinks_structure(self, tmp_path: Path) -> None:
        """File + console_level=OUTPUT -> one file handler at INFO, one console at OUTPUT."""
        log_file = tmp_path / "logs" / "test.log"
        root_logger = logging.getLogger()
        initial_handlers = root_logger.handlers[:]
        initial_level = root_logger.level

        try:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            setup_logging("INFO", str(log_file), console_level=OUTPUT)

            marked = self._marked_handlers()
            file_handlers = [h for h in marked if isinstance(h, logging.FileHandler)]
            console_handlers = [
                h
                for h in marked
                if isinstance(h, logging.StreamHandler)
                and not isinstance(h, logging.FileHandler)
            ]

            assert len(file_handlers) == 1
            assert file_handlers[0].level == logging.INFO

            assert len(console_handlers) == 1
            assert console_handlers[0].level == OUTPUT
            assert isinstance(console_handlers[0].formatter, CleanFormatter)

            # min(20, 25) == 20
            assert root_logger.level == logging.INFO
        finally:
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
            for handler in initial_handlers:
                root_logger.addHandler(handler)
            root_logger.setLevel(initial_level)

    def test_dual_mode_behavioural_file_gets_record_console_filters(
        self, tmp_path: Path
    ) -> None:
        """An INFO record lands in the file but is filtered from the OUTPUT console."""
        log_file = tmp_path / "logs" / "test.log"
        root_logger = logging.getLogger()
        initial_handlers = root_logger.handlers[:]
        initial_level = root_logger.level

        try:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            setup_logging("INFO", str(log_file), console_level=OUTPUT)

            # Redirect the marked console handler's stream to a StringIO so we can
            # capture what the console handler actually emits.
            console_handlers = [
                h
                for h in self._marked_handlers()
                if isinstance(h, logging.StreamHandler)
                and not isinstance(h, logging.FileHandler)
            ]
            assert len(console_handlers) == 1
            captured = io.StringIO()
            console_handlers[0].setStream(captured)

            logging.getLogger("dual_mode_x").info("trail line")

            # Flush + close file handlers so the record is on disk.
            for handler in self._marked_handlers():
                handler.flush()
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)

            file_contents = log_file.read_text(encoding="utf-8")
            assert "trail line" in file_contents

            console_output = captured.getvalue()
            assert "trail line" not in console_output
        finally:
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
            for handler in initial_handlers:
                root_logger.addHandler(handler)
            root_logger.setLevel(initial_level)

    def test_console_formatter_from_console_level(self, tmp_path: Path) -> None:
        """File + console_level=DEBUG -> console handler uses ExtraFieldsFormatter."""
        log_file = tmp_path / "logs" / "test.log"
        root_logger = logging.getLogger()
        initial_handlers = root_logger.handlers[:]
        initial_level = root_logger.level

        try:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            setup_logging("INFO", str(log_file), console_level="DEBUG")

            console_handlers = [
                h
                for h in self._marked_handlers()
                if isinstance(h, logging.StreamHandler)
                and not isinstance(h, logging.FileHandler)
            ]
            assert len(console_handlers) == 1
            assert isinstance(console_handlers[0].formatter, ExtraFieldsFormatter)
        finally:
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
            for handler in initial_handlers:
                root_logger.addHandler(handler)
            root_logger.setLevel(initial_level)

    def test_console_level_without_log_file(self) -> None:
        """console_level without log_file -> console only, root floor at DEBUG."""
        root_logger = logging.getLogger()
        initial_handlers = root_logger.handlers[:]
        initial_level = root_logger.level

        try:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            setup_logging("DEBUG", console_level=OUTPUT)

            marked = self._marked_handlers()
            file_handlers = [h for h in marked if isinstance(h, logging.FileHandler)]
            console_handlers = [
                h
                for h in marked
                if isinstance(h, logging.StreamHandler)
                and not isinstance(h, logging.FileHandler)
            ]

            assert len(file_handlers) == 0
            assert len(console_handlers) == 1
            assert console_handlers[0].level == OUTPUT
            assert root_logger.level == logging.DEBUG
        finally:
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
            for handler in initial_handlers:
                root_logger.addHandler(handler)
            root_logger.setLevel(initial_level)

    def test_backwards_compat_console_only(self) -> None:
        """setup_logging(INFO) with no console_level -> console only, no file."""
        root_logger = logging.getLogger()
        initial_handlers = root_logger.handlers[:]
        initial_level = root_logger.level

        try:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            setup_logging("INFO")

            marked = self._marked_handlers()
            file_handlers = [h for h in marked if isinstance(h, logging.FileHandler)]
            console_handlers = [
                h
                for h in marked
                if isinstance(h, logging.StreamHandler)
                and not isinstance(h, logging.FileHandler)
            ]

            assert len(file_handlers) == 0
            assert len(console_handlers) == 1
            assert root_logger.level == logging.INFO
        finally:
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
            for handler in initial_handlers:
                root_logger.addHandler(handler)
            root_logger.setLevel(initial_level)

    def test_backwards_compat_file_only(self, tmp_path: Path) -> None:
        """setup_logging(INFO, log_file) with no console_level -> file only."""
        log_file = tmp_path / "logs" / "test.log"
        root_logger = logging.getLogger()
        initial_handlers = root_logger.handlers[:]
        initial_level = root_logger.level

        try:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            setup_logging("INFO", str(log_file))

            marked = self._marked_handlers()
            file_handlers = [h for h in marked if isinstance(h, logging.FileHandler)]
            console_handlers = [
                h
                for h in marked
                if isinstance(h, logging.StreamHandler)
                and not isinstance(h, logging.FileHandler)
            ]

            assert len(file_handlers) == 1
            assert len(console_handlers) == 0
            assert root_logger.level == logging.INFO
        finally:
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
            for handler in initial_handlers:
                root_logger.addHandler(handler)
            root_logger.setLevel(initial_level)

    def test_console_level_accepts_string_and_int(self, tmp_path: Path) -> None:
        """console_level accepts both a string name and the OUTPUT int constant."""
        log_file = tmp_path / "logs" / "test.log"
        root_logger = logging.getLogger()
        initial_handlers = root_logger.handlers[:]
        initial_level = root_logger.level

        try:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            setup_logging("INFO", str(log_file), console_level="OUTPUT")
            console_str = [
                h
                for h in self._marked_handlers()
                if isinstance(h, logging.StreamHandler)
                and not isinstance(h, logging.FileHandler)
            ]
            assert len(console_str) == 1
            assert console_str[0].level == OUTPUT

            setup_logging("INFO", str(log_file), console_level=OUTPUT)
            console_int = [
                h
                for h in self._marked_handlers()
                if isinstance(h, logging.StreamHandler)
                and not isinstance(h, logging.FileHandler)
            ]
            assert len(console_int) == 1
            assert console_int[0].level == OUTPUT
        finally:
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
            for handler in initial_handlers:
                root_logger.addHandler(handler)
            root_logger.setLevel(initial_level)


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



class TestPublicExports:
    """Tests for the module's public export contract (__all__)."""

    def test_formatter_symbols_in_all(self) -> None:
        """CleanFormatter, ExtraFieldsFormatter, STANDARD_LOG_FIELDS are exported."""
        assert "CleanFormatter" in log_utils_module.__all__
        assert "ExtraFieldsFormatter" in log_utils_module.__all__
        assert "STANDARD_LOG_FIELDS" in log_utils_module.__all__

    def test_formatter_symbols_importable(self) -> None:
        """The exported formatter symbols resolve to non-None objects."""
        assert CleanFormatter is not None
        assert ExtraFieldsFormatter is not None
        assert STANDARD_LOG_FIELDS is not None

    def test_all_names_are_real_attributes(self) -> None:
        """Every name listed in __all__ resolves to a real module attribute."""
        for name in log_utils_module.__all__:
            assert hasattr(log_utils_module, name), f"{name} missing from module"
