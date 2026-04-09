"""Tests for log_utils module."""

import json
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder_utils.log_utils import (
    OUTPUT,
    CleanFormatter,
    ExtraFieldsFormatter,
    log_function_call,
    setup_logging,
)


class TestOutputLevel:
    """Verifies OUTPUT level constant."""

    def test_output_level_value(self) -> None:
        """OUTPUT level is 25, between INFO (20) and WARNING (30)."""
        assert OUTPUT == 25

    def test_output_level_registered(self) -> None:
        """OUTPUT level is registered with the logging module."""
        assert logging.getLevelName(OUTPUT) == "OUTPUT"

    def test_output_level_between_info_and_warning(self) -> None:
        """OUTPUT sits between INFO and WARNING."""
        assert logging.INFO < OUTPUT < logging.WARNING


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def test_setup_logging_console_only(self) -> None:
        """Test that console logging is configured correctly."""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        setup_logging("INFO")

        handlers = root_logger.handlers
        assert len(handlers) >= 1
        assert any(isinstance(h, logging.StreamHandler) for h in handlers)
        assert root_logger.level == logging.INFO

    def test_setup_logging_with_file(self) -> None:
        """Test that file logging is configured correctly."""
        temp_dir = tempfile.mkdtemp()
        try:
            log_file = os.path.join(temp_dir, "logs", "test.log")

            setup_logging("DEBUG", log_file)

            root_logger = logging.getLogger()
            handlers = root_logger.handlers
            assert any(isinstance(h, logging.FileHandler) for h in handlers)
            assert root_logger.level == logging.DEBUG

            # Verify log directory was created
            assert os.path.exists(os.path.dirname(log_file))

            # Verify file handler has correct path
            file_handlers = [h for h in handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) >= 1
            assert file_handlers[0].baseFilename == os.path.abspath(log_file)

            # Clean up by removing handlers
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
        finally:
            try:
                import shutil

                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

    def test_invalid_log_level(self) -> None:
        """Test that an invalid log level raises a ValueError."""
        with pytest.raises(ValueError):
            setup_logging("INVALID_LEVEL")

    def test_testing_env_handler_safety(self) -> None:
        """Test that pytest capture handlers are preserved in test environments."""
        root_logger = logging.getLogger()

        # setup_logging should not destroy pytest's capture handlers
        setup_logging("DEBUG")

        # We should still have at least one handler (new console or preserved pytest)
        assert len(root_logger.handlers) >= 1

        # Clean up
        for handler in root_logger.handlers[:]:
            if isinstance(handler, (logging.FileHandler, logging.StreamHandler)):
                if not hasattr(handler, "_store"):
                    root_logger.removeHandler(handler)


