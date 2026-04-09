"""Redaction utilities for sanitising sensitive data before logging."""

from typing import Any

__all__ = ["redact_for_logging", "REDACTED_VALUE", "RedactableDict"]

# Type alias for dictionaries that can have string or tuple keys
# Used by redact_for_logging to handle get_config_values() return format
RedactableDict = dict[str | tuple[str, ...], Any]

# Redaction placeholder for sensitive values
REDACTED_VALUE = "***"


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
