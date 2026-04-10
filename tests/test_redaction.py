"""Tests for redaction module."""

import pytest

from mcp_coder_utils.redaction import (
    REDACTED_VALUE,
    SENSITIVE_KEY_PATTERNS,
    RedactableDict,
    redact_env_vars,
    redact_for_logging,
)


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


class TestSensitiveKeyPatterns:
    """Tests for the SENSITIVE_KEY_PATTERNS constant."""

    def test_sensitive_key_patterns_contents(self) -> None:
        """Verify the frozenset contains exactly the 6 expected patterns."""
        expected = frozenset(
            {
                "token",
                "secret",
                "password",
                "credential",
                "api_key",
                "access_key",
            }
        )
        assert SENSITIVE_KEY_PATTERNS == expected

    def test_sensitive_key_patterns_is_frozenset(self) -> None:
        """Verify SENSITIVE_KEY_PATTERNS is immutable."""
        assert isinstance(SENSITIVE_KEY_PATTERNS, frozenset)


class TestRedactEnvVars:
    """Tests for the redact_env_vars function."""

    @pytest.mark.parametrize(
        ("key", "value"),
        [
            ("GITHUB_TOKEN", "ghp_abc123"),
            ("AWS_SECRET_KEY", "wJalrXUtnFEMI"),
            ("DB_PASSWORD", "hunter2"),
            ("MY_CREDENTIAL_FILE", "/path/to/cred"),
            ("AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7"),
            ("JENKINS_API_KEY", "abcdef12345"),
        ],
    )
    def test_redact_env_vars_sensitive_keys(self, key: str, value: str) -> None:
        """Sensitive env var keys are redacted."""
        result = redact_env_vars({key: value})
        assert result[key] == REDACTED_VALUE

    @pytest.mark.parametrize(
        "key",
        ["github_token", "GitHub_Token", "GITHUB_TOKEN", "Github_SECRET"],
    )
    def test_redact_env_vars_case_insensitive(self, key: str) -> None:
        """Matching is case-insensitive."""
        result = redact_env_vars({key: "sensitive_value"})
        assert result[key] == REDACTED_VALUE

    @pytest.mark.parametrize(
        ("key", "value"),
        [
            ("PATH", "/usr/bin"),
            ("HOME", "/home/user"),
            ("LANG", "en_US.UTF-8"),
            ("SHELL", "/bin/bash"),
        ],
    )
    def test_redact_env_vars_safe_keys_unchanged(self, key: str, value: str) -> None:
        """Non-sensitive env var keys pass through unchanged."""
        result = redact_env_vars({key: value})
        assert result[key] == value

    @pytest.mark.parametrize(
        "key",
        ["KEYBOARD_LAYOUT", "HKEY_LOCAL"],
    )
    def test_redact_env_vars_no_false_positive_on_key(self, key: str) -> None:
        """Keys containing 'key' as a word fragment are NOT redacted (no bare 'key' pattern)."""
        result = redact_env_vars({key: "some_value"})
        assert result[key] == "some_value"

    def test_redact_env_vars_extra_patterns(self) -> None:
        """Custom extra_patterns extend the default patterns."""
        env = {
            "DATABASE_CONN_STR": "Server=prod;Password=x",
            "GITHUB_TOKEN": "ghp_abc",
            "HOME": "/home/user",
        }
        result = redact_env_vars(env, extra_patterns=frozenset({"conn_str"}))
        assert result["DATABASE_CONN_STR"] == REDACTED_VALUE
        assert result["GITHUB_TOKEN"] == REDACTED_VALUE
        assert result["HOME"] == "/home/user"

    def test_redact_env_vars_empty_input(self) -> None:
        """Empty input returns empty dict."""
        result = redact_env_vars({})
        assert result == {}

    def test_redact_env_vars_returns_new_dict(self) -> None:
        """Original mapping is not mutated."""
        env = {"GITHUB_TOKEN": "ghp_abc", "PATH": "/usr/bin"}
        result = redact_env_vars(env)
        assert result is not env
        assert env["GITHUB_TOKEN"] == "ghp_abc"