class TestLogFunctionCall:
    """Tests for the log_function_call decorator."""

    @patch("mcp_coder_utils.log_utils.stdlogger")
    def test_log_function_call_basic(self, mock_stdlogger: MagicMock) -> None:
        """Test the basic functionality of the decorator."""

        @log_function_call
        def test_func(a: int, b: int) -> int:
            return a + b

        result = test_func(1, 2)

        assert result == 3
        assert mock_stdlogger.debug.call_count == 2

    @patch("mcp_coder_utils.log_utils.stdlogger")
    def test_log_function_call_with_exception(self, mock_stdlogger: MagicMock) -> None:
        """Test that exceptions are properly logged."""

        @log_function_call
        def failing_func() -> None:
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_func()

        assert mock_stdlogger.debug.call_count == 1
        assert mock_stdlogger.error.call_count == 1

    @patch("mcp_coder_utils.log_utils.stdlogger")
    def test_log_function_call_with_path_param(self, mock_stdlogger: MagicMock) -> None:
        """Test that Path objects are properly serialized."""

        @log_function_call
        def path_func(file_path: Path) -> str:
            return str(file_path)

        test_path = Path("/test/path")
        result = path_func(test_path)

        assert result == str(test_path)
        assert mock_stdlogger.debug.call_count == 2

        # First call should include function name
        first_call = mock_stdlogger.debug.call_args_list[0]
        assert first_call[0][0] == "Calling %s with parameters: %s"
        assert first_call[0][1] == "path_func"

    @patch("mcp_coder_utils.log_utils.stdlogger")
    def test_log_function_call_with_large_result(
        self, mock_stdlogger: MagicMock
    ) -> None:
        """Test that large results are properly truncated in logs."""

        @log_function_call
        def large_result_func() -> list[int]:
            return list(range(1000))

        result = large_result_func()

        assert len(result) == 1000
        assert mock_stdlogger.debug.call_count == 2

        second_call = mock_stdlogger.debug.call_args_list[1]
        assert second_call[0][0] == "%s completed in %sms with result: %s"
        assert second_call[0][1] == "large_result_func"
        result_arg = second_call[0][3]
        assert "<Large result of type list" in result_arg

    @patch("mcp_coder_utils.log_utils.structlog")
    @patch("mcp_coder_utils.log_utils.stdlogger")
    def test_log_function_call_with_structured_logging(
        self, mock_stdlogger: MagicMock, mock_structlog: MagicMock
    ) -> None:
        """Test that structured logging is used when available."""
        mock_structlogger = mock_structlog.get_logger.return_value

        with patch("mcp_coder_utils.log_utils.any", return_value=True):

            @log_function_call
            def test_func(a: int, b: int) -> int:
                return a + b

            result = test_func(1, 2)

            assert result == 3
            assert mock_stdlogger.debug.call_count == 2
            assert mock_structlogger.debug.call_count == 2


class TestExtraFieldsFormatter:
    """Tests for ExtraFieldsFormatter."""

    def test_extra_fields_appended(self) -> None:
        """Extra fields are appended to the log line."""
        formatter = ExtraFieldsFormatter("%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="hello",
            args=None,
            exc_info=None,
        )
        record.custom_field = "custom_value"
        output = formatter.format(record)
        assert "hello" in output
        assert "custom_field" in output
        assert "custom_value" in output

    def test_no_extra_fields(self) -> None:
        """No extra fields means standard output only."""
        formatter = ExtraFieldsFormatter("%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="hello",
            args=None,
            exc_info=None,
        )
        output = formatter.format(record)
        assert output == "hello"


class TestLogFunctionCallLoggerName:
    """Test that logger uses the calling module's name."""

    def test_logger_name_is_module(self) -> None:
        """The stdlogger uses mcp_coder_utils.log_utils as its name."""
        from mcp_coder_utils.log_utils import stdlogger

        assert stdlogger.name == "mcp_coder_utils.log_utils"


class TestCleanFormatter:
    """Tests for CleanFormatter bare CLI output."""

    def test_clean_format_message_only(self) -> None:
        """CleanFormatter outputs only the message, no timestamp or level."""
        formatter = CleanFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="bare message",
            args=None,
            exc_info=None,
        )
        output = formatter.format(record)
        assert output == "bare message"

    def test_clean_format_with_args(self) -> None:
        """CleanFormatter formats message with args."""
        formatter = CleanFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="value is %s",
            args=("hello",),
            exc_info=None,
        )
        output = formatter.format(record)
        assert output == "value is hello"


class TestSetupLoggingFormatterSelection:
    """Tests for correct formatter selection per config."""

    def test_console_uses_standard_formatter(self) -> None:
        """Console-only logging uses standard Formatter."""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        setup_logging("INFO")

        stream_handlers = [
            h
            for h in root_logger.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]
        assert len(stream_handlers) >= 1
        assert isinstance(stream_handlers[0].formatter, logging.Formatter)

    def test_file_uses_json_formatter(self) -> None:
        """File logging uses JsonFormatter."""
        from pythonjsonlogger.json import JsonFormatter as JF

        temp_dir = tempfile.mkdtemp()
        try:
            log_file = os.path.join(temp_dir, "test.log")

            setup_logging("DEBUG", log_file)

            root_logger = logging.getLogger()
            file_handlers = [
                h for h in root_logger.handlers if isinstance(h, logging.FileHandler)
            ]
            assert len(file_handlers) >= 1
            assert isinstance(file_handlers[0].formatter, JF)

            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
        finally:
            try:
                import shutil

                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
