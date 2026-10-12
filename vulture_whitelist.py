"""Vulture whitelist — declare false-positive unused symbols here.

Vulture flags symbols it cannot prove are used (e.g. fixtures, dynamic
attribute access). Reference them in this file to suppress the warning
without disabling the check globally.
"""

# Mock .side_effect assignments are used by unittest.mock at runtime
from unittest.mock import MagicMock
MagicMock.side_effect  # noqa

# Dynamic attributes set on LogRecord in tests (read by formatter)
import logging
logging.LogRecord.custom_field  # noqa
logging.LogRecord.user_id  # noqa
logging.LogRecord.request_id  # noqa
logging.LogRecord.action  # noqa

# Public toolkit dataclass fields, read by downstream consumers
from mcp_coder_utils.toolkit import ActionRequest, ActionResult, Finding
Finding.rule  # noqa
Finding.severity  # noqa
ActionRequest.depth  # noqa
ActionRequest.project_dir  # noqa
ActionResult.summary  # noqa

