"""Tests for redaction module."""

from mcp_coder_utils.redaction import RedactableDict, redact_for_logging


class TestRedactForLogging:
    """Tests for the redact_for_logging helper function."""

    def test_redact_flat_dict(self) -> None:
        """Test redaction of flat dictionary."""
        data: RedactableDict = {
            "token": "secret123",
            "username": "user",
        }
        result = redact_for_logging(data, {"token"})

        assert result["token"] == "***"
        assert result["username"] == "user"
        # Original should be unchanged
        assert data["token"] == "secret123"

    def test_redact_nested_dict(self) -> None:
        """Test redaction of nested dictionary."""
        data: RedactableDict = {"outer": {"token": "secret", "safe": "visible"}}
        result = redact_for_logging(data, {"token"})

        assert result["outer"]["token"] == "***"
        assert result["outer"]["safe"] == "visible"
        # Original should be unchanged
        assert data["outer"]["token"] == "secret"

    def test_redact_deeply_nested_dict(self) -> None:
        """Test redaction of deeply nested dictionary."""
        data: RedactableDict = {
            "github": {"token": "ghp_xxx"},
            "jenkins": {"api_token": "jenkins_xxx", "url": "http://example.com"},
        }
        result = redact_for_logging(data, {"token", "api_token"})

        assert result["github"]["token"] == "***"
        assert result["jenkins"]["api_token"] == "***"
        assert result["jenkins"]["url"] == "http://example.com"
        # Original should be unchanged
        assert data["github"]["token"] == "ghp_xxx"
        assert data["jenkins"]["api_token"] == "jenkins_xxx"

    def test_redact_empty_sensitive_fields(self) -> None:
        """Test with empty sensitive_fields set."""
        data: RedactableDict = {"token": "secret", "name": "test"}
        result = redact_for_logging(data, set())

        assert result["token"] == "secret"
        assert result["name"] == "test"

    def test_redact_non_matching_fields(self) -> None:
        """Test when no fields match sensitive_fields."""
        data: RedactableDict = {"name": "test", "value": 123}
        result = redact_for_logging(data, {"token", "password"})

        assert result["name"] == "test"
        assert result["value"] == 123


class TestRedactForLoggingTupleKeys:
    """Tests for redact_for_logging with tuple dictionary keys.

    Issue #327: get_config_values() returns dicts with tuple keys like
    ('github', 'token'). The redaction should check the last element
    of tuple keys against sensitive_fields.
    """

    def test_redact_tuple_key_matches_last_element(self) -> None:
        """Test that tuple keys are redacted when last element matches sensitive field."""
        data: RedactableDict = {
            ("github", "token"): "ghp_secret123",
            ("user", "name"): "john",
        }
        result = redact_for_logging(data, {"token"})

        assert result[("github", "token")] == "***"
        assert result[("user", "name")] == "john"
        # Original unchanged
        assert data[("github", "token")] == "ghp_secret123"

    def test_redact_mixed_string_and_tuple_keys(self) -> None:
        """Test redaction works with both string and tuple keys in same dict."""
        data: RedactableDict = {
            "token": "direct_secret",
            ("github", "token"): "tuple_secret",
            "username": "user",
        }
        result = redact_for_logging(data, {"token"})

        assert result["token"] == "***"
        assert result[("github", "token")] == "***"
        assert result["username"] == "user"

    def test_redact_tuple_key_no_match(self) -> None:
        """Test that tuple keys not matching sensitive fields are unchanged."""
        data: RedactableDict = {
            ("github", "username"): "user",
            ("jenkins", "url"): "http://example.com",
        }
        result = redact_for_logging(data, {"token", "api_token"})

        assert result[("github", "username")] == "user"
        assert result[("jenkins", "url")] == "http://example.com"

    def test_redact_empty_tuple_key_unchanged(self) -> None:
        """Test that empty tuple keys are handled safely (no crash, no match)."""
        data: RedactableDict = {
            (): "empty_tuple_value",
            ("normal", "key"): "normal_value",
        }
        result = redact_for_logging(data, {"token"})

        # Empty tuple should not crash and value should be unchanged
        assert result[()] == "empty_tuple_value"
        assert result[("normal", "key")] == "normal_value"
