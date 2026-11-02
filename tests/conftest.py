import os
import tempfile
import time
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    import gc

    tmp_dir_obj = tempfile.TemporaryDirectory()
    tmp_path = Path(tmp_dir_obj.name)

    try:
        yield tmp_path
    finally:
        # Force garbage collection and add delay on Windows to ensure file handles are released
        if os.name == "nt":
            gc.collect()
            time.sleep(0.5)  # Give Windows time to release file handles

        # Try to clean up, but ignore errors on Windows
        try:
            tmp_dir_obj.cleanup()
        except (PermissionError, OSError) as e:
            if os.name == "nt":
                # This is expected on Windows sometimes
                import warnings

                warnings.warn(
                    f"Could not clean up temp directory {tmp_path}: {e}",
                    stacklevel=2,
                )
            else:
                raise
