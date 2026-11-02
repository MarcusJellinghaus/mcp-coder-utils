"""Private process helpers shared by subprocess_runner and subprocess_streaming."""

import contextlib
import logging
import os
import signal
import subprocess
import threading
import time

# Same logger name as subprocess_runner: heartbeat output keeps its log category.
logger = logging.getLogger("mcp_coder_utils.subprocess_runner")


def _kill_process(
    process: subprocess.Popen[str], logger_instance: logging.Logger
) -> None:
    """Kill a subprocess and its children, platform-aware.

    On Unix, sends SIGTERM to the process group, waits briefly, then
    SIGKILL if the process is still alive.  On Windows, uses
    ``taskkill /F /T``.  Falls back to ``process.kill()`` on failure.

    Args:
        process: The subprocess to kill.
        logger_instance: Logger used for debug messages on fallback paths.
    """
    if os.name == "nt":
        try:
            subprocess.run(
                # taskkill is a Windows system tool, resolved via PATH by design.
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],  # noqa: S607
                capture_output=True,
                timeout=5,
                check=False,
            )
        except (subprocess.SubprocessError, OSError) as exc:
            logger_instance.debug(
                "Taskkill failed, using fallback",
                extra={"error": str(exc), "pid": process.pid},
            )
            process.kill()
    else:
        try:
            if (
                hasattr(os, "killpg")
                and hasattr(os, "getpgid")
                and hasattr(signal, "SIGTERM")
                and hasattr(signal, "SIGKILL")
            ):
                os.killpg(  # type: ignore[attr-defined,unused-ignore]
                    os.getpgid(process.pid),  # type: ignore[attr-defined,unused-ignore]
                    signal.SIGTERM,  # type: ignore[attr-defined,unused-ignore]
                )
                time.sleep(0.5)
                if process.poll() is None:
                    os.killpg(  # type: ignore[attr-defined,unused-ignore]
                        os.getpgid(process.pid),  # type: ignore[attr-defined,unused-ignore]
                        signal.SIGKILL,  # type: ignore[attr-defined,unused-ignore]
                    )
            else:
                process.kill()
        except (OSError, ProcessLookupError, AttributeError) as exc:
            logger_instance.debug(
                "Process group kill failed, using fallback",
                extra={"error": str(exc), "pid": process.pid},
            )
            process.kill()

    with contextlib.suppress(subprocess.TimeoutExpired):
        process.wait(timeout=2)


def _run_heartbeat(
    stop_event: threading.Event,
    interval: int,
    message: str,
    start_time: float,
) -> None:
    """Heartbeat loop — runs in a daemon thread, logs at regular intervals."""
    while not stop_event.wait(interval):
        elapsed = time.time() - start_time
        minutes, seconds = divmod(int(elapsed), 60)
        logger.info("%s (elapsed: %dm %ds)", message, minutes, seconds)
