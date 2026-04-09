"""Tests for log_utils redaction functionality."""

from unittest.mock import MagicMock, patch

from mcp_coder_utils.log_utils import (
    REDACTED_VALUE,
    _redact_for_logging,
    log_function_call,
)


class TestRedactForLogging:
    """Tests _redact_for_logging with various field types."""

    def test_redact_sensitive_field(self) -> None:
        """Sensitive fields are replaced with REDACTED_VALUE."""
        params = {"username": "alice", "password": "secret123"}
        result = _redact_for_logging(params, {"password"})
        assert result["username"] == "alice"
        assert result["password"] == REDACTED_VALUE

    def test_redact_no_sensitive_fields(self) -> None:
        """Without sensitive fields, all values are preserved."""
        params = {"name": "alice", "age": 30}
        result = _redact_for_logging(params, set())
        assert result == params

    def test_redact_all_sensitive(self) -> None:
        """All fields can be redacted."""
        params = {"token": "abc", "secret": "xyz"}
        result = _redact_for_logging(params, {"token", "secret"})
        assert result["token"] == REDACTED_VALUE
        assert result["secret"] == REDACTED_VALUE

    def test_redact_empty_params(self) -> None:
        """Empty params returns empty dict."""
        result = _redact_for_logging({}, {"password"})
        assert result == {}

    def test_redact_missing_sensitive_field(self) -> None:
        """Sensitive fields not in params are ignored."""
        params = {"name": "alice"}
        result = _redact_for_logging(params, {"password"})
        assert result == {"name": "alice"}

    def test_redact_preserves_non_string_values(self) -> None:
        """Non-string values are preserved for non-sensitive keys."""
        params = {"count": 42, "token": "secret"}
        result = _redact_for_logging(params, {"token"})
        assert result["count"] == 42
        assert result["token"] == REDACTED_VALUE


class TestRedactForLoggingTupleKeys:
    """Tests tuple-key redaction (nested field paths)."""

    def test_tuple_key_redacted_when_part_matches(self) -> None:
        """Tuple key is redacted if any component matches a sensitive field."""
        params = {("auth", "token"): "secret_value", "name": "alice"}
        result = _redact_for_logging(params, {"token"})
        assert result[("auth", "token")] == REDACTED_VALUE
        assert result["name"] == "alice"

    def test_tuple_key_not_redacted_when_no_match(self) -> None:
        """Tuple key is preserved if no component matches."""
        params = {("user", "name"): "alice"}
        result = _redact_for_logging(params, {"password"})
        assert result[("user", "name")] == "alice"

    def test_tuple_key_first_component_matches(self) -> None:
        """Tuple key redacted when first component is sensitive."""
        params = {("password", "hash"): "abc123"}
        result = _redact_for_logging(params, {"password"})
        assert result[("password", "hash")] == REDACTED_VALUE

    def test_mixed_tuple_and_string_keys(self) -> None:
        """Mixed tuple and string keys are handled correctly."""
        params = {
            "username": "alice",
            "password": "secret",
            ("api", "key"): "my-key",
        }
        result = _redact_for_logging(params, {"password", "key"})
        assert result["username"] == "alice"
        assert result["password"] == REDACTED_VALUE
        assert result[("api", "key")] == REDACTED_VALUE


class TestLogFunctionCallWithSensitiveFields:
    """Tests the sensitive_fields overload of log_function_call."""

    @patch("mcp_coder_utils.log_utils.stdlogger")
    def test_sensitive_fields_redacted_in_log(self, mock_stdlogger: MagicMock) -> None:
        """Sensitive fields are redacted in log output."""

        @log_function_call(sensitive_fields={"token"})
        def auth_func(user: str, token: str) -> str:
            return f"auth:{user}"

        result = auth_func("alice", "secret-token-123")

        assert result == "auth:alice"
        assert mock_stdlogger.debug.call_count == 2

        # Check that the logged parameters contain the redacted value
        first_call = mock_stdlogger.debug.call_args_list[0]
        params_json = first_call[0][2]
        assert REDACTED_VALUE in params_json
        assert "secret-token-123" not in params_json

    @patch("mcp_coder_utils.log_utils.stdlogger")
    def test_sensitive_fields_empty_set(self, mock_stdlogger: MagicMock) -> None:
        """Empty sensitive_fields set does not redact anything."""

        @log_function_call(sensitive_fields=set())
        def normal_func(data: str) -> str:
            return data

        result = normal_func("visible")

        assert result == "visible"
        first_call = mock_stdlogger.debug.call_args_list[0]
        params_json = first_call[0][2]
        assert "visible" in params_json

    @patch("mcp_coder_utils.log_utils.stdlogger")
    def test_decorator_without_sensitive_fields(
        self, mock_stdlogger: MagicMock
    ) -> None:
        """Bare decorator (no sensitive_fields) does not redact."""

        @log_function_call
        def plain_func(secret: str) -> str:
            return secret

        result = plain_func("plaintext")

        assert result == "plaintext"
        first_call = mock_stdlogger.debug.call_args_list[0]
        params_json = first_call[0][2]
        assert "plaintext" in params_json
