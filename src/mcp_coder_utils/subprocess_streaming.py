"""Subprocess streaming utilities with inactivity watchdog support.

Provides real-time line-by-line stdout streaming from subprocesses,
with an optional inactivity watchdog that kills hung processes.
"""

import logging
import os
import signal
import subprocess
import threading
import time
from collections.abc import Generator

from mcp_coder_utils.subprocess_runner import (
    CommandOptions,
    CommandResult,
    prepare_env,
)

logger = logging.getLogger(__name__)

__all__ = [
    "StreamResult",
    "stream_subprocess",
]


class StreamResult:
    """Iterator wrapper that yields stdout lines and holds the final CommandResult.

    Consume all lines before accessing ``.result`` — the result is only
    available after the generator is exhausted or the process terminates.
    """

    def __init__(self, lines: Generator[str, None, None]) -> None:
        self._lines = lines
        self._result: CommandResult | None = None

    def __iter__(self) -> "StreamResult":
        """Return the iterator object itself."""
        return self

    def __next__(self) -> str:
        """Return the next stdout line from the stream."""
        return next(self._lines)

    @property
    def result(self) -> CommandResult:
        """Return the final CommandResult after the stream is consumed.

        Raises:
            RuntimeError: If the iterator has not been fully consumed yet.
        """
        if self._result is None:
            raise RuntimeError("Result not available yet — consume all lines first.")
        return self._result


def _kill_process(process: subprocess.Popen[str]) -> None:
    """Kill a subprocess and its children, platform-aware."""
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                capture_output=True,
                timeout=5,
                check=False,
            )
        except (subprocess.SubprocessError, OSError) as exc:
            logger.debug(
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
            logger.debug(
                "Process group kill failed, using fallback",
                extra={"error": str(exc), "pid": process.pid},
            )
            process.kill()

    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass


def stream_subprocess(
    command: list[str],
    options: CommandOptions | None = None,
    inactivity_timeout_seconds: float | None = None,
) -> StreamResult:
    """Stream stdout lines from a subprocess with optional inactivity watchdog.

    Yields one line at a time (with trailing newline stripped). When the
    iterator is exhausted the caller can access the final
    :class:`CommandResult` via ``stream_result.result``.

    Args:
        command: Command and arguments as a list.
        options: Execution options (timeout_seconds in options is *not*
            used — use *inactivity_timeout_seconds* for watchdog control).
        inactivity_timeout_seconds: Kill the process if no stdout line is
            received for this many seconds.  ``None`` disables the watchdog.

    Returns:
        A :class:`StreamResult` that yields ``str`` lines and exposes
        ``.result`` after iteration.
    """
    if options is None:
        options = CommandOptions()

    def _generate() -> Generator[str, None, None]:
        env = prepare_env(command, options.env, options.env_remove)
        start_new_session = os.name != "nt"
        start_time = time.time()

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=options.cwd,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            shell=options.shell,
            start_new_session=start_new_session,
        )

        last_activity = time.time()
        watchdog_triggered = False
        stop_watchdog = threading.Event()

        def _watchdog() -> None:
            nonlocal watchdog_triggered
            while not stop_watchdog.is_set():
                if (time.time() - last_activity) > (inactivity_timeout_seconds or 0):
                    watchdog_triggered = True
                    logger.warning(
                        "Inactivity watchdog triggered",
                        extra={
                            "pid": process.pid,
                            "inactivity_timeout_seconds": inactivity_timeout_seconds,
                        },
                    )
                    _kill_process(process)
                    return
                stop_watchdog.wait(0.5)

        watchdog_thread: threading.Thread | None = None
        if inactivity_timeout_seconds is not None:
            watchdog_thread = threading.Thread(target=_watchdog, daemon=True)
            watchdog_thread.start()

        try:
            assert process.stdout is not None  # guaranteed by PIPE
            for raw_line in process.stdout:
                last_activity = time.time()
                yield raw_line.rstrip("\n").rstrip("\r")

            process.wait()

        finally:
            stop_watchdog.set()
            if watchdog_thread is not None:
                watchdog_thread.join(timeout=2)

            stderr = ""
            if process.stderr:
                try:
                    stderr = process.stderr.read()
                except (OSError, ValueError):
                    pass

            execution_time_ms = int((time.time() - start_time) * 1000)

            stream_result._result = CommandResult(  # noqa: W0212
                return_code=(
                    process.returncode if process.returncode is not None else 1
                ),
                stdout="",  # stdout was streamed line-by-line
                stderr=stderr,
                timed_out=watchdog_triggered,
                execution_error=(
                    f"Process killed due to inactivity "
                    f"(no output for {inactivity_timeout_seconds}s)"
                    if watchdog_triggered
                    else None
                ),
                command=command,
                runner_type="streaming",
                execution_time_ms=execution_time_ms,
            )

    stream_result = StreamResult(lines=_generate())
    return stream_result
