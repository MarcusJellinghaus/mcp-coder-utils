"""Redaction utilities for sanitising sensitive data before logging."""

from collections.abc import Mapping
from typing import Any

__all__ = [
    "redact_for_logging",
    "redact_env_vars",
    "SENSITIVE_KEY_PATTERNS",
    "REDACTED_VALUE",
    "RedactableDict",
]

# Type alias for dictionaries that can have string or tuple keys
# Used by redact_for_logging to handle get_config_values() return format
RedactableDict = dict[str | tuple[str, ...], Any]

# Redaction placeholder for sensitive values
REDACTED_VALUE = "***"

# Substring patterns for identifying sensitive env var keys (case-insensitive)
SENSITIVE_KEY_PATTERNS: frozenset[str] = frozenset(
    {
        "token",
        "secret",
        "password",
        "credential",
        "api_key",
        "access_key",
    }
)


def redact_for_logging(
    data: RedactableDict,
    sensitive_fields: set[str],
) -> RedactableDict:
    """Create a copy of data with sensitive fields redacted for logging.

    Args:
        data: Dictionary containing data to be logged.
        sensitive_fields: Set of field names whose values should be redacted.
            For tuple keys, the last element of the tuple is checked against
            sensitive_fields (e.g., ("github", "token") matches "token").

    Returns:
        A shallow copy of data with sensitive field values replaced by "***".
        Nested dictionaries are processed recursively.
    """
    result = data.copy()
    for key in result:
        # Check if key matches sensitive fields
        # For tuple keys, check the last element
        key_to_check: str | None = None
        if isinstance(key, str):
            key_to_check = key
        elif isinstance(key, tuple) and len(key) > 0:
            last_element = key[-1]
            if isinstance(last_element, str):
                key_to_check = last_element

        if key_to_check is not None and key_to_check in sensitive_fields:
            result[key] = REDACTED_VALUE
        elif isinstance(result[key], dict):
            result[key] = redact_for_logging(result[key], sensitive_fields)
    return result


def redact_env_vars(
    env: Mapping[str, str],
    extra_patterns: frozenset[str] | None = None,
) -> dict[str, str]:
    """Redact env var values whose keys contain sensitive substrings (case-insensitive).

    Args:
        env: Mapping of environment variable names to values.
        extra_patterns: Additional substring patterns to merge with defaults.

    Returns:
        A new dict with sensitive values replaced by the redaction placeholder.
    """
    patterns = (
        SENSITIVE_KEY_PATTERNS | extra_patterns
        if extra_patterns
        else SENSITIVE_KEY_PATTERNS
    )
    result: dict[str, str] = {}
    for key, value in env.items():
        key_lower = key.lower()
        if any(pattern in key_lower for pattern in patterns):
            result[key] = REDACTED_VALUE
        else:
            result[key] = value
    return result
