"""Vulture whitelist — declare false-positive unused symbols here.

Vulture flags symbols it cannot prove are used (e.g. fixtures, dynamic
attribute access). Reference them in this file to suppress the warning
without disabling the check globally.
"""

# Mock .side_effect assignments are used by unittest.mock at runtime
from unittest.mock import MagicMock
MagicMock.side_effect  # noqa
