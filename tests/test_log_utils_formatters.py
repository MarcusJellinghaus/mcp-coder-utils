import logging

from mcp_coder_utils.log_utils import OUTPUT, CleanFormatter, ExtraFieldsFormatter


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
